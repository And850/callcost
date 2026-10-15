import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/monitor_conversion.py'


def test_monitor_preserves_process_result_and_memory_samples(tmp_path):
    output = tmp_path / 'memory.jsonl'
    result = subprocess.run([sys.executable, str(SCRIPT), '--output', str(output), '--',
                             sys.executable, '-c', 'import time; time.sleep(0.1)'], capture_output=True)
    assert result.returncode == 0, result.stderr
    samples = [json.loads(line) for line in output.read_text().splitlines()]
    summary = json.loads(output.with_suffix('.summary.json').read_text())
    assert summary['sample_count'] == len(samples) >= 1
    assert summary['exit_code'] == 0 and not summary['stopped_for_memory_or_interrupt']
    assert summary['minimum_available_bytes'] > 0
    assert all(sample['swap_used_bytes'] >= 0 for sample in samples)


def test_memory_stop_cleanup_kills_descendant_even_after_shell_exits(tmp_path):
    import importlib.util
    import os
    import signal
    import time

    import psutil

    spec = importlib.util.spec_from_file_location('conversion_monitor', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    child_id = tmp_path / 'child.pid'
    ready = tmp_path / 'ready'
    child_code = ('import signal,time; from pathlib import Path; '
                  'signal.signal(signal.SIGTERM, signal.SIG_IGN); '
                  f'Path({str(ready)!r}).touch(); time.sleep(60)')
    parent_code = (f'import subprocess,sys,time; from pathlib import Path; '
                   f'p=subprocess.Popen([sys.executable,"-c",{child_code!r}]); '
                   f'Path({str(child_id)!r}).write_text(str(p.pid)); time.sleep(60)')
    parent = subprocess.Popen([sys.executable, '-c', parent_code], start_new_session=True)
    child = None
    try:
        deadline = time.monotonic() + 5
        while not child_id.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        child = psutil.Process(int(child_id.read_text()))
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert ready.exists()
        module.terminate_group(parent, grace_seconds=.2)
        deadline = time.monotonic() + 2
        while child.is_running() and child.status() != psutil.STATUS_ZOMBIE and time.monotonic() < deadline:
            time.sleep(.01)
        assert not child.is_running() or child.status() == psutil.STATUS_ZOMBIE
    finally:
        try:
            os.killpg(parent.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        parent.wait(timeout=5)
