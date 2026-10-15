# CallCost for LLMs

Measure the cost of an LLM call on your own Mac alongside answer quality on your own tasks.

CallCost is a Python command-line project comparing local models served by LM Studio with a Google Gemini API reference. Each configuration identifies a model, an installed quantisation variant and where it runs. Costs remain separate quantities: latency, memory, payload bytes, list-price money and on-device energy.

## Status

Project foundation and pre-registration. The runners, aggregation and blind review commands are not implemented yet. No benchmark results have been collected. The local model family and Gemini model have not been selected.

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
- Memory convention: memory savings use the median of per-call sampled RSS peaks.
- Variance kill: if, for adjacent quantisation levels, the interquartile ranges of per-call latency overlap AND the quality difference is under 5 percentage points, the levels are treated as indistinguishable.
- If no step meets the knee definition for a task type, report **no knee found** for that task type.

Compare adjacent levels within the same local model family, ordered from highest to lowest precision. Gemini is a reference point, not a step in the quantisation sequence. Percentage-point quality changes are distinct from relative percentage savings in latency and memory.

### Kill criteria

If quality and cost fall together smoothly with no knee, or run-to-run variance is larger than the difference between quantisation levels, the hypothesis fails and the README will say so. The registered variance rule above determines when adjacent levels are indistinguishable.

If running the tool on Andrii's own projects changes no decision, with no model swapped, no quantisation changed and nothing moved between local and cloud, the tool has failed at its purpose and the README will say so.

## Planned measurements

| Metric | Definition |
| --- | --- |
| Total latency | Client wall-clock time from starting a request to completing the response, using a monotonic clock. |
| TTFT | Time until the first non-empty answer-text chunk arrives. This is client-observed TTFT; streaming chunks need not contain one token. |
| Tokens | Provider-reported input, output and reasoning counts, with their source retained. |
| Decode tokens/s | Provider-reported generation rate where available. A client delivery estimate must be separately labelled. |
| Model load time | Explicit load-request duration, recorded separately from call latency and linked to calls by load event. |
| LM Studio RSS peak, sampled | Largest sampled sum of resident memory across identified LM Studio and inference-worker processes. |
| Payload bytes | Serialized request and received response body sizes, including streaming framing, excluding headers and transport overhead. |
| List-price equivalent | Input and billable output tokens multiplied by the prices recorded in config. Thinking tokens count when billed as output. |
| Energy, estimate, whole-machine delta | Integrated on-device power above an idle baseline, with the actual measured power domains recorded. |

Local loopback payloads are not zero bytes, although external inference traffic is approximately zero. Local API charges are zero, which does not imply electricity or hardware are free. Gemini list-price cost is reported even when development uses the free tier.

Cloud-side energy is not measured or estimated. Any energy collected during a Gemini request describes this Mac's client activity only.

Missing measurements are recorded as unavailable with a reason, never silently replaced with zero.

## Method

Run one request at a time. Keep temperature, output budget, context length and local inference settings fixed. Record the exact model files, quantisations and effective load settings. Each precision is a separately installed variant of the same base checkpoint and engine.

Use LM Studio's REST API to list, load and unload models. Disable prompt/KV cache reuse between calls if the API provides a supported control. If it does not, label the first measured appearance of each prompt separately from its four repeats and report both groups. Neither label proves the underlying cache state. Conversation storage and prompt caching are different mechanisms.

Fix Gemini's thinking budget or level in config and record it in metadata. Do not silently accept a provider default or discard thinking tokens from list-price calculations.

Record hardware, CPU/GPU core counts, RAM, macOS and LM Studio versions, timestamp, charger state and readable thermal information. Preserve configuration and prompt hashes, software version and the randomisation seed.

Report median (p50) and p95 per configuration per task type, with sample and failure counts. Keep raw per-call data in CSV and run metadata in JSON. Preserve measurement samples so derived numbers can be checked.

Log when repeated calls for the same prompt and configuration produce different answer text. Per configuration and task type, report the number of prompts with more than one distinct answer, alongside the number of prompts compared and any incomplete repeat groups. Compare exact answer text, including whitespace, and preserve the differing call IDs and answers. This counts output variation, not necessarily a change in correctness or evidence of a particular cause.

Automatic quality checks run first. Blind human review shuffles answers, hides configuration and timing, and records checklist decisions separately. Unreviewed criteria remain pending. Maths scoring checks the numeric final line with a declared decimal tolerance and logs parseability separately. No LLM is the primary judge.

See [the measurement method](docs/methodology.md) and [the implementation plan](docs/implementation-plan.md).

## Reproduction

There is no runnable benchmark command yet. The planned interface is:

```text
callcost run --prompts prompts/dataset.yaml --config configs/experiment.yaml
callcost report runs/<run-id>
callcost review runs/<run-id>
```

Before a full run, install the selected variants, fill in exact model identifiers and verified Gemini prices, fix the thinking setting, supply the ten real summaries and their checklists, and validate the complete 40-prompt dataset. Credentials are read from environment variables and never committed.

GSM8K selection will pin the upstream commit, original zero-based test-row indices, selection algorithm and seed. The sample and its source licence will be retained with the reproducible selection procedure.

Run artifacts and private prompt files are ignored by Git by default. Publish only deliberately selected artifacts.

## Limitations

- Sample size: 30 maths problems and 10 summaries are a small task sample, and five repeats do not create five times as many independent problems.
- Single device: results describe this Mac and do not support generalisation to other hardware.
- Thermal throttling: a laptop's thermal and power state can change performance during a run despite controlled ordering and logged conditions.
- Determinism: temperature 0 does not guarantee identical answers on a GPU because floating-point results can depend on execution order, so some answers may differ across repeats; the frequency must be measured rather than assumed small.
- LM Studio overhead: measurements include its server, runtime and associated process overhead rather than isolating model computation.
- Energy: the energy column is an estimate, whole-machine delta, and the measured CPU/GPU/ANE domains may omit other components and differ from wall-socket power.
- Cloud energy: energy used by Gemini's servers is outside scope and is neither measured nor estimated.
- Sampled RSS can miss brief peaks, double-count shared pages and imperfectly account for unified-memory allocations.
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
