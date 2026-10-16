# Current handoff, 16 October 2026

## Current authorization

- Code/docs edits, offline tests, small commits/pushes are authorized.
- Owner authorized a roughly 15-minute pre-check only after confirming a clean restart: exactly three held-out calls each on local-q8/local-q3, new swap observations and sudo-backed energy validation. Owner confirmed ready after restart. Boot time changed to 16 October 21:00:50 UTC; AC power and headless service were checked. One held-out local-q3 call completed before required-energy failure stopped the pre-check. No further model calls are authorized without confirming the replacement check.
- Neither full local nor full cloud pass is authorized. Wait for the pre-check report and owner approval. Owner confirmed Tier 1 prepaid billing with no auto-reload. AI Studio verification matched the environment key masked suffix to the sole listed key, confirmed Tier 1/Prepay/auto-reload off and the model limits; a contradictory outstanding-balance alert remains a cloud-readiness blocker. See private runs/billing-verification-20261016.json. No cloud inference was used.
- Ask before model calls beyond this pre-check, downloads, system settings or other long runs. Never auto-commit run artifacts or credentials.

## Built and committed

- Four pinned text-only MLX 3/4/6/8-bit conversions and Fairy's production reference passed earlier held-out preparation pilots. Fairy retains vision weights and is outside the knee sequence, alongside cloud.
- Quality-only knee and thinking amendments are committed. Local reasoning is off and checked on every call. Gemini 3.8 Flash uses low thinking, with thinking tokens separate and counted once in billable output.
- The dated 16 October pre-registration amendment was committed/pushed as `4b7f7e1` before implementation. It supersedes old swap exclusions: all completed calls enter quality/knee and the unchanged variance rule. All-call latency is primary; swap-free latency is secondary. Swap is a configuration cost on this 16 GB Mac, with whole-machine attribution limits. No benchmark observations exist.
- `c5c9671` implements per-call swap-in/out bytes, total swap-used and physical compressor memory before/after, raw snapshots/timestamps/missing reasons, configuration swapped share among known-counter calls, unknown counts and median volume (including known zero-volume calls). Pageouts alone no longer flag swapping. Unknown swap data never removes completed quality observations.
- `cf49892` implements explicit `--pass local` / `--pass cloud`, separate directories, pass identity, checkpoints and `LATEST-local` / `LATEST-cloud`. Local needs no Gemini key; cloud needs no LM Studio/model files/local-RAM gate. Cloud quota/rate-limit errors stop as `rate_limited` after a durable failed checkpoint, without an automatic retry loop.
- Pre-check mode uses only local-q8/local-q3 and the separate pencil prompt, exactly three calls each, no benchmark prompts or extra warm-ups/pilots. It records a 120-second unloaded idle window plus 120-second loaded-before/after windows for each model, roughly ten minutes idle within an approximately 15-minute check.
- Pre-check requires sudo and valid collector/baseline before calls. Missing in-call energy or requested swap observations preserves the completed response and stops before further inference. Separate validation requires all six calls, new metrics, same-segment idle windows and initial/post energy qualifications. Missing diagnostics after interruption remain `validation_incomplete`, never a false pass; completed calls are not repeated.
- Independent review identified and prompted these pre-check safeguards; final follow-up found no remaining material blocker, and offline regressions cover them. Latest fresh verification after energy timing correction: 89 tests and Ruff pass. The live pre-check failed after one completed call; replacement validation requires owner approval.
- Approved summaries were committed unchanged in `6f6de97`. Ignored `prompts/private/full.yaml` contains 30 pinned GSM8K + 10 approved summaries, preserving IDs, source records and scoring rules; schema and full-dataset checks pass. No benchmark prompt has been sent to a model.
- Saved-run reporting includes costs/quality, observation counts/missing reasons, secondary footprint/RSS, thinking/billable output, payloads, list-price equivalent, energy qualifications and per-prompt counts. Weight bytes are descriptive memory; no runtime-memory gate. Human summary scores remain pending; blind review tooling/charts remain unfinished.

## Next actions

1. Implementation and independent review are complete; obtain the owner's clean-restart confirmation. Keep charger/lid open, close unused apps and start LM Studio headlessly, server enabled, no model loaded. Check boot time and available RAM before the approved pre-check. Pre-check guard is 4 GiB RAM / 10 GiB disk. Do not lower guards or change system settings.
2. Launch the pre-check in Terminal so sudo authentication stays local to the user. Exact command:

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && sudo -v && ./scripts/run_full.sh --precheck --config configs/experiment.yaml
```

Enter sudo password only in Terminal. `--precheck` rejects `--no-energy`, `--smoke` and `--pass`. Monitor `runs/LATEST-precheck`, status/log, checkpoints and validation. Compare idle and inference swap rates with raw counter-window timestamps. These observations cannot prove causal process attribution. Audit parsed power samples, CPU/GPU/ANE units/domains, coverage, baseline qualifications and cleanup before calling energy validated.

3. Report back and wait for approval of each full pass. Full local retains its 10 GiB available-RAM and 10 GiB disk entry guards; neither guard proves swap-free inference, and swapping no longer invalidates answers. Preserve swapping as cost rather than trying to eliminate it by changing machine settings.
4. After owner confirms paid billing, inspect Google AI Studio for environment key/project mapping, paid plan/usage tier, active limits and actual spend-cap setting. Record evidence/project/tier/limits/check time without the key. Metadata GET or a successful inference is not proof of tier. Alerts-only budgets are not spend caps. Tier/billing/limits were checked in AI Studio without inference. A contradictory outstanding-balance alert remains despite positive prepaid credit; no cloud request is authorized.

## Full passes, only after separate approval

```sh
./scripts/run_full.sh --pass local --config configs/experiment.yaml --prompts prompts/private/full.yaml
./scripts/run_full.sh --pass cloud --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

