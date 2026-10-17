import importlib.util
import json
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts/plot_results.py'
    spec = importlib.util.spec_from_file_location('plot_results', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_run(path, configs):
    path.mkdir()
    prompts = [dict(id='m', task_type='maths'), dict(id='s', task_type='summarisation')]
    meta = dict(config={'run': {'repeats': 5}, 'configurations': configs}, dataset={'prompts': prompts})
    (path / 'metadata.json').write_text(json.dumps(meta))
    groups = []
    for c in configs:
        for task in ('maths', 'summarisation'):
            groups.append(dict(configuration_id=c['id'], task_type=task, cache_stratum='all', calls=5,
                quality={'score': .7, 'score_fraction': '7/10'}, quality_without_max_words={'score': .95},
                latency_s={'p50': 2, 'p95': 4, 'n': 5}, swap_free_latency_s={'p50': 1.8, 'p95': 3.5, 'n': 3}))
    (path / 'report.json').write_text(json.dumps(dict(collection={'complete': True}, groups=groups)))


def test_chart_data_uses_primary_scores_exact_sample_sizes_and_precision_order(tmp_path):
    plot = module()
    configs = [dict(id=f'local-q{n}', provider='lmstudio', comparison_role='quantisation_series', expected_quantisation=f'{n}bit') for n in (3,4,6,8)]
    configs += [dict(id='fairy-production', provider='lmstudio', comparison_role='production_reference')]
    make_run(tmp_path / 'local', configs)
    make_run(tmp_path / 'cloud', [dict(id='cloud', provider='gemini', comparison_role='cloud_reference')])
    data = plot.load_chart_data(tmp_path / 'local', tmp_path / 'cloud')
    task = data['tasks']['summarisation']
    assert task['unique_prompts'] == 1 and task['repeats'] == 5 and task['calls_per_configuration'] == 5
    assert [x['configuration_id'] for x in task['points']] == ['local-q8','local-q6','local-q4','local-q3','fairy-production','cloud']
    assert all(x['quality'] == .7 and x['latency_p50_s'] == 2 and x['latency_p95_s'] == 4 for x in task['points'])
    assert 'reviewer' not in json.dumps(data) and 'call_ids' not in json.dumps(data)
    report = json.loads((tmp_path / 'local/report.json').read_text())
    report['groups'][0]['latency_s']['p95'] = 1
    (tmp_path / 'local/report.json').write_text(json.dumps(report))
    with pytest.raises(ValueError):
        plot.load_chart_data(tmp_path / 'local', tmp_path / 'cloud')
