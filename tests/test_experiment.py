import csv
import json

import httpx
import pytest

from callcost.experiment import run_experiment
from callcost.schemas import Config, Dataset


def response(answer, thoughts=0):
    return {'candidates': [{'content': {'parts': [{'text': answer}]}, 'finishReason': 'STOP'}],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 3,
                              'thoughtsTokenCount': thoughts, 'totalTokenCount': 13 + thoughts}}


def test_run_preserves_schedule_and_exact_variation(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'private-test-key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', lambda: {'ac_power': True})
    config_data['measurement'] = {'energy': {'mode': 'off'}}
    count = 0

    def handler(request):
        nonlocal count
        count += 1
        answer = 'Answer: 4' if count != 6 else 'Answer: 4\n'
        return httpx.Response(200, stream=httpx.ByteStream(('data: ' + json.dumps(response(answer)) + '\n\n').encode()))

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        meta = run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data),
                              tmp_path / 'run', client=client)
    assert count == 8  # pilot + two warm-ups + five measured calls
    rows = list(csv.DictReader((tmp_path / 'run/calls.csv').open()))
    measured = [row for row in rows if row['phase'] == 'measured']
    assert [int(row['repeat']) for row in measured] == [1, 2, 3, 4, 5]
    assert [row['cache_stratum'] for row in measured] == ['first_appearance'] + ['repeat'] * 4
    assert meta['status'] == 'completed'
    assert meta['variation']['summary'][0]['varying_prompts'] == 1
    assert meta['variation']['summary'][0]['compared_prompts'] == 1
    assert meta['thinking_verification']['cloud']['verified']
    assert 'private-test-key' not in (tmp_path / 'run/metadata.json').read_text()
    assert all(row['energy_j'] == '' for row in rows)


def test_bad_pilot_keeps_partial_evidence_and_stops(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'private-test-key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', lambda: {})
    config_data['measurement'] = {'energy': {'mode': 'off'}}
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(
            200, stream=httpx.ByteStream(('data: ' + json.dumps(response('Answer: 4', 2)) + '\n\n').encode())))) as client:
        meta = run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data),
                              tmp_path / 'run', client=client)
    assert meta['status'] == 'failed'
    rows = list(csv.DictReader((tmp_path / 'run/calls.csv').open()))
    assert len(rows) == 1 and rows[0]['phase'] == 'pilot' and rows[0]['status'] == 'error'
    assert meta['variation']['summary'][0]['uncomparable_prompts'] == 1


def test_missing_credentials_does_not_create_run(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    with pytest.raises(ValueError, match='credential'):
        run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data), tmp_path / 'run')
    assert not (tmp_path / 'run').exists()


def test_interrupt_retains_partial_call_identity(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', dict)
    class Interrupted(httpx.SyncByteStream):
        def __iter__(self):
            yield ('data: ' + json.dumps(response('partial')) + '\n\n').encode()
            raise KeyboardInterrupt
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=Interrupted()))) as client:
        meta = run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data),
                              tmp_path / 'run', client=client)
    rows = list(csv.DictReader((tmp_path / 'run/calls.csv').open()))
    assert meta['status'] == 'interrupted'
    assert len(rows) == 1
    assert rows[0]['configuration_id'] == 'cloud' and rows[0]['answer'] == 'partial'
    assert rows[0]['status'] == 'error'


def test_two_configurations_keep_five_repeats_per_prompt_and_empty_quality_outcome(tmp_path, config_data, prompt_data, monkeypatch):
    from copy import deepcopy
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', dict)
    config_data['measurement'] = {'energy': {'mode': 'off'}}
    second = deepcopy(config_data['configurations'][0])
    second['id'] = 'second'
    config_data['configurations'].append(second)
    prompt = deepcopy(prompt_data['prompts'][0])
    prompt['id'] = 'math-2'
    prompt_data['prompts'].append(prompt)
    count = 0
    def handle(request):
        nonlocal count
        count += 1
        # Pilots are nonempty; empty measured text is an observable quality outcome.
        text = '' if count == 5 else 'Answer: 4'
        return httpx.Response(200, stream=httpx.ByteStream(('data: ' + json.dumps(response(text)) + '\n\n').encode()))
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        meta = run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data),
                              tmp_path / 'run', client=client)
    assert meta['status'] == 'completed' and count == 26
    assert meta['completed_measured_calls'] == 20
    assert all(group['completed_calls'] == 5 for group in meta['variation']['groups'])
    rows = list(csv.DictReader((tmp_path / 'run/calls.csv').open()))
    empty = [r for r in rows if r['phase'] == 'measured' and r['answer'] == '']
    assert len(empty) == 1 and empty[0]['status'] == 'completed'


def test_interrupt_after_provider_completion_preserves_csv(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    observed = 0
    def interrupted_conditions():
        nonlocal observed
        observed += 1
        if observed == 2:
            raise KeyboardInterrupt
        return {}
    monkeypatch.setattr('callcost.experiment.conditions', interrupted_conditions)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, stream=httpx.ByteStream(
            ('data: ' + json.dumps(response('Answer: 4')) + '\n\n').encode())))) as client:
        meta = run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data),
                              tmp_path / 'run', client=client)
    rows = list(csv.DictReader((tmp_path / 'run/calls.csv').open()))
    assert meta['status'] == 'interrupted'
    assert len(rows) == 1 and rows[0]['answer'] == 'Answer: 4'
    assert rows[0]['thinking_tokens'] == '0'


