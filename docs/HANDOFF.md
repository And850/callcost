# Published charts and Results, 17 October 2026

- Owner specified one chart per task: a connected 8→6→4→3 sequence at median all-call latency and primary quality, p50-to-p95 horizontal whiskers, bit labels, unconnected Fairy/cloud markers and sample sizes in captions.
- Owner explicitly selected README results, docs/data/results-20261017.json and SVG/PDF/PNG figures in docs/figures for commit and push together on 17 October. Only selected aggregate benchmark results are published; raw run artifacts remain private. No raw answers or review identity are exported. No model calls or reruns occurred.
- Offline generator: scripts/plot_results.py. Export from saved reports with --local-run and --cloud-run plus --export-only; render saved aggregate data with --data docs/data/results-20261017.json --output docs/figures using the optional plots dependency. SVG/PDF are native outputs; PNG previews were rasterised from SVG using existing bundled sharp, without downloads.
- Results retain primary max_words scoring, dated deviation, registered per-step variance and task knees, measurement limitations and kill criterion 2 currently unmet. Owner-requested additions include the In short paragraph, qualified hypothesis outcome and criterion 1 not triggered, swap shares, cloud retry/local response reliability, author-reviewer and AI-assisted prompt limitations, and current Status/Milestones. Provider billing reconciliation remains outstanding.

# Scored summary audit update, 17 October 2026

- Owner exported Downloads/summary-scores.json and authorized import plus full summary audit. Strict import completed into both original pass directories. Private exact export copy and import-provenance.json are in runs/blind-review-20261017. Do not import again or overwrite the review.
- Updated combined scored results: runs/audit-20261017-scored/audit.md and audit.json. Independent arithmetic/variance/knee/checkpoint-integrity verification is in independent-summary-checks.json beside them. Primary and length-sensitivity scores, exact text variation, all/swap-free p50/p95 and counts are present for every configuration. Both pass reports are regenerated; cloud remains outside the knee sequence.
- No actual Fairy production decision change is recorded. The scored audit compares the complete task-set picture and keeps practical usefulness criterion 2 explicitly unmet. Only an actual owner-confirmed change can alter that assessment.
- Original prompt file, responses and checkpoints are unchanged. No inference, reruns, billing/account changes, downloads or system changes occurred. Numeric results and raw review data remain ignored and uncommitted. Charts and provider-billing reconciliation remain outstanding.

# Summary protocol deviation update, 17 October 2026

- Owner identified that the intended later relaxed-length revision was never committed/run. README records what ran (6f6de97 tight summary instructions and 50-90-word max_words scoring checks), what was intended and identical prompts/rubrics across all configurations.
- Do not edit prompts/summarisation.yaml or rerun inference. Primary summary scores retain max_words; secondary quality_without_max_words drops only that automatic criterion and reweights the remaining criteria, retaining equal prompt weights. Knee/variance remain primary-only.
- Blind review remains in progress with its original packet and IDs unchanged. Both score columns stay unavailable until the human criteria are imported, then populate automatically on report regeneration.

# Billing reconciliation update, 17 October 2026

- Owner requests all saved Gemini usage across the repo, tax clarification and a provider-billed placeholder. No model calls are authorized or needed for this work.
- Private all-history inventory: runs/gemini-cost-ledger-20261017/report.md and ledger.json, including smoke, separate cloud segments/retries and zero-Gemini local pre-checks. No double-counting resumed checkpoints. The ledger omits answer text to avoid interfering with blind review.
- Provider billing remains pending: populate the ledger billing.json for all recorded usage, or the cloud run billing.json for this run only, from a matching export. Do not substitute the owner's approximate balance change for an invoiced amount. VAT applicability is explicitly uncertain; method documents Spain's 21% standard rate and account-dependent Google treatment. Do not label a numerical VAT fit as proof.
- Blind review is in progress. Do not regenerate its packet, change anonymous IDs or inspect/reveal the hidden key. No model calls, billing/account changes or benchmark reruns were performed.

# Current handoff update, 17 October 2026: collection finished, blind review pending

