# CallCost for LLMs

Measure the cost of an LLM call on your own Mac alongside answer quality on your own tasks.

CallCost is a Python command-line project comparing local models served by LM Studio with a Google Gemini API reference. Each configuration identifies a model, an installed quantisation variant and where it runs. Costs remain separate quantities: latency, memory, payload bytes, list-price money and on-device energy.

## Status

Local and Gemini runners, durable checkpoints/resume, automatic scoring, percentile aggregation and saved-run reports are implemented. Launcher/report review and offline regression fixes are complete; 84 tests and Ruff passed on 16 October 2026. The six-configuration held-out live smoke and deliberate interruption/resume passed on 15 October 2026. No benchmark prompts were used. Every smoke call recorded swap activity, so a fresh restart is required before the full run. Privileged energy remains unvalidated. No scored benchmark results have been collected. Human review tooling and charts remain unfinished. Follow [HANDOFF.md](docs/HANDOFF.md) for operational readiness and permissions.

The local family is Qwen3.5-9B in MLX format, with thinking off. The 3-, 4-, 6- and 8-bit variants have been independently converted from pinned official Qwen weights using mlx-lm 0.32.0 and group size 64. Each loads in LM Studio and passes a held-out thinking-off pilot. Fairy's existing 4-bit model is a fifth local configuration, labelled "Fairy's production model" and treated as a separate reference. See [model preparation](docs/model-preparation.md) for the inspected published candidates and conversion pins. The experiment config selects Gemini 3.8 Flash at thinking level low, with standard list prices checked on 15 October 2026. The 8-bit pilots had less than 1 GB available RAM, and sampled process RSS did not track total model memory; resolve these limits before a full benchmark.

Fairy is a separate project. The initial summaries are Fairy-style prompts written for the benchmark (invented texts), not real Fairy usage. Fairy code and integration are outside this repository.

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

### Kill criteria

If quality and cost fall together smoothly with no knee, or run-to-run variance is larger than the difference between quantisation levels, the hypothesis fails and the README will say so. The registered variance rule above determines when adjacent levels are indistinguishable.

If running the tool on Andrii's own projects changes no decision, with no model swapped, no quantisation changed and nothing moved between local and cloud, the tool has failed at its purpose and the README will say so.

## Measurements

| Metric | Definition |
| --- | --- |
| Total latency | Client wall-clock time from starting a request to completing the response, using a monotonic clock. |
| TTFT | Time until the first non-empty answer-text chunk arrives. This is client-observed TTFT; streaming chunks need not contain one token. |
| Tokens | Provider-reported input, output and reasoning counts, with their source retained. |
| Decode tokens/s | Provider-reported generation rate where available. A client delivery estimate must be separately labelled. |
| Model load time | Explicit load-request duration, recorded separately from call latency and linked to calls by load event. |
| Loaded weight bytes, descriptive | Exact encoded safetensors tensor payload bytes, not runtime peak memory. |
| LM Studio physical footprint peak, sampled, secondary | Largest complete contemporaneous process-group sum of `ri_phys_footprint`; invalid when process coverage is incomplete. |
| LM Studio RSS peak, sampled, secondary | Largest sampled sum of resident memory across identified LM Studio and inference-worker processes. |
| Payload bytes | Serialized request and received response body sizes, including streaming framing, excluding headers and transport overhead. |
| List-price equivalent | Input and billable output tokens multiplied by the prices recorded in config. Thinking tokens count when billed as output. |
| Energy, estimate, whole-machine delta | Integrated on-device power above an idle baseline, with the actual measured power domains recorded. |

Local loopback payloads are not zero bytes, although external inference traffic is approximately zero. Local API charges are zero, which does not imply electricity or hardware are free. Gemini list-price cost is reported even when development uses the free tier.

Cloud-side energy is not measured or estimated. Any energy collected during a Gemini request describes this Mac's client activity only.

Missing measurements are recorded as unavailable with a reason, never silently replaced with zero.

## Method

Run one request at a time. Keep temperature, output budget, context length and local inference settings fixed. Record the exact model files, quantisations and effective load settings. The four experimental precisions are separately installed text-only MLX conversions of the same pinned checkpoint using the same converter and group size. The existing production reference retains its original conversion and vision support, so it is excluded from the four-level knee calculation.

