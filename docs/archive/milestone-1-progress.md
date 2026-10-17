# Milestone 1 progress

Plan: [implementation plan](implementation-plan.md), milestone 1 only.

Starting commit: abb63c18a25baf9692316099c7c555c451cb34f7. Local HEAD, tracking branch and GitHub main matched before implementation; working tree was clean.

Work happens in the owner-requested fresh clone with normal Git commands. No additional worktree or API commits. Implement directly in this session, with a separate final code review.

## Execution tasks

1. Strict input schemas, streamed-call records and durable artifact storage.
2. LM Studio and Gemini adapters with offline streaming fixtures.
3. Machine conditions, process RSS and optional powermetrics instrumentation.
4. Sequential experiment orchestration, CLI and answer-variation logging.
5. Reproducible GSM8K sample, documentation, integration verification and review.

Interfaces: schemas feed both providers and the experiment coordinator; providers return the shared call result; collectors annotate it; storage writes immutable raw evidence; variation analysis consumes completed measured records.

## Decisions

- Missing usage, missing workers and unavailable power collection produce null values with reasons, not zeros.
- The initial documented LM Studio REST interface has no verified cache-disable control. Use its required first-appearance/repeat reporting fallback and record cache state as unknown.
- No model downloads or live paid inference are needed for offline runner implementation. Smoke tests using actual providers remain explicitly conditional on server availability and resolved model settings.
- New configurable settings will be documented with defaults; schema validation runs before network or load operations.

## Verification record

Implementation and verification entries will be appended as each task completes.

### 15 October 2026 implementation and verification

- Input validation, durable CSV/metadata storage and both streaming adapters implemented in small normal Git commits.
- Seeded configuration blocks, held-out thinking-off pilots, warm-ups, five measured repeats, first-appearance/repeat labels and exact-text answer variation implemented. Failures abort without retries and preserve partial evidence.
- Local installed Qwen3.5-9B MLX 4-bit pilot passed: explicit zero reasoning tokens, no reasoning content/tags, separate load timing, complete response evidence and process RSS samples. Native load rejected the alias with 404; resolve only the matching selected alias to its verified group key. All successful pilot instances were unloaded.
- Live worker discovery identified the bundled Node runtime executing `llmworker.js`. Its RSS is below weight-file size and is not a total unified-memory footprint. Comfortable headroom has not been established.
- Gemini has offline fixtures only because no key/model/prices are configured. Privileged powermetrics data remain unverified because non-interactive sudo required a password. These are remaining live validation tasks, not zero readings.
- Separate code review found interrupted-attempt loss, unsafe explicit process roots, empty-answer misclassification and missing baseline qualifications. Fixes and regression tests cover these, including interruption after the HTTP response while collecting conditions. Energy blocks now expose drift, missing post-baselines and negative deltas without claiming a statistical cutoff.
- GSM8K sample committed from pinned revision with 30 original test-row IDs, stable seed/hash selection, source checksum and upstream licence. Private summaries are still pending.
- Verified 47 automated tests and Ruff checks, installed CLI package/help, converter CLI help and shell syntax. A captured held-out LM Studio stream is retained as a parser fixture. No full dataset run has occurred.

### Conversion and reference amendment, before any full run

The owner explicitly selected official-source independent MLX conversions using pinned mlx-lm, same group size, and a fifth local configuration labelled Fairy's production model. This replaces the earlier proposed mlx-vlm preparation path. The four matched experimental variants use text-only mlx-lm conversion; the existing production reference retains vision support and stays outside the knee sequence.

Prepared mlx-lm 0.32.0 with locked dependencies under Python 3.13.2. Exact commands and pins are in `scripts/download_qwen_source.sh`, `scripts/convert_qwen_mlx.sh` and `docs/model-preparation.md`. Disk availability after environment setup was 192.78 GB against approximately 45 GB planned. No source weights or converted weights were downloaded. The owner explicitly requires confirmation before downloading; the code and commands are committed first for review.

Final conversion review also identified a missing source-integrity check. The preparation script now verifies exact file sets, lengths and SHA-256 hashes before converting, with regressions for modified, extra and missing source files. No model script was run.


### Approved conversion execution

The owner approved the approximately 19.33 GB download and all four conversions, requested memory monitoring and per-output pilots, and required a measured vision-weight caveat for Fairy's production reference. Started the pinned download through the committed script. Current memory pressure prompted a request to close memory-heavy apps before conversion. Header-only component accounting measured 912,020,960 vision payload bytes out of 5,950,062,560 total, or 15.3279%; runtime attribution remains explicitly unavailable. Added a two-second conversion resource monitor with a documented sustained-thrashing stop condition. The four quantisation commands and their settings are unchanged.

Conversion monitor review found that waiting only for the shell leader could leave a descendant alive after stopping. Fixed whole-group cleanup with a reproducer whose child ignores SIGTERM; regression failed before the fix and passed after it.

Approved source download completed: 19,329,392,091 bytes. All four shard hashes match upstream LFS metadata; public source manifest retained. Conversion has not started while the requested apps-closed confirmation is pending. Added the prior successful Fairy production pilot memory/load observation with explicit battery, swap, vision and RSS-attribution caveats.


### Conversion execution and output pilots completed

After the owner confirmed apps were closed, all four independent conversions completed through the committed script. Monitored wall time including verification/hashing: 103.119 seconds. Minimum sampled available memory: 1,200,488,448 bytes; maximum sampled swap growth: 4,160,356,352 bytes; guard not triggered. Layer configs confirm requested bits, affine mode and group size 64. All four tokenizer/template hashes agree and vision payload is zero. Runtime weight hashes agree with conversion manifests.

Initial concrete 8-bit inference returned HTTP 400 because the generated local entry had no reasoning control. Local model.yaml definitions now map enableThinking to enable_thinking, with explicit reasoning off requests and observed zero-token checks. They are installed only in new local cache entries; original Fairy catalog/model files are unchanged. No Hub artifacts were published. All four converted models and a fresh Fairy production reference returned Answer: 12 with zero reasoning tokens and no emitted thinking content. The final 8-bit pilot includes controller hashes; earlier attempts remain preserved.

Pilot RSS is inversely ordered across precisions, so it cannot establish total MLX memory savings. Both 8-bit successes had less than 1 GB available after the call. Comfortable 8-bit headroom and a defensible total-memory comparison remain unresolved for the future full run. No preregistered analysis definition was silently changed. A per-tensor comparison found 491/927 encoded language payload hashes differ between production and converted 4-bit despite equal shapes/dtypes/lengths, so their runtime difference is not a controlled vision-only comparison. Public preparation data and full local run identities preserve the evidence. No scored dataset run occurred.

Final preparation review found no important issues. It independently checked five raw pilot records, load metadata, controller hashes, conversion telemetry and the tensor comparison; 53 offline tests pass. Local configuration validation succeeds for five local configurations, and the final model-list check shows no loaded instances.
