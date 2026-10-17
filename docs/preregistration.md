# Pre-registration and amendments

The initial experiment remains frozen. The following sections are moved verbatim from the former root README, including historical operational wording. The later operational clarification and prospective judge exception do not replace the initial human scores. Current state and permissions live in [PLAN.md](../PLAN.md); the [history](log.md) and [judge protocol](judge-preregistration.md) retain the decision context.

Legacy `docs/...` link destinations inside frozen text resolve through the compatibility symlinks in `docs/docs/`. They are retained to avoid changing any frozen byte. Preparation/runtime evidence remains in `docs/data/`; published results are in [results/](../results/).

## Frozen-text relocation verification, 17 October 2026

SHA-256 covers each exact UTF-8 block, including its original trailing whitespace. Before and after hashes match; neither scores nor registered rules changed.

| Block | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| initial-registration | `8c4622bfeec2d77c2b30d1ec612c20234be2cd55658f5db6fe5ba9f32150af19` | `8c4622bfeec2d77c2b30d1ec612c20234be2cd55658f5db6fe5ba9f32150af19` |
| summary-deviation | `89819da0238ae1039e84549217ce1e19dc53c715ec5b278a47c5f40e3ad09136` | `89819da0238ae1039e84549217ce1e19dc53c715ec5b278a47c5f40e3ad09136` |
| separate-pass | `717dae5047699d3743291e3ccb9a010d5743ea9e206002bb03ecaec37fa5546e` | `717dae5047699d3743291e3ccb9a010d5743ea9e206002bb03ecaec37fa5546e` |
| prospective-judge | `b007a69df90ce1d61385b7daeaac34c78c1c6aa17985f9975f74abf5d2d4e460` | `b007a69df90ce1d61385b7daeaac34c78c1c6aa17985f9975f74abf5d2d4e460` |
| cloud-reference | `9cbe246d2665b676f045a154c9c8e5812fc988dd2f7fb99e7a82872a17076763` | `9cbe246d2665b676f045a154c9c8e5812fc988dd2f7fb99e7a82872a17076763` |
| operational-clarification | `933b74ec590453087727e798d114a69cce18c72adfd976d6f00d42f885689fac` | `933b74ec590453087727e798d114a69cce18c72adfd976d6f00d42f885689fac` |

**Dated operational clarification, 17 October 2026:** the 16 October separate-pass amendment below stops quota/rate-limit errors without retries. The later decision in `1b98743`, also recorded in AGENTS.md and HANDOFF.md, permits four extra HTTP 500/503 attempts with 10/30/90/270-second waits. Auth, billing and quota errors still stop immediately. This note clarifies operations without rewriting the frozen pre-registration text.

## Hypothesis

For a fixed task set, quality stays nearly flat across quantisation levels and then drops sharply at one step, while cost falls by a roughly steady amount per step. The knee can occur at different quantisation levels for different task types. The finding is the knee per task type, not a claim that local inference beats cloud inference.

## Pre-registration

These rules are recorded before the first full run. Any later amendment must be committed and identified in the results.

- Dataset: 30 reproducibly selected GSM8K test problems and 10 Fairy-style prompts written for the benchmark (invented texts). The summaries require owner review before any model sees them.
- Repeats: five measured calls per prompt per configuration. Warm-ups are additional and excluded from the results.
- Quality per configuration: mean score across prompts for that task type. Average repeated scores within each prompt first, so each prompt has equal weight.
- Knee, amended 15 October 2026: the first step after the baseline step where task quality falls by at least 10 percentage points AND at least twice the previous step's drop. Cost is not a gate. For every step, report weight-byte memory saving, sampled physical footprint as a secondary column, and p50 and p95 latency savings.
- Boundary convention: the first step down establishes the previous-drop reference and cannot itself qualify as a knee.
- Memory convention, amended 15 October 2026: descriptive memory savings use exact encoded tensor payload bytes for the loaded model. Sampled physical footprint and RSS remain secondary measurements. Neither is a knee gate.
- Swap convention, amended 16 October 2026: all completed answers contribute to quality and the knee regardless of swapping. All-call latency is primary; report swap-free latency separately, swapped-call share, unknown count and median swap volume. See the dated amendment below.
- Variance kill: if, for adjacent quantisation levels, the interquartile ranges of per-call latency overlap AND the quality difference is under 5 percentage points, the levels are treated as indistinguishable.
- If no step meets the knee definition for a task type, report **no knee found** for that task type.

