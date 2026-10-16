# Measurement method

Collection, exact-answer variation, automatic quality checks, percentile aggregation and saved-run reports are implemented. Human checklist scores remain pending; blind review tooling is not implemented. Offline tests and source review do not establish unattended readiness. Held-out Gemini inference and six-configuration live interruption/resume passed on 15 October 2026. All completed smoke calls recorded swap activity. Privileged power validation remains pending; no benchmark prompts were used. See [HANDOFF.md](HANDOFF.md) for current state and [pilot validation](pilot-validation.md) for earlier evidence.

## Timing and tokens

Use a monotonic clock for durations and UTC timestamps for provenance. Total latency covers request transmission through response completion. Client TTFT ends at the first non-empty answer-text event, not a connection event, reasoning event or empty role event. Record reasoning separately when the provider exposes it.

LM Studio's generation statistics supply provider-reported token counts and decode throughput. Preserve those separately from client measurements. Gemini streaming does not expose exact server token-generation timestamps, so its delivery timing must not be represented as server decode speed. A missing measurement remains unavailable with a reason.

## Model loads

Use `GET /api/v1/models`, `POST /api/v1/models/load` and `POST /api/v1/models/unload`. Loading selects an installed model variant, not a new precision. Record the variant identifier, actual file name, quantisation, file identity and effective load settings.

Measure load-request wall time and retain the provider's load duration separately. Each load event has an identifier referenced by subsequent calls. Do not repeat one load observation across calls and treat it as many independent load measurements. Operating-system file caches mean unloading is not proof of a cold disk load.

## Memory

Identify the LM Studio application and inference-worker processes by executable path and process relationships, including workers that are not direct children of the GUI. Save the identified process set. If identification is incomplete, flag the measurement rather than measuring only the Python client.

Sample process RSS every 100 ms using psutil. For each timestamp, sum the RSS of the identified processes, then take the largest sampled sum during the call. Do not sum the independent peak of each process, because those peaks may occur at different times.

The column label is `LM Studio RSS peak, sampled`. Keep sampling timestamps and process identities in raw JSONL; pre/post-call available system memory and swap are in conditions. Raw sample timestamps expose actual gaps. Include resident weights in the peak. This is not exact model-owned memory: shared pages, unified memory and sampling resolution limit attribution.

The knee uses quality only, as amended on 15 October 2026. Exact encoded weight bytes are the descriptive memory measure; sampled physical footprint and RSS remain secondary columns. Report adjacent weight-byte savings and p50/p95 latency savings independently of pending quality. As amended on 16 October, include all completed answers regardless of swap activity. Use all-call latency for primary comparisons and the unchanged variance rule, with swap-free latency as a secondary view. Show completed counts per prompt and swap-known/unknown counts. A complete saved schedule and completed run status are required before a definitive knee conclusion.

## Energy, estimate, whole-machine delta

Use a separate optional powermetrics collector with the required sudo privileges. Keep the benchmark itself unprivileged. Prefer machine-readable plist output and start with a 250 ms sampling interval, recording the actual intervals and coverage.

Measure a ten-second idle baseline with the model resident and measurement tools active after warm-up. Bracket the measured block with idle observations to expose baseline drift. Integrate power above baseline over each request window:

```text
estimated_energy_j = sum((power_w - baseline_power_w) * overlap_seconds)
```

Use the pre-block baseline for subtraction, and save the post-block baseline separately to reveal drift. As amended on 16 October, require provider `is_delta: true`. Anchor the first end to its monotonic receipt and advance subsequent interval ends by reported `elapsed_ns`; retain actual receipt times and receipt lags. Reject absolute timing drift of at least half a reported interval and reject parser failures. The first receipt has unknown fixed delivery delay, so this remains approximate call-boundary attribution rather than synchronised device telemetry. Samples describe time intervals. Use their overlap with the request window, record boundary approximation and reject insufficient coverage. Require at least two overlapping samples and at least 90% interval coverage; reject overlapping sample intervals beyond 10 ms. Preserve negative deltas rather than clamping to zero. Each configuration energy block records the absolute baseline drift, a descriptive shift/missing-baseline assessment and IDs of negative-delta calls. Calls link to that block through configuration ID. These qualifications must accompany energy estimates. There is no registered statistical drift cutoff, so a shift flag is not a significance claim or automatic correction. Short calls frequently have unavailable energy at this sample rate.

Use only supported, non-overlapping power domains. Record their names and units. A CPU/GPU/ANE sum is not wall-socket power and may omit memory, display and other components. Every presentation must retain the label `estimate, whole-machine delta` and identify the actual scope in its accompanying method.

