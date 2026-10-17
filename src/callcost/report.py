"""Read saved calls only. Missing observations never turn into zeros."""

import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from callcost.billing import gemini_attempts, reconcile_billing
from callcost.storage import write_json

METRICS = ('latency_s', 'ttft_s', 'decode_tokens_per_second', 'memory_peak_footprint_bytes',
           'memory_peak_rss_bytes', 'loaded_weight_bytes', 'input_tokens', 'output_tokens', 'thinking_tokens', 'billable_output_tokens',
           'request_payload_bytes', 'response_payload_bytes', 'list_price_cost', 'energy_j',
           'swap_volume_bytes', 'swap_used_before_bytes', 'swap_used_after_bytes',
           'compressed_memory_before_bytes', 'compressed_memory_after_bytes')


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


def score_answer(prompt, answer, human_checks=None):
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
    if human_checks is not None:
        if set(human_checks) != set(checks) or not all(type(v) is bool for v in human_checks.values()):
            raise ValueError('Human review must score every checklist criterion with a boolean')
        if any(human_checks[k] != v for k, v in checks.items() if v is not None):
            raise ValueError('Human review cannot override registered automatic checks')
        checks.update(human_checks)
    exact = None if None in checks.values() else Fraction(sum(checks.values()), len(checks))
    return {'score': None if exact is None else float(exact), 'score_fraction': None if exact is None else str(exact),
            'parseable': None, 'checks': checks}


def quality(rows, prompts, *, exclude_max_words=False):
    if not prompts:
        return {'score': None, 'reason': 'Scoring rules unavailable'}
    grouped = defaultdict(list)
    scores = []
    for row in rows:
        result = score_answer(prompts[row['prompt_id']], row['answer'], row.get('human_checks'))
        if exclude_max_words and prompts[row['prompt_id']]['scoring']['type'] == 'checklist':
            excluded = {item['id'] for item in prompts[row['prompt_id']]['scoring']['items']
                        if (item.get('automatic') or {}).get('type') == 'max_words'}
            checks = {key: value for key, value in result['checks'].items() if key not in excluded}
            exact = None if not checks or None in checks.values() else Fraction(sum(checks.values()), len(checks))
            result = dict(result, checks=checks, excluded_checks=sorted(excluded),
                          score=None if exact is None else float(exact),
                          score_fraction=None if exact is None else str(exact))
        scores.append(dict(call_id=row['call_id'], prompt_id=row['prompt_id'], **result))
        grouped[row['prompt_id']].append(None if result['score_fraction'] is None else Fraction(result['score_fraction']))
    complete = all(p in grouped and all(v is not None for v in grouped[p]) for p in prompts)
    mean = statistics.mean(statistics.mean(grouped[p]) for p in prompts) if complete else None
    return dict(score=None if mean is None else float(mean), score_fraction=None if mean is None else str(mean), reason=None if complete else 'Missing eligible prompts, calls or human scores',
                calls_per_prompt={p: len(grouped[p]) for p in prompts},
                parseable_calls=sum(s['parseable'] is True for s in scores),
                parse_attempts=sum(s['parseable'] is not None for s in scores), call_scores=scores)


def swap_summary(calls):
    known = [r for r in calls if r.get('swapping_occurred') is not None]
    swapped = sum(r.get('swapping_occurred') is True for r in known)
    return dict(swapped_calls=swapped, swap_known_calls=len(known),
                swap_unknown_calls=len(calls) - len(known),
                swapped_share_known=swapped / len(known) if known else None,
                swap_volume_bytes=distribution(r.get('swap_volume_bytes') for r in known))


