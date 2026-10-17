"""Inventory every saved Gemini HTTP attempt under runs/, without inference."""

import argparse
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from callcost.billing import amount, gemini_attempts, reconcile_billing
from callcost.storage import write_json

FIELDS = ('call_id', 'attempt', 'configuration_id', 'segment_id', 'schedule_index', 'phase', 'status',
          'started_at', 'http_status', 'provider_error_status', 'error', 'input_tokens', 'output_tokens',
          'thinking_tokens', 'billable_output_tokens', 'list_price_cost', 'currency', 'run_directory',
          'source', 'raw_request')


def build(runs, output):
    output.mkdir(parents=True, exist_ok=False)
    entries, inventory = [], []
    for directory in sorted(runs.iterdir()):
        if not directory.is_dir():
            continue
        attempts = gemini_attempts(directory)
        raw = []
        for f in (directory / 'raw').glob('*.request.json'):
            value = json.loads(f.read_text())
            if 'contents' in value and 'generationConfig' in value:
                raw.append(f.resolve())
        represented = {Path(x['raw_request']).resolve() for x in attempts}
        if set(raw) != represented:
            raise ValueError(f'Raw Gemini request/ledger mismatch in {directory}; investigate before claiming totals')
        if not attempts and not (directory / 'metadata.json').exists():
            continue
        inventory.append(dict(run=directory.name, gemini_http_attempts=len(attempts), raw_request_files=len(raw)))
        entries.extend({k: x.get(k) for k in FIELDS} for x in attempts)
    groups = defaultdict(list)
    for entry in entries:
        groups[(Path(entry['run_directory']).name, entry['segment_id'])].append(entry)
    totals = []
    for (run, segment), calls in groups.items():
        totals.append(dict(run=run, segment_id=segment, attempts=len(calls),
            completed=sum(x['status'] == 'completed' for x in calls),
            failed=sum(x['status'] != 'completed' for x in calls),
            known_list_price_cost=str(sum((amount(x['list_price_cost']) for x in calls if x['list_price_cost'] is not None), Decimal(0))),
            unknown_cost_attempts=sum(x['list_price_cost'] is None for x in calls)))
    billing = reconcile_billing(output, entries, scope='all_recorded_repository_gemini_calls')
    known = amount(billing['known_list_price_cost_excluding_tax'])
    vat_scenario = known * Decimal('.21')
    result = dict(scope='Saved Gemini inference attempts under this repository runs directory; not proof of unrecorded usage or provider charges',
                  attempts=len(entries), completed=sum(x['status'] == 'completed' for x in entries),
                  failed=sum(x['status'] != 'completed' for x in entries),
                  known_list_price_cost_excluding_tax=str(known), unknown_cost_attempts=billing['unknown_cost_attempts'],
                  scenario_only_vat_rate='0.21', scenario_only_vat=str(vat_scenario),
                  scenario_only_total_including_vat=str(known + vat_scenario),
                  vat_application_confirmed=False, billing_reconciliation=billing,
                  run_inventory=inventory, segment_totals=totals, http_attempts=entries)
    write_json(output / 'ledger.json', result)
    lines = ['# Repository Gemini cost ledger', '', result['scope'], '',
             '| Run / segment | Completed | Failed | Known list-price USD, excluding tax | Unknown-cost attempts |',
             '| --- | --- | --- | --- | --- |']
    for row in totals:
        lines.append(f'| {row["run"]} / {row["segment_id"]} | {row["completed"]} | {row["failed"]} | '
                     f'{row["known_list_price_cost"]} | {row["unknown_cost_attempts"]} |')
    lines += ['', f'Total: {result["attempts"]} HTTP attempts, {result["completed"]} completed, {result["failed"]} failed.',
              f'Known list-price cost excluding tax: USD {known}. Unknown-cost attempts: {billing["unknown_cost_attempts"]}.', '',
              f'Illustration only: 21% VAT adds USD {vat_scenario}, giving USD {known + vat_scenario}. '
              'VAT application to the prepaid balance is not established by this arithmetic. '
              'The smoke may have been free-tier; list-price equivalent is not an invoice.', '',
              'Provider billing reconciliation:', json.dumps(billing, indent=2), '',
              'Fill billing.json from the provider export with the same scope, currency and usage period. '
              'Do not count the initial cloud segment twice; this ledger includes it within the completed run. '
              'Failed requests without usage have unknown cost, not zero.']
    (output / 'report.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[:15]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, default=Path('runs'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.runs, args.output)
