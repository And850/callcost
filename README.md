# CallCost for LLMs

Measure the cost of an LLM call on your own Mac alongside answer quality on your own tasks.

CallCost is a Python command-line project comparing local models served by LM Studio with a Google Gemini API reference. Each configuration identifies a model, an installed quantisation variant and where it runs. Costs remain separate quantities: latency, memory, payload bytes, list-price money and on-device energy.

## Status

Milestone 1 runners and logging are implemented and tested with offline fixtures. A held-out pilot on the installed Qwen3.5-9B MLX 4-bit model verified streaming, loading/unloading, zero reasoning tokens and process RSS sampling. Gemini and energy validation are pending. Aggregation, quality scoring and blind review are later milestones. No benchmark results have been collected.

The local family is Qwen3.5-9B in MLX format, with thinking off. The 3-, 4-, 6- and 8-bit variants have been independently converted from pinned official Qwen weights using mlx-lm 0.32.0 and group size 64. Each loads in LM Studio and passes a held-out thinking-off pilot. Fairy's existing 4-bit model is a fifth local configuration, labelled "Fairy's production model" and treated as a separate reference. See [model preparation](docs/model-preparation.md) for the inspected published candidates and conversion pins. The Gemini model and prices remain to be filled in. The 8-bit pilots had less than 1 GB available RAM, and sampled process RSS did not track total model memory; resolve these limits before a full benchmark.

Fairy is a separate project. It will supply real summarisation requests, but its code and integration are outside this repository.

## Hypothesis

For a fixed task set, there is a quantisation level below which answer quality drops sharply while cost to the user keeps falling only slowly. The knee can occur at different quantisation levels for different task types. The finding is the knee per task type, not a claim that local inference beats cloud inference.

## Pre-registration

These rules are recorded before the first full run. Any later amendment must be committed and identified in the results.

- Dataset: 30 reproducibly selected GSM8K test problems and 10 real Fairy-style summarisation prompts supplied by Andrii.
- Repeats: five measured calls per prompt per configuration. Warm-ups are additional and excluded from the results.
- Quality per configuration: mean score across prompts for that task type. Average repeated scores within each prompt first, so each prompt has equal weight.
- Knee: the first step down in quantisation where quality falls by at least 10 percentage points AND at least twice the drop of the previous step, while the same step saves less than 20% in median latency and less than 20% in peak memory.
- Boundary convention: the first step down establishes the previous-drop reference and cannot itself qualify as a knee.
- Memory convention, amended 15 October 2026: memory savings use exact encoded tensor payload bytes for the loaded model. Sampled physical footprint and RSS remain secondary measurements, not inputs to the knee rule.
- Variance kill: if, for adjacent quantisation levels, the interquartile ranges of per-call latency overlap AND the quality difference is under 5 percentage points, the levels are treated as indistinguishable.
- If no step meets the knee definition for a task type, report **no knee found** for that task type.

Compare adjacent levels within the same local model family, ordered from highest to lowest precision. Gemini and Fairy's production model are reference points outside the four converted levels in the quantisation sequence. Percentage-point quality changes are distinct from relative percentage savings in latency and memory.

### Pre-registration amendment, 15 October 2026

Before any scored benchmark data, physical footprint was tested with Darwin `proc_pid_rusage`, `RUSAGE_INFO_V0`, `ri_phys_footprint`, sampled over the same LM Studio process group as RSS. Complete contemporaneous process-group samples were required. Valid 3-, 4- and 6-bit pilot peaks were 5,356,283,032, 6,471,723,096 and 8,655,694,824 bytes. They exceeded encoded weight bytes and increased with precision. Both 8-bit attempts lost process coverage during at least one in-call sample, so neither supplied a valid peak. Full validation therefore failed. The [validation record](docs/data/physical-footprint-validation.json) retains both attempts, errors and swap counters. These held-out calls are instrumentation checks, not benchmark results.