def test_resume_skips_completed_slots_preserves_failed_attempt_and_status(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', dict)
    config_data['measurement'] = {'energy': {'mode': 'off'}}
    config_data['run'] = {'warmup_runs': 0}
    count = 0
    class Interrupted(httpx.SyncByteStream):
        def __iter__(self):
            raise KeyboardInterrupt
            yield b''
    def handler(request):
        nonlocal count
        count += 1
        return httpx.Response(200, stream=Interrupted() if count == 3 else httpx.ByteStream(
            ('data: ' + json.dumps(response('Answer: 4')) + '\n\n').encode()))
    config, dataset = Config.model_validate(config_data), Dataset.model_validate(prompt_data)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = run_experiment(config, dataset, tmp_path / 'run', client=client)
        assert first['status'] == 'interrupted'
        assert json.loads((tmp_path / 'run/status.json').read_text())['calls_done'] == 2
        final = run_experiment(config, dataset, tmp_path / 'run', client=client, resume=True)
    assert final['status'] == 'completed' and count == 7
    records = [json.loads(p.read_text()) for p in sorted((tmp_path / 'run/checkpoints').glob('*.json'))]
    assert [r['schedule_index'] for r in records if r['status'] == 'completed'] == [0, 1, 2, 3, 4, 5]
    assert sum(r['status'] == 'error' for r in records) == 1
    status = json.loads((tmp_path / 'run/status.json').read_text())
    assert status['state'] == 'completed' and status['calls_done'] == status['calls_total'] == 6
    assert len(final['segments']) == 2
    config.run.max_output_tokens += 1
    with pytest.raises(ValueError, match='changed'):
        run_experiment(config, dataset, tmp_path / 'run', resume=True)


def test_interrupt_in_post_call_swap_snapshot_does_not_repeat_finished_inference(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', dict)
    calls = 0
    snapshots = 0
    def snapshot():
        nonlocal snapshots
        snapshots += 1
        if snapshots == 2:
            raise KeyboardInterrupt
        return None
    monkeypatch.setattr('callcost.experiment.snapshot', snapshot)
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, stream=httpx.ByteStream(('data: ' + json.dumps(response('Answer: 4')) + '\n\n').encode()))
    config_data['measurement'] = {'energy': {'mode': 'off'}}
    config = Config.model_validate(config_data)
    dataset = Dataset.model_validate(prompt_data)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = run_experiment(config, dataset, tmp_path / 'run', client=client)
        assert first['status'] == 'interrupted'
        saved = [json.loads(p.read_text()) for p in (tmp_path / 'run/checkpoints').glob('*.json')]
        assert len(saved) == 1 and saved[0]['status'] == 'completed'
        final = run_experiment(config, dataset, tmp_path / 'run', client=client, resume=True)
    assert calls == 8 and final['status'] == 'completed'


def test_resume_recovers_pilot_verification_without_repeating_completed_call(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', dict)
    config_data['measurement'] = {'energy': {'mode': 'off'}}
    config_data['run'] = {'warmup_runs': 0}
    config = Config.model_validate(config_data)
    dataset = Dataset.model_validate(prompt_data)
    count = 0

    def handler(request):
        nonlocal count
        count += 1
        return httpx.Response(200, stream=httpx.ByteStream(
            ('data: ' + json.dumps(response('Answer: 4')) + '\n\n').encode()))

    directory = tmp_path / 'run'
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        run_experiment(config, dataset, directory, client=client, pilot_only=True)
        metadata = json.loads((directory / 'metadata.json').read_text())
        pilot = next((directory / 'checkpoints').glob('*.json'))
        pilot_id = json.loads(pilot.read_text())['call_id']
        # Reproduce death after pilot checkpoint but before its metadata update.
        metadata['thinking_verification'] = {}
        metadata['status'] = 'running'
        (directory / 'metadata.json').write_text(json.dumps(metadata))
        resumed = run_experiment(config, dataset, directory, client=client, pilot_only=True, resume=True)
    assert resumed['status'] == 'completed'
    assert count == 1
    assert resumed['thinking_verification']['cloud']['verified'] is True
    assert resumed['thinking_verification']['cloud']['call_id'] == pilot_id


def test_cloud_quota_stops_with_checkpoint_and_no_retry(tmp_path, config_data, prompt_data, monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    monkeypatch.setattr('callcost.experiment.conditions', dict)
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(429, stream=httpx.ByteStream(json.dumps(
            {'error': {'status': 'RESOURCE_EXHAUSTED', 'message': 'quota exceeded'}}).encode()))

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        meta = run_experiment(Config.model_validate(config_data), Dataset.model_validate(prompt_data),
                              tmp_path/'run', client=client)
    assert len(requests) == 1
    assert meta['status'] == 'rate_limited'
    state = json.loads((tmp_path/'run/status.json').read_text())
    assert state['state'] == 'rate_limited' and 'no automatic retry' in state['error']
    row = json.loads(next((tmp_path/'run/checkpoints').glob('*.json')).read_text())
    assert row['http_status'] == 429 and row['provider_error_status'] == 'RESOURCE_EXHAUSTED'
    assert row['status'] == 'error'
