"""Whole-machine swap/compressor observations, never process attribution."""

import re
import time
from decimal import Decimal

from callcost.measurements.machine import command


def parse_vm_stat(text):
    if not text:
        return None
    page = re.search(r'page size of (\d+) bytes', text)
    values = {key.lower(): int(value) for key, value in
              re.findall(r'^(Pageins|Pageouts|Swapins|Swapouts):\s+(\d+)\.', text, re.MULTILINE)}
    if not page or int(page[1]) <= 0 or set(values) != {'pageins', 'pageouts', 'swapins', 'swapouts'}:
        return None
    compressed = re.search(r'^Pages occupied by compressor:\s+(\d+)\.', text, re.MULTILINE)
    return dict(values, page_size=int(page[1]),
                compressed_memory_bytes=int(compressed[1]) * int(page[1]) if compressed else None)


def parse_swapusage(text):
    match = re.search(r'\bused\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*([BKMGTP])\b', text or '', re.IGNORECASE)
    if not match:
        return None
    return int(Decimal(match[1]) * 1024 ** 'BKMGTP'.index(match[2].upper()))


def snapshot():
    started = time.perf_counter()
    vm_stat = command(['/usr/bin/vm_stat'])
    swapusage = command(['/usr/sbin/sysctl', '-n', 'vm.swapusage'])
    values = parse_vm_stat(vm_stat) or {}
    return dict(values, swap_used_bytes=parse_swapusage(swapusage),
                vm_stat_raw=vm_stat, swapusage_raw=swapusage,
                started_monotonic=started, ended_monotonic=time.perf_counter())


def swap_delta(before, after):
    result = {'swapping_occurred': None, 'missing_reason': None, 'swap_volume_bytes': None,
              'swap_snapshot_before': before, 'swap_snapshot_after': after}
    for source, target in (('swap_used_bytes', 'swap_used'), ('compressed_memory_bytes', 'compressed_memory')):
        for label, reading in (('before', before), ('after', after)):
            result[f'{target}_{label}_bytes'] = (reading or {}).get(source)
    result['swap_observation_missing'] = {
        key: ('vm.swapusage unavailable' if key.startswith('swap_used') else 'Compressor reading unavailable')
        for key, value in result.items() if key.endswith('_bytes') and key != 'swap_volume_bytes' and value is None}
    if not before or not after or not before.get('page_size') or before.get('page_size') != after.get('page_size'):
        return dict(result, missing_reason='vm_stat counters unavailable or page size changed')
    for name in ('swapins', 'swapouts', 'pageouts'):
        if before.get(name) is None or after.get(name) is None:
            return dict(result, missing_reason='vm_stat counters unavailable')
        pages = after[name] - before[name]
        if pages < 0:
            return dict(result, missing_reason='vm_stat counter reset')
        result[name + '_pages'] = pages
        result[name + '_bytes'] = pages * before['page_size']
    result['swap_volume_bytes'] = result['swapins_bytes'] + result['swapouts_bytes']
    result['swapping_occurred'] = result['swap_volume_bytes'] > 0
    return result