Compare adjacent levels within the same local model family, ordered from highest to lowest precision. Gemini and Fairy's production model are reference points outside the four converted levels in the quantisation sequence. Percentage-point quality changes are distinct from relative percentage savings in latency and memory.

### Pre-registration amendment, 15 October 2026

Before any scored benchmark data, physical footprint was tested with Darwin `proc_pid_rusage`, `RUSAGE_INFO_V0`, `ri_phys_footprint`, sampled over the same LM Studio process group as RSS. Complete contemporaneous process-group samples were required. Valid 3-, 4- and 6-bit pilot peaks were 5,356,283,032, 6,471,723,096 and 8,655,694,824 bytes. They exceeded encoded weight bytes and increased with precision. Both 8-bit attempts lost process coverage during at least one in-call sample, so neither supplied a valid peak. Full validation therefore failed. The [validation record](docs/data/physical-footprint-validation.json) retains both attempts, errors and swap counters. These held-out calls are instrumentation checks, not benchmark results.

The initial memory fallback selected **loaded weight bytes**, defined exactly as the sum of encoded tensor payload lengths in the selected safetensors files, excluding headers, tokenizers and configuration files. This is a static weight-footprint proxy, not measured peak runtime memory. For the four text-only levels it is 3,918,948,864, 5,038,041,600, 7,276,227,072 and 9,514,412,544 bytes. With these exact weights, adjacent savings are 23.53% (8 to 6 bit), 30.77% (6 to 4 bit) and 22.21% (4 to 3 bit). Every step exceeded the original 20% limit, making that gate unsatisfiable for these levels. This is a constraint of the amended experiment, not empirical evidence that no runtime-memory knee exists. The superseding amendment below removes this gate. Context length and cache settings remain fixed across levels; this proxy does not measure runtime cache or activation allocation. Keep sampled physical footprint and RSS in separately labelled columns with missing-value reasons. Fairy retains 912,020,960 encoded vision-weight bytes and remains outside the knee sequence.

Historical policy, superseded by the 16 October amendment below: record whole-machine `vm_stat` swap-ins, swap-outs and pageouts around every call, in pages and bytes. Flag a call if any counter increases. Retain and report these calls, but exclude them from every quantity used in knee analysis, including latency, quality and variance. Missing or reset counters also make a call ineligible, with a separate unknown count. Report eligible counts per prompt and configuration; do not treat missing prompts or an empty eligible group as zero quality or evidence of no knee. All validation pilots recorded swap activity, so a fresh, quiet launch remains necessary.

### Superseding pre-registration amendment, 15 October 2026

Before the first scored benchmark and before the unattended launcher smoke test, remove the original memory-saving and latency-saving gates. The exact weight-byte savings at every adjacent precision step exceed 20%, so the memory gate is unsatisfiable by construction for this series. A runtime-footprint gate would also depend on fixed process overhead. Decode latency on Apple Silicon may reflect memory bandwidth, making a proportional cost reduction plausible; this is a motivation, not a measured result. Earlier excluded model-preparation and instrumentation pilots exist; no task-set benchmark data has been collected.

The revised hypothesis is that task quality stays nearly flat across levels and then drops sharply at one step, while cost falls by a roughly steady amount per step. The knee is the first step after the baseline step where quality falls by at least 10 percentage points AND at least twice the previous step's drop. The baseline step cannot qualify. Cost is no longer a gate: show weight-byte memory saving, measured physical footprint as a secondary column, and p50 and p95 latency savings for every step. The variance rule and both kill criteria remain unchanged. If no eligible step meets the quality rule, report **no knee found**; missing eligible data or outstanding human scores are **insufficient data**, not evidence of no knee.

### Thinking pre-registration amendment, 15 October 2026

