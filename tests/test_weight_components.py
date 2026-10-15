import json
import struct

import pytest

from callcost.measurements.weights import inspect_weights


def write_tensors(path, tensors):
    header = json.dumps(tensors).encode()
    size = max((t['data_offsets'][1] for t in tensors.values()), default=0)
    path.write_bytes(struct.pack('<Q', len(header)) + header + bytes(size))


def test_vision_payload_is_encoded_tensor_bytes_not_whole_file_or_runtime(tmp_path):
    weight = tmp_path / 'model.safetensors'
    write_tensors(weight, {
        'language_model.model.x.weight': {'dtype': 'U32', 'shape': [2], 'data_offsets': [0, 8]},
        'vision_tower.blocks.0.weight': {'dtype': 'BF16', 'shape': [3], 'data_offsets': [8, 14]},
        'vision_tower.blocks.0.scales': {'dtype': 'F16', 'shape': [1], 'data_offsets': [14, 16]},
    })
    result = inspect_weights([weight, tmp_path / 'config.json'])
    assert result['tensor_payload_bytes'] == 16
    assert result['vision_payload_bytes'] == 8
    assert result['vision_fraction_of_tensor_payload'] == .5
    assert result['file_bytes'] > 16
    assert 'runtime' in result['scope']


def test_component_reader_rejects_out_of_bounds_or_overlapping_tensors(tmp_path):
    path = tmp_path / 'bad.safetensors'
    write_tensors(path, {'vision_tower.x': {'data_offsets': [0, 8]},
                         'language_model.x': {'data_offsets': [4, 8]}})
    with pytest.raises(ValueError, match='overlap'):
        inspect_weights([path])
    path.write_bytes(struct.pack('<Q', 9999) + b'{}')
    with pytest.raises(ValueError):
        inspect_weights([path])
