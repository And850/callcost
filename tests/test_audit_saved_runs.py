import hashlib
import importlib.util
import json
from pathlib import Path


def test_completed_human_review_is_not_reported_pending(tmp_path):
    path = Path(__file__).resolve().parents[1] / 'scripts/audit_saved_runs.py'
    spec = importlib.util.spec_from_file_location('audit_saved_runs', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    run = tmp_path / 'run'
    (run / 'checkpoints').mkdir(parents=True)
    prompt = dict(id='s', task_type='summarisation', scoring={'type': 'checklist', 'items': [
        {'id': 'length', 'automatic': {'type': 'max_words', 'value': 3}},
        {'id': 'faithful', 'human': True}]})
    schedule = [dict(configuration_id='cloud', prompt_id='s', phase='measured', repeat=i) for i in range(1, 6)]
    meta = dict(status='completed', errors=[], config={'configurations': [dict(id='cloud', comparison_role='cloud_reference')]},
                dataset={'prompts': [prompt]}, schedule=schedule)
    (run / 'metadata.json').write_text(json.dumps(meta))
    scores = {}
    for i in range(5):
        row = dict(call_id=str(i), configuration_id='cloud', prompt_id='s', task_type='summarisation',
                   phase='measured', status='completed', answer='summary', schedule_index=i, repeat=i+1,
                   cache_stratum='first_appearance' if i==0 else 'repeat', swapping_occurred=False,
                   latency_s=1, energy_j=None, memory_peak_rss_bytes=None)
        (run / 'checkpoints' / f'{i}.json').write_text(json.dumps(row))
        scores[str(i)] = dict(prompt_id='s', answer_sha256=hashlib.sha256(b'summary').hexdigest(),
                              checks={'length': True, 'faithful': True})
    (run / 'human_scores.json').write_text(json.dumps(dict(reviewer='Human', calls=scores)))
    out = tmp_path / 'audit'
    mod.audit([run], out)
    result = json.loads((out / 'audit.json').read_text())
    assert result['summary_review_complete'] is True
    assert not any('await blind' in s for s in result['limitations'])
    assert result['summary_length_sensitivity'][0]['primary']['score'] == 1
    assert result['kill_criterion_2']['status'] == 'not_met_no_recorded_decision_change'
