"""Atomic call checkpoints are authoritative; CSV is a recoverable export."""

import csv
import fcntl
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from callcost.records import CALL_FIELDS


def write_json(path: Path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class RunStore:
    def __init__(self, directory: Path, *, resume=False):
        self.directory = directory
        if not resume:
            directory.mkdir(parents=True, exist_ok=False)
        self.lease = (directory / '.writer.lock').open('a')
        try:
            fcntl.flock(self.lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lease.close()
            raise ValueError('Run has an active writer; do not launch a second resume') from None
        try:
            if resume and not (directory / 'checkpoints').is_dir():
                raise ValueError('Run predates resumable checkpoints; cannot safely resume')
            (directory / 'raw').mkdir(exist_ok=resume)
            (directory / 'checkpoints').mkdir(exist_ok=resume)
            self.rows = [json.loads(p.read_text()) for p in sorted((directory / 'checkpoints').glob('*.json'))]
            self.sequence = max((int(p.stem) for p in (directory / 'checkpoints').glob('*.json')), default=0)
            self.file = (directory / 'calls.csv').open('w', newline='', encoding='utf-8')
            self.writer = csv.DictWriter(self.file, fieldnames=CALL_FIELDS)
            self.writer.writeheader()
            for row in self.rows:
                self._csv(row)
            self.file.flush()
            os.fsync(self.file.fileno())
        except BaseException:
            self.lease.close()
            raise
        self.mutex = threading.Lock()
        self.status = None
        self.stop_event = threading.Event()
        self.heartbeat = threading.Thread(target=self._heartbeat, daemon=True)
        self.heartbeat.start()

    def _heartbeat(self):
        while not self.stop_event.wait(2):
            with self.mutex:
                if self.status and self.status['state'] == 'running':
                    self.status['last_update'] = datetime.now(timezone.utc).isoformat()
                    write_json(self.directory / 'status.json', self.status)

    def write_status(self, *, state, total, current, started_at, error=None):
        with self.mutex:
            self.status = dict(state=state, calls_done=len({r['schedule_index'] for r in self.rows
                               if r.get('status') == 'completed' and 'schedule_index' in r}),
                               calls_total=total, current_configuration=current, start_time=started_at,
                               last_update=datetime.now(timezone.utc).isoformat(), error=error,
                               pid=os.getpid())
            write_json(self.directory / 'status.json', self.status)

    def write_metadata(self, metadata):
        write_json(self.directory / 'metadata.json', metadata)

    def _csv(self, row):
        serialised = {key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                      if isinstance(value, (dict, list)) else value for key, value in row.items()}
        self.writer.writerow(serialised)

    def append_call(self, row):
        self.sequence += 1
        write_json(self.directory / 'checkpoints' / f'{self.sequence:08d}.json', row)
        self.rows.append(row)
        self._csv(row)
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        self.stop_event.set()
        self.heartbeat.join(timeout=5)
        self.file.close()
        self.lease.close()
