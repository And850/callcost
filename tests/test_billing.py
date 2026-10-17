import json
from decimal import Decimal

import pytest


def test_attempt_ledger_counts_manifest_once_and_retains_orphan(tmp_path):
    from callcost.billing import gemini_attempts
    (tmp_path / 'checkpoints').mkdir()
    (tmp_path / 'raw').mkdir()
    final = dict(call_id='c', provider='gemini', status='completed', list_price_cost='0.01', currency='USD')
    (tmp_path / 'checkpoints/1.json').write_text(json.dumps(final))
    (tmp_path / 'raw/c.attempts.json').write_text(json.dumps([
        dict(final, status='error', list_price_cost=None, attempt=1), dict(final, attempt=2)]))
    (tmp_path / 'raw/orphan.attempts.json').write_text(json.dumps([
        dict(call_id='orphan', status='error', list_price_cost='0.002', currency='USD', attempt=1)]))
    entries = gemini_attempts(tmp_path)
    assert len(entries) == 3
    assert sum((Decimal(x['list_price_cost']) for x in entries if x['list_price_cost'] is not None), Decimal(0)) == Decimal('.012')
    assert sum(x['list_price_cost'] is None for x in entries) == 1


def test_provider_billing_remains_pending_and_tax_is_not_assumed(tmp_path):
    from callcost.billing import reconcile_billing
    a = [dict(currency='USD', list_price_cost='1', status='completed')]
    result = reconcile_billing(tmp_path, a)
    assert result['billed_amount_from_provider'] is None and result['status'] == 'awaiting_provider_export'
    data = json.loads((tmp_path / 'billing.json').read_text())
    data.update(billed_amount_from_provider='1.21', evidence_source='invoice.csv')
    (tmp_path / 'billing.json').write_text(json.dumps(data))
    result = reconcile_billing(tmp_path, a)
    assert result['difference'] == '0.21' and result['status'] == 'unexplained'
    data['explained_adjustments'] = [{'amount': '.21', 'explanation': 'VAT on invoice', 'evidence_source': 'invoice.csv row 2'}]
    (tmp_path / 'billing.json').write_text(json.dumps(data))
    result = reconcile_billing(tmp_path, a)
    assert result['unexplained_difference'] == '0.00' and result['status'] == 'explained'
    data['scope'] = 'entire_billing_account'
    (tmp_path / 'billing.json').write_text(json.dumps(data))
    assert reconcile_billing(tmp_path, a)['status'] == 'not_comparable'


def test_unknown_attempt_cost_prevents_claiming_reconciled_total(tmp_path):
    from callcost.billing import reconcile_billing
    a = [dict(currency='USD', list_price_cost='1', status='completed'), dict(currency='USD', list_price_cost=None, status='error')]
    reconcile_billing(tmp_path, a)
    data = json.loads((tmp_path / 'billing.json').read_text())
    data.update(billed_amount_from_provider='1', evidence_source='invoice.csv')
    (tmp_path / 'billing.json').write_text(json.dumps(data))
    assert reconcile_billing(tmp_path, a)['status'] == 'unexplained'
    data['unknown_attempts_explanation'] = 'Invoice confirms failed requests were not charged'
    (tmp_path / 'billing.json').write_text(json.dumps(data))
    assert reconcile_billing(tmp_path, a)['status'] == 'matched'
    data['billed_amount_from_provider'] = 'NaN'
    (tmp_path / 'billing.json').write_text(json.dumps(data))
    with pytest.raises(ValueError):
        reconcile_billing(tmp_path, a)
