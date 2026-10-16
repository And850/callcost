"""Held-out idle observations to contextualise whole-machine swap activity."""

import time

from callcost.measurements.swap import snapshot, swap_delta

IDLE_SECONDS = 120
REQUIRED_SWAP_FIELDS = ('swap_volume_bytes', 'swap_used_before_bytes', 'swap_used_after_bytes',
                        'compressed_memory_before_bytes', 'compressed_memory_after_bytes')


def observe_idle(label, seconds=IDLE_SECONDS, progress=print):
    progress(f'Idle diagnostic: {label}, {seconds} seconds; no inference', flush=True)
    start = time.perf_counter()
    before = snapshot()
    while time.perf_counter() - start < seconds:
        time.sleep(min(30, seconds - (time.perf_counter() - start)))
        progress(f'Idle diagnostic: {label}, {time.perf_counter() - start:.0f}/{seconds} seconds', flush=True)
    after = snapshot()
    return dict(label=label, duration_s=time.perf_counter() - start, **swap_delta(before, after))


def assess_precheck(rows, blocks, windows, configuration_ids):
    calls = [r for r in rows if r['phase'] == 'precheck' and r['status'] == 'completed']
    reasons = []
    for identifier in configuration_ids:
        group = [r for r in calls if r['configuration_id'] == identifier]
        if len(group) != 3:
            reasons.append(f'{identifier}: requires three completed held-out calls')
    if any(any(r.get(key) is None for key in REQUIRED_SWAP_FIELDS) for r in calls):
        reasons.append('Required swap/storage/compressor observations unavailable')
    energy_calls = sum(r.get('energy_j') is not None for r in calls)
    if energy_calls != len(calls):
        reasons.append('In-call energy unavailable for one or more completed calls')
    for identifier, segment in {(r['configuration_id'], r['segment_id']) for r in calls}:
        for label in ('unloaded', 'loaded-before', 'loaded-after'):
            found = [w for w in windows if w['segment_id'] == segment and w['label'] == label
                     and (label == 'unloaded' or w['configuration_id'] == identifier)]
            if not found or any(any(w.get(key) is None for key in REQUIRED_SWAP_FIELDS) for w in found):
                reasons.append(f'{identifier}/{segment}: missing valid {label} diagnostic')
        found = [b for b in blocks if b['configuration_id'] == identifier and b['segment_id'] == segment]
        if not found or any(b.get('baseline_watts') is None or b.get('post_baseline_watts') is None or b.get('errors') for b in found):
            reasons.append(f'{identifier}/{segment}: missing valid energy baseline qualification')
    return dict(valid=not reasons, reasons=reasons, completed_calls=len(calls), energy_calls=energy_calls,
                interpretation='Idle/inference comparison is whole-machine evidence, not causal process attribution')
