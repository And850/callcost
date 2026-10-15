# Current handoff, 15 October 2026

## Done

- Four pinned MLX conversions and Fairy's production reference passed held-out preparation pilots. Fairy retains vision weights and is outside the knee sequence.
- The dated quality-only knee amendment is committed and pushed. Cost is reported per step, not a gate. No scored benchmark or launcher smoke data exists; excluded instrumentation pilots do exist.
- Physical-footprint validation failed to obtain complete coverage at 8-bit. Exact encoded weight bytes are the descriptive memory measure; footprint and RSS remain secondary. Swap counters and exclusions are implemented.
- Durable call checkpoints, CSV recovery, writer locking, resume input/source checks and live status are implemented. Interrupted attempts are retained.
- Launcher and report are committed as WIP. Launcher includes preflight, sudo keepalive, caffeinate, logging, notifications and LATEST handling.
- `max_words` and regex `pattern` alias are implemented. Ten Fairy-style prompts written for the benchmark (invented texts) are committed and schema-validated. No model has seen them; owner review is pending.
- `configs/experiment.yaml` contains five local configurations and Gemini 3.8 Flash at thinking level low. Prices are USD 0.75/3.75 per million input/output tokens, including thinking. Update rates for runs from 1 January 2027, when they double.
- Key presence was confirmed in an interactive login shell without printing it, and an authenticated model-metadata GET succeeded. This was not an inference test. LM Studio was last started with `--run-as-service`.

## Not done

- No six-configuration live launcher smoke or deliberate interruption/resume test. No Gemini inference, full benchmark, blind review UI, charts or CI budget mode.
- Launcher accepts one prompt file. Default config is `configs/experiment.yaml`; default prompts are `prompts/private/full.yaml`, which has not been created.
- Reporting needs review for complete per-step cost presentation, secondary footprint columns, incomplete data and quality-only knee behavior. JSON currently contains more metrics than the terminal table. Independent final code review is outstanding.
- README retains older milestone instructions; this file is the current operational state.

## Untested or limited evidence

- Last recorded automated result: 69 tests passed and Ruff passed, before the final config and launcher-default edit. Those final changes were not rechecked. No known failing existing test was left at that point. This is not fresh verification.
- Real preflight/server startup, sudo keepalive, privileged powermetrics, caffeinate, notifications and live resume remain unverified together. Unit tests are not evidence of unattended readiness.
- Full preflight requires 10 GiB available RAM and 10 GiB free disk; smoke uses 4 GiB RAM. These entry guards do not prove 8-bit fits without swapping. Last observed available RAM was about 5.6 GiB; instrumentation pilots recorded swap activity.
- Owner authorized code/docs review, fixes, tests and small commits/pushes on 15 October. Ask before every model call, any download, system-setting changes or runs longer than a few minutes. Summary prompts remain unapproved.

## Next steps, in order

1. If `runs/LATEST` exists, read its referenced `status.json`, then `run.log` before doing anything else with a run. LATEST may be absent because the launcher has not run. A hard kill can leave stale status; check the recorded process before assuming it is still active. Checkpoints are authoritative.
2. Obtain Andrii's confirmation that `prompts/summarisation.yaml` has been reviewed. Do not send those prompts to any model before confirmation. Obtain authorization to lift the wrap-up restriction before further tests or model runs.
3. Merge `datasets/gsm8k/prompts.json` and `prompts/summarisation.yaml` into ignored `prompts/private/full.yaml`, retaining IDs, source records and scoring rules. Validate 30 maths and 10 summarisation prompts.
4. Finish launcher/report review and resolve the gaps above. Run the existing suite and Ruff once authorized. Complete independent review before claiming readiness.
5. With approval, test six configurations on one held-out prompt each, one call each, including deliberate interruption and `--resume`. Never use the summaries for this smoke. Verify checkpoints, counts, logs, cleanup and notifications, and energy authentication or explicit decline. Commit fixes before a real run.
6. Request approval for the full run. Restart, close other apps, keep charger and lid open, use Terminal with the inherited key, and satisfy preflight. Keep Terminal open; Codex can quit. Do not auto-commit results.

## Run command, only once ready and authorized

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && ./scripts/run_full.sh --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

## Resuming after a run

Read `runs/LATEST`, then the referenced `status.json`, then `run.log`. From the repo root, `./scripts/run_full.sh --resume` uses saved inputs and refuses changed files/source. Completed checkpoints must not be repeated; an interrupted request without a completed checkpoint may need a new attempt.

To generate a saved-run report without model calls:

```sh
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST)"
```

This writes `report.json` and `report.md`. Human scores remain pending until reviewed; missing eligible prompts mean insufficient data. Results stay ignored by Git.

## Launcher/report review follow-up, 15 October 2026

- README thinking amendment and GitHub account instruction committed and pushed before review.
- Independent review identified: incomplete collection could yield knee conclusions; hard-kill pilot verification metadata recovery; costs hidden by pending scores; human-readable reporting omissions. Fix these in separate commits before live validation.
- Fixed incomplete-collection conclusions: report checks completed checkpoint identities against the full saved schedule and completed run status. Swap-excluded repeats do not need replacement; eligible prompt counts remain visible. Regression includes a complete schedule with reduced eligible repeats.
- First fix verified with 70 tests and Ruff; no inference. No launcher run or benchmark data collected.
