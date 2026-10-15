"""Count encoded tensor payload by component without loading model arrays."""

import json
import struct
from pathlib import Path

VISION_PREFIXES = ('vision_tower.', 'model.visual.', 'visual.')
LANGUAGE_PREFIXES = ('language_model.', 'model.language_model.')


def inspect_weights(paths):
    files = []
    totals = {'vision': 0, 'language': 0, 'other': 0}
    for path in sorted({Path(p) for p in paths if Path(p).suffix == '.safetensors'}):
        size = path.stat().st_size
        with path.open('rb') as stream:
            length_bytes = stream.read(8)
            if len(length_bytes) != 8:
                raise ValueError('Truncated safetensors length')
            length = struct.unpack('<Q', length_bytes)[0]
            if length > min(size - 8, 100_000_000):
                raise ValueError('Invalid safetensors header length')
            header = json.loads(stream.read(length))
        payload_limit = size - 8 - length
        counts = {'vision': 0, 'language': 0, 'other': 0}
        intervals = []
        tensor_counts = {'vision': 0, 'language': 0, 'other': 0}
        for key, tensor in header.items():
            if key == '__metadata__':
                continue
            left, right = tensor['data_offsets']
            if type(left) is not int or type(right) is not int or not 0 <= left <= right <= payload_limit:
                raise ValueError('Tensor offset outside safetensors payload')
            intervals.append((left, right))
            component = ('vision' if key.startswith(VISION_PREFIXES) else
                         'language' if key.startswith(LANGUAGE_PREFIXES) else 'other')
            counts[component] += right - left
            tensor_counts[component] += 1
        cursor = 0
        for left, right in sorted(intervals):
            if left < cursor:
                raise ValueError('Tensor payload intervals overlap')
            cursor = right
        for component, value in counts.items():
            totals[component] += value
        files.append({'name': path.name, 'file_bytes': size, 'header_and_prefix_bytes': length + 8,
                      'payload_bytes_by_component': counts, 'tensor_counts_by_component': tensor_counts})
    total = sum(totals.values())
    return {'scope': 'encoded safetensors payload bytes, not runtime resident or allocated memory',
            'classification': {'vision_prefixes': VISION_PREFIXES, 'language_prefixes': LANGUAGE_PREFIXES},
            'file_bytes': sum(f['file_bytes'] for f in files), 'tensor_payload_bytes': total,
            'vision_payload_bytes': totals['vision'], 'language_payload_bytes': totals['language'],
            'other_payload_bytes': totals['other'],
            'vision_fraction_of_tensor_payload': totals['vision'] / total if total else None,
            'files': files, 'unavailable_reason': None if files else 'No safetensors files supplied'}
