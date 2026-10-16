# Update in progress, 16 October 2026

Owner authorized the new swap instrumentation and reporting, separate resumable local/cloud passes, and a post-restart held-out pre-check (three calls each on local-q8/local-q3 with required energy validation). Neither full pass is authorized. Wait for clean-state confirmation before pre-check; wait for billing-on confirmation and key/project paid-tier verification before the cloud pass. The 16 October README amendment supersedes old swap exclusions below and was committed/pushed as `4b7f7e1` before implementation. No benchmark checkpoints exist; the prior held-out smoke is excluded instrumentation evidence.

# Current handoff, 15 October 2026

## Done

- Four pinned text-only MLX conversions and Fairy's production reference passed held-out preparation pilots. Fairy retains vision weights and is outside the knee sequence.
- Quality-only knee and local/cloud thinking amendments are committed and pushed before benchmark or launcher smoke data. Earlier excluded preparation/instrumentation pilots exist; no scored benchmark data exists. An excluded launcher smoke now exists, described below.
- Local thinking is off. Gemini 3.8 Flash runs at thinking level low; thinking tokens are reported separately and included once in billable output. Cloud is outside the knee sequence.
- Physical-footprint validation lacked complete 8-bit coverage. Exact encoded weight bytes are descriptive memory; physical footprint/RSS are secondary. Prior swap exclusions are superseded by the 16 October amendment above.
- Durable call checkpoints, CSV recovery, writer locking, resume input/source checks and live status are implemented. Failed/interrupted attempts are retained; completed checkpoints must not be repeated.
- Launcher includes preflight, sudo keepalive, caffeinate, logging, notifications and LATEST handling. Live smoke verified credential inheritance, local/cloud requests, deliberate interruption/resume, logs/status, notifications, model cleanup and caffeinate cleanup. Sudo keepalive and privileged energy remain unverified because no cached authorization was available.
- Launcher/report independent source review completed. Separate fixes committed and pushed: incomplete collection cannot yield knee conclusions; resume restores pilot verification from checkpoints; pending quality does not suppress step costs; reports show metric counts/reasons, secondary footprint/RSS, tokens, billable output, payloads, list-price costs, energy qualifications and eligible counts; standalone LM Studio daemon roots join the sampled process group.
- Fresh offline verification after code fixes: 75 tests passed; Ruff passed. Independent follow-up found no remaining source-level blockers in reviewed changes. These checks do not establish unattended readiness.
- Ignored `prompts/private/full.yaml` now contains 30 pinned GSM8K problems plus 10 owner-approved summaries, retaining original IDs, source records and scoring rules. Schema, unique IDs, pinned maths identity and full-launcher dataset checks pass. Source CLI validates six configurations, 40 prompts and five repeats. No benchmark prompt has been sent to a model.
- `max_words` and regex `pattern` alias are implemented. Owner approved summaries on 15 October 2026. The existing file was committed unchanged after the smoke in `6f6de97` and pushed.
- Config contains five local configurations and Gemini 3.8 Flash at low thinking. Recorded standard USD prices are 0.75/3.75 per million input/output tokens, including thinking. Update rates for runs from 1 January 2027, when they double.
- Earlier key-presence and authenticated metadata GET succeeded without printing credentials; this was not inference. LM Studio was last started with `--run-as-service`.

## Permissions

- Owner authorizes repository reads, code/docs edits, test suite and small commits/pushes.
- Ask before every model call (local or Gemini), any download, system-setting changes and any run longer than a few minutes.
- Summaries are now owner-approved. Smoke authorization covered six completed held-out calls and one interrupted attempt; those calls are complete. The full benchmark still requires separate approval. Do not make additional model calls without approval.
- Do not auto-commit benchmark artifacts. Never force-push or rewrite history.

## Remaining full-run blockers, in order

1. Restart the Mac and close unused apps. Every completed smoke call recorded whole-machine swap activity; smoke cannot establish swap-free full-run readiness. Keep AC power and lid open. Full preflight still requires at least 10 GiB available RAM and 10 GiB free disk. Do not lower guards or change system settings silently.
2. Start LM Studio headlessly with its server enabled and no model instances loaded. In the same interactive Terminal, ensure `GEMINI_API_KEY` is present without printing it. Key inheritance was confirmed for the smoke by running through an interactive login shell; Codex's default tool shell did not inherit the key.
3. Choose energy: authorize it in Terminal with `sudo -v`, or explicitly decline with `--no-energy`. Privileged collector/schema and sudo keepalive were not exercised in the smoke. With optional energy, unavailable collection must remain unavailable with reasons; do not claim it was validated.
4. Obtain separate full-run approval, then use the command below. Reserve roughly 12 to 14 hours conservatively; the actual workload may finish earlier. There are 1,200 measured requests plus six held-out pilots and 12 warm-ups, 1,218 scheduled requests. Tiny-prompt smoke timings are not a measured full-workload runtime estimate.

