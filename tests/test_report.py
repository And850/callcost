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
    assert all(g['knee_eligible']['calls'] == 1 for g in result['groups'] if g['cache_stratum'] == 'all')
