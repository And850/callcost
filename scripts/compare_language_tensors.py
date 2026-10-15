"""Compare encoded language tensors in production and converted MLX safetensors."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


def language_tensors(root):
    tensors = {}
    for file in sorted(root.glob('*.safetensors')):
        with file.open('rb') as stream:
            prefix = stream.read(8)
            if len(prefix) != 8:
                raise ValueError('Truncated safetensors prefix')
            length = struct.unpack('<Q', prefix)[0]
            size = file.stat().st_size
            if length > min(size - 8, 100_000_000):
                raise ValueError('Invalid safetensors header length')
            header = json.loads(stream.read(length))
            for name, entry in header.items():
                if not name.startswith('language_model.'):
                    continue
                left, right = entry['data_offsets']
                if type(left) is not int or type(right) is not int or not 0 <= left <= right <= size - 8 - length:
                    raise ValueError('Tensor payload outside file bounds')
                if name in tensors:
                    raise ValueError('Duplicate tensor name across model shards')
                stream.seek(8 + length + left)
                digest = hashlib.sha256()
                remaining = right - left
                while remaining:
                    chunk = stream.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError('Truncated tensor payload')
                    digest.update(chunk)
                    remaining -= len(chunk)
                tensors[name] = {'dtype': entry['dtype'], 'shape': entry['shape'],
                                 'bytes': right - left, 'sha256': digest.hexdigest()}
    if not tensors:
        raise ValueError(f'No language tensors found in {root}')
    return tensors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('production', type=Path)
    parser.add_argument('converted', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    production, converted = language_tensors(args.production), language_tensors(args.converted)
    changed = sorted(k for k in production.keys() & converted.keys() if production[k] != converted[k])
    missing, extra = sorted(production.keys() - converted.keys()), sorted(converted.keys() - production.keys())
    report = {'method': 'Compare tensor names, dtype, shape, encoded length and SHA-256 of data_offsets payload',
              'scope': 'Encoded tensor comparison, not runtime behaviour or memory attribution',
              'production_tensor_count': len(production), 'converted_tensor_count': len(converted),
              'production_language_bytes': sum(t['bytes'] for t in production.values()),
              'missing': missing, 'extra': extra, 'changed': changed,
              'identical': not (changed or missing or extra),
              'production_tensors': production, 'converted_tensors': converted}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'{len(changed)} changed encoded tensors, {len(missing)} missing, {len(extra)} extra')


if __name__ == '__main__':
    main()