Use LM Studio's REST API to list, load and unload models. Disable prompt/KV cache reuse between calls if the API provides a supported control. If it does not, label the first measured appearance of each prompt separately from its four repeats and report both groups. Neither label proves the underlying cache state. Conversation storage and prompt caching are different mechanisms.

Thinking is off for all local configurations, both the quantisation series and Fairy's reference, using LM Studio `reasoning: "off"`. A held-out local pilot must show zero reasoning tokens and no reasoning content or `<think>` tags before measured calls begin. Missing local evidence stops the run. Preserve the setting, observed counts, evidence source and pilot call ID in metadata, and check every later local call too. The cloud reference runs at `gemini-3.8-flash`'s lowest available level, `thinking_level: low`, because this model cannot disable thinking. Its thinking tokens are reported separately and included in billable output. The cloud is a reference point outside the knee calculation, so this does not affect the knee rule.

Record hardware, CPU/GPU core counts, RAM, macOS and LM Studio versions, timestamp, charger state and readable thermal information. Preserve configuration and prompt hashes, software version and the randomisation seed.

Report median (p50) and p95 per configuration per task type, with sample and failure counts. Keep raw per-call data in CSV and run metadata in JSON. Preserve measurement samples so derived numbers can be checked.

Log when repeated calls for the same prompt and configuration produce different answer text. Per configuration and task type, report the number of prompts with more than one distinct answer, alongside the number of prompts compared and any incomplete repeat groups. Compare exact answer text, including whitespace, and preserve the differing call IDs and answers. This counts output variation, not necessarily a change in correctness or evidence of a particular cause.

Automatic quality checks run first. Blind human review shuffles answers, hides configuration and timing, and records checklist decisions separately. Unreviewed criteria remain pending. Maths scoring checks the numeric final line with a declared decimal tolerance and logs parseability separately. No LLM is the primary judge.

See [the measurement method](docs/methodology.md) and [the implementation plan](docs/implementation-plan.md).

## Reproduction