def aggregate(rows, prompts=None, phase='measured', configurations=None):
    grouped = defaultdict(list)
    for config in configurations or []:
        for task in {p['task_type'] for p in prompts or []}:
            for stratum in ('all', 'first_appearance', 'repeat'):
                grouped[(config['id'], task, stratum)] = []
    for row in rows:
        if row['phase'] == phase:
            key = (row['configuration_id'], row['task_type'])
            grouped[(*key, 'all')].append(row)
            grouped[(*key, row['cache_stratum'])].append(row)
    result = []
    for (config, task, stratum), attempts in sorted(grouped.items()):
        calls = [r for r in attempts if r['status'] == 'completed']
        eligible = calls  # Amendment 2026-10-16: swapping is cost, not a quality exclusion.
        swap_free = [r for r in calls if r.get('swapping_occurred') is False]
        task_prompts = {p['id']: p for p in prompts or [] if p['task_type'] == task}
        def summary(group):
            result = {}
            reason_fields = {'memory_peak_footprint_bytes': 'footprint_missing_reason',
                             'memory_peak_rss_bytes': 'memory_missing_reason', 'energy_j': 'energy_missing_reason'}
            for metric in METRICS:
                d = distribution(r.get(metric) for r in group)
                d['missing_reasons'] = dict(Counter(
                    r.get(reason_fields.get(metric)) or r.get('missing', {}).get(metric)
                    or r.get('swap_observation_missing', {}).get(metric) or 'Not recorded for this call'
                    for r in group if r.get(metric) is None))
                d['unavailable_reason'] = 'No completed calls in this group' if not group else None
                result[metric] = d
            return result
        result.append(dict(configuration_id=config, task_type=task, cache_stratum=stratum, calls=len(calls),
                           failed_attempts=len(attempts) - len(calls),
                           failed_call_ids=[r['call_id'] for r in attempts if r['status'] != 'completed'],
                           currencies=sorted({r['currency'] for r in calls if r.get('currency')}),
                           **{k: v for k, v in swap_summary(calls).items() if k != 'swap_volume_bytes'},
                           swap_free_latency_s=dict(distribution(r.get('latency_s') for r in swap_free),
                                                   unavailable_reason=None if swap_free else 'No calls with known zero swap-in and swap-out'),
                           quality=quality(calls, task_prompts),
                           quality_without_max_words=quality(calls, task_prompts, exclude_max_words=True)
                               if task == 'summarisation' else None, **summary(calls),
                           knee_eligible=dict(calls=len(eligible), quality=quality(eligible, task_prompts), **summary(eligible)),
                           call_ids=[r['call_id'] for r in calls],
                           knee_eligible_call_ids=[r['call_id'] for r in eligible]))
    return result


def knee_findings(groups, configurations, tasks):
    sequence = sorted((c for c in configurations if c.get('comparison_role') == 'quantisation_series'),
                      key=lambda c: int(re.search(r'\d+', c['expected_quantisation'])[0]), reverse=True)
    if not sequence:
        return []
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
                              upper_footprint_bytes=a.get('memory_peak_footprint_bytes', dict(distribution([]), unavailable_reason='No eligible footprint observations')),
                              lower_footprint_bytes=b.get('memory_peak_footprint_bytes', dict(distribution([]), unavailable_reason='No eligible footprint observations')),
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


def load_human_scores(directory, rows, prompts):
    path = directory / 'human_scores.json'
    if not path.exists():
        return None
    review = json.loads(path.read_text())
    by_id = {r['call_id']: r for r in rows}
    for call_id, saved in review['calls'].items():
        row = by_id.get(call_id)
        if (row is None or row['status'] != 'completed' or row['phase'] != 'measured'
                or row['prompt_id'] != saved['prompt_id']
                or hashlib.sha256(row['answer'].encode()).hexdigest() != saved['answer_sha256']):
            raise ValueError('Human score identity does not match saved completed answer')
        prompt = prompts[row['prompt_id']]
        if prompt['scoring']['type'] != 'checklist':
            raise ValueError('Human checklist scores cannot change maths scoring')
        score_answer(prompt, row['answer'], saved['checks'])
        row['human_checks'] = saved['checks']
    return {k: review.get(k) for k in ('packet_id', 'reviewer', 'reviewed_at')}


