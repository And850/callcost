import importlib.util
import json
from pathlib import Path

import pytest


def module():
    path = Path(__file__).resolve().parents[1] / 'scripts/review_summaries.py'
    spec = importlib.util.spec_from_file_location('review_summaries', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_blind_packet_deduplicates_and_hides_identity(tmp_path):
    review = module()
    run = tmp_path / 'secret-config-run'
    (run / 'checkpoints').mkdir(parents=True)
    prompt = {'id': 's1', 'task_type': 'summarisation', 'prompt': 'Summarise', 'input': 'Source',
              'scoring': {'type': 'checklist', 'items': [{'id': 'faithful', 'description': 'Faithful', 'human': True},
                   {'id': 'short', 'description': 'At most ten words', 'automatic': {'type': 'max_words', 'value': 10}}]}}
    (run / 'metadata.json').write_text(json.dumps({'status': 'completed', 'dataset': {'prompts': [prompt]}}))
    for i in range(2):
        (run / 'checkpoints' / f'{i}.json').write_text(json.dumps({'call_id': str(i), 'prompt_id': 's1',
            'configuration_id': 'secret-model', 'phase': 'measured', 'status': 'completed', 'answer': 'Same answer </script><script>throw Error(1)</script>'}))
    out = tmp_path / 'review'
    review.prepare([run], out)
    packet = json.loads((out / 'packet.json').read_text())
    assert len(packet['items']) == 1
    html = (out / 'review.html').read_text()
    assert '</script><script>throw Error(1)</script>' not in html
    assert 'secret-model' not in html and 'secret-config-run' not in html
    assert len(json.loads((out / 'key.json').read_text())['mapping'][packet['items'][0]['id']]) == 2
    scores = {'packet_id': packet['packet_id'], 'reviewer': 'Human', 'scores': {packet['items'][0]['id']: {'faithful': True, 'short': True}}}
    scorefile = out / 'scores.json'
    scorefile.write_text(json.dumps(scores))
    review.import_scores(out, scorefile)
    saved = json.loads((run / 'human_scores.json').read_text())
    assert len(saved['calls']) == 2
    scores['scores'][packet['items'][0]['id']]['faithful'] = 'true'
    scorefile.write_text(json.dumps(scores))
    with pytest.raises(ValueError):
        review.import_scores(out, scorefile)


def test_blind_import_rejects_changed_rubric(tmp_path):
    review = module()
    run = tmp_path / 'run'
    (run / 'checkpoints').mkdir(parents=True)
    prompt = {'id': 's', 'task_type': 'summarisation', 'prompt': 'Summarise truthfully',
              'scoring': {'type': 'checklist', 'items': [{'id': 'faithful', 'description': 'No invented facts', 'human': True}]}}
    (run / 'metadata.json').write_text(json.dumps({'status': 'completed', 'dataset': {'prompts': [prompt]}}))
    (run / 'checkpoints/1.json').write_text(json.dumps({'call_id': 'c', 'prompt_id': 's', 'phase': 'measured', 'status': 'completed', 'answer': 'Text'}))
    out = tmp_path / 'review'
    review.prepare([run], out)
    packet = json.loads((out / 'packet.json').read_text())
    packet['items'][0]['checklist'][0]['description'] = 'Invented facts allowed'
    (out / 'packet.json').write_text(json.dumps(packet))
    f = tmp_path / 'scores.json'
    f.write_text(json.dumps({'packet_id': packet['packet_id'], 'reviewer': 'Human',
                            'scores': {packet['items'][0]['id']: {'faithful': True, 'short': True}}}))
    with pytest.raises(ValueError):
        review.import_scores(out, f)
    assert not (run / 'human_scores.json').exists()
