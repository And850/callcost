"""Terminal-owned launcher. All authentication precedes inference."""

import argparse
import fcntl
import getpass
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
import psutil

from callcost.experiment import PILOT, file_identity, run_experiment
from callcost.measurements.machine import command, conditions
from callcost.measurements.memory import is_lmstudio_daemon
from callcost.report import report_run
from callcost.schemas import Config, Dataset, load_document
from callcost.storage import write_json

GIB = 1024 ** 3
FULL_MIN_MEMORY = 10 * GIB
SMOKE_MIN_MEMORY = 4 * GIB
MIN_DISK = 10 * GIB
ROOT = Path(__file__).resolve().parents[2]


def latest_run(runs, pointer='LATEST'):
    name = (runs / pointer).read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name in ('.', '..'):
        raise ValueError('Invalid runs/LATEST pointer')
    path = (runs / name).resolve(strict=True)
    if path.parent != runs.resolve():
        raise ValueError('runs/LATEST points outside runs directory')
    return path


def select_pass(config, run_pass):
    provider = {'local': 'lmstudio', 'cloud': 'gemini', 'precheck': 'lmstudio'}[run_pass]
    selected = config.model_copy(deep=True)
    selected.configurations = [c for c in selected.configurations if c.provider == provider]
    if run_pass == 'precheck':
        selected.configurations = [c for c in selected.configurations if c.id in ('local-q8', 'local-q3')]
        if {c.id for c in selected.configurations} != {'local-q8', 'local-q3'}:
            raise ValueError('Pre-check requires local-q8 and local-q3')
        selected.measurement.energy.mode = 'required_powermetrics'
    if not selected.configurations:
        raise ValueError(f'No {run_pass} configurations selected')
    return selected


def lms_path():
    path = shutil.which('lms') or str(Path.home() / '.cache/lm-studio/bin/lms')
    if not Path(path).is_file():
        raise ValueError('LM Studio CLI missing: install lms before launching')
    return path


def headless_state():
    processes = []
    for process in psutil.process_iter(['pid', 'exe', 'cmdline']):
        info = process.info
        exe, args = info.get('exe') or '', info.get('cmdline') or []
        if exe.endswith('/LM Studio.app/Contents/MacOS/LM Studio'):
            processes.append(dict(pid=info['pid'], mode='service' if '--run-as-service' in args else 'desktop',
                                  executable=exe))
        elif is_lmstudio_daemon(exe):
            processes.append(dict(pid=info['pid'], mode='daemon', executable=exe))
    return dict(headless=bool(processes) and all(p['mode'] != 'desktop' for p in processes), processes=processes)


