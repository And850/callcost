"""Sample the LM Studio process group, including resident model weights."""

import json
import threading
import time

import psutil


def peak_rss(samples, start, end):
    selected = [s for s in samples if start <= s['time'] <= end]
    if not selected:
        return None, 'No memory samples inside call window'
    if any(s['error'] or not s['rss'] for s in selected):
        return None, 'Incomplete process group or failed memory sample'
    identities = [set(s['rss']) for s in selected]
    if any(group != identities[0] for group in identities):
        return None, 'Process group changed during call'
    return max(sum(s['rss'].values()) for s in selected), None


def process_role(executable, arguments):
    is_app = '/LM Studio.app/' in executable
    is_worker = any(marker in arguments for marker in (
        '/.cache/lm-studio/extensions/backends/', '/.lmstudio/extensions/backends/'))
    return is_app, is_worker


def discover_processes(explicit_ids):
    found = {}
    worker_found = False
    if explicit_ids:
        roots = [psutil.Process(pid) for pid in explicit_ids]
        for root in roots:
            if not any(process_role(root.exe(), ' '.join(root.cmdline()))):
                raise ValueError('Explicit root is not a recognised LM Studio process')
            found[root.pid] = root
            found.update({p.pid: p for p in root.children(recursive=True)})
        worker_found = any(process_role(p.exe(), ' '.join(p.cmdline()))[1] for p in found.values())
    else:
        for process in psutil.process_iter(['pid', 'exe', 'cmdline']):
            info = process.info
            is_app, is_worker = process_role(info.get('exe') or '', ' '.join(info.get('cmdline') or []))
            if is_app or is_worker:
                found[process.pid] = process
                worker_found |= is_worker
    if not worker_found:
        raise ValueError('LM Studio inference worker not identified; check process coverage')
    for process in list(found.values()):
        found.update({p.pid: p for p in process.children(recursive=True)})
    return list(found.values())


class MemorySampler:
    def __init__(self, path, interval_ms, process_ids):
        self.path = path
        self.interval = interval_ms / 1000
        self.process_ids = process_ids
        self.samples = []
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._collect, daemon=True)
        self.thread.start()

    def _collect(self):
        with self.path.open('w', encoding='utf-8') as stream:
            while not self.stop_event.is_set():
                sample = {'time': time.perf_counter(), 'rss': {}, 'processes': [], 'error': None}
                try:
                    for process in discover_processes(self.process_ids):
                        identity = f'{process.pid}:{process.create_time()}'
                        sample['rss'][identity] = process.memory_info().rss
                        sample['processes'].append({'pid': process.pid, 'created': process.create_time(),
                                                    'executable': process.exe()})
                except (psutil.Error, ValueError, OSError) as error:
                    sample['error'] = str(error)
                self.samples.append(sample)
                stream.write(json.dumps(sample) + '\n')
                stream.flush()
                self.stop_event.wait(self.interval)

    def finish(self, start, end):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        if self.thread and self.thread.is_alive():
            return None, 'Memory collector failed to stop'
        return peak_rss(self.samples, start, end)
