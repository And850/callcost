#!/bin/bash
# Run from the repository root, only after the owner's explicit download approval.
set -euo pipefail

.venv-convert/bin/python - <<'PY'
import shutil
from importlib.metadata import version
assert version('mlx-lm') == '0.32.0', 'Use the pinned conversion environment'
free = shutil.disk_usage('.').free
print(f'Available disk: {free / 1e9:.2f} GB; required planning allowance: 45 GB')
if free < 45_000_000_000:
    raise SystemExit('Insufficient free disk for the planned source and four outputs')
PY
mkdir -p models/provenance
.venv-convert/bin/hf download Qwen/Qwen3.5-9B \
  --revision c202236235762e1c871ad0ccb60c8ee5ba337b9a \
  --local-dir models/source/Qwen3.5-9B \
  --max-workers 2 2>&1 | tee models/provenance/download.log
.venv-convert/bin/python scripts/write_model_manifest.py \
  models/source/Qwen3.5-9B models/provenance/source-files.json