def environment_preflight(config, disk_path, client, *, smoke=False, require_five=True, resume_metadata=None):
    # Check keys first, without printing their values or touching the server.
    for setting in config.configurations:
        env = getattr(setting, 'api_key_env', None) if setting.provider == 'gemini' else config.lmstudio.api_key_env
        if env and not os.environ.get(env):
            raise ValueError(f'Preflight failed: set {env} in this Terminal, do not put it in config')
    local = [c for c in config.configurations if c.provider == 'lmstudio']
    cloud = [c for c in config.configurations if c.provider == 'gemini']
    if require_five and local:
        series = [c for c in local if c.comparison_role == 'quantisation_series']
        refs = [c for c in local if c.comparison_role == 'production_reference']
        if len(local) != 5 or len(refs) != 1 or {c.expected_quantisation for c in series} != {'3bit', '4bit', '6bit', '8bit'}:
            raise ValueError('Preflight failed: need four MLX levels (3/4/6/8 bit) and Fairy production reference')
    if require_five and cloud and len(cloud) != 1:
        raise ValueError('Preflight failed: cloud pass needs exactly one Gemini reference')
    current = conditions()
    if current.get('ac_power') is not True:
        raise ValueError('Preflight failed: connect the charger (or charger state unavailable)')
    minimum = (SMOKE_MIN_MEMORY if smoke else FULL_MIN_MEMORY) if local else 0
    # A previous run can leave its own model loaded. Check RAM after explicit recovery,
    # never silently unload another client's model to pass this gate.
    if current['available_memory_bytes'] < minimum:
        raise ValueError(f'Preflight failed: available memory {current["available_memory_bytes"]/GIB:.2f} GiB; '
                         f'need {minimum/GIB:.0f} GiB before loading. Restart and close other apps. '
                         'If a prior run left a model loaded, explicitly unload that instance first.')
    free_disk = shutil.disk_usage(disk_path).free
    if free_disk < MIN_DISK:
        raise ValueError(f'Preflight failed: need {MIN_DISK/GIB:.0f} GiB free disk, have {free_disk/GIB:.2f}')
    for setting in local:
        for path in setting.model_files:
            if not path.is_file():
                raise ValueError(f'Preflight failed: missing model file {path}')
    if not local:
        return dict(conditions=current, minimum_available_memory_bytes=minimum,
                    minimum_disk_bytes=MIN_DISK, disk_free_bytes=free_disk,
                    headless={'headless': None, 'reason': 'Cloud-only pass; LM Studio not required'},
                    boot_time=datetime.fromtimestamp(psutil.boot_time(), timezone.utc).isoformat(),
                    uptime_seconds=time.time() - psutil.boot_time(), gpu_wired_limit_raw='Not applicable')
    headers = {'Authorization': f'Bearer {os.environ[config.lmstudio.api_key_env]}'} if config.lmstudio.api_key_env else {}
    url = config.lmstudio.base_url + '/api/v1/models'
    try:
        response = client.get(url, headers=headers, timeout=5)
    except httpx.TransportError:
        cli = lms_path()
        for args in ([cli, 'daemon', 'up'], [cli, 'server', 'start', '--port', str(urlparse(url).port or 1234), '--bind', '127.0.0.1']):
            result = subprocess.run(args, capture_output=True, text=True, timeout=90)
            if result.returncode:
                raise ValueError('Preflight failed: lms could not start the headless server; run lms daemon up and inspect its output')
        response = client.get(url, headers=headers, timeout=10)
    if not response.is_success:
        raise ValueError(f'Preflight failed: LM Studio server HTTP {response.status_code}')
    models = response.json()['models']
    for setting in local:
        matches = [m for m in models if m['key'] == setting.model_key or setting.model_key in m.get('variants', [])]
        if len(matches) != 1:
            raise ValueError(f'Preflight failed: model missing or ambiguous: {setting.id}')
        model = matches[0]
        if (model.get('format') != setting.model_format or
            (model.get('quantization') or {}).get('name', '').casefold() != setting.expected_quantisation.casefold() or
            (model['key'] != setting.model_key and model.get('selected_variant') != setting.model_key)):
            raise ValueError(f'Preflight failed: installed format/quantisation/selection mismatch: {setting.id}')
    known = {(v['load_request_key'], v['instance_id']) for v in (resume_metadata or {}).get('loads', [])}
    loaded = [(m['key'], i['id']) for m in models for i in m.get('loaded_instances', [])]
    if any(pair not in known for pair in loaded):
        raise ValueError('Preflight failed: unrelated model loaded. Unload it explicitly before launching')
    state = headless_state()
    if local and not state['headless']:
        raise ValueError('Preflight failed: LM Studio GUI is active. Quit it, then run lms daemon up for headless service')
    boot_time = psutil.boot_time()
    return dict(conditions=current, minimum_available_memory_bytes=minimum, minimum_disk_bytes=MIN_DISK,
                disk_free_bytes=free_disk, headless=state,
                boot_time=datetime.fromtimestamp(boot_time, timezone.utc).isoformat(),
                uptime_seconds=time.time() - boot_time,
                restarted='User checklist; boot time recorded, not inferred from a yes/no claim',
                apps_closed='User checklist; resource and process observations do not prove every app was closed',
                gpu_wired_limit_raw=command(['/usr/sbin/sysctl', 'iogpu.wired_limit_mb']),
                daemon_status=command([lms_path(), 'daemon', 'status']),
                observed_model_inventory=models,
                processes=[dict(pid=p.pid, name=p.info.get('name'), rss_bytes=(p.info.get('memory_info').rss
                                if p.info.get('memory_info') else None))
                           for p in psutil.process_iter(['name', 'memory_info'])
                           if p.info.get('memory_info') and p.info['memory_info'].rss >= 100 * 1024 ** 2])


