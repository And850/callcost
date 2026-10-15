from callcost.schemas import Config, Dataset
from callcost.variation import answer_hash, variation_report


def test_variation_ignores_failed_and_excluded_calls(config_data, prompt_data):
    config = Config.model_validate(config_data)
    dataset = Dataset.model_validate(prompt_data)
    rows = [{'phase': 'measured', 'configuration_id': 'cloud', 'prompt_id': 'math-1',
             'status': 'completed', 'answer_sha256': answer_hash(a), 'call_id': str(i)}
            for i, a in enumerate(['A', 'A', 'B', 'A', 'B'])]
    rows += [dict(rows[0], phase='warmup', answer_sha256=answer_hash('C')),
             dict(rows[0], status='error', answer_sha256=answer_hash('D'))]
    report = variation_report(config, dataset, rows)
    assert report['groups'][0]['distinct_answers'] == 2
    assert report['summary'][0]['varying_prompts'] == 1
    assert report['summary'][0]['incomplete_prompts'] == 0
    partial = variation_report(config, dataset, rows[:1])
    assert partial['summary'][0]['compared_prompts'] == 0
    assert partial['summary'][0]['uncomparable_prompts'] == 1
    assert partial['summary'][0]['incomplete_prompts'] == 1
