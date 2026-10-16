"""Sequential experiments. Persist evidence before treating a call as successful."""

import hashlib
import json
import os
import random
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import httpx

from callcost.measurements.energy import SCOPE, PowerCollector, baseline_assessment
from callcost.measurements.machine import command, conditions, machine_metadata
from callcost.measurements.memory import MemorySampler, peak_footprint
from callcost.measurements.swap import snapshot, swap_delta
from callcost.measurements.weights import inspect_weights
from callcost.providers.gemini import GeminiProvider
from callcost.providers.lmstudio import LMStudioProvider
from callcost.records import CallResult
from callcost.schemas import LocalConfig, Prompt
from callcost.signals import defer_termination
from callcost.storage import RunStore
from callcost.thinking import verify_cloud_thinking, verify_thinking_off
from callcost.variation import answer_hash, variation_report

PILOT = Prompt.model_validate({
    'id': 'held-out-pilot', 'task_type': 'pilot',
    'prompt': 'A box contains 7 red pencils and 5 blue pencils. How many pencils are there? '
              'End with Answer: <number>.',
    'scoring': {'type': 'numeric_final_line', 'expected': '12'},
})


def file_identity(path):
    path = Path(path).expanduser().resolve(strict=True)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}


def preflight(config):
    """Validate credentials and hash supplied weight/config files before loading anything."""
    identities = {}
    for setting in config.configurations:
        key_name = config.lmstudio.api_key_env if isinstance(setting, LocalConfig) else setting.api_key_env
        if key_name and not os.environ.get(key_name):
            raise ValueError(f'Missing credential environment variable {key_name}')
        if isinstance(setting, LocalConfig):
            identities[setting.id] = [file_identity(path) for path in setting.model_files]
    return identities


def make_provider(setting, config, client, raw_directory):
    if isinstance(setting, LocalConfig):
        key = os.environ.get(config.lmstudio.api_key_env) if config.lmstudio.api_key_env else None
        return LMStudioProvider(setting, config.lmstudio, config.run, client, key, evidence_directory=raw_directory)
    return GeminiProvider(setting, config.run, client, os.environ[setting.api_key_env])


def measured_call(provider, prompt, config, store, phase, repeat, load, files, power, baseline):
    setting = provider.configuration
    call_id = uuid.uuid4().hex
    before = conditions()
    sampler = None
    if isinstance(setting, LocalConfig):
        sampler = MemorySampler(store.directory / 'raw' / f'{call_id}.memory.jsonl',
                                config.measurement.memory_sample_ms,
                                config.measurement.lmstudio_process_ids)
        sampler.start()
    swap_before = snapshot()
    interrupted = False
    result = None
    try:
        result = provider.generate(prompt, store.directory / 'raw', call_id)
    finally:
        # Stop collection even when inference or post-response work is interrupted.
        if sampler:
            sampler.stop_event.set()
            try:
                sampler.thread.join(timeout=5)
            except KeyboardInterrupt:
                if result is None:
                    raise
                interrupted = True
    swap_after = None
    start, end = result.started_monotonic, result.ended_monotonic
    memory = energy = None
    memory_reason = 'Memory collection interrupted' if sampler else 'LM Studio process memory is not applicable to Gemini'
    energy_reason = 'Energy collection disabled or unavailable; see metadata'
    after = {'unavailable_reason': 'Post-call conditions interrupted'}
    try:
        swap_after = snapshot()
        if sampler:
            memory, memory_reason = sampler.finish(start, end)
        if power:
            energy, energy_reason = power.estimate(start, end, baseline)
        after = conditions()
    except KeyboardInterrupt:
        interrupted = True
    if interrupted:
        # A completed response remains complete even if a telemetry read is interrupted.
        result.error = 'Interrupted by user'
    swap = swap_delta(swap_before, swap_after)
    try:
        if setting.provider == 'gemini' and setting.thinking.thinking_level is not None:
            evidence = verify_cloud_thinking(result, setting.thinking.thinking_level, require_answer=phase in ('pilot', 'smoke'))
        else:
            evidence = verify_thinking_off(result, require_answer=phase in ('pilot', 'smoke'))
    except ValueError as error:
        result.status = 'error'
        result.error = result.error or str(error)
        evidence = None
    footprint, footprint_reason = peak_footprint(sampler.samples, start, end) if sampler else (None, 'Local process memory is not applicable to Gemini')
    row = dict(asdict(result), call_id=call_id, configuration_id=setting.id,
               configuration_label=getattr(setting, 'label', None) or setting.id,
               comparison_role=getattr(setting, 'comparison_role', 'cloud_reference'), provider=setting.provider,
               prompt_id=prompt.id, task_type=prompt.task_type, repeat=repeat, phase=phase,
               cache_stratum=('first_appearance' if repeat == 1 else 'repeat') if phase == 'measured' else 'excluded',
               load_id=load['load_id'] if load else None, model_files=files,
               quantisation=getattr(setting, 'expected_quantisation', None),
               memory_peak_rss_bytes=memory, memory_missing_reason=memory_reason,
               memory_peak_footprint_bytes=footprint, footprint_missing_reason=footprint_reason,
               loaded_weight_bytes=inspect_weights(setting.model_files)['tensor_payload_bytes'] if sampler else None,
               **{k: v for k, v in swap.items() if k != 'missing_reason'},
               swap_missing_reason=swap['missing_reason'],
               knee_eligible=result.status == 'completed',
               energy_j=energy, energy_missing_reason=energy_reason, energy_scope=SCOPE,
               conditions={'before': before, 'after': after}, answer_sha256=answer_hash(result.answer),
               varies_from_first_answer=None, raw_request=f'raw/{call_id}.request.json',
               raw_response=f'raw/{call_id}.response.bin')
    return row, evidence


