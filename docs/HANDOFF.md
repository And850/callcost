# Current handoff, 15 October 2026

## Done

- Four pinned text-only MLX conversions and Fairy's production reference passed held-out preparation pilots. Fairy retains vision weights and is outside the knee sequence.
- Quality-only knee and local/cloud thinking amendments are committed and pushed before benchmark or launcher smoke data. Earlier excluded preparation/instrumentation pilots exist; no scored benchmark or launcher smoke data exists.
- Local thinking is off. Gemini 3.8 Flash runs at thinking level low; thinking tokens are reported separately and included once in billable output. Cloud is outside the knee sequence.
- Physical-footprint validation lacked complete 8-bit coverage. Exact encoded weight bytes are descriptive memory; physical footprint/RSS are secondary. Swap-active/unknown observations remain reported but are excluded from knee inputs.
- Durable call checkpoints, CSV recovery, writer locking, resume input/source checks and live status are implemented. Failed/interrupted attempts are retained; completed checkpoints must not be repeated.
- Launcher includes preflight, sudo keepalive, caffeinate, logging, notifications and LATEST handling. Live integration remains unverified.
- Launcher/report independent source review completed. Separate fixes committed and pushed: incomplete collection cannot yield knee conclusions; resume restores pilot verification from checkpoints; pending quality does not suppress step costs; reports show metric counts/reasons, secondary footprint/RSS, tokens, billable output, payloads, list-price costs, energy qualifications and eligible counts; standalone LM Studio daemon roots join the sampled process group.
- Fresh offline verification after code fixes: 75 tests passed; Ruff passed. Independent follow-up found no remaining source-level blockers in reviewed changes. These checks do not establish unattended readiness.
- Ignored `prompts/private/full.yaml` now contains exactly the pinned 30 GSM8K problems, including IDs, source records and scoring rules. Source CLI validation passed for six configurations and 30 prompts. Full-dataset guard correctly refuses this incomplete file. No summaries have been added or sent to a model.
- `max_words` and regex `pattern` alias are implemented. `prompts/summarisation.yaml` remains under owner review; concurrent owner edits were preserved and excluded from assistant commits.
- Config contains five local configurations and Gemini 3.8 Flash at low thinking. Recorded standard USD prices are 0.75/3.75 per million input/output tokens, including thinking. Update rates for runs from 1 January 2027, when they double.
- Earlier key-presence and authenticated metadata GET succeeded without printing credentials; this was not inference. LM Studio was last started with `--run-as-service`.

## Permissions

- Owner authorizes repository reads, code/docs edits, test suite and small commits/pushes.
- Ask before every model call (local or Gemini), any download, system-setting changes and any run longer than a few minutes.
- Summaries require explicit owner approval before any model sees them. No model calls were made during this review.
- Do not auto-commit benchmark artifacts. Never force-push or rewrite history.

## Remaining full-run blockers, in order

1. Obtain approval for the held-out six-configuration smoke and deliberate interruption/resume. No summaries in smoke. Verify counts, checkpoints, local load/unload, thinking/token accounting, cleanup, status/logs, notifications, caffeinate and energy authentication or explicit decline. Commit any resulting fixes before a full run.
2. Obtain owner confirmation of summary review, then add the ten approved summaries to the private input. Validate exactly 30 maths + 10 summaries, pinned maths identity, IDs and scoring rules. The full launcher currently rejects the maths-only staging file.
3. Request separate approval for the full run. Restart, close other apps, keep charger and lid open, inherit credentials from Terminal, and satisfy preflight. Keep Terminal open; Codex may quit.

Human review tooling, reviewed summary scores and charts are still required for final results by 22 November 2026. They do not need to precede raw collection; pending human scores must remain insufficient data for summary knee conclusions. CI budget mode remains a later milestone.

## Untested limits and command caveats

- Full preflight needs 10 GiB available RAM and 10 GiB free disk; smoke needs 4 GiB RAM. These entry guards do not prove swap-free 8-bit inference. Earlier available RAM was about 5.6 GiB and instrumentation pilots recorded swap activity.
- Resume checks RAM before owned-instance recovery. If a prior run left a large model loaded, explicitly unload that recorded instance before resuming; never silently unload another client's model.
- Actual headless worker process identity, privileged powermetrics schema and all launcher facilities together remain live-smoke checks. Secondary measurements can be unavailable with reasons.
- `.venv/bin/callcost` currently loads an older installed package and rejects the current thinking-level config. Use `PYTHONPATH=src .venv/bin/python -m callcost` for current source. The launcher already sets its own source path. No packages were installed or downloaded during this review.
- README older milestone status and methodology RSS-knee wording were updated to match the committed amendments. The registered thresholds and exclusions were not changed.

## Run state and commands

`runs/LATEST` is absent as of this review. Before future run work, read LATEST if present, its referenced `status.json`, then the end of `run.log`. A hard kill can leave stale status; check the recorded process. Checkpoints are authoritative.

Held-out smoke command, only when separately authorized:

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && ./scripts/run_full.sh --smoke --config configs/experiment.yaml
```

Full command, only after summary approval, complete input, live validation and separate full-run approval:

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && ./scripts/run_full.sh --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

Resume an authorized interrupted launcher run with `./scripts/run_full.sh --resume`; it uses saved inputs and refuses changed input/source files. Completed checkpoints are not repeated; an interrupted request without a completed checkpoint may need a new attempt.

Saved-run reporting without model calls:

```sh
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST)"
```

This writes `report.json` and `report.md`. Incomplete collection, missing eligible prompts and pending human scores cannot establish a knee or no knee. Results stay ignored by Git.
