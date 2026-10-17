from callcost.report import knee_findings, quality, score_answer


def test_numeric_format_failure_is_zero_and_decimal_tolerance_is_applied():
    prompt = {'scoring': {'type': 'numeric_final_line', 'expected': '1.25', 'absolute_tolerance': '0.001'}}
    assert score_answer(prompt, 'work\nAnswer: 1.251')['score'] == 1
    assert score_answer(prompt, 'Answer: 1.252')['score'] == 0
    assert score_answer(prompt, 'Answer: 1.25\nextra')['parseable'] is False
    # Model-generated exponents must not crash offline reporting.
    assert score_answer(prompt, 'Answer: 1e999999999999999999999999')['score'] == 0


def test_quality_weights_prompts_equally_and_human_checks_remain_pending():
    prompts = {'a': {'scoring': {'type': 'expected_answer', 'expected': 'yes'}},
               'b': {'scoring': {'type': 'expected_answer', 'expected': 'yes'}}}
    rows = [dict(call_id=str(i), prompt_id=p, answer=a) for i, (p, a) in
            enumerate([('a', 'yes'), ('a', 'yes'), ('a', 'yes'), ('b', 'no')])]
    assert quality(rows, prompts)['score'] == .5
    assert quality(rows[:-1], prompts)['score'] is None
    prompt = {'scoring': {'type': 'checklist', 'items': [
        {'id': 'auto', 'automatic': {'type': 'substring', 'value': 'deadline'}},
        {'id': 'human', 'human': True}]}}
    result = score_answer(prompt, 'deadline tomorrow')
    assert result['checks'] == {'auto': True, 'human': None} and result['score'] is None


def test_knee_honours_exact_ten_percentage_point_boundary_and_first_step_exclusion():
    configurations = [dict(id=str(i), comparison_role='quantisation_series', expected_quantisation=f'{i}bit')
                      for i in (3, 4, 6, 8)]
    groups = []
    for identifier, q, latency, memory in [('8', .95, 10, 100), ('6', .9, 9, 90),
                                         ('4', .8, 8, 80), ('3', .7, 7, 70)]:
        groups.append(dict(configuration_id=identifier, task_type='maths', cache_stratum='all',
                           knee_eligible=dict(quality={'score': q}, latency_s={'p50': latency, 'q1': latency-.1, 'q3': latency+.1},
                                              loaded_weight_bytes={'p50': memory})))
    finding = knee_findings(groups, configurations, ['maths'])[0]
    assert finding['finding'] == 'knee found'
    assert finding['knee']['lower'] == '4'
    assert finding['steps'][0]['qualifies'] is False
    groups[1]['knee_eligible']['quality']['score'] = None
    assert knee_findings(groups, configurations, ['maths'])[0]['finding'] == 'insufficient data or pending human review'


def test_max_words_counts_whitespace_and_respects_inclusive_limit():
    p = {'scoring': {'type': 'checklist', 'items': [
        {'id': 'length', 'automatic': {'type': 'max_words', 'value': 3}}]}}
    assert score_answer(p, ' one\ttwo\nthree ')['score'] == 1
    assert score_answer(p, 'one two three four')['score'] == 0
    assert score_answer(p, '')['score'] == 1


