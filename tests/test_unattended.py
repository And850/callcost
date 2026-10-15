import httpx
import pytest

from callcost.schemas import Config


def test_preflight_missing_key_does_not_start_server_or_create_output(tmp_path, config_data, monkeypatch):
    from callcost.unattended import environment_preflight
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    with httpx.Client(transport=httpx.MockTransport(lambda r: pytest.fail('HTTP before credential validation'))) as client:
        with pytest.raises(ValueError, match='GEMINI_API_KEY'):
            environment_preflight(Config.model_validate(config_data), tmp_path, client, require_five=False)
    assert not list(tmp_path.iterdir())


def test_preflight_rejects_low_ram_before_loading_any_model(tmp_path, config_data, monkeypatch):
    from callcost.unattended import environment_preflight
    monkeypatch.setenv('GEMINI_API_KEY', 'key')
    monkeypatch.setattr('callcost.unattended.conditions', lambda: {'ac_power': True, 'available_memory_bytes': 10})
    with httpx.Client(transport=httpx.MockTransport(lambda r: pytest.fail('HTTP before RAM validation'))) as client:
        with pytest.raises(ValueError, match='memory'):
            environment_preflight(Config.model_validate(config_data), tmp_path, client, require_five=False)


def test_report_excludes_swapped_calls_from_knee_but_keeps_all_calls(tmp_path):
    from callcost.report import aggregate
    rows = [dict(status='completed', phase='measured', configuration_id='a', task_type='maths',
                 prompt_id='p', call_id=str(i), cache_stratum='repeat', latency_s=t, swapping_occurred=swap,
                 memory_peak_footprint_bytes=100, loaded_weight_bytes=50)
            for i, (t, swap) in enumerate([(1, False), (3, False), (100, True), (200, None)])]
    result = aggregate(rows)
    assert len(result) == 2  # Combined observations and repeat-only stratum.
    assert result[0]['latency_s']['p50'] == 51.5
    assert result[0]['latency_s']['p95'] == 200
    assert result[0]['knee_eligible']['latency_s']['p50'] == 2
    assert result[0]['swapped_calls'] == 1 and result[0]['swap_unknown_calls'] == 1
    assert result[0]['knee_eligible']['calls'] == 2


def test_latest_pointer_cannot_escape_runs_directory(tmp_path):
    from callcost.unattended import latest_run
    (tmp_path / 'LATEST').write_text('../private')
    with pytest.raises(ValueError, match='LATEST'):
        latest_run(tmp_path)
