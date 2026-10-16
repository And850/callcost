import plistlib

import pytest

from callcost.measurements.energy import integrate_delta, parse_power_sample
from callcost.measurements.memory import peak_rss
from callcost.records import CallResult
from callcost.thinking import verify_thinking_off


def test_rss_uses_contemporaneous_sum_and_rejects_missing_workers():
    samples = [{'time': 1.1, 'rss': {'10': 100, '11': 10}, 'error': None},
               {'time': 1.2, 'rss': {'10': 10, '11': 100}, 'error': None}]
    assert peak_rss(samples, 1, 2) == (110, None)
    samples[1]['error'] = 'worker exited'
    value, reason = peak_rss(samples, 1, 2)
    assert value is None and reason
    assert peak_rss([], 1, 2)[0] is None


def test_power_sample_units_and_domain_scope():
    sample = parse_power_sample(plistlib.dumps({'elapsed_ns': 250_000_000, 'is_delta': True,
        'processor': {'cpu_power': 1000, 'gpu_power': 2000, 'ane_power': 0}}), 10)
    assert sample['start'] == 9.75 and sample['end'] == 10
    assert sample['watts'] == 3
    assert sample['domains'] == ['cpu_power', 'gpu_power', 'ane_power']
    with pytest.raises(ValueError):
        parse_power_sample(plistlib.dumps({'elapsed_ns': 1, 'is_delta': True, 'processor': {'cpu_power': 1}}), 10)


def test_integrates_overlap_keeps_negative_and_rejects_gaps():
    samples = [{'start': 0, 'end': 1, 'watts': 2}, {'start': 1, 'end': 2, 'watts': 4}]
    energy, reason = integrate_delta(samples, .5, 1.5, baseline_watts=4)
    assert energy == -1 and reason is None
    assert integrate_delta(samples, 0, 3, baseline_watts=1)[0] is None
    assert integrate_delta(samples[:1], .5, .75, baseline_watts=1)[0] is None
    assert integrate_delta(samples + samples, 0, 2, baseline_watts=1)[0] is None


@pytest.mark.parametrize('tokens,text,reasoning', [(1, '4', False), (0, '<think>x</think>4', False),
                                                  (None, '4', False), (0, '4', True)])
def test_pilot_rejects_unverified_or_visible_thinking(tokens, text, reasoning):
    result = CallResult(status='completed', answer=text, thinking_tokens=tokens)
    result.reasoning_content_observed = reasoning
    with pytest.raises(ValueError):
        verify_thinking_off(result)


def test_pilot_accepts_zero_tokens_and_no_thinking():
    result = CallResult(status='completed', answer='Answer: 4', thinking_tokens=0)
    assert verify_thinking_off(result)['verified'] is True


def test_explicit_roots_cannot_measure_the_benchmark_process():
    import os

    from callcost.measurements.memory import discover_processes
    with pytest.raises(ValueError, match='LM Studio'):
        discover_processes([os.getpid()])


def test_empty_measured_answer_is_not_automatically_an_infrastructure_failure():
    result = CallResult(status='completed', answer='', thinking_tokens=0)
    assert verify_thinking_off(result, require_answer=False)['verified']


def test_energy_assessment_exposes_drift_missing_baseline_and_negative_deltas():
    from callcost.measurements.energy import baseline_assessment
    calls = [{'call_id': 'negative', 'energy_j': -2}, {'call_id': 'positive', 'energy_j': 3},
             {'call_id': 'missing', 'energy_j': None}]
    value = baseline_assessment(2, 4, calls)
    assert value['status'] == 'baseline_shift_observed' and value['drift_watts'] == 2
    assert value['negative_delta_call_ids'] == ['negative']
    assert baseline_assessment(2, None, calls)['status'] == 'post_baseline_unavailable'
    assert baseline_assessment(2, 2, calls)['status'] == 'no_observed_shift'


def test_native_node_worker_identity_and_sampling_boundaries():
    from callcost.measurements.memory import process_role
    app = '/Applications/LM Studio.app/Contents/Resources/app/.webpack/lib/llmworker.js'
    node = '/Users/example/.cache/lm-studio/.internal/utils/node'
    assert process_role(node, f'{node} -e wrapper {app}') == (False, True)
    assert process_role('/usr/bin/python3', 'my-llmworker.js') == (False, False)
    assert peak_rss([{'started': .9, 'time': 1.1, 'rss': {'a': 100}, 'error': None}], 1, 2)[0] is None


def test_footprint_peak_sums_same_instant_and_requires_complete_processes():
    from callcost.measurements.memory import peak_footprint
    samples = [{'time': 1.1, 'footprint': {'a': 100, 'b': 20}, 'error': None},
               {'time': 1.2, 'footprint': {'a': 20, 'b': 110}, 'error': None}]
    assert peak_footprint(samples, 1, 2) == (130, None)
    samples[1]['footprint'] = {'a': 200}
    assert peak_footprint(samples, 1, 2)[0] is None


def test_swap_deltas_do_not_confuse_pageins_with_swapins():
    from callcost.measurements.swap import parse_vm_stat, swap_delta
    first = parse_vm_stat('Mach Virtual Memory Statistics: (page size of 16384 bytes)\n'
                          'Pageins: 20.\nPageouts: 4.\nSwapins: 6.\nSwapouts: 8.\n')
    second = dict(first, pageins=99, swapins=8)
    result = swap_delta(first, second)
    assert result['swapins_pages'] == 2 and result['swapins_bytes'] == 32768
    assert result['pageouts_pages'] == 0 and result['swapping_occurred'] is True
    assert swap_delta(first, dict(first, pageins=99))['swapping_occurred'] is False
    assert swap_delta(first, dict(first, pageouts=5))['swapping_occurred'] is False
    assert swap_delta(first, dict(first, swapins=5))['swapping_occurred'] is None
    assert swap_delta(first, None)['swapping_occurred'] is None
    assert parse_vm_stat('Pageouts: 0.') is None