def report_run(directory):
    directory = Path(directory)
    metadata = json.loads((directory / 'metadata.json').read_text())
    rows = [json.loads(p.read_text()) for p in sorted((directory / 'checkpoints').glob('*.json'))]
    human_review = load_human_scores(directory, rows, {p['id']: p for p in metadata['dataset']['prompts']})
    phase = 'precheck' if metadata.get('precheck') else 'smoke' if metadata.get('smoke') else 'measured'
    groups = aggregate(rows, metadata['dataset']['prompts'] if phase == 'measured' else [], phase,
                       metadata['config']['configurations'])
    findings = [] if phase != 'measured' else knee_findings(groups, metadata['config']['configurations'],
                                                       sorted({p['task_type'] for p in metadata['dataset']['prompts']}))
    collection = collection_status(metadata, rows)
    if not collection['complete']:
        for finding in findings:
            finding.update(finding='insufficient data: collection incomplete', knee=None)
            for step in finding['steps']:
                step['qualifies'] = None
    retry_summary = []
    manifests = [json.loads(p.read_text()) for p in (directory / 'raw').glob('*.attempts.json')]
    for c in metadata['config']['configurations']:
        records = [a for a in manifests if a and a[0]['configuration_id'] == c['id']]
        retry_summary.append(dict(configuration_id=c['id'], retries=sum(len(a) - 1 for a in records),
                                  calls_retried=sum(len(a) > 1 for a in records),
                                  failed_http_attempts=sum(x['status'] != 'completed' for a in records for x in a),
                                  usage_cost_unknown_attempts=sum(x['status'] != 'completed' and x.get('list_price_cost') is None
                                                                for a in records for x in a)))
    billing_attempts = gemini_attempts(directory)
    billing = reconcile_billing(directory, billing_attempts) if billing_attempts else None
    result = dict(billing_reconciliation=billing, human_review=human_review, retry_summary=retry_summary, run_status=metadata['status'], run_pass=metadata.get('run_pass'), collection=collection,
                  precheck=metadata.get('precheck', False), smoke=metadata.get('smoke', False),
                  diagnostic_windows=metadata.get('diagnostic_windows', []),
                  precheck_validation=metadata.get('precheck_validation'),
                  quantiles='p50 median; p95 nearest rank; Q1/Q3 linear interpolation',
                  memory_for_knee='none; quality-only knee, amendment 2026-10-15; weight bytes are descriptive cost',
                  energy_scope='estimate, whole-machine delta; CPU + GPU + ANE; client device only',
                  failed_attempts=sum(r['status'] != 'completed' for r in rows), groups=groups,
                  knee=findings, variation=metadata.get('variation'),
                  summary_scoring_policy='Primary: pre-registered checklist including max_words. Secondary: post-collection sensitivity excluding max_words only; all other criteria and equal prompt weights retained. Knee/variance use primary only.',
                  analysis_policy='2026-10-16: all completed calls; all-call latency primary; swap-free latency secondary',
                  configuration_swap=[dict(configuration_id=c['id'], **swap_summary(
                      [r for r in rows if r['phase'] == phase and r['status'] == 'completed' and r['configuration_id'] == c['id']]))
                      for c in metadata['config']['configurations']],
                  energy_blocks=metadata.get('energy_blocks', []),
                  production_reference_caveat=metadata.get('production_reference_caveat'))
    write_json(directory / 'report.json', result)
    lines = [f'{phase.upper()} ONLY, no benchmark conclusions' if phase != 'measured' else 'CallCost saved-run report',
             f'Collection: {collection["completed_slots"]}/{collection["expected_slots"]} scheduled slots completed; '
             f'complete={collection["complete"]}.',
             'All completed answers enter quality/knee analysis, including swap-active and swap-unknown calls (amendment 2026-10-16).',
             'Memory: descriptive weight bytes; sampled physical footprint is secondary. Knee uses quality only.',
             'Knee and variance cover the four converted local levels; cloud and Fairy are references outside that sequence.',
             'Energy: estimate, whole-machine delta; CPU + GPU + ANE; client device only.',
             'Values are p50/p95 with valid observation counts. GB uses 1e9 bytes.',
             'Step costs and variance use all completed observations; swap-free latency is secondary. Costs remain available while human quality is pending.',
             '',
             '| Configuration / task / cache | Calls / failed | Swap / unknown | Knee eligible | Quality all completed | Latency all s | Latency swap-free s | TTFT s | Weight GB | Footprint GB, secondary | RSS GB, secondary | Energy J |',
             '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    def cell(value):
        return str(value).replace('|', r'\|').replace('\n', ' ')
    def pair(group, metric, scale=1):
        d = group[metric]
        reasons = '; '.join(f'{cell(reason)} ({count})' for reason, count in d.get('missing_reasons', {}).items())
        number_format = '.9g' if metric == 'list_price_cost' else '.3f'
        value = 'unavailable' if not d['n'] else '/'.join(format(d[q]/scale, number_format) for q in ('p50', 'p95'))
        detail = reasons or d.get('unavailable_reason')
        return f'{value} (n={d["n"]}' + (f'; {detail}' if detail else '') + ')'
    def score(q):
        return ('unavailable: ' + cell(q.get('reason') or 'Pending scores')) if q['score'] is None else f'{100*q["score"]:.1f}%'
    def label(g):
        return f'{g["configuration_id"]} / {g["task_type"]} / {g["cache_stratum"]}'
    for g in groups:
        lines.append(f'| {label(g)} | {g["calls"]}/{g["failed_attempts"]} | {g["swapped_calls"]}/{g["swap_unknown_calls"]} | '
                     f'{g["knee_eligible"]["calls"]} | {score(g["quality"])} | '
                     f'{pair(g,"latency_s")} | {pair(g,"swap_free_latency_s")} | {pair(g,"ttft_s")} | '
                     f'{pair(g,"loaded_weight_bytes",1e9)} | {pair(g,"memory_peak_footprint_bytes",1e9)} | '
                     f'{pair(g,"memory_peak_rss_bytes",1e9)} | {pair(g,"energy_j")} |')
    summary_groups = [g for g in groups if g['task_type'] == 'summarisation' and g['cache_stratum'] == 'all']
    if summary_groups:
        lines += ['', 'Summary scores: primary and length-check sensitivity (deviation note, 17 October 2026).',
                  'Primary includes the pre-registered max_words check and alone supplies knee/variance quality. '
                  'Secondary removes only max_words, reweights remaining criteria within each prompt, then retains equal prompt weighting. '
                  'Sentence instructions and all other checks remain. Both scores await any pending human checks.',
                  '| Configuration | Primary, including max_words | Secondary, excluding max_words |',
                  '| --- | --- | --- |']
        for g in summary_groups:
            lines.append(f'| {g["configuration_id"]} | {score(g["quality"])} | {score(g["quality_without_max_words"])} |')
    lines += ['', '| Configuration / task / cache | Input tokens | Visible output tokens | Thinking tokens | Billable output tokens | Decode tokens/s | Request bytes | Response bytes | List-price equivalent |',
              '| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for g in groups:
        lines.append(f'| {label(g)} | ' + ' | '.join(pair(g, metric) for metric in (
            'input_tokens', 'output_tokens', 'thinking_tokens', 'billable_output_tokens',
            'decode_tokens_per_second', 'request_payload_bytes', 'response_payload_bytes'))
            + f' | {pair(g,"list_price_cost")} {"/".join(g["currencies"]) or "currency unavailable; see raw calls"} |')
    lines += [''] + [f'{f["task_type"]}: {f["finding"]}' for f in findings]
    lines += ['', '| Task / adjacent step | Quality drop, pp | Weight saving | Latency p50/p95 saving | Upper / lower footprint GB, secondary | Indistinguishable | Qualifies |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for finding in findings:
        for step in finding['steps']:
            def percent(key):
                v = step[key]
                return ('unavailable: ' + step['cost_missing_reasons'].get(key, 'Pending quality')) if v is None else f'{100*v:.2f}%'
            drop = 'pending' if step['quality_drop'] is None else f'{100*step["quality_drop"]:.2f}'
            footprints = ' / '.join(pair({'footprint': step[k]}, 'footprint', 1e9)
                                    for k in ('upper_footprint_bytes', 'lower_footprint_bytes'))
            lines.append(f'| {finding["task_type"]} / {step["upper"]} to {step["lower"]} | {drop} | '
                         f'{percent("weight_byte_saving")} | {percent("latency_p50_saving")}/{percent("latency_p95_saving")} | '
                         f'{footprints} | {step["indistinguishable"]} | {step["qualifies"]} |')
    lines += ['', 'Completed calls per prompt (swapping retained):']
    for g in groups:
        counts = g['knee_eligible']['quality'].get('calls_per_prompt', {})
        lines.append(f'{label(g)}: ' + (', '.join(f'{p}={n}' for p, n in counts.items()) or 'Scoring rules unavailable'))
    lines += ['', 'Swap is part of configuration cost on this 16 GB Mac; counters are whole-machine observations.',
              '| Configuration | Swapped / known | Unknown | Swapped share, known calls | Median swap-in + swap-out bytes, known calls | Volume observations |',
              '| --- | --- | --- | --- | --- | --- |']
    for swap in result['configuration_swap']:
        share = 'unavailable' if swap['swapped_share_known'] is None else f'{100*swap["swapped_share_known"]:.1f}%'
        volume = swap['swap_volume_bytes']
        lines.append(f'| {swap["configuration_id"]} | {swap["swapped_calls"]}/{swap["swap_known_calls"]} | '
                     f'{swap["swap_unknown_calls"]} | {share} | {volume["p50"] if volume["n"] else "unavailable"} | {volume["n"]} |')
    if result['production_reference_caveat']:
        lines += ['', result['production_reference_caveat']]
    lines += ['', 'Energy baseline qualifications (descriptive, no registered drift cutoff):']
    for block in result['energy_blocks']:
        lines.append(cell(json.dumps({k: block.get(k) for k in (
            'configuration_id', 'segment_id', 'mode', 'assessment', 'unavailable_reason')}, ensure_ascii=False)))
    if result['precheck']:
        lines += ['', f'Pre-check validation: {result["precheck_validation"]}', 'Idle swap diagnostics (whole-machine, no causal process attribution):',
                  '| Configuration | Window | Seconds | Swap-in bytes | Swap-out bytes | Swap volume bytes/s |',
                  '| --- | --- | --- | --- | --- | --- |']
        for w in result['diagnostic_windows']:
            rate = w['swap_volume_bytes'] / w['duration_s'] if w.get('swap_volume_bytes') is not None and w['duration_s'] else None
            lines.append(f'| {w.get("configuration_id") or "unloaded"} | {w["label"]} | {w["duration_s"]:.2f} | '
                         f'{w.get("swapins_bytes")} | {w.get("swapouts_bytes")} | {rate} |')
    if billing is not None:
        lines += ['', 'Provider billing reconciliation (list price excludes tax):',
                  '| Field | Value |', '| --- | --- |',
                  f'| Known list-price cost excluding tax | {billing["known_list_price_cost_excluding_tax"]} {billing["currency"]} |',
                  f'| Billed amount from provider | {billing["billed_amount_from_provider"] if billing["billed_amount_from_provider"] is not None else "pending provider export"} |',
                  f'| Difference: billed minus known list price | {billing["difference"] if billing["difference"] is not None else "unavailable"} |',
                  f'| Unexplained difference after documented adjustments | {billing["unexplained_difference"] if billing["unexplained_difference"] is not None else "unavailable"} |',
                  f'| Reconciliation status | {billing["status"]} |',
                  f'| Unknown-cost HTTP attempts | {billing["unknown_cost_attempts"]} |',
                  'Documented adjustments: ' + json.dumps(billing['explained_adjustments'], ensure_ascii=False),
                  'Fill billing.json from a scope-matched provider export. Unexplained differences remain explicit.']
    if human_review:
        lines += ['', 'Human checklist review: ' + json.dumps(human_review)]
    lines += ['', 'Cloud HTTP retry attempts (successful-attempt latency only):']
    lines += [json.dumps(x) for x in retry_summary]
    text = '\n'.join(lines) + '\n'
    (directory / 'report.md').write_text(text)
    return text
