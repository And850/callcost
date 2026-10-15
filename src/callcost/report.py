"""Read saved calls only. Missing observations never turn into zeros."""

import json
import math
import re
import statistics
from collections import defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from callcost.storage import write_json

METRICS = ('latency_s', 'ttft_s', 'decode_tokens_per_second', 'memory_peak_footprint_bytes',
           'memory_peak_rss_bytes', 'loaded_weight_bytes', 'input_tokens', 'output_tokens', 'thinking_tokens', 'billable_output_tokens',
           'request_payload_bytes', 'response_payload_bytes', 'list_price_cost', 'energy_j')


def distribution(values):
    values = sorted(float(v) for v in values if v is not None)
    if not values:
        return {'n': 0, 'p50': None, 'p95': None, 'q1': None, 'q3': None}
    def quantile(p):
        index = (len(values) - 1) * p
        left = int(index)
        return values[left] + (values[min(left + 1, len(values) - 1)] - values[left]) * (index - left)
    return dict(n=len(values), p50=statistics.median(values),
                p95=values[math.ceil(.95 * len(values)) - 1], q1=quantile(.25), q3=quantile(.75))


def score_answer(prompt, answer):
    rule = prompt['scoring']
    if rule['type'] == 'numeric_final_line':
        lines = answer.strip().splitlines()
        match = re.fullmatch(r'Answer:\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)', lines[-1]) if lines else None
        correct = False
        try:
            with localcontext() as context:
                context.prec = max(64, len(answer) + len(str(rule['expected'])) + 32)
                correct = match is not None and abs(Decimal(match[1]) - Decimal(rule['expected'])) <= Decimal(rule.get('absolute_tolerance', '0'))
        except ArithmeticError:
            match = None
        return {'score': float(correct), 'score_fraction': str(int(correct)), 'parseable': match is not None}
    if rule['type'] == 'expected_answer':
        return {'score': float(answer == rule['expected']), 'score_fraction': str(int(answer == rule['expected'])), 'parseable': None}
    checks = {}
    for item in rule['items']:
        check = item.get('automatic')
        value = None
        if check:
            kind, target = check['type'], check.get('value')
            if kind == 'substring':
                value = target in answer if check.get('case_sensitive', True) else target.casefold() in answer.casefold()
            elif kind == 'max_words':
                value = len(answer.split()) <= target
            elif kind == 'regex':
                value = re.search(target, answer, 0 if check.get('case_sensitive', True) else re.IGNORECASE) is not None
            else:
                try:
                    json.loads(answer, parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
                    value = True
                except ValueError:
                    value = False
        checks[item['id']] = value
    exact = None if None in checks.values() else Fraction(sum(checks.values()), len(checks))
    return {'score': None if exact is None else float(exact), 'score_fraction': None if exact is None else str(exact),
            'parseable': None, 'checks': checks}


def quality(rows, prompts):
    if not prompts:
        return {'score': None, 'reason': 'Scoring rules unavailable'}
    grouped = defaultdict(list)
    scores = []
    for row in rows:
        result = score_answer(prompts[row['prompt_id']], row['answer'])
        scores.append(dict(call_id=row['call_id'], prompt_id=row['prompt_id'], **result))
        grouped[row['prompt_id']].append(None if result['score_fraction'] is None else Fraction(result['score_fraction']))
    complete = all(p in grouped and all(v is not None for v in grouped[p]) for p in prompts)
    mean = statistics.mean(statistics.mean(grouped[p]) for p in prompts) if complete else None
    return dict(score=None if mean is None else float(mean), score_fraction=None if mean is None else str(mean), reason=None if complete else 'Missing eligible prompts, calls or human scores',
                calls_per_prompt={p: len(grouped[p]) for p in prompts},
                parseable_calls=sum(s['parseable'] is True for s in scores),
                parse_attempts=sum(s['parseable'] is not None for s in scores), call_scores=scores)


def aggregate(rows, prompts=None, phase='measured'):
    grouped = defaultdict(list)
    for row in rows:
        if row['phase'] == phase and row['status'] == 'completed':
            key = (row['configuration_id'], row['task_type'])
            grouped[(*key, 'all')].append(row)
            grouped[(*key, row['cache_stratum'])].append(row)
    result = []
    for (config, task, stratum), calls in sorted(grouped.items()):
        eligible = [r for r in calls if r.get('swapping_occurred') is False]
        task_prompts = {p['id']: p for p in prompts or [] if p['task_type'] == task}
        def summary(group):
            return {metric: distribution(r.get(metric) for r in group) for metric in METRICS}
        result.append(dict(configuration_id=config, task_type=task, cache_stratum=stratum, calls=len(calls),
                           swapped_calls=sum(r.get('swapping_occurred') is True for r in calls),
                           swap_unknown_calls=sum(r.get('swapping_occurred') is None for r in calls),
                           quality=quality(calls, task_prompts), **summary(calls),
                           knee_eligible=dict(calls=len(eligible), quality=quality(eligible, task_prompts), **summary(eligible)),
                           call_ids=[r['call_id'] for r in calls],
                           knee_eligible_call_ids=[r['call_id'] for r in eligible]))
    return result


def knee_findings(groups, configurations, tasks):
    sequence = sorted((c for c in configurations if c.get('comparison_role') == 'quantisation_series'),
                      key=lambda c: int(re.search(r'\d+', c['expected_quantisation'])[0]), reverse=True)
    findings = []
    for task in tasks:
        levels = [next((g for g in groups if g['configuration_id'] == c['id'] and g['task_type'] == task
                        and g['cache_stratum'] == 'all'), None) for c in sequence]
        ready = len(levels) == 4 and all(
            g is not None and g['knee_eligible']['quality']['score'] is not None
            and all(g['knee_eligible']['latency_s'].get(k) is not None for k in ('p50', 'q1', 'q3'))
            for g in levels)
        steps, previous_drop = [], None
        for index, (upper, lower) in enumerate(zip(levels, levels[1:])):
            a = upper['knee_eligible'] if upper else {}
            b = lower['knee_eligible'] if lower else {}
            costs, reasons = {}, {}
            for name, metric, quantile in (
                ('latency_p50_saving', 'latency_s', 'p50'),
                ('latency_p95_saving', 'latency_s', 'p95'),
                ('weight_byte_saving', 'loaded_weight_bytes', 'p50'),
            ):
                before, after = a.get(metric, {}).get(quantile), b.get(metric, {}).get(quantile)
                costs[name] = (float(1 - Fraction(str(after)) / Fraction(str(before)))
                               if before is not None and before > 0 and after is not None else None)
                if costs[name] is None:
                    reasons[name] = 'Missing eligible observations or nonpositive upper baseline'
            qa, qb = a.get('quality', {}), b.get('quality', {})
            drop = (Fraction(qa.get('score_fraction') or str(qa['score']))
                    - Fraction(qb.get('score_fraction') or str(qb['score']))
                    if qa.get('score') is not None and qb.get('score') is not None else None)
            overlap = (max(a['latency_s']['q1'], b['latency_s']['q1'])
                       <= min(a['latency_s']['q3'], b['latency_s']['q3'])) if ready else None
            indistinguishable = overlap and abs(drop) < Fraction(1, 20) if ready else None
            qualifies = (previous_drop is not None and drop >= Fraction(1, 10) and drop >= 2 * previous_drop
                         and not indistinguishable) if ready else None
            steps.append(dict(upper=sequence[index]['id'], lower=sequence[index + 1]['id'],
                              quality_drop=None if drop is None else float(drop), **costs,
                              cost_missing_reasons=reasons,
                              upper_footprint_bytes=a.get('memory_peak_footprint_bytes', distribution([])),
                              lower_footprint_bytes=b.get('memory_peak_footprint_bytes', distribution([])),
                              indistinguishable=indistinguishable, qualifies=qualifies))
            previous_drop = drop
        knee = next((s for s in steps if s['qualifies']), None)
        findings.append(dict(task_type=task, finding='insufficient data or pending human review' if not ready else
                             'knee found' if knee else 'no knee found', knee=knee, steps=steps))
    return findings


def collection_status(metadata, rows):
    schedule = metadata.get('schedule', [])
    completed = set()
    duplicates = []
    for row in rows:
        index = row.get('schedule_index')
        if row['status'] != 'completed' or type(index) is not int or not 0 <= index < len(schedule):
            continue
        if any(row.get(key) != value for key, value in schedule[index].items()):
            continue
        if index in completed:
            duplicates.append(index)
        completed.add(index)
    return dict(expected_slots=len(schedule), completed_slots=len(completed),
                duplicate_completed_slots=duplicates,
                complete=bool(schedule) and len(completed) == len(schedule) and not duplicates
                         and metadata['status'] == 'completed')


def report_run(directory):
    directory = Path(directory)
    metadata = json.loads((directory / 'metadata.json').read_text())
    rows = [json.loads(p.read_text()) for p in sorted((directory / 'checkpoints').glob('*.json'))]
    phase = 'smoke' if metadata.get('smoke') else 'measured'
    groups = aggregate(rows, metadata['dataset']['prompts'] if phase == 'measured' else [], phase)
    findings = [] if phase == 'smoke' else knee_findings(groups, metadata['config']['configurations'],
                                                       sorted({p['task_type'] for p in metadata['dataset']['prompts']}))
    collection = collection_status(metadata, rows)
    if not collection['complete']:
        for finding in findings:
            finding.update(finding='insufficient data: collection incomplete', knee=None)
    result = dict(run_status=metadata['status'], collection=collection, smoke=metadata.get('smoke', False),
                  quantiles='p50 median; p95 nearest rank; Q1/Q3 linear interpolation',
                  memory_for_knee='none; quality-only knee, amendment 2026-10-15; weight bytes are descriptive cost',
                  energy_scope='estimate, whole-machine delta; CPU + GPU + ANE; client device only',
                  failed_attempts=sum(r['status'] != 'completed' for r in rows), groups=groups,
                  knee=findings, variation=metadata.get('variation'))
    write_json(directory / 'report.json', result)
    lines = ['SMOKE ONLY, no benchmark conclusions' if phase == 'smoke' else 'CallCost saved-run report',
             f'Collection: {collection["completed_slots"]}/{collection["expected_slots"]} scheduled slots completed; '
             f'complete={collection["complete"]}.',
             'All completed calls shown. Knee inputs exclude swap-active and swap-unknown calls.',
             'Memory: descriptive weight bytes; sampled physical footprint is secondary. Knee uses quality only.',
             'Energy: estimate, whole-machine delta; CPU + GPU + ANE; client device only.',
             '| Configuration / task / cache | Calls | Swap / unknown | Knee eligible | Quality | Latency p50/p95 s | TTFT p50/p95 s | Weight GB | Footprint p50/p95 GB | Energy p50/p95 J |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    def pair(group, metric, scale=1):
        d = group[metric]
        return 'unavailable' if not d['n'] else f'{d["p50"]/scale:.3f}/{d["p95"]/scale:.3f}'
    for g in groups:
        q = g['quality']['score']
        label = f'{g["configuration_id"]} / {g["task_type"]} / {g["cache_stratum"]}'
        score = 'pending' if q is None else f'{100*q:.1f}%'
        lines.append(f'| {label} | {g["calls"]} | {g["swapped_calls"]}/{g["swap_unknown_calls"]} | '
                     f'{g["knee_eligible"]["calls"]} | {score} | {pair(g,"latency_s")} | {pair(g,"ttft_s")} | '
                     f'{pair(g,"loaded_weight_bytes",1e9)} | {pair(g,"memory_peak_footprint_bytes",1e9)} | {pair(g,"energy_j")} |')
    lines.extend(f'{f["task_type"]}: {f["finding"]}' for f in findings)
    text = '\n'.join(lines) + '\n'
    (directory / 'report.md').write_text(text)
    return text