Local: 1,015 calls (1,000 measured + five pilots + ten warm-ups), overnight. Cloud: **203 calls** (200 measured + one pilot + two warm-ups), before failed-request attempts explicitly authorized later. Input/settings are identical across passes, with source/input hashes and collection times preserved. Keep Terminal/lid open. Optional full-run energy uses `sudo -v` first or explicit `--no-energy`; pre-check always requires energy.

Cloud smoke usage was 27 input, five visible output and 28 thinking tokens, 33 billable output. At configured USD 0.75/3.75 per million input/output, that is USD 0.000144 per smoke-size call, **USD 0.029232 for 203 such calls**. Actual benchmark inputs/answers are longer; this is a tiny-prompt list-price extrapolation, not the real cost or a spending cap. Owner confirmed paid prepaid billing. Tier 1 and model limits were verified in AI Studio, but a contradictory outstanding-balance warning remains a cloud-readiness blocker.

Resume with `./scripts/run_full.sh --pass local --resume` or `--pass cloud --resume`; read the matching pointer/status/log first. `LATEST` tracks only the most recently touched run. Input/source changes refuse resume; completed checkpoints are never repeated. A cloud quota/rate-limit stop retains the attempt; resolve quota and obtain new-request approval before explicit resume. No automatic retry loop exists.

## Existing evidence and caveats

- `runs/LATEST` and `runs/LATEST-precheck` point to `20261016T210833.862187Z-precheck`, failed required-energy diagnostic. Local/cloud pointers do not yet exist. Before run work, read the appropriate pointer, status, then end of run.log. Check recorded PID if status may be stale; checkpoints are authoritative.
- Earlier smoke had six completed held-out calls plus one retained interrupted 6-bit attempt across two segments; completed 4-bit was skipped on resume. Zero benchmark calls. All five local thinking checks passed; Gemini recorded 28 thinking tokens. Six local load/unload operations left no models loaded. Caffeinate cleanup and notification delivery commands succeeded.
- Every completed old smoke call flagged swap activity under the old flag (which included pageouts). Re-reading raw counters confirmed nonzero swap-in bytes in all six completed calls, independently of pageouts; the 8-bit call had 1,298,546,688 swap-in bytes. These are excluded instrumentation observations, not benchmark findings. Old smoke energy was unavailable without cached sudo. Fairy secondary memory was unavailable because a sampled process exited.
- Four converted models had usable secondary samples in smoke; physical-footprint validation previously lacked complete 8-bit coverage. Exact encoded weights remain descriptive memory. Missing secondary metrics are valid unavailable observations with reasons.
- `.venv/bin/callcost` contains an older installed package. Use current source with `PYTHONPATH=src .venv/bin/python -m callcost`; launcher sets this itself. No packages/downloads/system settings were changed.
- Last known LM Studio mode was app `--run-as-service`. Standalone llmster discovery is tested offline but not live. Resume checks RAM before owned-instance recovery; explicitly unload a recorded leftover instance if needed, never someone else's model.
- Real results target: 22 November 2026; WAICY submission: 29 November. Human summary review and charts remain needed after raw collection. CI budget mode is a later milestone.

- Exhausted prepaid balance now stops the whole cloud pass through the same durable `rate_limited`/no-retry path as quota errors, including HTTP 402 and PAYMENT_REQUIRED. Regression coverage includes depleted-balance responses. Verified: 86 tests and Ruff.
- Tier verification via AI Studio is complete, but the Rate Limit page reports an outstanding-balance warning despite positive prepaid credit. Do not make payment/change billing automatically; cloud approval remains pending resolution. Browser used for verification was quit before the pre-check.

## Failed pre-check and energy correction, 16 October 2026

- Run `20261016T210833.862187Z-precheck` is failed, 1/6 calls completed, zero benchmark calls. Preserve it and all raw data. Local-q3 repeat 1 completed; no 8-bit calls occurred. Unloaded and 3-bit loaded-before idle windows both lasted 120 seconds with zero swap-in/out; the completed 3-bit call also had zero swap-in/out and zero swap storage before/after. Compressor usage increased during the call; raw before/after bytes are retained. These limited observations do not establish the 8-bit behavior or causal attribution.
- Sudo and keepalive worked with zero refresh failures. Powermetrics produced 48 valid delta records with CPU/GPU/ANE mW fields and no parser errors. The 3-bit call's energy remained unavailable because receipt-derived windows overlapped up to 18.6 ms, exceeding the existing 10 ms guard. Post-baseline/loaded-after diagnostics were not reached. Models and caffeinate were cleaned up.
- Offline fix reconstructs provider delta intervals from elapsed_ns, retaining receipt lags. Drift of at least half a sample interval is rejected; is_delta must be true. Missing-interval and synthetic-energy regressions pass. The initial receipt anchor's fixed delay is unknown and remains an explicit limitation. Two-sample/90%/10ms integration checks were not relaxed. Final independent review found no further material blocker; live validation remains pending.
- README has a dated energy instrumentation amendment before benchmark data. Original failed checkpoint/report remain unchanged. Offline replay lives ignored in `runs/power-timing-replay-20261016.json` and is not accepted live validation.
- Source changes intentionally prevent resuming the failed check. Ask approval for a fresh ~15-minute pre-check of six new held-out calls; keep the first attempt separate and retained. Do not issue more calls or either full pass automatically.
- Computer Use cannot control Terminal (tool safety restriction). User manually ran the exact sudo/pre-check command. Any replacement check must also authenticate in their Terminal, never by sending a password to chat.
