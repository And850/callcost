"""Run the committed conversion commands while preserving memory/swap observations."""

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import psutil


def pressure_stop(available_bytes, swap_growth_bytes):
    # Preparation guard, not an experiment exclusion or a memory-footprint metric.
    return available_bytes < 512 * 1024**2 and swap_growth_bytes > 4 * 1024**3


def group_is_running(group_id):
    for member in psutil.process_iter(['pid', 'status']):
        try:
            if os.getpgid(member.pid) == group_id and member.info['status'] != psutil.STATUS_ZOMBIE:
                return True
        except (ProcessLookupError, PermissionError):
            continue
    return False


def terminate_group(process, grace_seconds=10):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait(timeout=5)
        return
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        process.poll()  # Reap an exited leader, but keep checking its descendants.
        if not group_is_running(process.pid):
            break
        time.sleep(.05)
    if group_is_running(process.pid):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('Supply a conversion command after --')
    if args.output.exists() or args.output.with_suffix('.summary.json').exists():
        parser.error('Memory log or summary already exists; use a new output name')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    baseline_swap = psutil.swap_memory().used
    started = time.monotonic()
    process = subprocess.Popen(command, start_new_session=True)
    root = psutil.Process(process.pid)
    low_since = None
    stopped = False
    samples = []
    try:
        with args.output.open('x') as stream:
            while process.poll() is None:
                now = time.monotonic()
                virtual, swap = psutil.virtual_memory(), psutil.swap_memory()
                members = []
                try:
                    for member in [root, *root.children(recursive=True)]:
                        try:
                            arguments = member.cmdline()
                            members.append({'pid': member.pid, 'created': member.create_time(),
                                            'rss_bytes': member.memory_info().rss,
                                            'name': member.name(),
                                            'conversion_output': arguments[arguments.index('--mlx-path') + 1]
                                            if '--mlx-path' in arguments else None})
                        except psutil.Error:
                            pass
                except psutil.Error:
                    pass
                sample = {'elapsed_s': now - started, 'monotonic_s': now,
                          'available_bytes': virtual.available, 'swap_used_bytes': swap.used,
                          'swap_growth_bytes': swap.used - baseline_swap, 'processes': members,
                          'process_group_rss_bytes': sum(p['rss_bytes'] for p in members)}
                samples.append(sample)
                stream.write(json.dumps(sample) + '\n')
                stream.flush()
                low = pressure_stop(virtual.available, sample['swap_growth_bytes'])
                low_since = (low_since if low_since is not None else now) if low else None
                if low_since is not None and now - low_since >= 10:
                    print('Stopping conversion: sustained low available memory and >4 GiB swap growth', flush=True)
                    stopped = True
                    break
                if len(samples) % 15 == 1:
                    print(f'Conversion monitor: available {virtual.available / 1e9:.2f} GB, '
                          f'swap {swap.used / 1e9:.2f} GB, elapsed {now - started:.0f}s', flush=True)
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
    except KeyboardInterrupt:
        stopped = True
    finally:
        if group_is_running(process.pid):
            terminate_group(process)
        else:
            process.wait(timeout=5)
        summary = {'command': command, 'exit_code': process.returncode, 'stopped_for_memory_or_interrupt': stopped,
                   'duration_s': time.monotonic() - started, 'sample_count': len(samples),
                   'minimum_available_bytes': min((s['available_bytes'] for s in samples), default=None),
                   'maximum_swap_growth_bytes': max((s['swap_growth_bytes'] for s in samples), default=None),
                   'maximum_process_group_rss_bytes': max((s['process_group_rss_bytes'] for s in samples), default=None),
                   'rss_note': 'Sampled process RSS can omit GPU allocations and double-count shared pages',
                   'guard': '<512 MiB available and >4 GiB swap growth for at least 10 seconds'}
        args.output.with_suffix('.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return 1 if stopped else process.returncode


if __name__ == '__main__':
    raise SystemExit(main())