def run_experiment(config, dataset, directory, *, pilot_only=False, client=None, input_files=None,
                   progress=print, resume=False, smoke=False, launch_metadata=None, energy_mode=None, run_pass=None):
    files = preflight(config)
    components = {s.id: inspect_weights(s.model_files)
                  for s in config.configurations if isinstance(s, LocalConfig)}
    machine = machine_metadata()
    if machine['platform'] != 'Darwin':
        raise ValueError('Milestone 1 runs are supported only on macOS')
    directory = Path(directory)
    rng = random.Random(config.run.shuffle_seed)
    settings = list(config.configurations)
    rng.shuffle(settings)
    schedule = []
    for setting in settings:
        schedule.append((setting, PILOT, 'smoke' if smoke else 'pilot', 1 if smoke else 0))
        if not pilot_only and not smoke:
            schedule.extend((setting, PILOT, 'warmup', n + 1) for n in range(config.run.warmup_runs))
            for repeat in range(1, config.run.repeats + 1):
                prompts = list(dataset.prompts)
                rng.shuffle(prompts)
                schedule.extend((setting, prompt, 'measured', repeat) for prompt in prompts)
    runtime_identity = {str(p.relative_to(Path(__file__).parent)): file_identity(p)['sha256']
                        for p in sorted(Path(__file__).parent.rglob('*.py'))}
    metadata = {'schema_version': 2, 'run_pass': run_pass, 'smoke': smoke, 'runtime_identity': runtime_identity, 'status': 'running', 'pilot_only': pilot_only,
                'started_at': datetime.now(timezone.utc).isoformat(), 'machine': machine,
                'config': config.model_dump(mode='json'), 'dataset': dataset.model_dump(mode='json'),
                'input_files': input_files or [], 'model_files': files,
                'model_weight_components': components,
                'production_reference_caveat': 'Fairy retains vision weights; encoded component bytes are not a runtime RSS subtraction or a load-time attribution'
                    if any(getattr(s, 'comparison_role', None) == 'production_reference' for s in config.configurations) else None,
                'software': {name: version(name) for name in ('callcost', 'httpx', 'pydantic', 'PyYAML', 'psutil')},
                'git': {'commit': command(['git', 'rev-parse', 'HEAD']),
                        'status': command(['git', 'status', '--porcelain'])},
                'schedule': [dict(configuration_id=s.id, prompt_id=p.id, phase=phase, repeat=r)
                             for s, p, phase, r in schedule],
                'ordering': 'seeded configuration blocks; independently shuffled prompts per repeat',
                'cache': 'No verified cache-disable API. Labels describe exposure, not proven cache state.',
                'thinking_verification': {}, 'loads': [], 'energy_blocks': [], 'errors': [], 'segments': []}
    if resume:
        previous = json.loads((directory / 'metadata.json').read_text())
        for key in ('config', 'dataset', 'model_files', 'input_files', 'runtime_identity', 'schedule', 'smoke', 'pilot_only', 'software', 'run_pass'):
            if previous.get(key) != metadata.get(key):
                raise ValueError(f'Resume refused: {key} changed since this run started')
        for key in ('chip', 'ram_bytes', 'macos_build', 'lmstudio_version'):
            if previous['machine'].get(key) != machine.get(key):
                raise ValueError(f'Resume refused: machine {key} changed')
        metadata = previous
        metadata.pop('stop_reason', None)
        metadata['status'] = 'running'
    store = RunStore(directory, resume=resume)
    rows, first_answers = list(store.rows), {}
    for row in rows:
        if row['phase'] == 'measured' and row['status'] == 'completed':
            first_answers.setdefault((row['configuration_id'], row['prompt_id']), row['answer_sha256'])
    done = {r['schedule_index'] for r in rows if r['status'] == 'completed'}
    segment = {'id': uuid.uuid4().hex, 'started_at': datetime.now(timezone.utc).isoformat(),
               'resumed': resume, 'conditions': launch_metadata,
               'energy_mode': energy_mode or config.measurement.energy.mode,
               'cache_note': 'A resumed segment reloads models; exposure labels do not prove cache state'}
    metadata['segments'].append(segment)
    current_id = None
    def status(state='running', error=None):
        store.write_status(state=state, total=len(schedule), current=current_id,
                           started_at=metadata['started_at'], error=error)
    status()
    owned_client = client is None
    client = client or httpx.Client(trust_env=False)
    provider = power = None
    try:
        if resume:
            # A hard kill may occur after the durable pilot checkpoint but before
            # its metadata update. Verify that observation again, never repeat it.
            for row in rows:
                if row['phase'] not in ('pilot', 'smoke') or row['status'] != 'completed':
                    continue
                setting = next(s for s in settings if s.id == row['configuration_id'])
                result = CallResult(**{key: row[key] for key in CallResult.__dataclass_fields__ if key in row})
                if setting.provider == 'gemini' and setting.thinking.thinking_level is not None:
                    evidence = verify_cloud_thinking(result, setting.thinking.thinking_level)
                else:
                    evidence = verify_thinking_off(result)
                metadata['thinking_verification'][setting.id] = dict(
                    evidence, call_id=row['call_id'],
                    method='reasoning: off' if isinstance(setting, LocalConfig) else
                            f'thinkingConfig.thinkingLevel: {setting.thinking.thinking_level}' if setting.thinking.thinking_level else 'thinkingConfig.thinkingBudget: 0')
        store.write_metadata(metadata)
        if resume:
            recover_owned_instances(metadata, config, client, store.directory / 'raw')
        for setting in settings:
            if not any(i not in done and item[0].id == setting.id for i, item in enumerate(schedule)):
                continue
            current_id = setting.id
            status()
            progress(f'{setting.id}: preparing model and thinking-control pilot', flush=True)
            provider = make_provider(setting, config, client, store.directory / 'raw')
            # Finish recording an accepted load before delivering a terminal signal.
            with defer_termination():
                load = provider.prepare()
                if load:
                    metadata['loads'].append(load)
                    store.write_metadata(metadata)
            baseline = None
            energy_block = {'configuration_id': setting.id, 'segment_id': segment['id'],
                            'scope': SCOPE, 'mode': segment['energy_mode']}
            metadata['energy_blocks'].append(energy_block)
            for index, (current, prompt, phase, repeat) in enumerate(schedule):
                if current.id != setting.id or index in done:
                    continue
                # Instrument energy after pilot/warm-up, with a loaded idle model baseline.
                if phase in ('measured', 'smoke') and 'attempted' not in energy_block:
                    energy_block['attempted'] = True
                    energy = config.measurement.energy
                    if energy_block['mode'] != 'off':
                        power = PowerCollector(store.directory / 'raw' / f'{setting.id}.{segment["id"]}.power', energy.sample_ms)
                        if power.start():
                            baseline = power.baseline(energy.idle_baseline_seconds)
                        energy_block['baseline_watts'] = baseline
                        energy_block['errors'] = list(power.errors)
                        if baseline is None:
                            energy_block['unavailable_reason'] = 'Power samples or idle baseline unavailable; inspect raw stderr'
                            power.close()
                            power = None
                            if energy_block['mode'] == 'required_powermetrics':
                                raise ValueError('Required energy collection unavailable')
                    store.write_metadata(metadata)
                progress(f'{setting.id}: {phase} {prompt.id}, repeat {repeat}', flush=True)
                row, evidence = measured_call(provider, prompt, config, store, phase, repeat, load,
                                              files.get(setting.id), power, baseline)
                if phase == 'measured' and row['status'] == 'completed':
                    key = (setting.id, prompt.id)
                    first_answers.setdefault(key, row['answer_sha256'])
                    row['varies_from_first_answer'] = row['answer_sha256'] != first_answers[key]
                row['schedule_index'] = index
                row['segment_id'] = segment['id']
                with defer_termination():
                    store.append_call(row)
                    rows.append(row)
                    status()
                    if phase in ('pilot', 'smoke') and evidence is not None:
                        metadata['thinking_verification'][setting.id] = dict(
                            evidence, call_id=row['call_id'],
                            method='reasoning: off' if isinstance(setting, LocalConfig) else
                                    f'thinkingConfig.thinkingLevel: {setting.thinking.thinking_level}' if setting.thinking.thinking_level else 'thinkingConfig.thinkingBudget: 0')
                        store.write_metadata(metadata)
                if row['error'] == 'Interrupted by user':
                    raise KeyboardInterrupt
                if row['status'] != 'completed':
                    if setting.provider == 'gemini' and (row.get('http_status') == 429 or row.get('provider_error_status') == 'RESOURCE_EXHAUSTED'):
                        metadata['stop_reason'] = 'quota_or_rate_limit'
                        raise ValueError('Cloud quota/rate-limit reached; stopped with no automatic retry. Resolve quota before manually resuming.')
                    raise ValueError(f'Call {row["call_id"]} failed: {row["error"]}')
                if config.run.cooldown_seconds:
                    time.sleep(config.run.cooldown_seconds)
            if power:
                energy_block['post_baseline_watts'] = power.baseline(config.measurement.energy.idle_baseline_seconds)
                energy_block['errors'] = list(power.errors)
                energy_block['assessment'] = baseline_assessment(
                    baseline, energy_block['post_baseline_watts'],
                    [r for r in rows if r['configuration_id'] == setting.id and r['segment_id'] == segment['id']])
                power.close()
                power = None
            provider.close()
            provider = None
        metadata['status'] = 'completed'
    except (Exception, KeyboardInterrupt) as error:
        metadata['status'] = ('interrupted' if isinstance(error, KeyboardInterrupt) else
                              'rate_limited' if metadata.get('stop_reason') == 'quota_or_rate_limit' else 'failed')
        # Avoid including HTTP exception text, which may include secret headers/URLs.
        metadata['errors'].append(str(error) if isinstance(error, ValueError) else type(error).__name__)
    finally:
        for resource in (power, provider):
            if resource:
                try:
                    resource.close()
                except Exception as error:
                    metadata['errors'].append(f'Cleanup failed: {type(error).__name__}')
                    metadata['status'] = 'failed'
        for block in metadata['energy_blocks']:
            if 'assessment' not in block:
                block['assessment'] = baseline_assessment(block.get('baseline_watts'), None,
                    [r for r in rows if r['configuration_id'] == block['configuration_id'] and r['segment_id'] == block['segment_id']])
        metadata['finished_at'] = datetime.now(timezone.utc).isoformat()
        segment['finished_at'] = metadata['finished_at']
        segment['status'] = metadata['status']
        status(metadata['status'],
               None if metadata['status'] == 'completed' else metadata['errors'][-1])
        metadata['variation'] = variation_report(config, dataset, rows)
        metadata['completed_measured_calls'] = sum(r['phase'] == 'measured' and r['status'] == 'completed' for r in rows)
        store.write_metadata(metadata)
        store.close()
        if owned_client:
            client.close()
    return metadata


