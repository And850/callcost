# Handoff, 15 October 2026

Work in `/Users/andreyryzhanskiy/Documents/CallCost/callcost`, the fresh clone of `And850/callcost`. Use normal git add/commit/push. No automatic result commits.

## Done

- Four pinned MLX conversions and Fairy production reference passed earlier held-out pilots. Fairy retains 912,020,960 vision-weight bytes; it is outside the quantisation sequence.
- Physical footprint was attempted. Both 8-bit validation attempts had incomplete process coverage. Exact encoded weight bytes are the descriptive memory measure; sampled footprint and RSS remain secondary. Swap deltas and exclusions are implemented. Earlier instrumentation pilots recorded swapping and are not benchmark results.
- Quality-only knee amendment is committed and pushed, initially `d3bf74e`, method clarification `c534937`. Cost is reported per step, not a gate. Variance and both kill criteria are unchanged. No scored benchmark or launcher smoke data exists.
- Durable JSON checkpoints, CSV recovery, writer locking, resume input/source checks and live status are implemented. Interrupted attempts are retained.
- Launcher and report code are preserved as WIP in `11430af`. Launcher includes preflight, sudo keepalive, caffeinate, logging, notifications and LATEST handling. No live launcher run has occurred.
- `max_words` and regex `pattern` input alias are implemented. Ten Fairy-style prompts written for the benchmark (invented texts) are committed. Their schema validated in the last existing test run. No model has seen these summaries. Owner review is pending.
- `configs/experiment.yaml` selects all five local configurations plus Gemini 3.8 Flash, thinking level low, USD 0.75/3.75 per million input/output tokens, including thinking. Prices double from 1 January 2027; update config then. Cloud thinking cannot be disabled and is logged separately.
- Key presence was confirmed in an interactive login shell without printing it. An authenticated model-metadata GET succeeded. This is not an inference test. LM Studio was restarted as a desktop background service with `--run-as-service`.

## Not done or not tested

- No live launcher smoke, deliberate interruption/resume, Gemini inference or privileged powermetrics verification. No full benchmark, blind review UI, charts or CI budget mode.
- Last automated result before wrap-up: 69 tests passed and Ruff passed. No further tests were run after the wrap-up request. The final config and launcher-default change were not rechecked. No known failing existing test was left at that point.
- Launcher currently accepts one prompt file. Its default is `prompts/private/full.yaml`, which has not been created. Config defaults to `configs/experiment.yaml`.
- Reporting needs review, especially complete per-step cost presentation, secondary footprint columns, incomplete data and quality-only knee behavior. JSON contains more metrics than the terminal table. No independent final code review has occurred.
- Full preflight requires 10 GiB available RAM and 10 GiB free disk. Instrumentation-only smoke uses 4 GiB RAM. These are entry guards, not proof that 8-bit inference fits without swapping. Last observed available RAM was about 5.6 GiB.
- README contains older milestone instructions; use this handoff for current operational state.

## Exact next steps

1. Wait for Andrii to confirm review of `prompts/summarisation.yaml`. Do not infer on these prompts before confirmation. The current wrap-up restriction permits no further tests or model runs until work is resumed.
2. Merge `datasets/gsm8k/prompts.json` and `prompts/summarisation.yaml` into ignored `prompts/private/full.yaml`, retaining every prompt ID, source and scoring rule. Validate 30 maths + 10 summarisation prompts.
3. Finish launcher/report review and resolve the gaps above. Once authorized to resume normal work, run the existing suite and Ruff. Do not claim readiness from unit tests alone.
4. Verify the six-configuration held-out smoke, one call each, including deliberate interruption and `--resume`. Authenticate energy interactively or explicitly decline it. This smoke must never use the summarisation dataset. Check checkpoints, counts, logs, cleanup and notifications. Commit fixes before the real run.
5. Restart, close other apps, keep charger and lid open, start from Terminal with the key inherited, and satisfy preflight. Keep Terminal open; Codex can quit. After all preceding steps, run:

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && ./scripts/run_full.sh --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

## Resuming after a run

First read `runs/LATEST`, then that directory's `status.json`, then `run.log`. LATEST may not exist yet because the new launcher has not run. Check whether a recorded running PID is still alive; a hard kill can leave stale status. Checkpoints are authoritative. No completed checkpoint should be inferred again. An interrupted request without a completed checkpoint may need a new attempt.

From the repo root, resume with `./scripts/run_full.sh --resume`. It uses saved inputs and refuses changed files/source. Reports make no model calls:

```sh
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST)"
```

Reports write `report.json` and `report.md`. Human scores remain pending; missing eligible prompts mean insufficient data. Results stay ignored by Git.