The knee memory clause now uses **loaded weight bytes**, defined exactly as the sum of encoded tensor payload lengths in the selected safetensors files, excluding headers, tokenizers and configuration files. This is a static weight-footprint proxy, not measured peak runtime memory. For the four text-only levels it is 3,918,948,864, 5,038,041,600, 7,276,227,072 and 9,514,412,544 bytes. Context length and cache settings remain fixed across levels; this proxy does not measure runtime cache or activation allocation. Keep sampled physical footprint and RSS in separately labelled columns with missing-value reasons. Fairy retains 912,020,960 encoded vision-weight bytes and remains outside the knee sequence.

Record whole-machine `vm_stat` swap-ins, swap-outs and pageouts around every call, in pages and bytes. Flag a call if any counter increases. Retain and report these calls, but exclude them from every quantity used in knee analysis, including latency, quality and variance. Missing or reset counters also make a call ineligible, with a separate unknown count. Report eligible counts per prompt and configuration; do not treat missing prompts or an empty eligible group as zero quality or evidence of no knee. All validation pilots recorded swap activity, so a fresh, quiet launch remains necessary.

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
| Loaded weight bytes, knee proxy | Exact encoded safetensors tensor payload bytes, not runtime peak memory. |
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

Hold thinking off for every configuration: LM Studio `reasoning: "off"` and a Gemini model supporting `thinkingBudget: 0`. A held-out pilot must show zero reasoning tokens and no reasoning content or `<think>` tags before measured calls begin. Missing evidence stops the run. Preserve the setting, observed counts, evidence source and pilot call ID in metadata, and check every later call too. Count any observed thinking tokens in list-price calculations even if they invalidate the call.

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
.venv/bin/callcost models
.venv/bin/callcost validate --prompts datasets/gsm8k/prompts.json --config configs/private/experiment.yaml
.venv/bin/callcost run --prompts datasets/gsm8k/prompts.json --config configs/private/experiment.yaml --output runs/pilot-001 --pilot-only
.venv/bin/callcost run --prompts prompts/private/dataset.yaml --config configs/private/experiment.yaml --output runs/experiment-001
.venv/bin/pytest -q
```

See the [pilot validation record](docs/pilot-validation.md) for what has and has not been exercised on this Mac.

Copy `configs/example.yaml` to `configs/private/experiment.yaml` and fill every placeholder. Quote `"off"` in YAML. Supply exact LM Studio keys and quantisation names from `callcost models`; list all model weight, configuration, tokenizer and template files so they can be hashed. Relative file paths resolve against the config directory. The REST API does not prove that this supplied file list belongs to the selected model; check that mapping against the installed directory before a run.

The output directory must not exist. Each run saves `calls.csv`, `metadata.json`, exact request/response bodies and instrument samples under `raw/`. It prints progress and the answer-variation count per configuration/task. The p50/p95 cost-quality table is milestone 2. Pilot and warm-up rows are retained but excluded from measured repeats. Any provider or thinking-verification failure stops the run, preserves partial evidence and returns non-zero; calls are never retried silently.

LM Studio must already be running with its local server enabled and existing model instances unloaded. CallCost only unloads the instance it loaded. Set the configured Gemini credential environment variable before running; credentials are not written to run artifacts. Input and output text are saved locally, so treat run directories as private unless deliberately publishing them.

Energy is optional by default. If you want power measurement, run `sudo -v` yourself immediately before the benchmark. CallCost invokes only the collector through `sudo -n`; it never prompts for a password and the benchmark stays unprivileged. Without access or supported samples, energy remains unavailable. `required_powermetrics` stops the run when collection cannot start or establish a baseline. See [measurement details](docs/methodology.md) for coverage and scope limits.

Before a full run, review the [completed preparation and its measurement limits](docs/model-preparation.md), use the registered weight proxy and check 8-bit headroom, fill in exact model identifiers and verified Gemini prices, fix the thinking setting, supply the ten real summaries and their checklists, and validate the complete 40-prompt dataset. Credentials are read from environment variables and never committed.

The committed [GSM8K sample](datasets/gsm8k/prompts.json) records original zero-based test-row indices. Rebuild it with `python3 scripts/prepare_gsm8k.py`. The [selection manifest](datasets/gsm8k/selection.json) pins the source commit, source SHA-256, row indices and stable hash-ranking procedure using seed 2027. Its upstream licence is retained alongside the sample. The ten private summaries still need to be supplied and merged into a 40-prompt file before a full run.

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