def recover_owned_instances(metadata, config, client, raw_directory):
    """Only unload a precisely recorded instance left by this interrupted run."""
    if not metadata['loads']:
        return
    key = os.environ.get(config.lmstudio.api_key_env) if config.lmstudio.api_key_env else None
    headers = {'Authorization': f'Bearer {key}'} if key else {}
    response = client.get(config.lmstudio.base_url + '/api/v1/models', headers=headers, timeout=10)
    response.raise_for_status()
    known = {(load['load_request_key'], load['instance_id']) for load in metadata['loads']}
    loaded = [(model['key'], instance['id']) for model in response.json()['models']
              for instance in model.get('loaded_instances', [])]
    if any(pair not in known for pair in loaded):
        raise ValueError('Unrecorded LM Studio instance is loaded; unload it explicitly before resuming')
    for model_key, instance_id in loaded:
        response = client.post(config.lmstudio.base_url + '/api/v1/models/unload', headers=headers,
                               json={'instance_id': instance_id}, timeout=config.run.timeout_seconds)
        prefix = raw_directory / f'resume-unload-{uuid.uuid4().hex}'
        prefix.with_suffix('.json').write_text(json.dumps({'model_key': model_key, 'instance_id': instance_id,
                                                         'http_status': response.status_code}))
        prefix.with_suffix('.response.bin').write_bytes(response.content)
        response.raise_for_status()
