# Blind summary review

This is offline human scoring, with no model calls. Use the fixed prompt checklists. Do not view the hidden identity key or match answers to configuration reports before finishing.

The preparation tool combines completed local and cloud runs, shuffles anonymous cards and groups exact duplicate answers to the same prompt. Each card contains the full instruction/source, answer and original checklist. Configuration, timing, repeat count and run identity are omitted. Each decision maps back to every matching completed call, preserving the original per-prompt and per-repeat weighting.

From the repository root:

```sh
PYTHONPATH=src .venv/bin/python scripts/review_summaries.py prepare --runs "runs/$(cat runs/LATEST-local)" "runs/$(cat runs/LATEST-cloud)" --output runs/blind-review-20261017
open runs/blind-review-20261017/review.html
```

Preparation requires completed source runs and a new output directory. If the packet has already been prepared, open its existing HTML file instead of preparing it again. Keep `key.json` hidden until scoring is finished; `packet.json` contains only anonymous review content. All packet, key, exported score and imported review files stay private and ignored under `runs/`.

Enter your reviewer name. Read the source and answer, then mark each human criterion Pass or Fail. Automatic criteria are prefilled and locked to the original rules. Use Previous/Next to move between cards. Progress is saved in browser storage; keep using the same browser and file path. The page displays a warning if storage is unavailable. Do not clear browser data before export.

When every card is scored, click **Export completed scores**. Save `summary-scores.json` locally. Import it using its actual saved path:

```sh
PYTHONPATH=src .venv/bin/python scripts/review_summaries.py import --review runs/blind-review-20261017 --scores /absolute/path/to/summary-scores.json
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST-local)"
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST-cloud)"
```

Import checks packet identity, original source and rubric, automatic results, answer hashes, prompt IDs and complete boolean decisions before writing any run's `human_scores.json`. Existing human-score files are not overwritten. Reports validate the saved answer/rubric association again and keep the checkpoints unchanged. Human decisions fill the pending checklist items; automatic criteria retain their registered behavior. No summary knee or variance conclusion is available until these scores exist.