def test_root_powermetrics_cleanup_uses_noninteractive_signal_if_needed(tmp_path, monkeypatch):
    import io

    from callcost.measurements.energy import PowerCollector
    class RootProcess:
        pid = 12345
        stdout = io.BytesIO()
        def poll(self):
            return None
        def terminate(self):
            raise PermissionError('root process')
        def wait(self, timeout):
            return 0
    commands = []
    def run(args, **kwargs):
        commands.append(args)
    monkeypatch.setattr('callcost.measurements.energy.subprocess.run', run)
    collector = PowerCollector(tmp_path, 250)
    collector.process = RootProcess()
    collector.stderr = io.BytesIO()
    collector.close()
    assert commands == [['/usr/bin/sudo', '-n', '/bin/kill', '-TERM', '12345']]


@pytest.mark.parametrize('explicit', [False, True])
def test_headless_daemon_is_a_memory_root_but_does_not_replace_worker_evidence(monkeypatch, explicit):
    from callcost.measurements.memory import discover_processes

    class Process:
        def __init__(self, pid, executable, args):
            self.pid, self.executable, self.args = pid, executable, args
            self.info = {'pid': pid, 'exe': executable, 'cmdline': args}

        def exe(self):
            return self.executable

        def cmdline(self):
            return self.args

        def children(self, recursive):
            return [worker] if self.pid == 10 else []

    daemon = Process(10, '/Users/example/.lmstudio/llmster/bin/llmster', [])
    worker = Process(11, '/Users/example/.lmstudio/extensions/backends/mlx/worker',
                     ['/Users/example/.lmstudio/extensions/backends/mlx/worker'])
    unrelated = Process(12, '/tmp/llmster', [])
    processes = [daemon, worker, unrelated]
    monkeypatch.setattr('callcost.measurements.memory.psutil.process_iter', lambda attrs: iter(processes))
    monkeypatch.setattr('callcost.measurements.memory.psutil.Process', lambda pid: daemon if pid == 10 else unrelated)
    found = discover_processes([10] if explicit else [])
    assert {p.pid for p in found} == {10, 11}
    with pytest.raises(ValueError, match='recognised LM Studio'):
        discover_processes([12])
    processes[:] = [daemon]
    # A server without a recognised inference worker cannot establish coverage.
    monkeypatch.setattr(daemon, 'children', lambda recursive: [])
    with pytest.raises(ValueError, match='worker not identified'):
        discover_processes([10] if explicit else [])


def test_swap_usage_compressor_and_volume_are_recorded_without_pageout_false_positive(monkeypatch):
    from callcost.measurements.swap import snapshot, swap_delta
    readings = iter([
        'Mach Virtual Memory Statistics: (page size of 16384 bytes)\n'
        'Pageins: 20.\nPageouts: 4.\nSwapins: 6.\nSwapouts: 8.\nPages occupied by compressor: 100.\n',
        'total = 1024.00M used = 128.50M free = 895.50M (encrypted)',
    ])
    monkeypatch.setattr('callcost.measurements.swap.command', lambda args: next(readings))
    before = snapshot()
    assert before['swap_used_bytes'] == 134742016
    assert before['compressed_memory_bytes'] == 1638400
    assert before['vm_stat_raw'] and before['swapusage_raw']
    after = dict(before, swapins=8, swapouts=11, compressed_memory_bytes=1802240, swap_used_bytes=268435456)
    delta = swap_delta(before, after)
    assert delta['swapins_bytes'] == 32768 and delta['swapouts_bytes'] == 49152
    assert delta['swap_volume_bytes'] == 81920
    assert delta['swap_used_before_bytes'] == 134742016
    assert delta['swap_used_after_bytes'] == 268435456
    assert delta['compressed_memory_before_bytes'] == 1638400
    assert delta['compressed_memory_after_bytes'] == 1802240
    assert swap_delta(before, dict(before, pageouts=99))['swapping_occurred'] is False
    unknown = swap_delta(before, None)
    assert unknown['swap_used_before_bytes'] == 134742016
    assert unknown['swap_volume_bytes'] is None


def test_power_timeline_uses_reported_intervals_and_retains_receipt_jitter():
    from callcost.measurements.energy import align_power_sample
    samples = []
    end = None
    for receipt in (.25, .52, .75, 1.02):
        raw = dict(start=receipt-.25, end=receipt, watts=10)
        sample = align_power_sample(raw, end)
        samples.append(sample)
        end = sample['end']
    assert samples[1]['start'] == .25 and samples[1]['end'] == .5
    assert samples[1]['received_monotonic'] == .52
    energy, reason = integrate_delta(samples, .25, .75, 2)
    assert energy == 4 and reason is None
    # A real missing/delayed interval cannot be silently repaired by alignment.
    with pytest.raises(ValueError, match='timing'):
        align_power_sample(dict(start=1.75, end=2, watts=10), .25)
    with pytest.raises(ValueError, match='timing'):
        align_power_sample(dict(start=.5, end=.75, watts=10), .25)


@pytest.mark.parametrize('delta', [False, None])
def test_power_timeline_requires_provider_delta_intervals(delta):
    payload = {'elapsed_ns': 250_000_000, 'is_delta': delta,
               'processor': {'cpu_power': 1000, 'gpu_power': 0, 'ane_power': 0}}
    if delta is None:
        payload.pop('is_delta')
    with pytest.raises(ValueError, match='delta'):
        parse_power_sample(plistlib.dumps(payload), 10)