Use Python 3.12 or newer on macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[dev]'
PYTHONPATH=src .venv/bin/python -m callcost models
PYTHONPATH=src .venv/bin/python -m callcost validate --prompts datasets/gsm8k/prompts.json --config configs/private/experiment.yaml
PYTHONPATH=src .venv/bin/python -m callcost run --prompts datasets/gsm8k/prompts.json --config configs/private/experiment.yaml --output runs/pilot-001 --pilot-only
PYTHONPATH=src .venv/bin/python -m callcost run --prompts prompts/private/dataset.yaml --config configs/private/experiment.yaml --output runs/experiment-001
.venv/bin/pytest -q
```

See the [pilot validation record](docs/pilot-validation.md) for what has and has not been exercised on this Mac.

Commands above use the current checkout source. A previously installed `.venv/bin/callcost` can contain an older packaged version; the launcher also explicitly uses checkout source.

Copy `configs/example.yaml` to `configs/private/experiment.yaml` and fill every placeholder. Quote `"off"` in YAML. Supply exact LM Studio keys and quantisation names from `callcost models`; list all model weight, configuration, tokenizer and template files so they can be hashed. Relative file paths resolve against the config directory. The REST API does not prove that this supplied file list belongs to the selected model; check that mapping against the installed directory before a run.

The output directory must not exist. Each run saves `calls.csv`, `metadata.json`, exact request/response bodies and instrument samples under `raw/`. It prints progress and the answer-variation count per configuration/task. Saved-run reports include p50/p95 costs, quality across all completed answers and adjacent step comparisons; human checklist scores remain pending. Pilot and warm-up rows are retained but excluded from measured repeats. Any provider or thinking-verification failure stops the run, preserves partial evidence and returns non-zero; calls are never retried silently.

LM Studio must already be running with its local server enabled and existing model instances unloaded. CallCost only unloads the instance it loaded. Set the configured Gemini credential environment variable before running; credentials are not written to run artifacts. Input and output text are saved locally, so treat run directories as private unless deliberately publishing them.

Energy is optional by default. If you want power measurement, run `sudo -v` yourself immediately before the benchmark. CallCost invokes only the collector through `sudo -n`; it never prompts for a password and the benchmark stays unprivileged. Without access or supported samples, energy remains unavailable. `required_powermetrics` stops the run when collection cannot start or establish a baseline. See [measurement details](docs/methodology.md) for coverage and scope limits.

Before a full run, review the [completed preparation and its measurement limits](docs/model-preparation.md), use the registered weight proxy and check 8-bit headroom, fill in exact model identifiers and verified Gemini prices, fix the thinking setting, complete owner review of the ten invented-text summaries and their checklists, and validate the complete 40-prompt dataset. Credentials are read from environment variables and never committed.

The committed [GSM8K sample](datasets/gsm8k/prompts.json) records original zero-based test-row indices. Rebuild it with `python3 scripts/prepare_gsm8k.py`. The [selection manifest](datasets/gsm8k/selection.json) pins the source commit, source SHA-256, row indices and stable hash-ranking procedure using seed 2027. Its upstream licence is retained alongside the sample. The ten Fairy-style prompts written for the benchmark (invented texts) are in `prompts/summarisation.yaml`. Owner review was confirmed on 15 October 2026. The ignored `prompts/private/full.yaml` contains all 40 approved prompts and passes the full-dataset guard, including pinned maths identity. The launcher validates this input; it does not merge files. No benchmark prompt has been sent to a model.

Run artifacts and private prompt files are ignored by Git by default. Publish only deliberately selected artifacts.

## Limitations

- Sample size: 30 maths problems and 10 summaries are a small task sample, and five repeats do not create five times as many independent problems.
- Single device: results describe this Mac and do not support generalisation to other hardware.
- Thermal throttling: a laptop's thermal and power state can change performance during a run despite controlled ordering and logged conditions.
- Determinism: temperature 0 does not guarantee identical answers on a GPU because floating-point results can depend on execution order, so some answers may differ across repeats; the frequency must be measured rather than assumed small.
- LM Studio overhead: measurements include its server, runtime and associated process overhead rather than isolating model computation.
- Energy: the energy column is an estimate, whole-machine delta, and the measured CPU/GPU/ANE domains may omit other components and differ from wall-socket power.
- Cloud energy: energy used by Gemini's servers is outside scope and is neither measured nor estimated.
- Sampled RSS can miss brief peaks, double-count shared pages and omit GPU/unified-memory allocations; the installed MLX pilot reported RSS below weight-file size, so RSS cannot establish that a model fits comfortably in RAM.
- Public benchmark questions may have appeared in model training data; GSM8K accuracy does not establish unseen-task reasoning ability.
- Cloud model updates, service load and network conditions limit exact reproducibility.

## References and boundaries

Methodological references are [MLPerf Inference](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc) and [MLPerf Client](https://mlcommons.org/benchmarks/client/), particularly their separation of quality and performance. This project does not claim MLPerf compliance.

Software Carbon Intensity is [ISO/IEC 21031:2024](https://www.iso.org/standard/86612.html). The Green Software Foundation announced [SCI for AI ratification in December 2025](https://greensoftware.foundation/articles/sci-ai-specification-ratified-standard-for-measuring-ai-emissions-across-the/). CallCost does not calculate a full SCI score or carbon emissions.

API references: [LM Studio REST](https://lmstudio.ai/docs/developer/rest), [Gemini generation and usage metadata](https://ai.google.dev/api/generate-content), and [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing). Dataset source: [GSM8K](https://github.com/openai/grade-school-math).

## Milestones

| Target | Deliverable |
| --- | --- |
| 25 October 2026 | LM Studio and Gemini runners, per-call CSV and run conditions. |
| 8 November 2026 | p50/p95 aggregation, terminal table and blind review. |
| 22 November 2026 | First real dataset results and charts. |
| 29 November 2026 | WAICY submission deadline supplied by the project owner. |
| 4 to 6 December 2026 | Finals and live Q&A dates supplied by the project owner. |
| 15 December 2026 | Repository and chart freeze, with CI budget mode as the final implementation milestone. |

Later charts will show quality against a named cost metric, with quantisation points connected within each model and a separate cloud reference point. Later CI mode will compare with a stored baseline from the previous commit and fail when a configured cost budget is exceeded.

Non-goals: routing, Fairy integration, a GUI, multi-device support, cloud energy estimates and a full SCI implementation.

## Licence

MIT. See [LICENSE](LICENSE). Third-party datasets retain their own licence notices.

## Summarisation prompt review

`prompts/summarisation.yaml` contains ten Fairy-style prompts written for the benchmark (invented texts). Andrii confirmed review on 15 October 2026; the approved file is committed unchanged. These prompts have not been sent to any model. The full benchmark still requires separate approval. `max_words` counts whitespace-separated words with `len(answer.split())` and passes when the count is at most the integer limit. Regex checks accept `pattern` as an input alias for `value`. Automatic checks prefill only what they establish; human checklist items remain pending.

## Cloud reference configuration

`configs/experiment.yaml` contains all five local configurations and `gemini-3.8-flash` with `thinking: {thinking_level: low}`. Cloud thinking cannot be disabled for this model, unlike the local models. Thinking tokens are logged separately and included once in billable output. The requested level is recorded; the API does not expose proof of its internal reasoning depth. This difference limits direct interpretation of the cloud reference. See Google's [thinking documentation](https://ai.google.dev/gemini-api/docs/thinking).

The configured standard prices are USD 0.75 per million input tokens and USD 3.75 per million output tokens, including thinking. The run reports a list-price equivalent regardless of billing tier; paid billing requires owner confirmation and verification before the cloud pass. These rates apply through 31 December 2026 and double on 1 January 2027; update the config before a later run. Source: [Google pricing](https://ai.google.dev/gemini-api/docs/pricing), checked 15 October 2026. The launcher inherits `GEMINI_API_KEY` from Terminal; its presence was confirmed in an interactive login shell without printing it.

## Resuming after a run

Read `runs/LATEST`, then the named run's `status.json`, then `run.log`. The held-out launcher smoke and interruption/resume test passed; follow [HANDOFF.md](docs/HANDOFF.md) before the first full run. LATEST may not exist yet. Resume local with `./scripts/run_full.sh --pass local --resume`, or cloud with `./scripts/run_full.sh --pass cloud --resume`. Read `runs/LATEST-local` or `runs/LATEST-cloud` first; `runs/LATEST` is only the most recently touched run. To produce a saved-run report without inference, from the repository root run:

```sh
PYTHONPATH=src .venv/bin/python -m callcost report --run "runs/$(cat runs/LATEST)"
```

## Separate local/cloud collection and paid-tier check, 16 October 2026

Neither command below is authorization to run. After the held-out pre-check, each full pass requires owner approval. Both use the same approved private 40-prompt input. The local pass has five configurations and 1,015 scheduled calls (1,000 measured, five pilots, ten warm-ups). Cloud has 203 (200 measured, one pilot, two warm-ups). The cloud remains outside the knee. Pass directories, saved hashes/checkpoints and `LATEST-local` / `LATEST-cloud` are independent.

```sh
./scripts/run_full.sh --pass local --config configs/experiment.yaml --prompts prompts/private/full.yaml
./scripts/run_full.sh --pass cloud --config configs/experiment.yaml --prompts prompts/private/full.yaml
```

The cloud reference smoke used 27 input tokens, five visible output tokens and 28 thinking tokens, hence 33 billable output tokens. At the configured USD 0.75/3.75 per million input/output, this is USD 0.000144 per smoke-size request, or **USD 0.029232 for 203 such requests**. This is a tiny-prompt extrapolation, not the full benchmark's price or a spending cap: actual input lengths and answers will differ. Thinking counts once in billable output. Resume adds only outstanding requests, plus any deliberately authorized new attempt after a failed request.

After the owner says billing is enabled, verify in Google AI Studio that the environment key belongs to the intended project, that project's paid plan/usage tier and active model limits, and the actual spend-cap setting. Record the project/tier/limits, evidence source and check time without storing the secret key before cloud approval. A model-metadata GET or a successful inference is not proof of a paid tier. See [Google billing](https://ai.google.dev/gemini-api/docs/billing), [key/project association](https://ai.google.dev/gemini-api/docs/api-key) and [active rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). An [alerts-only budget](https://docs.cloud.google.com/billing/docs/how-to/budgets) does not itself cap spending; verify an actual [spend-cap budget](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps) if available for the project/account.

HTTP 402/429 or `PAYMENT_REQUIRED`/`RESOURCE_EXHAUSTED` (including exhausted prepaid balance) stops cloud collection with `rate_limited` status and a retained failed checkpoint/raw response. There is no automatic retry loop. Resolve quota/billing/rate limits, obtain approval for any new request, then resume explicitly. Never rerun completed checkpoints.

The authorized pre-check after the owner's clean restart is `sudo -v && ./scripts/run_full.sh --precheck`. It performs only three held-out calls each on local-q8/local-q3, idle swap diagnostics and required energy validation. It cannot start a full pass or send any benchmark prompt. Keep the Terminal and lid open; enter the sudo password only in Terminal. Pre-check and full-pass permissions remain separate.
