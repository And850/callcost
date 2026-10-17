"""Reproducible offline audit from immutable checkpoints; never issues model calls."""

import argparse
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from callcost.report import distribution, report_run, score_answer


def audit(runs, output):
    result = {'runs': [], 'configurations': [], 'variance': [], 'limitations': [
        'Summary quality and summary variance decisions await blind human checklist scores.',
        'Five repeats are not five independent task samples; the maths task set has 30 problems.',
        'No demonstrated Fairy production decision has changed. The tool has not yet met kill criterion 2. '
        'Do not substitute a possible recommendation for an actual changed decision. If nothing changes after review, '
        'the registered usefulness criterion fails.',
        'Exact text variation includes whitespace and does not necessarily imply changed correctness.',
        'Swap is whole-machine traffic; collection order/background activity confound process attribution.',
        'Energy remains estimate, whole-machine delta for CPU + GPU + ANE, with receipt-anchor and baseline limitations.'
    ]}
    lines = ['# Saved-run audit', '', 'Preliminary until blind summary review and measurement audit are complete.', '',
             '| Configuration | Maths correct / 150 | Wrong, parseable | Unparseable | Varying maths / 30 | Varying summaries / 10 |',
             '| --- | --- | --- | --- | --- | --- |']
    latency = []
    q3_format_cases = defaultdict(list)
    for run in runs:
        report_run(run)
        meta = json.loads((run / 'metadata.json').read_text())
        report = json.loads((run / 'report.json').read_text())
        rows = [json.loads(f.read_text()) for f in sorted((run / 'checkpoints').glob('*.json'))]
        prompts = {p['id']: p for p in meta['dataset']['prompts']}
        done = [r for r in rows if r['phase'] == 'measured' and r['status'] == 'completed']
        counts = Counter((r['configuration_id'], r['prompt_id']) for r in done)
        if not report['collection']['complete'] or any(n != 5 for n in counts.values()):
            raise ValueError('Audit requires complete five-repeat collection')
        known_cost = sum((Decimal(r['list_price_cost']) for r in rows if r.get('list_price_cost') is not None), Decimal(0))
        unknown_cost_failures = sum(r['status'] != 'completed' and r.get('list_price_cost') is None for r in rows)
        additional_failures = []
        retry_count = 0
        checkpoint_ids = {r['call_id'] for r in rows}
        for f in (run / 'raw').glob('*.attempts.json'):
            attempts = json.loads(f.read_text())
            retry_count += max(0, len(attempts) - 1)
            unrepresented = attempts[:-1] if attempts and attempts[-1]['call_id'] in checkpoint_ids else attempts
            for x in unrepresented:
                additional_failures.append(x)
                if x.get('list_price_cost') is None:
                    unknown_cost_failures += 1
                else:
                    known_cost += Decimal(x['list_price_cost'])
        result['runs'].append(dict(directory=str(run.resolve()), collection=report['collection'],
              known_list_price_cost=str(known_cost), unknown_cost_failed_attempts=unknown_cost_failures,
              failed_checkpoint_attempts=sum(r['status'] != 'completed' for r in rows),
              automatic_retry_attempts=retry_count, retry_summary=report.get('retry_summary'),
              historical_errors=meta['errors']))
        for config in meta['config']['configurations']:
            cid = config['id']
            cr = [r for r in done if r['configuration_id'] == cid]
            maths = Counter()
            for r in cr:
                if r['task_type'] == 'maths':
                    s = score_answer(prompts[r['prompt_id']], r['answer'])
                    maths['correct' if s['score'] == 1 else 'wrong_parseable' if s['parseable'] else 'unparseable'] += 1
                    if cid == 'local-q3' and not s['parseable']:
                        q3_format_cases[r['prompt_id']].append(dict(call_id=r['call_id'], output_tokens=r.get('output_tokens'),
                            final_line=r['answer'].strip().splitlines()[-1] if r['answer'].strip() else '',
                            truncated=r.get('truncated'), finish_reason=r.get('finish_reason'),
                            near_output_limit=(r.get('output_tokens') or 0) >= meta['config']['run']['max_output_tokens'] - 1))
            variation = {}
            for task in ('maths', 'summarisation'):
                answers = defaultdict(set)
                for r in cr:
                    if r['task_type'] == task:
                        answers[r['prompt_id']].add(r['answer'])
                variation[task] = dict(varying=sum(len(v) > 1 for v in answers.values()), prompts=len(answers))
                group = [r for r in cr if r['task_type'] == task]
                all_calls = distribution(r['latency_s'] for r in group)
                swap_free = distribution(r['latency_s'] for r in group if r.get('swapping_occurred') is False)
                latency.append((cid, task, all_calls, swap_free))
            missing_energy = Counter(r.get('energy_missing_reason') for r in cr if r.get('energy_j') is None)
            result['configurations'].append(dict(configuration_id=cid, maths=dict(maths), variation=variation,
                missing_energy=dict(missing_energy), missing_memory=sum(r.get('memory_peak_rss_bytes') is None for r in cr)))
            lines.append(f'| {cid} | {maths["correct"]} | {maths["wrong_parseable"]} | {maths["unparseable"]} | '
                         f'{variation["maths"]["varying"]}/{variation["maths"]["prompts"]} | '
                         f'{variation["summarisation"]["varying"]}/{variation["summarisation"]["prompts"]} |')
        for finding in report['knee']:
            for step in finding['steps']:
                a = next(g for g in report['groups'] if g['configuration_id'] == step['upper'] and g['task_type'] == finding['task_type'] and g['cache_stratum'] == 'all')
                b = next(g for g in report['groups'] if g['configuration_id'] == step['lower'] and g['task_type'] == finding['task_type'] and g['cache_stratum'] == 'all')
                result['variance'].append(dict(task=finding['task_type'], **step,
                    upper_latency_iqr=[a['latency_s']['q1'], a['latency_s']['q3']],
                    lower_latency_iqr=[b['latency_s']['q1'], b['latency_s']['q3']]))
    lines += ['', 'Latency: all completed measured calls versus known swap-free calls, seconds.', '',
              '| Configuration | Task | All p50 / p95 (n) | Swap-free p50 / p95 (n) |', '| --- | --- | --- | --- |']
    for cid, task, a, b in latency:
        def fmt(d):
            return f'{d["p50"]:.3f} / {d["p95"]:.3f} ({d["n"]})' if d['n'] else 'unavailable (0)'
        lines.append(f'| {cid} | {task} | {fmt(a)} | {fmt(b)} |')
    result['q3_unparseable_cases'] = dict(q3_format_cases)
    lines += ['', 'Q3 unparseable final-line diagnostics (registered scores unchanged):']
    for pid, cases in sorted(q3_format_cases.items()):
        kind = 'Possible output-budget cutoff; truncation metadata unavailable' if cases[0]['near_output_limit'] else 'Final-line format violation; not evidence by itself of a wrong mathematical value'
        lines.append(f'- {pid}: {len(cases)} calls. {kind}. Call IDs: ' + ', '.join(c['call_id'] for c in cases))
    result['latency'] = [dict(configuration_id=c, task=t, all=a, swap_free=b) for c, t, a, b in latency]
    lines += ['', '## Registered variance rule', '',
              'All-call latency IQR overlap AND absolute quality gap below 5 percentage points implies indistinguishable.', '',
              '| Task / step | Upper IQR s | Lower IQR s | Quality drop pp | Indistinguishable | Knee step |',
              '| --- | --- | --- | --- | --- | --- |']
    for s in result['variance']:
        drop = 'pending' if s['quality_drop'] is None else f'{100*s["quality_drop"]:.2f}'
        lines.append(f'| {s["task"]}: {s["upper"]} to {s["lower"]} | {s["upper_latency_iqr"]} | '
                     f'{s["lower_latency_iqr"]} | {drop} | {s["indistinguishable"]} | {s["qualifies"]} |')
    lines += ['', '## Costs and collection', '']
    for run in result['runs']:
        lines.append(f'- {Path(run["directory"]).name}: {run["collection"]["completed_slots"]} completed slots; '
                     f'known list-price cost USD {run["known_list_price_cost"]}; '
                     f'{run["unknown_cost_failed_attempts"]} failed HTTP attempts have unknown cost. '
                     f'Automatic retries: {run["automatic_retry_attempts"]}.')
    lines += ['', '## Energy and memory qualifications', '']
    for c in result['configurations']:
        lines.append(f'- {c["configuration_id"]}: missing measured energy {c["missing_energy"]}; '
                     f'missing secondary memory {c["missing_memory"]}.')
    lines += ['', 'The local q6 collector recorded timing/parser errors and no post baseline. '
        'Offline inspection found valid raw power domains and delta flags, but the cumulative timeline exceeded '
        'the half-interval receipt-drift guard. Subsequent estimates were conservatively unavailable because '
        'the collector retains errors and does not re-anchor. Exact rejected receipt times were not retained, '
        'so jitter versus a missing interval cannot be established. The short held-out pre-check did not reach '
        'this longer-block failure. This is collection/timing uncertainty, not a report rendering bug. '
        'Do not recover estimates by inventing receipt times or relaxing guards. '
        'Cloud client energy was deliberately disabled.', '',
        'Local memory gaps include incomplete process coverage and the observed psutil permission/SystemError. '
        'These secondary gaps do not invalidate answers or the static weight metric.', '',
        '## Interpretation limits and kill criterion 2', '']
    lines += ['- ' + text for text in result['limitations']]
    output.mkdir(parents=True, exist_ok=False)
    (output / 'audit.json').write_text(json.dumps(result, indent=2) + '\n')
    (output / 'audit.md').write_text('\n'.join(lines) + '\n')
    print(output / 'audit.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.runs, args.output)