class SudoSession:
    def __init__(self):
        self.stop = threading.Event()
        self.thread = None
        self.record = {'authorized': False, 'keepalive_failures': []}

    def start(self, disabled=False):
        if disabled:
            self.record['reason'] = 'Energy declined with --no-energy or disabled in config'
            return False
        try:
            cached = subprocess.run(['/usr/bin/sudo', '-n', '-v'], capture_output=True, timeout=10).returncode == 0
            if not cached:
                if not sys.stdin.isatty():
                    self.record['reason'] = 'No interactive Terminal; energy unavailable without cached sudo'
                    return False
                password = getpass.getpass('sudo password for powermetrics (Enter to continue without energy): ')
                if not password:
                    self.record['reason'] = 'User declined sudo'
                    return False
                try:
                    authorized = subprocess.run(['/usr/bin/sudo', '-S', '-p', '', '-v'], input=password + '\n',
                                                text=True, capture_output=True, timeout=30).returncode == 0
                finally:
                    password = None
                if not authorized:
                    self.record['reason'] = 'Sudo authentication failed; continuing without energy'
                    return False
            self.record.update(authorized=True, reason='Sudo verified; noninteractive refresh every 30 seconds')
            self.thread = threading.Thread(target=self._keepalive, daemon=True)
            self.thread.start()
            return True
        except (OSError, subprocess.TimeoutExpired, EOFError):
            self.record['reason'] = 'Sudo unavailable; continuing without energy'
            return False

    def _keepalive(self):
        while not self.stop.wait(30):
            try:
                code = subprocess.run(['/usr/bin/sudo', '-n', '-v'], capture_output=True, timeout=10).returncode
                if code:
                    self.record['keepalive_failures'].append(datetime.now(timezone.utc).isoformat())
            except (OSError, subprocess.TimeoutExpired):
                self.record['keepalive_failures'].append(datetime.now(timezone.utc).isoformat())

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=11)


class RunLog:
    def __init__(self, terminal, directory):
        self.terminal, self.directory = terminal, directory
        self.pending = ''
        self.stream = None

    def write(self, value):
        self.terminal.write(value)
        self.terminal.flush()
        self.pending += value
        if self.stream is None and self.directory.is_dir():
            self.stream = (self.directory / 'run.log').open('a', buffering=1)
        if self.stream:
            self.stream.write(self.pending)
            self.stream.flush()
            self.pending = ''
        return len(value)

    def flush(self):
        self.terminal.flush()
        if self.stream:
            self.stream.flush()

    def close(self):
        if self.stream:
            self.stream.close()


def notify(message):
    script = 'on run argv\ndisplay notification (item 1 of argv) with title "CallCost"\nend run'
    result = command(['/usr/bin/osascript', '-e', script, message])
    return result is not None


