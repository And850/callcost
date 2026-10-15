"""Sequential experiments. Persist evidence before treating a call as successful."""

import hashlib
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
from callcost.schemas import LocalConfig, Prompt
from callcost.storage import RunStore
from callcost.thinking import verify_thinking_off
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
    swap_after = snapshot()
    swap = swap_delta(swap_before, swap_after)
    start, end = result.started_monotonic, result.ended_monotonic
    memory = energy = None
    memory_reason = 'Memory collection interrupted' if sampler else 'LM Studio process memory is not applicable to Gemini'
    energy_reason = 'Energy collection disabled or unavailable; see metadata'
    after = {'unavailable_reason': 'Post-call conditions interrupted'}
    try:
        if sampler:
            memory, memory_reason = sampler.finish(start, end)
        if power:
            energy, energy_reason = power.estimate(start, end, baseline)
        after = conditions()
    except KeyboardInterrupt:
        interrupted = True
    if interrupted:
        result.status = 'error'
        result.error = 'Interrupted by user'
    try:
        evidence = verify_thinking_off(result, require_answer=phase == 'pilot')
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
               knee_eligible=result.status == 'completed' and swap['swapping_occurred'] is False,
               energy_j=energy, energy_missing_reason=energy_reason, energy_scope=SCOPE,
               conditions={'before': before, 'after': after}, answer_sha256=answer_hash(result.answer),
               varies_from_first_answer=None, raw_request=f'raw/{call_id}.request.json',
               raw_response=f'raw/{call_id}.response.bin')
    return row, evidence


def run_experiment(config, dataset, directory, *, pilot_only=False, client=None, input_files=None,
                   progress=print):
    files = preflight(config)
    components = {s.id: inspect_weights(s.model_files)
                  for s in config.configurations if isinstance(s, LocalConfig)}
    machine = machine_metadata()
    if machine['platform'] != 'Darwin':
        raise ValueError('Milestone 1 runs are supported only on macOS')
    store = RunStore(Path(directory))
    rng = random.Random(config.run.shuffle_seed)
    settings = list(config.configurations)
    rng.shuffle(settings)
    schedule = []
    for setting in settings:
        schedule.append((setting, PILOT, 'pilot', 0))
        if not pilot_only:
            schedule.extend((setting, PILOT, 'warmup', n + 1) for n in range(config.run.warmup_runs))
            for repeat in range(1, config.run.repeats + 1):
                prompts = list(dataset.prompts)
                rng.shuffle(prompts)
                schedule.extend((setting, prompt, 'measured', repeat) for prompt in prompts)
    metadata = {'schema_version': 1, 'status': 'running', 'pilot_only': pilot_only,
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
                'thinking_verification': {}, 'loads': [], 'energy_blocks': [], 'errors': []}
    rows, first_answers = [], {}
    owned_client = client is None
    client = client or httpx.Client(trust_env=False)
    provider = power = None
    try:
        store.write_metadata(metadata)
        for setting in settings:
            progress(f'{setting.id}: preparing model and thinking-off pilot', flush=True)
            provider = make_provider(setting, config, client, store.directory / 'raw')
            load = provider.prepare()
            if load:
                metadata['loads'].append(load)
                store.write_metadata(metadata)
            baseline = None
            energy_block = {'configuration_id': setting.id, 'scope': SCOPE, 'mode': config.measurement.energy.mode}
            metadata['energy_blocks'].append(energy_block)
            for current, prompt, phase, repeat in schedule:
                if current.id != setting.id:
                    continue
                # Instrument energy after pilot/warm-up, with a loaded idle model baseline.
                if phase == 'measured' and 'attempted' not in energy_block:
                    energy_block['attempted'] = True
                    energy = config.measurement.energy
                    if energy.mode != 'off':
                        power = PowerCollector(store.directory / 'raw' / f'{setting.id}.power', energy.sample_ms)
                        if power.start():
                            baseline = power.baseline(energy.idle_baseline_seconds)
                        energy_block['baseline_watts'] = baseline
                        energy_block['errors'] = list(power.errors)
                        if baseline is None:
                            energy_block['unavailable_reason'] = 'Power samples or idle baseline unavailable; inspect raw stderr'
                            power.close()
                            power = None
                            if energy.mode == 'required_powermetrics':
                                raise ValueError('Required energy collection unavailable')
                    store.write_metadata(metadata)
                progress(f'{setting.id}: {phase} {prompt.id}, repeat {repeat}', flush=True)
                row, evidence = measured_call(provider, prompt, config, store, phase, repeat, load,
                                              files.get(setting.id), power, baseline)
                if phase == 'measured' and row['status'] == 'completed':
                    key = (setting.id, prompt.id)
                    first_answers.setdefault(key, row['answer_sha256'])
                    row['varies_from_first_answer'] = row['answer_sha256'] != first_answers[key]
                store.append_call(row)
                rows.append(row)
                if row['error'] == 'Interrupted by user':
                    raise KeyboardInterrupt
                if row['status'] != 'completed':
                    raise ValueError(f'Call {row["call_id"]} failed: {row["error"]}')
                if phase == 'pilot':
                    metadata['thinking_verification'][setting.id] = dict(
                        evidence, call_id=row['call_id'],
                        method='reasoning: off' if isinstance(setting, LocalConfig) else 'thinkingConfig.thinkingBudget: 0')
                    store.write_metadata(metadata)
                if config.run.cooldown_seconds:
                    time.sleep(config.run.cooldown_seconds)
            if power:
                energy_block['post_baseline_watts'] = power.baseline(config.measurement.energy.idle_baseline_seconds)
                energy_block['errors'] = list(power.errors)
                energy_block['assessment'] = baseline_assessment(
                    baseline, energy_block['post_baseline_watts'],
                    [r for r in rows if r['configuration_id'] == setting.id])
                power.close()
                power = None
            provider.close()
            provider = None
        metadata['status'] = 'completed'
    except (Exception, KeyboardInterrupt) as error:
        metadata['status'] = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'failed'
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
                    [r for r in rows if r['configuration_id'] == block['configuration_id']])
        metadata['finished_at'] = datetime.now(timezone.utc).isoformat()
        metadata['variation'] = variation_report(config, dataset, rows)
        metadata['completed_measured_calls'] = sum(r['phase'] == 'measured' and r['status'] == 'completed' for r in rows)
        store.write_metadata(metadata)
        store.close()
        if owned_client:
            client.close()
    return metadata
