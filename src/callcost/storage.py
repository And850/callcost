"""Append calls durably; replace metadata atomically; never overwrite a run."""

import csv
import json
import os
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


class RunStore:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=False)
        (directory / 'raw').mkdir()
        self.file = (directory / 'calls.csv').open('x', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=CALL_FIELDS)
        self.writer.writeheader()
        self.file.flush()

    def write_metadata(self, metadata):
        write_json(self.directory / 'metadata.json', metadata)

    def append_call(self, row):
        serialised = {key: json.dumps(value, ensure_ascii=False, allow_nan=False)
                      if isinstance(value, (dict, list)) else value for key, value in row.items()}
        self.writer.writerow(serialised)
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        self.file.close()
