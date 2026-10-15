#!/bin/bash
# Run from the repository root after downloading and hashing the pinned source.
set -euo pipefail

.venv-convert/bin/python - <<'PY'
import json
from importlib.metadata import version
from pathlib import Path
assert version('mlx-lm') == '0.32.0', 'Use the pinned converter'
manifest = json.loads(Path('models/provenance/source-files.json').read_text())
assert manifest['source_repository'] == 'Qwen/Qwen3.5-9B'
assert manifest['source_revision'] == 'c202236235762e1c871ad0ccb60c8ee5ba337b9a'
assert Path('models/source/Qwen3.5-9B/config.json').is_file(), 'Pinned local source is missing'
for bits in (3, 4, 6, 8):
    if Path(f'models/converted/Qwen3.5-9B-{bits}bit').exists():
        raise SystemExit(f'Output for {bits} bits already exists; do not overwrite provenance')
PY
.venv-convert/bin/python scripts/write_model_manifest.py \
  models/source/Qwen3.5-9B models/provenance/source-files.json --verify
mkdir -p models/provenance models/converted
.venv-convert/bin/python --version > models/provenance/python-version.txt
.venv-convert/bin/python -m pip freeze > models/provenance/conversion-environment.txt
cp scripts/convert_qwen_mlx.sh models/provenance/conversion-commands.sh

# All four independent processes read the same original checkpoint. No Hub fallback.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
.venv-convert/bin/mlx_lm.convert \
  --hf-path models/source/Qwen3.5-9B --mlx-path models/converted/Qwen3.5-9B-3bit \
  --quantize --q-bits 3 --q-group-size 64 --q-mode affine --dtype bfloat16 \
  2>&1 | tee models/provenance/convert-3bit.log
.venv-convert/bin/mlx_lm.convert \
  --hf-path models/source/Qwen3.5-9B --mlx-path models/converted/Qwen3.5-9B-4bit \
  --quantize --q-bits 4 --q-group-size 64 --q-mode affine --dtype bfloat16 \
  2>&1 | tee models/provenance/convert-4bit.log
.venv-convert/bin/mlx_lm.convert \
  --hf-path models/source/Qwen3.5-9B --mlx-path models/converted/Qwen3.5-9B-6bit \
  --quantize --q-bits 6 --q-group-size 64 --q-mode affine --dtype bfloat16 \
  2>&1 | tee models/provenance/convert-6bit.log
.venv-convert/bin/mlx_lm.convert \
  --hf-path models/source/Qwen3.5-9B --mlx-path models/converted/Qwen3.5-9B-8bit \
  --quantize --q-bits 8 --q-group-size 64 --q-mode affine --dtype bfloat16 \
  2>&1 | tee models/provenance/convert-8bit.log

# Retain source licence and hash all saved artifacts after conversion.
for bits in 3 4 6 8; do
  cp models/source/Qwen3.5-9B/LICENSE "models/converted/Qwen3.5-9B-${bits}bit/LICENSE"
  .venv-convert/bin/python scripts/write_model_manifest.py \
    "models/converted/Qwen3.5-9B-${bits}bit" "models/provenance/${bits}bit-files.json"
done