def check_full_dataset(config, dataset):
    counts = {task: sum(p.task_type == task for p in dataset.prompts) for task in ('maths', 'summarisation')}
    if len(dataset.prompts) != 40 or counts != {'maths': 30, 'summarisation': 10} or config.run.repeats != 5:
        raise ValueError('Full run requires 30 maths + 10 summarisation prompts and exactly five measured repeats')
    reference = json.loads((ROOT / 'datasets/gsm8k/prompts.json').read_text())
    expected = {p['id']: p for p in reference['prompts']}
    actual = {p.id: p.model_dump(mode='json', exclude_none=True) for p in dataset.prompts if p.task_type == 'maths'}
    # Canonicalise schema defaults before comparing prompt text, answers and pinned source rows.
    expected = {p.id: p.model_dump(mode='json', exclude_none=True) for p in Dataset.model_validate(reference).prompts}
    if actual != expected:
        raise ValueError('Full run maths prompts differ from the pinned 30-problem GSM8K selection')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Unattended CallCost run, keep this Terminal open')
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/experiment.yaml')
    parser.add_argument('--prompts', type=Path, default=ROOT / 'prompts/private/full.yaml')
    parser.add_argument('--pass', dest='run_pass', choices=('local', 'cloud'), help='Independent full-run pass')
    parser.add_argument('--resume', action='store_true', help='Resume runs/LATEST using its saved inputs')
    parser.add_argument('--smoke', action='store_true', help='One held-out call/configuration; no benchmark evidence')
    parser.add_argument('--precheck', action='store_true', help='Six held-out local calls with idle windows and required energy')
    parser.add_argument('--accept-cloud-retry-upgrade', action='store_true', help='Explicitly accept the recorded cloud retry source upgrade on resume')
    parser.add_argument('--no-energy', action='store_true', help='Decline sudo and record energy unavailable')
    args = parser.parse_args(argv)
    runs = ROOT / 'runs'
    directory = None
    lease = caffeinate = log = None
    sudo = SudoSession()
    original_out, original_err = sys.stdout, sys.stderr
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    result_code = 1
    try:
        # Existing runs directory is an ignored operational workspace, not a benchmark output.
        runs.mkdir(exist_ok=True)
        lease = (runs / '.launcher.lock').open('a')
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another unattended launcher is active') from None
        previous = None
        if args.precheck and (args.run_pass or args.smoke or args.no_energy):
            raise ValueError('--precheck cannot be combined with --pass, --smoke or --no-energy')
        if args.resume:
            directory = latest_run(runs, 'LATEST-precheck' if args.precheck else f'LATEST-{args.run_pass}' if args.run_pass else 'LATEST')
            previous = json.loads((directory / 'metadata.json').read_text())
            config = Config.model_validate(previous['config'])
            dataset = Dataset.model_validate(previous['dataset'])
            smoke = previous.get('smoke', False)
            run_pass = previous.get('run_pass')
            precheck = previous.get('precheck', False)
            if args.precheck and not precheck:
                raise ValueError('Resume refused: not a pre-check run')
            if args.run_pass and run_pass != args.run_pass:
                raise ValueError('Resume refused: pass identity does not match')
            inputs = previous['input_files']
            for identity in inputs:
                if file_identity(Path(identity['path'])) != identity:
                    raise ValueError('Resume refused: original input file changed')
            if previous['status'] == 'completed':
                print(f'Run already completed: {directory}. No inference repeated.')
                print(report_run(directory))
                result_code = 0
                return 0
        else:
            config = Config.model_validate(load_document(args.config))
            smoke = args.smoke
            precheck = args.precheck
            run_pass = 'precheck' if precheck else args.run_pass
            if not smoke and not precheck and not run_pass:
                raise ValueError('Full collection requires --pass local or --pass cloud')
            if run_pass:
                config = select_pass(config, run_pass)
            dataset = Dataset(schema_version=1, prompts=[PILOT]) if smoke or precheck else Dataset.model_validate(load_document(args.prompts))
            for setting in config.configurations:
                if setting.provider == 'lmstudio':
                    setting.model_files = [(args.config.resolve().parent / p.expanduser()).resolve() for p in setting.model_files]
            if not smoke and not precheck:
                check_full_dataset(config, dataset)
            inputs = [file_identity(args.config)] + ([] if smoke or precheck else [file_identity(args.prompts)])
            directory = runs / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ') + f'-{run_pass or "smoke"}')
        log = RunLog(original_out, directory)
        sys.stdout = sys.stderr = log
        print(f'Preflight: {"PRE-CHECK ONLY" if precheck else "SMOKE ONLY" if smoke else "full benchmark"}; {directory.name}')
        with httpx.Client(trust_env=False) as client:
            launch = environment_preflight(config, ROOT, client, smoke=smoke or precheck, require_five=not precheck, resume_metadata=previous)
        print(f'Clean-state checklist: restart and close other apps before a full run. Boot: {launch["boot_time"]}; '
              f'uptime {launch["uptime_seconds"]/60:.1f} min.')
        print(f'LM Studio headless: {launch["headless"]["headless"]}; charger: AC; '
              f'available RAM: {launch["conditions"]["available_memory_bytes"]/GIB:.2f} GiB; '
              f'free disk: {launch["disk_free_bytes"]/GIB:.1f} GiB; GPU wired limit: {launch["gpu_wired_limit_raw"]}')
        print('Checklist: restarted [verify boot time]; apps closed [verify yourself]; '
              'LM Studio headless [checked for local pass; not required for cloud]; GPU wired limit [0 means system default].')
        energy = sudo.start(args.no_energy or config.measurement.energy.mode == 'off')
        launch['sudo'] = sudo.record
        print(f'Energy: {sudo.record["reason"]}')
        if config.measurement.energy.mode == 'required_powermetrics' and not energy:
            raise ValueError('Required energy needs sudo authorization in this Terminal; stopped before any model call')
        print('Keep this Terminal open and the lid open. Codex and other apps may now be quit.')
        caffeinate = subprocess.Popen(['/usr/bin/caffeinate', '-i', '-s', '-w', str(os.getpid())],
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(.05)
        if caffeinate.poll() is not None:
            raise ValueError('caffeinate failed to start; run stopped before inference')
        launch['caffeinate'] = {'pid': caffeinate.pid, 'flags': '-i -s -w launcher_pid'}
        def progress(message, **kwargs):
            # RunStore has created the directory before its first progress message.
            if directory.is_dir():
                for name in ('LATEST', f'LATEST-{run_pass}') if run_pass else ('LATEST',):
                    pointer = runs / f'{name}.tmp'
                    pointer.write_text(directory.name + '\n')
                    pointer.replace(runs / name)
            print(message, **kwargs)
        metadata = run_experiment(config, dataset, directory, resume=args.resume, smoke=smoke,
                                  input_files=inputs, launch_metadata=launch,
                                  energy_mode=None if energy else 'off', progress=progress, run_pass=run_pass, precheck=precheck,
                                  accept_cloud_retry_upgrade=args.accept_cloud_retry_upgrade)
        print(f'Run {metadata["status"]}: {directory}')
        for error in metadata['errors']:
            print(error)
        print(report_run(directory))
        result_code = 0 if metadata['status'] == 'completed' else 1
    except (ValueError, OSError, httpx.HTTPError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        message = str(error) if isinstance(error, (ValueError, OSError)) else type(error).__name__
        print(f'CallCost stopped: {message}', file=sys.stderr)
    finally:
        sudo.close()
        if caffeinate and caffeinate.poll() is None:
            caffeinate.terminate()
            caffeinate.wait(timeout=5)
        if directory and directory.is_dir():
            write_json(directory / f'launcher-exit-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")}.json',
                       {'sudo': sudo.record, 'exit_code': result_code})
        notification = notify('Run completed' if result_code == 0 else 'Run failed or interrupted. Check status.json and run.log.')
        if log:
            print(f'Completion notification delivered: {notification}')
        sys.stdout, sys.stderr = original_out, original_err
        if log:
            log.close()
        if lease:
            lease.close()
        signal.signal(signal.SIGTERM, previous_sigterm)
    return result_code


if __name__ == '__main__':
    raise SystemExit(main())
