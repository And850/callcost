from pathlib import Path

from callcost.schemas import Config, Dataset, load_document


def test_precheck_schedule_is_six_held_out_calls_and_full_passes_keep_registered_counts():
    from callcost.experiment import PILOT, build_schedule
    from callcost.unattended import select_pass
    config = Config.model_validate(load_document(Path('configs/experiment.yaml')))
    dataset = Dataset.model_validate(dict(schema_version=1, prompts=
        load_document(Path('datasets/gsm8k/prompts.json'))['prompts'] +
        load_document(Path('prompts/summarisation.yaml'))['prompts']))
    local = select_pass(config, 'local')
    cloud = select_pass(config, 'cloud')
    precheck = select_pass(config, 'precheck')
    assert len(config.configurations) == 6
    assert len(build_schedule(local, dataset)[1]) == 1015
    assert len(build_schedule(cloud, dataset)[1]) == 203
    _, schedule = build_schedule(precheck, dataset, precheck=True)
    assert len(schedule) == 6
    assert {s.id for s, _, _, _ in schedule} == {'local-q8', 'local-q3'}
    assert all(p == PILOT and phase == 'precheck' for _, p, phase, _ in schedule)
    for identifier in ('local-q8', 'local-q3'):
        assert [repeat for s, _, _, repeat in schedule if s.id == identifier] == [1, 2, 3]


def test_idle_observation_preserves_swap_readings_and_duration(monkeypatch):
    from callcost.precheck import observe_idle
    clock = [10.0]
    before = dict(page_size=16384, swapins=2, swapouts=3, pageouts=0,
                  swap_used_bytes=0, compressed_memory_bytes=100)
    after = dict(before, swapins=3)
    readings = iter([before, after])
    monkeypatch.setattr('callcost.precheck.snapshot', lambda: next(readings))
    monkeypatch.setattr('callcost.precheck.time.perf_counter', lambda: clock[0])
    monkeypatch.setattr('callcost.precheck.time.sleep', lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    result = observe_idle('loaded-before', 120, lambda *args, **kwargs: None)
    assert result['duration_s'] == 120
    assert result['swapins_bytes'] == 16384
    assert result['swapouts_bytes'] == 0
    assert result['swap_snapshot_before'] == before
    assert result['swap_snapshot_after'] == after


def test_precheck_validation_requires_energy_and_idle_observations_after_last_checkpoint():
    from callcost.precheck import REQUIRED_SWAP_FIELDS, assess_precheck
    rows = [dict(configuration_id='local-q8', segment_id='s', phase='precheck', status='completed', energy_j=1,
                 **dict.fromkeys(REQUIRED_SWAP_FIELDS, 0))
            for _ in range(3)]
    block = dict(configuration_id='local-q8', segment_id='s', baseline_watts=1, post_baseline_watts=1, errors=[])
    windows = [dict(label=label, configuration_id=None if label=='unloaded' else 'local-q8',
                    segment_id='s', **dict.fromkeys(REQUIRED_SWAP_FIELDS, 0)) for label in ('unloaded', 'loaded-before')]
    assert assess_precheck(rows, [block], windows, ['local-q8'])['valid'] is False
    windows.append(dict(label='loaded-after', configuration_id='local-q8', segment_id='s', **dict.fromkeys(REQUIRED_SWAP_FIELDS, 0)))
    assert assess_precheck(rows, [block], windows, ['local-q8'])['valid'] is True
    rows[0]['energy_j'] = None
    assert assess_precheck(rows, [block], windows, ['local-q8'])['valid'] is False
    rows[0]['energy_j'] = 1
    block['post_baseline_watts'] = None
    assert assess_precheck(rows, [block], windows, ['local-q8'])['valid'] is False
    block['post_baseline_watts'] = 1
    rows[0]['swap_used_before_bytes'] = None
    assert assess_precheck(rows, [block], windows, ['local-q8'])['valid'] is False
    rows[0]['swap_used_before_bytes'] = 0
    windows[0]['compressed_memory_after_bytes'] = None
    assert assess_precheck(rows, [block], windows, ['local-q8'])['valid'] is False


def test_precheck_preserves_response_but_stops_before_next_call_if_energy_missing(tmp_path, monkeypatch):
    import json
    from dataclasses import asdict

    from callcost.experiment import PILOT, run_experiment
    from callcost.records import CallResult

    file = tmp_path/'model.json'
    file.write_text('{}')
    config = Config.model_validate(dict(schema_version=1, configurations=[dict(
        id='local-q8', provider='lmstudio', model_key='fake', expected_quantisation='8bit', model_files=[str(file)])]))
    config.measurement.energy.mode = 'required_powermetrics'
    monkeypatch.setattr('callcost.experiment.machine_metadata', lambda: {'platform': 'Darwin'})
    from callcost.precheck import REQUIRED_SWAP_FIELDS
    monkeypatch.setattr('callcost.experiment.observe_idle', lambda label, **kwargs: dict(
        label=label, duration_s=120, **dict.fromkeys(REQUIRED_SWAP_FIELDS, 0)))
    class Provider:
        def prepare(self):
            return None
        def close(self):
            pass
    class Power:
        errors = []
        def __init__(self, *args):
            pass
        def start(self):
            return True
        def baseline(self, seconds):
            return 1
        def close(self):
            pass
    monkeypatch.setattr('callcost.experiment.make_provider', lambda *args: Provider())
    monkeypatch.setattr('callcost.experiment.PowerCollector', Power)
    count = []
    def call(provider, prompt, config, store, phase, repeat, *args):
        count.append(repeat)
        return dict(asdict(CallResult(status='completed', answer='Answer: 12', thinking_tokens=0)),
                    call_id=f'{repeat:032d}', phase=phase, configuration_id='local-q8',
                    prompt_id=PILOT.id, task_type='pilot', repeat=repeat, cache_stratum='excluded', energy_j=None), {'verified': True}
    monkeypatch.setattr('callcost.experiment.measured_call', call)
    meta = run_experiment(config, Dataset(schema_version=1, prompts=[PILOT]), tmp_path/'run', precheck=True)
    assert count == [1]
    assert meta['status'] == 'failed'
    assert any('Required pre-check energy' in e for e in meta['errors'])
    row = json.loads(next((tmp_path/'run/checkpoints').glob('*.json')).read_text())
    assert row['status'] == 'completed' and row['energy_j'] is None
