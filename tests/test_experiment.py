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
