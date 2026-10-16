"""Energy estimate, whole-machine delta, for explicitly recorded SoC domains."""

import json
import math
import plistlib
import subprocess
import threading
import time

DOMAINS = ['cpu_power', 'gpu_power', 'ane_power']
SCOPE = 'estimate, whole-machine delta; CPU + GPU + ANE; client device only'


def parse_power_sample(payload, received_monotonic):
    sample = plistlib.loads(payload)
    if sample.get('is_delta') is not True:
        raise ValueError('Power timing requires provider delta intervals')
    seconds = sample['elapsed_ns'] / 1_000_000_000
    processor = sample.get('processor', {})
    values = [processor.get(key) for key in DOMAINS]
    if not seconds > 0 or not all(type(v) in (float, int) and math.isfinite(v) and v >= 0 for v in values):
        raise ValueError('Unsupported powermetrics sample or missing power domains')
    return {'start': received_monotonic - seconds, 'end': received_monotonic,
            'watts': sum(values) / 1000, 'domains': DOMAINS, 'elapsed_s': seconds,
            'timing_basis': 'receipt monotonic minus reported elapsed_ns',
            'power_source_unit': 'mW', 'timestamp_raw': str(sample.get('timestamp'))}


def align_power_sample(sample, previous_end):
    """Anchor once; subsequent device-reported delta intervals are contiguous.

    Receipt jitter is retained, not misinterpreted as overlapping power windows.
    A discrepancy of half a sample interval makes timing unavailable.
    The first receipt anchor has unknown delivery lag; attribution is approximate.
    """
    received = sample['end']
    elapsed = sample.get('elapsed_s', sample['end'] - sample['start'])
    end = received if previous_end is None else previous_end + elapsed
    if elapsed <= 0 or abs(received - end) >= elapsed / 2:
        raise ValueError('Power timing differs by at least half a reported sample interval')
    return dict(sample, start=end-elapsed, end=end, received_monotonic=received,
                receipt_lag_s=received-end,
                timing_basis='first receipt anchor plus cumulative reported elapsed_ns; receipt lag retained')


def integrate_delta(samples, start, end, baseline_watts):
    selected = sorted((s for s in samples if s['start'] < end and s['end'] > start), key=lambda s: s['start'])
    if end <= start or len(selected) < 2:
        return None, 'Fewer than two overlapping power samples'
    coverage = 0.0
    energy = 0.0
    cursor = start
    for sample in selected:
        left, right = max(start, sample['start']), min(end, sample['end'])
        if left < cursor - 0.01:
            return None, 'Power sample intervals overlap; timing attribution uncertain'
        duration = max(0, right - max(left, cursor))
        energy += (sample['watts'] - baseline_watts) * duration
        coverage += duration
        cursor = right
    if coverage / (end - start) < .9:
        return None, 'Less than 90% power-sample coverage'
    return energy, None


class PowerCollector:
    def __init__(self, directory, sample_ms):
        self.directory = directory
        self.sample_ms = sample_ms
        self.samples = []
        self.timeline_end = None
        self.errors = []
        self.process = None
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        self.directory.mkdir()
        self.stderr = (self.directory / 'stderr.txt').open('wb')
        args = ['sudo', '-n', '/usr/bin/powermetrics', '--format', 'plist', '--sample-rate',
                str(self.sample_ms), '--samplers', 'cpu_power,gpu_power,ane_power', '--buffer-size', '0']
        try:
            self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=self.stderr)
        except OSError as error:
            self.stderr.close()
            self.errors.append(str(error))
            return False
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()
        # Wait for supported data or a failed non-interactive sudo invocation.
        deadline = time.monotonic() + max(3, self.sample_ms / 1000 * 4)
        while time.monotonic() < deadline and self.process.poll() is None and not self.samples:
            time.sleep(.05)
        return bool(self.samples)

    def _read(self):
        pending = b''
        with (self.directory / 'raw.plist').open('wb') as raw, (self.directory / 'samples.jsonl').open('w') as parsed:
            while not self.stop_event.is_set():
                chunk = self.process.stdout.read1(65536)
                if not chunk:
                    break
                raw.write(chunk)
                raw.flush()
                pending += chunk
                while b'\0' in pending:
                    payload, pending = pending.split(b'\0', 1)
                    if not payload.strip():
                        continue
                    try:
                        sample = align_power_sample(parse_power_sample(payload, time.perf_counter()), self.timeline_end)
                        self.timeline_end = sample['end']
                        self.samples.append(sample)
                        parsed.write(json.dumps(sample) + '\n')
                        parsed.flush()
                    except (ValueError, KeyError, TypeError, plistlib.InvalidFileException) as error:
                        self.errors.append(f'Unsupported power sample: {type(error).__name__}')

    def baseline(self, seconds):
        start = time.perf_counter()
        time.sleep(seconds)
        end = time.perf_counter()
        selected = [s for s in self.samples if start <= s['start'] and s['end'] <= end]
        duration = sum(s['end'] - s['start'] for s in selected)
        if len(selected) < 2 or duration < seconds * .8:
            return None
        return sum(s['watts'] * (s['end'] - s['start']) for s in selected) / duration

    def estimate(self, start, end, baseline):
        if baseline is None:
            return None, 'Idle power baseline unavailable'
        if self.errors:
            return None, 'Unsupported or invalid power sample encountered'
        # Capture the interval containing the end of the call; this wait is outside latency.
        time.sleep(self.sample_ms / 1000 * 1.2)
        return integrate_delta(self.samples, start, end, baseline)

    def close(self):
        self.stop_event.set()
        if self.process:
            if self.process.poll() is None:
                try:
                    self.process.terminate()
                except PermissionError:
                    subprocess.run(['/usr/bin/sudo', '-n', '/bin/kill', '-TERM', str(self.process.pid)],
                                   capture_output=True, check=True, timeout=5)
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        self.process.kill()
                    except PermissionError:
                        subprocess.run(['/usr/bin/sudo', '-n', '/bin/kill', '-KILL', str(self.process.pid)],
                                       capture_output=True, check=True, timeout=5)
                    self.process.wait(timeout=5)
            if self.thread:
                self.thread.join(timeout=5)
            self.process.stdout.close()
            self.stderr.close()


def baseline_assessment(before, after, calls):
    """Expose drift without introducing an unregistered significance cutoff."""
    drift = None if before is None or after is None else after - before
    status = ('baseline_unavailable' if before is None else
              'post_baseline_unavailable' if after is None else
              'baseline_shift_observed' if drift != 0 else 'no_observed_shift')
    return {'status': status, 'drift_watts': drift,
            'negative_delta_call_ids': [c['call_id'] for c in calls
                                        if c['energy_j'] is not None and c['energy_j'] < 0],
            'interpretation': 'Descriptive qualification, not a significance test; no registered drift cutoff'}