During Gemini requests, this measures only the Mac's client activity. Cloud-side energy remains outside scope. If collection is unavailable, report an unavailable value and reason. Battery percentages and Activity Monitor Energy Impact are not joule measurements.

## Caching and scheduling

Consult the installed LM Studio version and its supported API controls before the first run. The REST documentation checked on 15 October 2026 does not document an explicit prompt-cache-disable parameter. `store: false` disables conversation storage; it does not establish that prompt/KV reuse is disabled. KV cache offloading controls placement, not reuse.

When a supported cache-disable control exists, use it and record the requested and verified setting. Otherwise record the first measured appearance of each prompt per configuration separately from the four subsequent measured appearances. Report both strata with their own sample counts. Do not label either stratum as proven uncached or cached. Keep warm-up prompts separate from the scored dataset.

Use one request at a time and seeded configuration blocks: load one configuration, run a held-out pilot, run the configured warm-ups, then shuffle all task prompts independently for each of five repeat rounds before unloading. Configuration order is seeded too. This preserves repeat cache exposure, but a single block per model cannot remove thermal or time-of-day confounding. Keep configuration settings fixed. Preserve the actual schedule, loading events and cache policy so reloads and cache exposure can be audited. A fresh chat does not prove a fresh runtime cache.

## Gemini thinking and price

The experiment uses Gemini 3.8 Flash with `thinking: {thinking_level: low}`. This model cannot disable thinking. The native request sends `thinkingConfig.thinkingLevel`, without a budget. Log thinking tokens separately and count them once in billable output. The requested level is recorded, while the effective internal level is not exposed. Local configurations use `reasoning: "off"`; their held-out pilots must return a nonempty answer, zero reasoning tokens and no observed reasoning content or `<think>` tags. Missing reasoning-token evidence is not zero. Cloud pilots require a completed, nonempty answer and observable token accounting, not zero thoughts. Subsequent calls retain these separate checks. The cloud reference is not a thinking-off comparison. Record settings, evidence sources and effective model identifiers.

Use provider usage metadata for input, visible output, thinking and cached token counts. Calculate the declared standard list-price equivalent using configured prices. Include billable thinking tokens exactly once. When Gemini omits `thoughtsTokenCount`, infer it only if complete counts permit `totalTokenCount - promptTokenCount - candidatesTokenCount - toolUsePromptTokenCount`; record that accounting source. No tools are requested, so absent tool-use count is zero. Cached input is charged at the configured standard input rate: this is a standard list-price equivalent, not a claim about a cache-discounted bill. Record currency, price source and checked date; report this as a list-price equivalent rather than the actual free-tier bill. Never infer missing usage from response length.

## Quality and statistics

Numeric answers must appear on the final non-empty line as `Answer: <number>`. Parse the declared numeric grammar, compare with Decimal arithmetic and the prompt's fixed absolute tolerance, and record parseability independently of correctness. A format failure fails the scoring rule.

Checklist scores are the fraction of equally weighted criteria passed. Automatic criteria must describe only what their check can establish. Semantic faithfulness remains a human criterion. Average repeated scores within prompts, then average prompts equally within a task. Pending human scores must not be interpreted as failures or silently removed from a complete quality score.

Keep call failures, timeouts, truncation and missing observations explicit. A refusal or unparseable completed answer is a quality outcome. Infrastructure failures must not disappear through silent retries. Incomplete results must not support an unqualified knee conclusion.

Use the ordinary median for p50 and nearest-rank p95. Display the number of valid observations for each metric. For IQRs, use linear interpolation at ranks `(n - 1) * 0.25` and `(n - 1) * 0.75` in zero-based sorted data. Closed IQR intervals that touch count as overlapping. Keep prompts as the independent task units when describing uncertainty.

The four independently converted mlx-lm configurations form the quantisation sequence. `comparison_role: production_reference` identifies Fairy's existing model, whose conversion retains vision support. Preserve its label and exclude it from that sequence, alongside the Gemini cloud reference.

Apply the README's knee and indistinguishability rules without selecting thresholds after seeing outcomes. Keep cache strata visible; do not silently select the stratum producing the strongest claim. Any remaining analysis conventions must be committed before a full run.

## Answer variation across repeats

