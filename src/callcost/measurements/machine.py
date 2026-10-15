"""Read only the machine fields needed to reproduce a run."""

import json
import platform
import plistlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import psutil


def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def conditions():
    charger = command(['/usr/bin/pmset', '-g', 'batt'])
    thermal = command(['/usr/bin/pmset', '-g', 'therm'])
    return {'timestamp': datetime.now(timezone.utc).isoformat(),
            'ac_power': None if not charger else "drawing from 'AC Power'" in charger,
            'charger_raw': charger, 'thermal_raw': thermal,
            'thermal_state': 'unavailable',
            'thermal_note': 'pmset diagnostics retained; absence of warnings is not a nominal-state measurement',
            'available_memory_bytes': psutil.virtual_memory().available,
            'swap_used_bytes': psutil.swap_memory().used}


def machine_metadata():
    data = {'platform': platform.system(), 'python': platform.python_version(),
            'cpu_cores_physical': psutil.cpu_count(logical=False),
            'cpu_cores_logical': psutil.cpu_count(), 'ram_bytes': psutil.virtual_memory().total,
            'macos_version': command(['/usr/bin/sw_vers', '-productVersion']),
            'macos_build': command(['/usr/bin/sw_vers', '-buildVersion']),
            'chip': None, 'gpu_cores': None, 'lmstudio_version': None}
    profiler = command(['/usr/sbin/system_profiler', 'SPHardwareDataType', 'SPDisplaysDataType', '-json'])
    if profiler:
        parsed = json.loads(profiler)
        hardware = parsed.get('SPHardwareDataType', [{}])[0]
        data['chip'] = hardware.get('chip_type')
        data['model'] = hardware.get('machine_model')
        graphics = parsed.get('SPDisplaysDataType', [{}])[0]
        cores = graphics.get('sppci_cores')
        data['gpu_cores'] = int(cores) if str(cores).isdigit() else None
    for base in (Path('/Applications'), Path.home() / 'Applications'):
        path = base / 'LM Studio.app/Contents/Info.plist'
        if path.exists():
            with path.open('rb') as stream:
                data['lmstudio_version'] = plistlib.load(stream).get('CFBundleShortVersionString')
            break
    return data
