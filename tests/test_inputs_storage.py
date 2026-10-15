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


@pytest.mark.parametrize('thinking', [{'budget': 1}, {'budget': -1}, {'level': 'minimal'}, {}])
def test_thinking_must_be_explicitly_off(config_data, thinking):
    config_data['configurations'][0]['thinking'] = thinking
    with pytest.raises(ValueError):
        Config.model_validate(config_data)


def test_production_reference_label_and_role_are_preserved():
    from callcost.schemas import LocalConfig
    reference = LocalConfig(id='fairy-production', provider='lmstudio',
        label="Fairy's production model", comparison_role='production_reference',
        model_key='qwen/qwen3.5-9b@4bit', expected_quantisation='4bit', model_files=['model.safetensors'])
    assert reference.model_dump()['comparison_role'] == 'production_reference'
    assert reference.label == "Fairy's production model"


def test_resume_recovers_checkpoint_even_if_csv_was_not_written(tmp_path):
    from callcost.storage import write_json
    path = tmp_path / 'run'
    store = RunStore(path)
    store.append_call({'call_id': 'one', 'answer': 'first', 'status': 'completed', 'schedule_index': 0})
    store.close()
    # Power loss after atomic checkpoint, before CSV append.
    write_json(path / 'checkpoints/00000002.json', {'call_id': 'two', 'answer': 'second',
                                                  'status': 'completed', 'schedule_index': 1})
    (path / 'calls.csv').write_text('torn CSV')
    resumed = RunStore(path, resume=True)
    assert [r['call_id'] for r in resumed.rows] == ['one', 'two']
    with pytest.raises(ValueError, match='active writer'):
        RunStore(path, resume=True)
    resumed.close()
    rows = list(csv.DictReader((path / 'calls.csv').open()))
    assert [r['answer'] for r in rows] == ['first', 'second']


def test_supplied_summary_checks_accept_max_words_and_regex_pattern():
    from callcost.schemas import AutomaticCheck, Dataset
    check = AutomaticCheck.model_validate({'type': 'max_words', 'value': 80})
    assert check.value == 80
    for value in (-1, True, '80'):
        with pytest.raises(ValueError):
            AutomaticCheck.model_validate({'type': 'max_words', 'value': value})
    assert AutomaticCheck.model_validate({'type': 'regex', 'pattern': 'abc'}).value == 'abc'
    with pytest.raises(ValueError):
        AutomaticCheck.model_validate({'type': 'regex', 'pattern': 'abc', 'value': 'different'})
    dataset = Dataset.model_validate(load_document(__import__('pathlib').Path('prompts/summarisation.yaml')))
    assert len(dataset.prompts) == 10 and {p.task_type for p in dataset.prompts} == {'summarisation'}