def test_partial_schedule_cannot_establish_knee_even_when_every_prompt_is_scored(tmp_path):
    import json

    from callcost.report import report_run

    configurations = [dict(id=str(i), comparison_role='quantisation_series', expected_quantisation=f'{i}bit')
                      for i in (8, 6, 4, 3)]
    prompt = dict(id='p', task_type='maths', scoring={'type': 'expected_answer', 'expected': 'yes'})
    schedule = [dict(configuration_id=str(i), prompt_id='p', phase='measured', repeat=r)
                for i in (8, 6, 4, 3) for r in range(1, 6)]
    (tmp_path / 'checkpoints').mkdir()
    (tmp_path / 'metadata.json').write_text(json.dumps(dict(
        status='completed', config={'configurations': configurations}, dataset={'prompts': [prompt]},
        schedule=schedule)))  # Even a stale status cannot replace durable checkpoints.
    for index, identifier in enumerate((8, 6, 4, 3)):
        row = dict(status='completed', phase='measured', configuration_id=str(identifier), task_type='maths',
                   prompt_id='p', call_id=str(index), cache_stratum='first_appearance',
                   latency_s=identifier, loaded_weight_bytes=identifier, swapping_occurred=False,
                   answer='yes', schedule_index=index * 5, repeat=1)
        (tmp_path / 'checkpoints' / f'{index:08d}.json').write_text(json.dumps(row))
    report_run(tmp_path)
    result = json.loads((tmp_path / 'report.json').read_text())
    assert result['collection']['completed_slots'] == 4
    assert result['collection']['expected_slots'] == 20
    assert result['collection']['complete'] is False
    assert result['knee'][0]['finding'] == 'insufficient data: collection incomplete'

    for index, slot in enumerate(schedule):
        row = dict(status='completed', task_type='maths', call_id=str(index), cache_stratum='repeat',
                   latency_s=1, loaded_weight_bytes=1, swapping_occurred=index % 5 != 0,
                   answer='yes', schedule_index=index, **slot)
        (tmp_path / 'checkpoints' / f'{index:08d}.json').write_text(json.dumps(row))
    report_run(tmp_path)
    result = json.loads((tmp_path / 'report.json').read_text())
    assert result['collection']['complete'] is True
    assert result['knee'][0]['finding'] == 'no knee found'
    assert all(g['knee_eligible']['calls'] == 5 for g in result['groups'] if g['cache_stratum'] == 'all')


def test_pending_quality_keeps_all_adjacent_costs_and_secondary_footprints():
    configurations = [dict(id=str(i), comparison_role='quantisation_series', expected_quantisation=f'{i}bit')
                      for i in (8, 6, 4, 3)]
    groups = [dict(configuration_id=str(i), task_type='summarisation', cache_stratum='all',
                   knee_eligible=dict(quality={'score': None}, calls=5,
                                      latency_s={'p50': i, 'p95': i * 2, 'q1': i - .1, 'q3': i + .1},
                                      loaded_weight_bytes={'p50': i * 100},
                                      memory_peak_footprint_bytes={'n': 5, 'p50': i * 110, 'p95': i * 120}))
              for i in (8, 6, 4, 3)]
    finding = knee_findings(groups, configurations, ['summarisation'])[0]
    assert finding['finding'] == 'insufficient data or pending human review'
    assert finding['knee'] is None
    assert len(finding['steps']) == 3
    first = finding['steps'][0]
    assert first['weight_byte_saving'] == .25
    assert first['latency_p50_saving'] == .25
    assert first['latency_p95_saving'] == .25
    assert first['upper_footprint_bytes']['p50'] == 880
    assert first['lower_footprint_bytes']['p50'] == 660
    assert all(s['qualifies'] is None for s in finding['steps'])
    # Absent configurations still leave the registered adjacent steps visible.
    missing = knee_findings(groups[:-1], configurations, ['summarisation'])[0]
    assert len(missing['steps']) == 3
    assert missing['steps'][-1]['weight_byte_saving'] is None
    assert missing['steps'][-1]['cost_missing_reasons']['weight_byte_saving']


def test_saved_report_exposes_missing_measurements_tokens_costs_and_empty_groups(tmp_path):
    import json

    from callcost.report import report_run

    prompts = [dict(id='p', task_type='maths', scoring={'type': 'expected_answer', 'expected': 'yes'}),
               dict(id='s', task_type='summarisation', scoring={'type': 'expected_answer', 'expected': 'yes'})]
    (tmp_path / 'checkpoints').mkdir()
    (tmp_path / 'metadata.json').write_text(json.dumps(dict(
        status='failed', config={'configurations': [{'id': 'cloud', 'provider': 'gemini'}]},
        dataset={'prompts': prompts}, schedule=[])))
    row = dict(status='completed', phase='measured', configuration_id='cloud', task_type='maths',
               prompt_id='p', call_id='c', cache_stratum='first_appearance', answer='yes',
               latency_s=1, swapping_occurred=False, memory_peak_footprint_bytes=None,
               footprint_missing_reason='Process coverage incomplete', thinking_tokens=3,
               output_tokens=4, billable_output_tokens=7, list_price_cost='0.001', currency='USD',
               request_payload_bytes=100, response_payload_bytes=200)
    (tmp_path / 'checkpoints/00000001.json').write_text(json.dumps(row))
    text = report_run(tmp_path)
    result = json.loads((tmp_path / 'report.json').read_text())
    group = next(g for g in result['groups'] if g['task_type'] == 'maths' and g['cache_stratum'] == 'all')
    assert group['memory_peak_footprint_bytes']['missing_reasons'] == {'Process coverage incomplete': 1}
    empty = next(g for g in result['groups'] if g['task_type'] == 'summarisation' and g['cache_stratum'] == 'all')
    assert empty['calls'] == 0 and empty['quality']['score'] is None
    assert empty['latency_s']['p50'] is None
    assert 'Process coverage incomplete' in text
    assert 'RSS' in text and 'Thinking' in text and 'Billable output' in text
    assert '0.001' in text and 'USD' in text
    assert '100.000/100.000' in text and '200.000/200.000' in text
    assert 'n=1' in text and 'No completed calls' in text
    assert 'Quality all completed' in text
    assert 'Weight saving' in text and 'Latency p50/p95 saving' in text


