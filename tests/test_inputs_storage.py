import csv
import json

import pytest

from callcost.schemas import Config, Dataset, load_document, render_prompt
from callcost.storage import RunStore


def test_defaults_and_no_answer_leak(config_data, prompt_data):
    config = Config.model_validate(config_data)
    assert config.run.repeats == 5
    assert config.run.temperature == 0
    prompt = Dataset.model_validate(prompt_data).prompts[0]
    assert render_prompt(prompt) == prompt_data['prompts'][0]['prompt']


@pytest.mark.parametrize('change', ['short_repeats', 'unknown', 'price', 'thinking', 'duplicate'])
def test_reject_invalid_configuration(config_data, change):
    if change == 'short_repeats':
        config_data['run'] = {'repeats': 4}
    elif change == 'unknown':
        config_data['run'] = {'temperatur': 0}
    elif change == 'price':
        config_data['configurations'][0]['pricing']['input_per_million'] = None
    elif change == 'thinking':
        config_data['configurations'][0]['thinking'] = {'budget': 0, 'level': 'low'}
    else:
        config_data['configurations'] *= 2
    with pytest.raises(ValueError):
        Config.model_validate(config_data)


def test_reject_duplicate_prompts_and_missing_scoring(prompt_data):
    prompt_data['prompts'] *= 2
    with pytest.raises(ValueError):
        Dataset.model_validate(prompt_data)
    prompt_data['prompts'] = [dict(prompt_data['prompts'][0])]
    del prompt_data['prompts'][0]['scoring']
    with pytest.raises(ValueError):
        Dataset.model_validate(prompt_data)


@pytest.mark.parametrize('name,text', [('bad.json', '{"a": 1, "a": 2}'), ('bad.yaml', 'a: 1\na: 2\n')])
def test_duplicate_mapping_keys_rejected(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    with pytest.raises(ValueError, match='Duplicate'):
        load_document(path)


def test_storage_preserves_multiline_answer_and_null(tmp_path):
    store = RunStore(tmp_path / 'run')
    store.write_metadata({'status': 'running', 'missing': None})
    store.append_call({'call_id': 'one', 'answer': 'a,"quoted"\n雪', 'ttft_s': None})
    store.close()
    with (tmp_path / 'run/calls.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    assert rows[0]['answer'] == 'a,"quoted"\n雪'
    assert rows[0]['ttft_s'] == ''
    assert json.loads((tmp_path / 'run/metadata.json').read_text())['missing'] is None
    with pytest.raises(FileExistsError):
        RunStore(tmp_path / 'run')