Temperature 0 controls token sampling but does not guarantee reproducible GPU arithmetic or identical output. Floating-point addition and multiplication are not associative, and changes in evaluation order can alter results. Numerical changes can affect greedy token selection when candidate scores are close. This is a general limitation, not proof that any observed difference was caused by GPU arithmetic. See the [numerical accuracy](https://docs.pytorch.org/docs/stable/notes/numerical_accuracy.html) and [reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html) explanations in PyTorch's documentation; citing them does not imply LM Studio uses PyTorch.

Within a single run, group measured calls by configuration ID and prompt ID. Compare the exact decoded answer text without trimming, case folding or other normalisation. Retain each answer and its call ID, plus the number of distinct answers in the group. Log the group and participating call IDs whenever at least two distinct answers are observed. Compare answer text rather than provider IDs, timestamps or reasoning metadata.

For each configuration and task type, report `varying_prompts / compared_prompts`: the number of prompt groups containing more than one distinct answer divided by the number with at least two completed measured responses. For example, answers A, A, B, A, B for one prompt contribute one varying prompt, not two or five. Record the distinct-answer count of two for that group.

Exclude warm-ups and failed attempts from text comparisons, but keep their records and failure counts. A provider-completed truncated response remains an observed answer with its truncation flag. Groups with fewer than the configured five completed measured responses are explicitly incomplete; those with fewer than two cannot be compared and must not be reported as stable. Display incomplete and uncomparable group counts alongside the variation count. Compare all measured repeats, including the first appearance, while retaining their cache-stratum labels.

Output variation is independent of quality scoring. Two different answers may both be correct, and five identical answers may all be wrong. Do not attribute differences automatically to quantisation, floating-point arithmetic or caching.

## Run artifacts

`calls.csv` contains per-attempt identity, prompt/configuration IDs, repeat and cache-stratum labels, status, answer, timing, token usage and cost measurements. `metadata.json` stores machine/software conditions, input hashes, model identity, load events, settings, pricing and the schedule. Raw memory and power samples preserve the basis of derived values. Later review decisions will reference anonymous answer IDs with a separate hidden identity mapping.

Record chip, CPU/GPU cores, RAM, macOS, LM Studio version, model file and quantisation, charger state, timestamp and readable thermal state. Missing thermal readings mean unavailable, not nominal. Secrets and machine serial numbers are not needed in run metadata.

## Sources

- [LM Studio REST API](https://lmstudio.ai/docs/developer/rest)
- [LM Studio conversation storage](https://lmstudio.ai/docs/developer/rest/stateful-chats)
- [LM Studio load parameters](https://lmstudio.ai/docs/developer/rest/load)
- [Gemini usage metadata](https://ai.google.dev/api/generate-content)
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [psutil](https://psutil.io/)
- The installed macOS `powermetrics --help` and manual, whose version and supported samplers must be recorded with an instrumented run.

## Current instrumentation limits

The automatic process selector recognises the LM Studio app bundle, standalone `llmster` daemon roots under LM Studio installation directories, and known inference-backend paths, plus the bundled Node runtime executing `llmworker.js` as observed on LM Studio 0.4.24. If it cannot identify a worker, memory is unavailable. Explicit `measurement.lmstudio_process_ids` add manually identified roots and descendants; they must still have recognised LM Studio identities. Automatic app/worker discovery remains active so explicit roots cannot silently replace the complete app group with just the Python client or GUI. A changing process set, failed sample or no in-window sample makes the peak unavailable. RSS is not physical footprint and has no proven relationship to model-only unified-memory use.

The powermetrics parser currently accepts only delta plist samples (`is_delta: true`) with `elapsed_ns` and numeric nonnegative `processor.cpu_power`, `gpu_power` and `ane_power` in mW. The installed help confirms these samplers and NUL-separated plist output, and 48 actual records parsed under sudo in the 16 October held-out check. Live call-energy validation remains incomplete because that check stopped on receipt-timing overlap; the amended timeline correction is tested offline and awaits a newly authorized check. Unsupported schemas produce unavailable energy, not substituted readings. Raw samples and stderr are retained.

Model file hashes identify the files supplied in config; the native model-list API does not independently prove that they are the files loaded by the runtime. Verify this mapping manually. The runner refuses to start if any LM Studio instance is already loaded and records the returned model identity, format, quantisation and echoed context length. It does not change the installed model files.

On LM Studio 0.4.24, the models endpoint listed a `@4bit` variant alias that the load endpoint rejected with HTTP 404. For an alias, CallCost requires the listed `selected_variant` to match exactly, checks the reported quantisation, then sends the accepted group key. An unselected alias is rejected rather than silently loading another precision. The API behaviour for multiple newly converted variants must be validated before the full experiment; prepare separately addressable installed variants if the native API cannot select a member of a grouped listing. Requests, responses and HTTP statuses for list/load/unload are preserved alongside inference evidence.

## Weight components for the production reference

For local safetensors models, inspect headers without loading arrays. Sum encoded tensor payload lengths by vision/language prefixes, including quantisation weights, scales and biases. Keep per-file byte counts and explicit scope in `metadata.json.model_weight_components`. Fairy's production reference retains vision weights while the four mlx-lm conversions are text-only. Its memory and load observations must carry this caveat. Encoded vision-weight bytes do not measure incremental runtime RSS, and cannot be subtracted from measured RSS to create a comparable text-only value. See [the measured component report](data/fairy-production-weight-components.json).

## Pre-registration amendment, 15 October 2026

The knee is the first step after the baseline step where task quality falls by at least 10 percentage points and at least twice the previous step's drop. The first step establishes the baseline drop and cannot qualify. Cost is not a gate. Report each step's weight-byte memory saving and p50 and p95 latency savings, with measured physical footprint as a secondary column.

The original memory and latency gates were removed before scored benchmark data and before the unattended launcher smoke test. Every adjacent weight-byte saving exceeds 20%, making the original memory gate unsatisfiable for this series. A measured-footprint gate would depend on fixed overhead, and memory bandwidth may make latency fall proportionally with weight size. These are design reasons, not findings from the task dataset. Earlier excluded instrumentation pilots exist. The revised hypothesis is nearly flat quality followed by a sharp drop, while cost falls by a roughly steady amount per step. The variance rule and both kill criteria in the README are unchanged.

Superseded on 16 October 2026: the earlier exclusion of swap-active/unknown calls no longer applies. All completed answers enter quality and the knee. Whole-machine swap-in/out volumes, swap storage and compressor memory describe configuration cost on this 16 GB Mac; unknown metrics remain unavailable with reasons. Missing completed prompts or pending human scores cannot establish either a knee or no knee.

## First summarisation dataset

The ten summaries in `prompts/summarisation.yaml` are Fairy-style prompts written for the benchmark (invented texts), not real Fairy usage. Andrii confirmed review on 15 October 2026 and the approved file was committed unchanged. They have not been sent to a model; the full benchmark still requires separate approval. `max_words` splits on whitespace and compares the count with an inclusive integer maximum; regex `pattern` is an alias for `value`. All supplied scoring rules are retained. Human criteria remain pending until blind review.

## Separate passes and held-out pre-check, 16 October 2026

`--pass local` selects the five local configurations, with 1,000 measured calls plus five pilots and ten warm-ups, 1,015 scheduled calls. `--pass cloud` selects one cloud reference, with 200 measured calls plus one pilot and two warm-ups, 203 scheduled calls. Inputs/settings are identical across passes and hashed independently. Each pass has its own directory, checkpoints and latest pointer. The cloud pass does not require LM Studio or the local available-memory guard. No two launchers run concurrently. Different pass collection windows remain visible in timestamps/conditions.

For each request, save raw `vm_stat` and `sysctl -n vm.swapusage` observations with monotonic timestamps. Convert swap-in/out page deltas to bytes with the reported page size. Physical compressor usage is `Pages occupied by compressor` times page size. Preserve reported swapusage units/raw text; conversion does not imply precision beyond the system reading. Flag swapping only when swap-in or swap-out increases, not merely pageouts. Volume is the sum of both directions. Unknown/reset counters are unknown cost, never a quality exclusion. Configuration swapped share uses known-counter calls as its denominator, with unknown counts separate; median volume includes known zero-volume calls. Report all-call and known-swap-free latency distributions separately.

`--precheck` loads only local-q8/local-q3 and uses exactly three calls each on the separate held-out pencil prompt. It reads no benchmark prompt file. No extra pilots/warm-ups are added. Collect a 120-second unloaded idle window, then 120-second loaded idle windows before and after each configuration's three calls. This supplies roughly ten minutes of idle observations within an approximately 15-minute diagnostic. Compare swap byte rates over saved observation windows; whole-machine background activity prevents definitive causal attribution to inference.

Pre-check requires sudo-backed powermetrics. Missing startup/baseline prevents calls; missing in-call energy or requested swap readings preserves the completed response and stops before the next call. A separate validation record requires all six calls, valid new metrics, valid initial/post energy baselines and all required idle windows. Missing diagnostics after interruption remain validation-incomplete rather than a false success, and completed calls are never silently repeated. Raw/parsed power samples, units, domains and coverage qualify every energy estimate, whole-machine delta. The pre-check does not authorize either full pass.
