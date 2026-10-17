"""Saved Gemini HTTP-attempt ledger and evidence-based billing reconciliation."""

import csv
import json
from decimal import Decimal, InvalidOperation

from callcost.storage import write_json


def amount(value):
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Billing amounts must be decimal numbers') from None
    if not number.is_finite():
        raise ValueError('Billing amounts must be finite')
    return number


def gemini_attempts(directory):
    checkpoints = sorted((directory / 'checkpoints').glob('*.json'))
    if checkpoints:
        rows = [json.loads(p.read_text()) for p in checkpoints]
    elif (directory / 'calls.csv').exists():
        with (directory / 'calls.csv').open() as stream:
            rows = list(csv.DictReader(stream))
    else:
        rows = []
    by_id = {r['call_id']: r for r in rows if r.get('provider') == 'gemini'}
    entries, represented = [], set()
    for path in sorted((directory / 'raw').glob('*.attempts.json')):
        attempts = json.loads(path.read_text())
        for index, attempt in enumerate(attempts):
            call_id = attempt['call_id']
            row = by_id.get(call_id, {})
            number = attempt.get('attempt', index + 1)
            raw_id = call_id if index == len(attempts) - 1 else f'{call_id}.attempt-{number}'
            entries.append(dict(attempt, call_id=call_id, attempt=number,
                phase=row.get('phase'), segment_id=row.get('segment_id'), schedule_index=row.get('schedule_index'),
                source=str(path), raw_request=str(directory / 'raw' / f'{raw_id}.request.json')))
            represented.add(call_id)
    for call_id, row in by_id.items():
        if call_id not in represented:
            entries.append(dict(row, attempt=1, source='checkpoint or legacy CSV',
                                raw_request=str(directory / 'raw' / f'{call_id}.request.json')))
    identities = [(x['call_id'], x['attempt']) for x in entries]
    if len(identities) != len(set(identities)):
        raise ValueError('Duplicate Gemini HTTP attempt identities')
    for entry in entries:
        if entry.get('list_price_cost') == '':
            entry['list_price_cost'] = None
        entry['run_directory'] = str(directory.resolve())
    return entries


def reconcile_billing(directory, entries, scope='this_run'):
    currencies = {x.get('currency') for x in entries if x.get('list_price_cost') is not None}
    currencies.discard(None)
    currencies.discard('')
    if len(currencies) > 1:
        raise ValueError('Cannot sum provider costs across currencies')
    known = sum((amount(x['list_price_cost']) for x in entries if x.get('list_price_cost') is not None), Decimal(0))
    unknown = sum(x.get('list_price_cost') is None for x in entries)
    template = dict(billed_amount_from_provider=None, currency=next(iter(currencies)) if len(currencies) == 1 else 'USD',
                    scope=scope, period_start=None, period_end=None, evidence_source=None,
                    explained_adjustments=[], unknown_attempts_explanation=None,
                    note='Pending provider export. List price excludes tax. Do not infer VAT from the balance display.')
    path = directory / 'billing.json'
    if not path.exists():
        write_json(path, template)
    supplied = json.loads(path.read_text())
    result = dict(known_list_price_cost_excluding_tax=str(known), unknown_cost_attempts=unknown,
                  billed_amount_from_provider=supplied.get('billed_amount_from_provider'),
                  currency=supplied.get('currency'), scope=supplied.get('scope'),
                  evidence_source=supplied.get('evidence_source'), period_start=supplied.get('period_start'),
                  period_end=supplied.get('period_end'), difference=None, explained_adjustments=[],
                  unexplained_difference=None, status='awaiting_provider_export',
                  unknown_attempts_explanation=supplied.get('unknown_attempts_explanation'))
    if result['billed_amount_from_provider'] is None:
        return result
    billed = amount(result['billed_amount_from_provider'])
    if currencies != {result['currency']} or result['scope'] != scope:
        result['status'] = 'not_comparable'
        return result
    difference = billed - known
    explained = Decimal(0)
    for adjustment in supplied.get('explained_adjustments', []):
        if not adjustment.get('explanation') or not adjustment.get('evidence_source'):
            raise ValueError('Each explained billing adjustment needs an explanation and evidence source')
        explained += amount(adjustment['amount'])
        result['explained_adjustments'].append(adjustment)
    residual = difference - explained
    result.update(difference=str(difference), unexplained_difference=str(residual), status='unexplained')
    if residual == 0 and supplied.get('evidence_source') and (not unknown or supplied.get('unknown_attempts_explanation')):
        result['status'] = 'explained' if explained != 0 else 'matched'
    return result