Human review tooling, reviewed summary scores and charts are still required for final results by 22 November 2026. They do not need to precede raw collection; pending human scores must remain insufficient data for summary knee conclusions. CI budget mode remains a later milestone.

## Untested limits and command caveats

- Full preflight needs 10 GiB available RAM and 10 GiB free disk; smoke needs 4 GiB RAM. These entry guards do not prove swap-free 8-bit inference. Earlier available RAM was about 5.6 GiB and instrumentation pilots recorded swap activity.
- Resume checks RAM before owned-instance recovery. If a prior run left a large model loaded, explicitly unload that recorded instance before resuming; never silently unload another client's model.
- Live service-mode memory samples were available for all four converted models. Fairy's secondary RSS/footprint were unavailable because a sampled process exited; this was retained with its reason. Standalone llmster mode remains unexercised. Privileged powermetrics schema and sudo keepalive remain unverified.
- `.venv/bin/callcost` currently loads an older installed package and rejects the current thinking-level config. Use `PYTHONPATH=src .venv/bin/python -m callcost` for current source. The launcher already sets its own source path. No packages were installed or downloaded during this review.
- README older milestone status and methodology RSS-knee wording were updated to match the committed amendments. The registered thresholds and exclusions were not changed.

## Run state and commands

`runs/LATEST` points to `20261015T194429.663048Z`, completed smoke only. Before future run work, read LATEST if present, its referenced `status.json`, then the end of `run.log`. A hard kill can leave stale status; check the recorded process. Checkpoints are authoritative.

## Completed held-out smoke, 15 October 2026

- One separate `held-out-pilot` prompt, checked against all 40 benchmark prompt IDs/texts before launch. All actual saved requests match that held-out prompt. No benchmark prompts were used.
- Six completed configuration calls, one retained interrupted 6-bit attempt, two segments. A completed 4-bit checkpoint was skipped on resume. Exactly one successful checkpoint per schedule slot; CSV retains all seven attempts. Zero measured benchmark calls.
- All five local configurations verified zero reasoning tokens and no observed reasoning content/tags. Gemini low-thinking reference completed, with 28 thinking tokens recorded separately and counted once in billable output.
- Six local load and unload operations, including interrupted/reloaded 6-bit. No model left loaded. Caffeinate child exited after each segment. Completion notifications reported delivered for interruption and completion; visible receipt was not independently observed.
- All six completed calls recorded swap activity. Fairy secondary memory was unavailable with a process-exit reason. Energy was unavailable because no cached sudo authorization existed and the tool shell was noninteractive; no password was requested.
- Audit confirmed completed status 6/6, immutable completed-call identity on resume, retained interrupted attempt, correct thinking accounting, request isolation and cleanup. Raw artifacts remain ignored and were not committed.
- Local decode rates on the tiny held-out prompt ranged from about 17.6 to 33.2 tokens/s. Extrapolating every local measured call to the 1,024-token output limit gives about 10.8 hours of local decoding alone, before input processing/cloud/telemetry. Reserve 12 to 14 hours; this is a planning estimate, not a benchmark result.

Full command, after the clean-state checklist and separate full-run approval:

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && ./scripts/run_full.sh --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

Append `--no-energy` to explicitly decline energy. Keep Terminal and the lid open; Codex may quit once the run starts.

Resume an authorized interrupted launcher run with `./scripts/run_full.sh --resume`; it uses saved inputs and refuses changed input/source files. Completed checkpoints are not repeated; an interrupted request without a completed checkpoint may need a new attempt.

Saved-run reporting without model calls:

```sh
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST)"
```

This writes `report.json` and `report.md`. Incomplete collection, missing eligible prompts and pending human scores cannot establish a knee or no knee. Results stay ignored by Git.

- 16 October instrumentation/report fix: per-call swap-in/out volume, raw before/after vm_stat + vm.swapusage and physical compressor bytes; pageouts alone do not flag swapping. All completed answers now contribute to knee/quality, with all-call latency primary and swap-free latency secondary, configuration share/unknown counts/median volume. Offline regressions pass; live pre-check still awaits restart.

- 16 October separate passes implemented: `--pass local` filters to five local configurations, `--pass cloud` to one cloud reference. Full launch requires an explicit pass. Separate directories, pass identity and `LATEST-local`/`LATEST-cloud` pointers prevent cross-pass resume. Cloud needs no local model/server or local-RAM threshold; local needs no Gemini key. Cloud HTTP 429 / RESOURCE_EXHAUSTED stops as `rate_limited` after a durable error checkpoint, no retry loop. Verified: 80 tests and Ruff. Full collection remains unauthorized.
