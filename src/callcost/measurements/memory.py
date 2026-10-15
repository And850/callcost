"""Sample the LM Studio process group, with RSS and macOS physical footprint."""

import ctypes
import json
import os
import sys
import threading
import time

import psutil


class RusageInfoV0(ctypes.Structure):
    # Darwin SDK sys/resource.h, RUSAGE_INFO_V0. Times are not used here.
    _fields_ = [('ri_uuid', ctypes.c_uint8 * 16)] + [(name, ctypes.c_uint64) for name in (
        'ri_user_time', 'ri_system_time', 'ri_pkg_idle_wkups', 'ri_interrupt_wkups',
        'ri_pageins', 'ri_wired_size', 'ri_resident_size', 'ri_phys_footprint',
        'ri_proc_start_abstime', 'ri_proc_exit_abstime')]


_LIBPROC = None


def physical_footprint(pid):
    global _LIBPROC
    if sys.platform != 'darwin':
        raise OSError('Physical footprint requires macOS')
    if _LIBPROC is None:
        _LIBPROC = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        _LIBPROC.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        _LIBPROC.proc_pid_rusage.restype = ctypes.c_int
    info = RusageInfoV0()
    if _LIBPROC.proc_pid_rusage(pid, 0, ctypes.byref(info)) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))
    return info.ri_phys_footprint


def peak_rss(samples, start, end):
    return peak_process_sum(samples, start, end, 'rss')


def peak_footprint(samples, start, end):
    return peak_process_sum(samples, start, end, 'footprint')


def peak_process_sum(samples, start, end, metric):
    selected = [s for s in samples if start <= s.get('started', s['time']) <= s['time'] <= end]
    if not selected:
        return None, 'No memory samples inside call window'
    if any(s['error'] or not s.get(metric) or (metric == 'footprint' and s.get('footprint_error')) for s in selected):
        return None, 'Incomplete process group or failed memory sample'
    identities = [set(s[metric]) for s in selected]
    if any(group != identities[0] for group in identities):
        return None, 'Process group changed during call'
    return max(sum(s[metric].values()) for s in selected), None


def process_role(executable, arguments):
    is_app = '/LM Studio.app/' in executable
    is_worker = any(marker in arguments for marker in (
        '/.cache/lm-studio/extensions/backends/', '/.lmstudio/extensions/backends/'))
    native_node = executable.endswith('/.internal/utils/node') and ('/.cache/lm-studio/' in executable or '/.lmstudio/' in executable)
    is_worker |= native_node and '/LM Studio.app/Contents/Resources/app/.webpack/lib/llmworker.js' in arguments
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
    # Always include the application group, even when explicit roots were supplied.
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
                sample = {'started': time.perf_counter(), 'rss': {}, 'footprint': {}, 'footprint_error': None, 'processes': [], 'error': None}
                try:
                    for process in discover_processes(self.process_ids):
                        identity = f'{process.pid}:{process.create_time()}'
                        sample['rss'][identity] = process.memory_info().rss
                        try:
                            sample['footprint'][identity] = physical_footprint(process.pid)
                        except OSError as error:
                            sample['footprint_error'] = str(error)
                        sample['processes'].append({'pid': process.pid, 'created': process.create_time(),
                                                    'executable': process.exe()})
                except (psutil.Error, ValueError, OSError) as error:
                    sample['error'] = str(error)
                sample['time'] = time.perf_counter()
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
