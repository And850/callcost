"""Save reproducible model-file identities without including Hugging Face cache internals."""

import argparse
import hashlib
import json
from pathlib import Path

SOURCE_REPOSITORY = 'Qwen/Qwen3.5-9B'
SOURCE_REVISION = 'c202236235762e1c871ad0ccb60c8ee5ba337b9a'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--verify', action='store_true', help='Compare current files with an existing manifest')
    args = parser.parse_args()
    files = []
    for path in sorted(args.directory.rglob('*')):
        relative = path.relative_to(args.directory)
        if not path.is_file() or any(part.startswith('.') for part in relative.parts):
            continue
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        files.append({'path': relative.as_posix(), 'bytes': path.stat().st_size, 'sha256': digest})
    if not files:
        raise ValueError('No model files found')
    manifest = {'source_repository': SOURCE_REPOSITORY, 'source_revision': SOURCE_REVISION,
                'files': files, 'total_bytes': sum(f['bytes'] for f in files)}
    if args.verify:
        expected = json.loads(args.output.read_text(encoding='utf-8'))
        if expected != manifest:
            raise SystemExit('Source file set, size, hash or provenance differs from the recorded manifest')
        print(f'Verified {len(files)} files against {args.output}')
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
