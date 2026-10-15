import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/write_model_manifest.py'


@pytest.mark.parametrize('mutation', ['changed', 'extra', 'missing'])
def test_conversion_source_verification_rejects_changed_files(tmp_path, mutation):
    source = tmp_path / 'source'
    source.mkdir()
    weight = source / 'model.safetensors'
    weight.write_bytes(b'original')
    manifest = tmp_path / 'manifest.json'
    base = [sys.executable, str(SCRIPT), str(source), str(manifest)]
    assert subprocess.run(base, capture_output=True).returncode == 0
    assert subprocess.run(base + ['--verify'], capture_output=True).returncode == 0
    if mutation == 'changed':
        weight.write_bytes(b'modified')  # Same length, so hashing is essential.
    elif mutation == 'extra':
        (source / 'extra.safetensors').write_bytes(b'extra')
    else:
        weight.unlink()
    result = subprocess.run(base + ['--verify'], capture_output=True)
    assert result.returncode != 0