Before any scored benchmark data or launcher smoke data, clarify the thinking policy: thinking is off for all local configurations (the quantisation series and Fairy's reference). The cloud reference runs at `gemini-3.8-flash`'s lowest available level, `thinking_level: low`, because this model cannot disable thinking. Its thinking tokens are reported separately and included in billable output. The cloud is a reference point outside the knee calculation, so this does not affect the knee rule. This supersedes the earlier requirement that cloud thinking be disabled and aligns the method with the recorded cloud configuration. Excluded local preparation and instrumentation pilots already exist.

### Swap and separate-pass pre-registration amendment, 16 October 2026

Before any scored benchmark data, supersede the 15 October swap exclusion. Excluded preparation/instrumentation pilots and a held-out launcher smoke already exist; no benchmark prompts have been used. Swapping is part of the resource cost of a configuration on this 16 GB Mac, not a reason to discard its completed answer. All completed calls, including swap-active and swap-unknown calls, contribute to quality, quality-only knee analysis and the registered variance rule. Failures and pending human scores retain their existing treatment; temperature 0 still does not guarantee identical answers. The knee thresholds, first-step convention and both kill criteria are unchanged.

Record per-call whole-machine swap-in and swap-out page deltas from `vm_stat`, multiplied by the reported page size to obtain bytes. Record `vm.swapusage` used bytes and physical compressor memory (`Pages occupied by compressor` times page size) before and after every call, retaining raw readings and missing/reset-counter reasons. Pageouts remain separately recorded but do not alone establish swap activity. Swap volume means swap-in plus swap-out bytes, not net growth in swap storage. Missing counters are unknown, never zero.

Report latency p50/p95 for all completed calls and separately for calls with known zero swap-in and swap-out deltas. Report the swapped-call share among calls with known counters, the unknown count and median swap volume across calls with known counters for each configuration. All-call latency supplies the primary adjacent cost comparisons and the unchanged latency-IQR variance rule; swap-free latency is a labelled secondary view. Unknown swap counters do not remove completed answers from quality. These system-wide measurements can include background activity and are not per-process attribution.

Collect the five local configurations in an independently resumable local pass and the single Gemini reference in an independently resumable cloud pass. Both retain the same approved 40 prompts, five measured repeats, fixed settings, pilots and warm-ups. Preserve pass identity, input/source hashes and separate pointers/checkpoints. The cloud and Fairy reference remain outside the four-level knee sequence. A cloud quota/rate-limit error stops the pass with a clear status and retained attempt, without an automatic retry loop. Splitting collection changes neither the knee rule nor the reference roles; timestamps and conditions expose the different collection windows.

### Energy instrumentation amendment, 16 October 2026

Before any benchmark data, a held-out required-energy pre-check stopped after its first completed 3-bit call. All 48 raw power records parsed, but receipt-based interval reconstruction created apparent overlaps up to 18.6 ms and the existing 10 ms overlap guard correctly rejected the energy estimate. The original failed run and completed response remain unchanged; an offline replay is a diagnostic, not a passed live validation.

Require powermetrics `is_delta: true` and reconstruct successive intervals from reported `elapsed_ns`, anchored to the first sample receipt. Retain each actual receipt and its lag from the reconstructed end. Reject timing drift of at least half a reported interval, which guards against treating a missed full interval as continuous coverage. Parser failures invalidate attribution. The first receipt has unknown fixed delivery delay, so call-boundary attribution remains approximate. The existing two-sample, 90% coverage and 10 ms overlap guards remain unchanged. This is an instrumentation correction to the estimate, whole-machine delta; it changes no quality, knee, variance or swap rule. A fresh held-out validation needs owner authorization; completed calls are not silently repeated or relabelled.

### Kill criteria

If quality and cost fall together smoothly with no knee, or run-to-run variance is larger than the difference between quantisation levels, the hypothesis fails and the README will say so. The registered variance rule above determines when adjacent levels are indistinguishable.

If running the tool on Andrii's own projects changes no decision, with no model swapped, no quantisation changed and nothing moved between local and cloud, the tool has failed at its purpose and the README will say so.

### Summarisation protocol deviation, 17 October 2026

What ran: `prompts/summarisation.yaml` as committed in `6f6de97`, with tight short-form instructions (mostly two or three sentences) and automatic `max_words` checklist limits of 50 to 90 words. These word limits are scoring criteria; the transmitted instructions retain their original wording. The prompt file and both runs' saved summary prompts/rubrics match. All five local configurations and the cloud reference received identical summary prompt content and were scored against the same checklist rules.

What was intended: a later revision with longer length allowances. That revision never reached the committed prompt file or the collected runs. This note records the deviation after collection; it does not retrospectively amend the pre-registration or change any prompt or response.

Summary results report both the **primary pre-registered score, including `max_words`**, and a **secondary post-collection sensitivity score, excluding only `max_words`**. For the secondary score, average the remaining checklist criteria within each answer, then average repeats within each prompt and give each prompt equal weight as before. Original sentence instructions and every other criterion remain unchanged. The primary score alone supplies registered quality, knee and variance conclusions. The secondary analysis rescores existing answers; it does not estimate responses to the intended longer prompts. Pending human criteria remain pending in both versions. No reruns are performed.

## Cloud reference configuration

`configs/experiment.yaml` contains all five local configurations and `gemini-3.8-flash` with `thinking: {thinking_level: low}`. Cloud thinking cannot be disabled for this model, unlike the local models. Thinking tokens are logged separately and included once in billable output. The requested level is recorded; the API does not expose proof of its internal reasoning depth. This difference limits direct interpretation of the cloud reference. See Google's [thinking documentation](https://ai.google.dev/gemini-api/docs/thinking).

The configured standard prices are USD 0.75 per million input tokens and USD 3.75 per million output tokens, including thinking. The run reports a list-price equivalent regardless of billing tier; paid billing requires owner confirmation and verification before the cloud pass. These rates apply through 31 December 2026 and double on 1 January 2027; update the config before a later run. Source: [Google pricing](https://ai.google.dev/gemini-api/docs/pricing), checked 15 October 2026. The launcher inherits `GEMINI_API_KEY` from Terminal; its presence was confirmed in an interactive login shell without printing it.

## Separate local/cloud collection and paid-tier check, 16 October 2026

Neither command below is authorization to run. After the held-out pre-check, each full pass requires owner approval. Both use the same approved private 40-prompt input. The local pass has five configurations and 1,015 scheduled calls (1,000 measured, five pilots, ten warm-ups). Cloud has 203 (200 measured, one pilot, two warm-ups). The cloud remains outside the knee. Pass directories, saved hashes/checkpoints and `LATEST-local` / `LATEST-cloud` are independent.

```sh
./scripts/run_full.sh --pass local --config configs/experiment.yaml --prompts prompts/private/full.yaml
./scripts/run_full.sh --pass cloud --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

The cloud reference smoke used 27 input tokens, five visible output tokens and 28 thinking tokens, hence 33 billable output tokens. At the configured USD 0.75/3.75 per million input/output, this is USD 0.000144 per smoke-size request, or **USD 0.029232 for 203 such requests**. This is a tiny-prompt extrapolation, not the full benchmark's price or a spending cap: actual input lengths and answers will differ. Thinking counts once in billable output. Resume adds only outstanding requests, plus any deliberately authorized new attempt after a failed request.

After the owner says billing is enabled, verify in Google AI Studio that the environment key belongs to the intended project, that project's paid plan/usage tier and active model limits, and the actual spend-cap setting. Record the project/tier/limits, evidence source and check time without storing the secret key before cloud approval. A model-metadata GET or a successful inference is not proof of a paid tier. See [Google billing](https://ai.google.dev/gemini-api/docs/billing), [key/project association](https://ai.google.dev/gemini-api/docs/api-key) and [active rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). An [alerts-only budget](https://docs.cloud.google.com/billing/docs/how-to/budgets) does not itself cap spending; verify an actual [spend-cap budget](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps) if available for the project/account.

HTTP 402/429 or `PAYMENT_REQUIRED`/`RESOURCE_EXHAUSTED` (including exhausted prepaid balance) stops cloud collection with `rate_limited` status and a retained failed checkpoint/raw response. These errors are not retried. The 17 October decision in `1b98743` separately permits up to four retries for HTTP 500/503, with retained attempts and 10/30/90/270-second waits. Resolve quota/billing/rate limits, obtain approval for any new request, then resume explicitly. Never rerun completed checkpoints.

The authorized pre-check after the owner's clean restart is `sudo -v && ./scripts/run_full.sh --precheck`. It performs only three held-out calls each on local-q8/local-q3, idle swap diagnostics and required energy validation. It cannot start a full pass or send any benchmark prompt. Keep the Terminal and lid open; enter the sudo password only in Terminal. Pre-check and full-pass permissions remain separate.

## Prospective quality-policy amendment, 17 October 2026 (draft, not effective)

For runs collected after this amendment is approved, committed and pushed, an LLM judge may become the primary evaluator of human-type summary checklist items only after held-out validation under [judge-preregistration.md](docs/judge-preregistration.md). Required unweighted Cohen's kappa is at least 0.6; raw agreement is secondary. Cloud-answer agreement is assessed separately because Gemini 3.8 Flash also generated the cloud reference answers. If that stratum fails, it remains human-scored. Failed or undefined metric validation means summaries remain human-scored and the app demo uses maths only.

This prospective exception supersedes the no-primary-LLM-judge rule only for eligible future runs. It does not change the original pre-registration, hypothesis, knee, variance or kill criteria. The 17 October initial results and human scores will never be rescored or replaced. Using copies of those answers to validate a judge is a separate validation experiment, not a new score for the initial results. Exact maths and existing automatic checks remain deterministic. No model calls are authorized by this draft.
