#!/bin/bash
set -euo pipefail
CALLCOST_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$CALLCOST_ROOT"
if [ ! -x "$CALLCOST_ROOT/.venv/bin/python" ]; then
    echo 'CallCost: missing .venv. Follow the installation instructions in README.md.' >&2
    exit 1
fi
export PYTHONPATH="$CALLCOST_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$CALLCOST_ROOT/.venv/bin/python" -u -m callcost.unattended "$@"
