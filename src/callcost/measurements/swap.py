"""Whole-machine vm_stat counter deltas, never process-level swap attribution."""

import re

from callcost.measurements.machine import command


def parse_vm_stat(text):
    if not text:
        return None
    page = re.search(r'page size of (\d+) bytes', text)
    values = {key.lower(): int(value) for key, value in
              re.findall(r'^(Pageins|Pageouts|Swapins|Swapouts):\s+(\d+)\.', text, re.MULTILINE)}
    if not page or int(page[1]) <= 0 or set(values) != {'pageins', 'pageouts', 'swapins', 'swapouts'}:
        return None
    return dict(values, page_size=int(page[1]))


def snapshot():
    return parse_vm_stat(command(['/usr/bin/vm_stat']))


def swap_delta(before, after):
    result = {'swapping_occurred': None, 'missing_reason': None}
    if not before or not after or before['page_size'] != after['page_size']:
        return dict(result, missing_reason='vm_stat counters unavailable or page size changed')
    for name in ('swapins', 'swapouts', 'pageouts'):
        pages = after[name] - before[name]
        if pages < 0:
            return {'swapping_occurred': None, 'missing_reason': 'vm_stat counter reset'}
        result[name + '_pages'] = pages
        result[name + '_bytes'] = pages * before['page_size']
    result['swapping_occurred'] = any(result[name + '_pages'] > 0 for name in ('swapins', 'swapouts', 'pageouts'))
    return result
