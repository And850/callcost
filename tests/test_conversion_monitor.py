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
