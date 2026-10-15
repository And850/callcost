"""Rebuild the preregistered sample without a datasets-library dependency."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

REVISION = '3101c7d5072418e28b9008a6636bde82a006892c'
BASE = f'https://raw.githubusercontent.com/openai/grade-school-math/{REVISION}'
SEED = '2027'
COUNT = 30


def select_rows(rows):
    # Rank original row indices by stable hashes, independent of Python RNG changes.
    ranked = sorted(range(len(rows)), key=lambda i: hashlib.sha256(f'{SEED}:{i}'.encode()).digest())
    return sorted(ranked[:COUNT])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('datasets/gsm8k'))
    args = parser.parse_args()
    with urlopen(BASE + '/grade_school_math/data/test.jsonl', timeout=30) as response:
        data = response.read()
    rows = [json.loads(line) for line in data.splitlines()]
    indices = select_rows(rows)
    prompts = []
    for index in indices:
        row = rows[index]
        expected = row['answer'].rsplit('#### ', 1)[1].strip().replace(',', '')
        prompts.append({'id': f'gsm8k-test-{index}', 'task_type': 'maths',
                        'prompt': row['question'] + '\nShow your working. End with Answer: <number>.',
                        'scoring': {'type': 'numeric_final_line', 'expected': expected,
                                    'absolute_tolerance': '0.000001'},
                        'source': {'dataset': 'GSM8K test', 'revision': REVISION, 'row_index': index,
                                   'url': BASE + '/grade_school_math/data/test.jsonl'}})
    manifest = {'revision': REVISION, 'source_sha256': hashlib.sha256(data).hexdigest(),
                'source_rows': len(rows), 'selection': 'smallest SHA-256(seed + colon + zero-based row index), then row order',
                'seed': SEED, 'count': COUNT, 'row_indices': indices}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('prompts.json', {'schema_version': 1, 'prompts': prompts}), ('selection.json', manifest)]:
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    with urlopen(BASE + '/LICENSE', timeout=30) as response:
        (args.output / 'LICENSE').write_bytes(response.read())
    print(f'Wrote {COUNT} test problems from pinned revision {REVISION}')


if __name__ == '__main__':
    main()