- Both local and cloud passes are complete. Read LATEST-local / LATEST-cloud, each status.json and run.log. Do not resume or issue more model calls. Cloud was explicitly approved, --no-energy, with paid prepaid billing confirmed by the owner.
- Cloud retry policy and initial resume were committed/pushed as 1b98743. Raw failure attempts and original checkpoints remain private. Every collected automatic retry was 503 UNAVAILABLE; source versions are retained per segment. Later hardening pins accepted source transitions and excludes standalone INTERNAL status outside HTTP 500/503.
- Offline combined audit: runs/audit-20261017/audit.md and audit.json. Original measurements and reports remain in the pass directories. No raw benchmark results are committed.
- Local energy audit: the local run's energy-audit.json replays available estimates from retained samples/baselines. Missing q6 timing observations remain unavailable, not reconstructed. No local rerun was performed or authorized.
- Blind review is prepared at runs/blind-review-20261017/review.html, with a separate hidden key. Follow docs/blind-review.md. Automatic criteria are fixed; human criteria need owner scores. No LLM judges answers. Do not inspect key.json before finishing.
- Import the exported scores with scripts/review_summaries.py import, regenerate both reports, then revisit summary quality, all three summary variance steps and the knee. No actual Fairy production decision has yet been changed; do not claim usefulness criterion 2 is met.
- Current task authorization: code/docs/tests and small commits/pushes; no further model calls, reruns, downloads or system changes without approval. Preserve the frozen pre-registration.

# Authorization update, 17 October 2026: cloud retries and audit

- Owner authorizes HTTP 500/503 or UNAVAILABLE retries, four additional attempts with 10/30/90/270-second backoff; auth/quota/billing stop immediately. Owner approves resume of the retained cloud pass with --no-energy after this committed implementation. Completed checkpoints must not repeat. Source upgrade is explicit and recorded per segment.
- After cloud collection, audit q3 parseability versus wrong answers, exact-text variation, all/swap-free latency, local missing energy, every variance step and kill criterion 2. Prepare blind summary review. No local rerun is authorized.

# Current authorization update, 17 October 2026

- Local collection completed: 1,015/1,015 calls in `20261016T213431.178691Z-local`. Preserve all artifacts; no repeat calls are authorized.
- Owner now explicitly approves the separate cloud pass with `--no-energy`, without a clean restart. Owner reconfirmed Tier 1, prepaid balance, auto-reload off and considers the AI Studio warning resolved or a display issue. This supersedes the historical cloud block below. Prior key/project/tier verification remains recorded privately.
- Cloud was launched in its own directory with --no-energy, then stopped on HTTP 503 UNAVAILABLE (provider high demand). LATEST-cloud identifies the retained partial run. No retry was made; obtain approval before new requests/resume, preserve completed checkpoints. Cloud client energy is deliberately unavailable due to background-noise attribution limits, documented in methodology.md. No benchmark results are committed; read private artifacts for counts and costs.
- Audit follows cloud collection; owner will send the audit list. Do not change frozen pre-registration or auto-publish run results.

# Current handoff, 16 October 2026

## Current authorization

- Code/docs edits, offline tests, small commits/pushes are authorized.
- Owner authorized a roughly 15-minute pre-check only after confirming a clean restart: exactly three held-out calls each on local-q8/local-q3, new swap observations and sudo-backed energy validation. Owner confirmed ready after restart. Boot time changed to 16 October 21:00:50 UTC; AC power and headless service were checked. The first check stopped after one call. The owner then approved a fresh six-call check; it completed and validated successfully, as recorded below. No further model calls are authorized here.
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
- Independent review identified and prompted these pre-check safeguards; final follow-up found no remaining material blocker, and offline regressions cover them. Latest fresh verification after energy timing correction: 89 tests and Ruff pass. The first live pre-check failed after one completed call; the separately approved replacement passed six calls, as recorded below.
- Approved summaries were committed unchanged in `6f6de97`. Ignored `prompts/private/full.yaml` contains 30 pinned GSM8K + 10 approved summaries, preserving IDs, source records and scoring rules; schema and full-dataset checks pass. No benchmark prompt has been sent to a model.
- Saved-run reporting includes costs/quality, observation counts/missing reasons, secondary footprint/RSS, thinking/billable output, payloads, list-price equivalent, energy qualifications and per-prompt counts. Weight bytes are descriptive memory; no runtime-memory gate. Human summary scores remain pending; blind review tooling/charts remain unfinished.

## Next actions

1. Fresh held-out pre-check completed and passed. Give the owner the local-only command below for their Terminal launch tonight, with Codex and unused apps closed, charger connected, lid and Terminal open, headless LM Studio server running and no model loaded. Do not start the full pass from chat.
2. Full local retains its 10 GiB available-RAM and 10 GiB disk entry guards. After cleanup, available RAM was 10.04 GiB, only just above the guard. If the guard fails, stop and close unused apps; do not lower it or change system settings. Passing it does not prove swap-free inference.
3. Cloud stays blocked until the owner resolves the AI Studio outstanding-balance warning and separately approves cloud collection. This must not block local. Before cloud collection, recheck billing/key/project/tier/limits without printing credentials. No cloud call is authorized now.

