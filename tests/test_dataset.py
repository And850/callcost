import importlib.util
import json
from pathlib import Path

from callcost.schemas import Dataset


def test_committed_sample_is_reproducible_and_preserves_row_identity():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('prepare_gsm8k', root / 'scripts/prepare_gsm8k.py')
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    manifest = json.loads((root / 'datasets/gsm8k/selection.json').read_text())
    data = Dataset.model_validate_json((root / 'datasets/gsm8k/prompts.json').read_text())
    selected = script.select_rows([None] * manifest['source_rows'])
    assert selected == manifest['row_indices']
    assert len(selected) == len(set(selected)) == 30
    assert [p.source.row_index for p in data.prompts] == selected
    assert {p.source.revision for p in data.prompts} == {script.REVISION}
    assert all(p.id == f'gsm8k-test-{p.source.row_index}' for p in data.prompts)
