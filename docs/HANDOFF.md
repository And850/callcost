# Current handoff, 16 October 2026

## Current authorization

- Code/docs edits, offline tests, small commits/pushes are authorized.
- Owner authorized a roughly 15-minute pre-check only after confirming a clean restart: exactly three held-out calls each on local-q8/local-q3, new swap observations and sudo-backed energy validation. Clean-state confirmation is pending. No new model calls have been made in this work.
- Neither full local nor full cloud pass is authorized. Wait for the pre-check report and owner approval. Wait for the owner's "billing is on" message, then verify the actual key/project paid tier and active limits before any cloud pass.
- Ask before model calls beyond this pre-check, downloads, system settings or other long runs. Never auto-commit run artifacts or credentials.

## Built and committed

- Four pinned text-only MLX 3/4/6/8-bit conversions and Fairy's production reference passed earlier held-out preparation pilots. Fairy retains vision weights and is outside the knee sequence, alongside cloud.
- Quality-only knee and thinking amendments are committed. Local reasoning is off and checked on every call. Gemini 3.8 Flash uses low thinking, with thinking tokens separate and counted once in billable output.
- The dated 16 October pre-registration amendment was committed/pushed as `4b7f7e1` before implementation. It supersedes old swap exclusions: all completed calls enter quality/knee and the unchanged variance rule. All-call latency is primary; swap-free latency is secondary. Swap is a configuration cost on this 16 GB Mac, with whole-machine attribution limits. No benchmark observations exist.
- `c5c9671` implements per-call swap-in/out bytes, total swap-used and physical compressor memory before/after, raw snapshots/timestamps/missing reasons, configuration swapped share among known-counter calls, unknown counts and median volume (including known zero-volume calls). Pageouts alone no longer flag swapping. Unknown swap data never removes completed quality observations.
- `cf49892` implements explicit `--pass local` / `--pass cloud`, separate directories, pass identity, checkpoints and `LATEST-local` / `LATEST-cloud`. Local needs no Gemini key; cloud needs no LM Studio/model files/local-RAM gate. Cloud quota/rate-limit errors stop as `rate_limited` after a durable failed checkpoint, without an automatic retry loop.
- Pre-check mode uses only local-q8/local-q3 and the separate pencil prompt, exactly three calls each, no benchmark prompts or extra warm-ups/pilots. It records a 120-second unloaded idle window plus 120-second loaded-before/after windows for each model, roughly ten minutes idle within an approximately 15-minute check.
- Pre-check requires sudo and valid collector/baseline before calls. Missing in-call energy or requested swap observations preserves the completed response and stops before further inference. Separate validation requires all six calls, new metrics, same-segment idle windows and initial/post energy qualifications. Missing diagnostics after interruption remain `validation_incomplete`, never a false pass; completed calls are not repeated.
- Independent review identified and prompted these pre-check safeguards; final follow-up found no remaining material blocker, and offline regressions cover them. Latest fresh verification: 84 tests and Ruff pass. Live pre-check is still pending.
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
4. After owner confirms paid billing, inspect Google AI Studio for environment key/project mapping, paid plan/usage tier, active limits and actual spend-cap setting. Record evidence/project/tier/limits/check time without the key. Metadata GET or a successful inference is not proof of tier. Alerts-only budgets are not spend caps. This check has not been performed and no new cloud request is authorized.

## Full passes, only after separate approval

```sh
./scripts/run_full.sh --pass local --config configs/experiment.yaml --prompts prompts/private/full.yaml
./scripts/run_full.sh --pass cloud --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

Local: 1,015 calls (1,000 measured + five pilots + ten warm-ups), overnight. Cloud: **203 calls** (200 measured + one pilot + two warm-ups), before failed-request attempts explicitly authorized later. Input/settings are identical across passes, with source/input hashes and collection times preserved. Keep Terminal/lid open. Optional full-run energy uses `sudo -v` first or explicit `--no-energy`; pre-check always requires energy.

Cloud smoke usage was 27 input, five visible output and 28 thinking tokens, 33 billable output. At configured USD 0.75/3.75 per million input/output, that is USD 0.000144 per smoke-size call, **USD 0.029232 for 203 such calls**. Actual benchmark inputs/answers are longer; this is a tiny-prompt list-price extrapolation, not the real cost or a spending cap. Paid billing is pending owner confirmation; no tier has been verified.

Resume with `./scripts/run_full.sh --pass local --resume` or `--pass cloud --resume`; read the matching pointer/status/log first. `LATEST` tracks only the most recently touched run. Input/source changes refuse resume; completed checkpoints are never repeated. A cloud quota/rate-limit stop retains the attempt; resolve quota and obtain new-request approval before explicit resume. No automatic retry loop exists.

## Existing evidence and caveats

- `runs/LATEST` currently points to `20261015T194429.663048Z`, completed smoke only. Local/cloud/pre-check pointers do not yet exist. Before run work, read the appropriate pointer, status, then end of run.log. Check recorded PID if status may be stale; checkpoints are authoritative.
- Earlier smoke had six completed held-out calls plus one retained interrupted 6-bit attempt across two segments; completed 4-bit was skipped on resume. Zero benchmark calls. All five local thinking checks passed; Gemini recorded 28 thinking tokens. Six local load/unload operations left no models loaded. Caffeinate cleanup and notification delivery commands succeeded.
- Every completed old smoke call flagged swap activity under the old flag (which included pageouts). Re-reading raw counters confirmed nonzero swap-in bytes in all six completed calls, independently of pageouts; the 8-bit call had 1,298,546,688 swap-in bytes. These are excluded instrumentation observations, not benchmark findings. Old smoke energy was unavailable without cached sudo. Fairy secondary memory was unavailable because a sampled process exited.
- Four converted models had usable secondary samples in smoke; physical-footprint validation previously lacked complete 8-bit coverage. Exact encoded weights remain descriptive memory. Missing secondary metrics are valid unavailable observations with reasons.
- `.venv/bin/callcost` contains an older installed package. Use current source with `PYTHONPATH=src .venv/bin/python -m callcost`; launcher sets this itself. No packages/downloads/system settings were changed.
- Last known LM Studio mode was app `--run-as-service`. Standalone llmster discovery is tested offline but not live. Resume checks RAM before owned-instance recovery; explicitly unload a recorded leftover instance if needed, never someone else's model.
- Real results target: 22 November 2026; WAICY submission: 29 November. Human summary review and charts remain needed after raw collection. CI budget mode is a later milestone.
