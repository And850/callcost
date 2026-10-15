import hashlib
import importlib.util
import json
import struct
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/compare_language_tensors.py'


def reader():
    spec = importlib.util.spec_from_file_location('compare_language_tensors', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.language_tensors


def test_hashes_only_named_language_payload_and_respects_header_offset(tmp_path):
    header = {'vision_tower.x': {'dtype': 'F32', 'shape': [1], 'data_offsets': [0, 4]},
              'language_model.x': {'dtype': 'U32', 'shape': [1], 'data_offsets': [4, 8]}}
    data = json.dumps(header).encode()
    path = tmp_path / 'model.safetensors'
    path.write_bytes(struct.pack('<Q', len(data)) + data + b'VISION!!')
    tensors = reader()(tmp_path)
    assert list(tensors) == ['language_model.x']
    assert tensors['language_model.x']['sha256'] == hashlib.sha256(b'ON!!').hexdigest()
    assert tensors['language_model.x']['bytes'] == 4


def test_rejects_negative_tensor_span_instead_of_reading_unbounded_file(tmp_path):
    header = {'language_model.x': {'dtype': 'U32', 'shape': [1], 'data_offsets': [4, 0]}}
    data = json.dumps(header).encode()
    (tmp_path / 'model.safetensors').write_bytes(struct.pack('<Q', len(data)) + data + b'data')
    with pytest.raises(ValueError, match='bounds'):
        reader()(tmp_path)