## Full passes, only after separate approval

```sh
./scripts/run_full.sh --pass local --config configs/experiment.yaml --prompts prompts/private/full.yaml
./scripts/run_full.sh --pass cloud --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

Local: 1,015 calls (1,000 measured + five pilots + ten warm-ups), overnight. Cloud: **203 calls** (200 measured + one pilot + two warm-ups), before failed-request attempts explicitly authorized later. Input/settings are identical across passes, with source/input hashes and collection times preserved. Keep Terminal/lid open. Optional full-run energy uses `sudo -v` first or explicit `--no-energy`; pre-check always requires energy.

Cloud smoke usage was 27 input, five visible output and 28 thinking tokens, 33 billable output. At configured USD 0.75/3.75 per million input/output, that is USD 0.000144 per smoke-size call, **USD 0.029232 for 203 such calls**. Actual benchmark inputs/answers are longer; this is a tiny-prompt list-price extrapolation, not the real cost or a spending cap. Owner confirmed paid prepaid billing. Tier 1 and model limits were verified in AI Studio, but a contradictory outstanding-balance warning remains a cloud-readiness blocker.

Resume with `./scripts/run_full.sh --pass local --resume` or `--pass cloud --resume`; read the matching pointer/status/log first. `LATEST` tracks only the most recently touched run. Input/source changes refuse resume; completed checkpoints are never repeated. A cloud quota/rate-limit stop retains the attempt; resolve quota and obtain new-request approval before explicit resume. No automatic retry loop exists.

## Existing evidence and caveats

- `runs/LATEST` and `runs/LATEST-precheck` point to `20261016T212019.875153Z-precheck`, completed and validated. The failed prior check remains preserved separately. Local/cloud pointers do not yet exist. Before run work, read the appropriate pointer, status, then end of run.log. Check recorded PID if status may be stale; checkpoints are authoritative.
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

## Fresh pre-check outcome, 16 October 2026

- Owner approved six new held-out calls and started the fresh Terminal command. Run `20261016T212019.875153Z-precheck` finished with exit 0, completed 6/6, `precheck_validation.valid: true`, no errors and zero benchmark calls. Every saved request matches the separate pencil pilot; all six local thinking checks passed. Prior failed evidence remains unchanged.
- Local-q3: latencies 1.77/1.67/1.75 s, zero swap-in/out in all calls and both loaded idle windows. Unloaded idle also had zero swap traffic.
- Local-q8: latencies 8.94/3.26/3.12 s, decode rates 19.15/18.94/19.66 tokens/s. Swap traffic was 1,122,304,000 / 14,172,160 / 1,376,256 bytes, mostly swap-in. Swapped share 3/3, median volume 14,172,160 bytes; no swap-free call latency is available for q8. Its loaded-before and loaded-after 120-second idle windows recorded 2,655,764,480 and 3,128,606,720 bytes. Swapping therefore occurs outside inference too; whole-machine counters cannot establish process causality. The short prompt does not prove comfortable headroom for long benchmark inputs. Swapping remains a measured cost, not a quality exclusion.
- All requested swap/storage/compressor fields are present. Q8 compressor memory before/after calls is retained in raw evidence, including approximately 8.44 to 1.22 GB during its first call. Secondary sampled footprint reached 10.89 GB; encoded weight bytes remain the descriptive memory metric.
- Sudo-backed powermetrics produced 537 q3 and 579 q8 parsed samples, mW converted to watts for CPU + GPU + ANE, with no collector errors. All six energy estimates were usable: q3 32.20/32.78/32.69 J; q8 78.70/52.50/49.43 J. Label as estimate, whole-machine delta. Baselines shifted (q3 1.44 to 2.42 W; q8 2.16 to 1.76 W); initial receipt-anchor uncertainty remains. These are instrumentation observations, not benchmark findings.
- Both models unloaded, launcher exited, sudo refresh failures were zero. Post-cleanup available RAM was 10,777,821,184 bytes (10.04 GiB), swap used 2,298,347,520 bytes. GPU wired limit was observed as 12288 MiB; no system settings were changed by this work.
- Local-only launch, executed by the owner after closing Codex:

```sh
cd /Users/andreyryzhanskiy/Documents/CallCost/callcost && sudo -v && ./scripts/run_full.sh --pass local --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

- Local has 1,015 scheduled calls. Reserve roughly 12 to 14 hours as a planning allowance, not a measured full-workload prediction. Longer prompts, output lengths and swapping can extend it. Cloud is separate and blocked; no Gemini key/billing is needed locally. Neither full pass was started here.