def test_configuration_swap_summary_includes_zero_volume_and_unknown_counts():
    from callcost.report import swap_summary
    calls = [dict(status='completed', swapping_occurred=swap, swap_volume_bytes=volume)
             for swap, volume in [(False, 0), (True, 100), (True, 300), (None, None)]]
    result = swap_summary(calls)
    assert result['swapped_share_known'] == 2/3
    assert result['swap_unknown_calls'] == 1
    assert result['swap_volume_bytes']['p50'] == 100
    assert result['swap_volume_bytes']['n'] == 3


def test_human_checklist_review_completes_quality_without_changing_auto_defaults():
    from callcost.report import score_answer
    prompt = {'scoring': {'type': 'checklist', 'items': [
        {'id': 'automatic', 'automatic': {'type': 'substring', 'value': 'Thursday'}},
        {'id': 'faithful', 'human': True}]}}
    assert score_answer(prompt, 'Thursday')['score'] is None
    result = score_answer(prompt, 'Thursday', {'automatic': True, 'faithful': False})
    assert result['score'] == .5 and result['checks'] == {'automatic': True, 'faithful': False}


def test_saved_human_scores_bind_to_exact_answer_and_rubric(tmp_path):
    import hashlib
    import json

    import pytest

    from callcost.report import load_human_scores
    prompt = {'scoring': {'type': 'checklist', 'items': [{'id': 'faithful', 'human': True}]}}
    row = dict(call_id='c', prompt_id='p', status='completed', phase='measured', answer='text')
    record = dict(reviewer='Human', calls={'c': dict(prompt_id='p', answer_sha256=hashlib.sha256(b'text').hexdigest(), checks={'faithful': True})})
    (tmp_path / 'human_scores.json').write_text(json.dumps(record))
    load_human_scores(tmp_path, [row], {'p': prompt})
    assert row['human_checks'] == {'faithful': True}
    record['calls']['c']['answer_sha256'] = 'different'
    (tmp_path / 'human_scores.json').write_text(json.dumps(record))
    with pytest.raises(ValueError):
        load_human_scores(tmp_path, [row], {'p': prompt})


def test_report_counts_durable_http_retries_by_configuration(tmp_path):
    import json

    from callcost.report import report_run
    (tmp_path / 'raw').mkdir()
    (tmp_path / 'checkpoints').mkdir()
    (tmp_path / 'metadata.json').write_text(json.dumps(dict(status='failed', schedule=[],
        config={'configurations': [{'id': 'cloud', 'comparison_role': 'cloud_reference'}]}, dataset={'prompts': []})))
    (tmp_path / 'raw/c.attempts.json').write_text(json.dumps([
        dict(configuration_id='cloud', status='error', list_price_cost=None),
        dict(configuration_id='cloud', status='error', list_price_cost=None),
        dict(configuration_id='cloud', status='completed', list_price_cost='0.01')]))
    text = report_run(tmp_path)
    record = json.loads((tmp_path / 'report.json').read_text())['retry_summary'][0]
    assert record['retries'] == 2 and record['calls_retried'] == 1
    assert record['failed_http_attempts'] == 2 and record['usage_cost_unknown_attempts'] == 2
    assert 'retries' in text
