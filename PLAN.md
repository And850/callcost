# CallCost plan

Current plan, owner decisions through 17 October 2026. Edit this file in place; append history to [docs/log.md](docs/log.md). Superseded plans live in [docs/archive/](docs/archive/).

## 1. Purpose and thesis

CallCost measures the hidden energy and memory cost of one LLM call on a constrained laptop. Priority: on-device energy per call first, then memory (encoded weight GiB, sampled footprint and whole-machine swap), then latency and money. Answer quality is a secondary constraint on useful work. Every reported number must trace to retained evidence and every design decision must be explainable by the owner.

Scope is single calls in fresh, empty chats, not ongoing conversations. Existing requests carry no earlier turns; storage being off does not prove an empty runtime cache. Longer contexts were not measured. A numerical lower bound for all chat use is not established. Energy is **estimate, whole-machine delta**, CPU + GPU + ANE above a loaded idle baseline, not per-process, wall-socket or cloud-server energy.

## 2. Short history

| Date | Decision or outcome |
| --- | --- |
| 12 September 2026 | Owner's problem lock: what one model call costs on the user's device. |
| 14 September 2026 | Knee hypothesis: task quality may stay flat across precision levels, then drop sharply. |
| 15 to 16 October 2026 | Before benchmark collection, amend memory to encoded tensor payload bytes, make the knee quality-only, fix thinking settings, include swapped answers, separate local/cloud passes and correct energy timing. Frozen text remains in the pre-registration. |
| 17 October 2026 | Initial local/cloud results, blinded author summary review, offline audit and published figures. Maths knee 4→3 bit; no summary knee. |
| 17 October 2026 | Refocus presentation on energy and memory. Plan a macOS web app; abandon the self-built configurator. Keep the initial human scores and registered rules unchanged. |
| 17 October 2026 | Limit judge validation to human-type criteria, await a hard monetary cap, and consider Bonsai for the demo only. Reorganise the repository without changing measurements. |

The September dates are owner-supplied history. Exact dated decisions, original wording and the first agreed refocus plan are preserved in [the log](docs/log.md).

## 3. What CallCost does now

The Python CLI benchmarks installed LM Studio configurations and a Gemini API reference, one request at a time. It retains per-call measurements, controls, checkpoints and raw evidence; supports explicit independent local/cloud resume; scores maths deterministically; imports blinded human summary checklists; and reports counts, missing reasons, percentiles, variation and registered knee/variance findings. The initial results are indexed in [results/](results/).

The planned macOS local web app asks which installed local model this computer should use for a task, based on measured energy and memory. Flow: read chip/RAM/available memory/swap, choose maths or summaries from the existing sets, choose installed models, probe, score quality and recommend. It is not implemented. Probes take minutes; the video will use an earlier or sped-up recording. Powermetrics requires sudo entered only in the owner's Terminal.

| Planned mode | Prompt count × repeats | Qualification |
| --- | --- | --- |
| Quick | 5 × 2 | Rough estimate, explicitly labelled. |
| Standard | 10 × 3 | Existing task sets. |
| Full | 30 × 5 | Requires 30 distinct prompts; the current ten-summary set cannot fill this mode. |

App defaults, chosen after viewing the initial data, are **exploratory, not pre-registered**, and user-adjustable: eligible quality is within five percentage points of the best local candidate; choose the lowest median energy among eligible models; warn when more than 50% of calls swap. The saved-data check provisionally picks q4 for both tasks, without a swap warning. Q6's missing energy majority prevents a definitive full-data winner. Missing values never become zero or inferred measurements. This check is not a production deployment decision.

## 4. What it uses

| Component | Role and limits |
| --- | --- |
| Qwen3.5-9B MLX 3/4/6/8 bit | Four independently converted text-only configurations, same pinned checkpoint and group size 64; thinking off. The only initial knee sequence. |
| Fairy's production model | Separate existing MLX 4-bit reference retaining vision weights; outside the knee sequence. Fairy code/integration stays separate. |
| Gemini `gemini-3.8-flash` | Initial cloud reference with low thinking. Also the proposed new judge, with self-preference checked separately on cloud answers. |
| PrismML Ternary Bonsai 2 27B | Demo-only candidate, never part of the initial results or Qwen knee. Owner-supplied Apache 2.0, about 5.9 GB PTQ1_0 GGUF and MLX 2-bit companion details are unverified by CallCost. No download approved. |
| LM Studio | Installed local model discovery/load/unload and inference; runtime settings and identity retained. |
| mlx-lm 0.32.0 | Pinned converter used for the Qwen weights; see [model preparation](docs/model-preparation.md) and `requirements-conversion.lock`. |
| Powermetrics | Optional sudo-backed CPU/GPU/ANE power collector with retained samples, baseline and rejection guards. |
| DeepEval | Proposed Apache 2.0 framework for future summary evaluation; not installed, pinned or validated yet. Maths and automatic checklist checks remain deterministic. |
| Apple M1 Pro, 16 GB RAM | The single measured Mac. Swap is whole-machine activity; the results do not generalise to other devices. |

Before a separately approved Bonsai probe, inspect the exact model revision/licence and runtime requirements, then LM Studio's architecture and PTQ1_0/MLX support. Ordinary GGUF support does not establish Bonsai compatibility. If neither build works in LM Studio, assess a PrismML OpenAI-compatible llama.cpp-server adapter covering request/stream/usage parsing, load lifecycle and process-group sampling; no adapter code or installation is authorized now.

Check the selected Bonsai build's thinking control and later verify observed metadata. If thinking cannot be disabled, retain available thinking tokens, count them once where billed and disclose the difference from thinking-off Qwen. Missing reasoning counts are unavailable, not zero; absent tags alone do not prove thinking is off. Defer the candidate if observability is inadequate.

A llama.cpp fork/PTQ1_0 kernel and MLX differ in backend, quantisation, offload, threading and memory mapping. Even the MLX companion differs in architecture, parameter count, conversion and kernels. Record runtime/fork versions, build flags, model hashes and effective context/cache/output settings. Such future probes compare complete configurations; they cannot attribute energy/latency differences to ternary weights alone or create a Qwen knee step. Separate load cost from call cost. Vendor benchmark numbers must never appear as CallCost results or recommendation inputs. Details remain in the [historical same-day revisions](docs/archive/plan-2026-10-17.md).

## 5. Method summary

The [original pre-registration and dated amendments](docs/preregistration.md) remain byte-identical, with relocation hashes recorded there. The initial dataset is 30 pinned GSM8K maths problems plus ten Fairy-style prompts written for the benchmark (invented texts), with five measured repeats per configuration. Average repeats within each prompt, then prompts equally. The initial human summary scores remain primary permanently; no rescoring or reruns. The registered quality-only knee, variance rule and kill criteria are unchanged.

Report energy p50/p95 and availability; static encoded weight GiB separately from sampled footprint/RSS and coverage; swap shares, unknown counts and median volume; all-call and known swap-free latency; payload bytes and list-price equivalent money. Retain raw evidence privately, failed attempts and missing reasons. Whole-machine measurements cannot prove inference alone caused swap or energy differences. Cloud-server energy is outside scope. [Methodology](docs/methodology.md), [model preparation](docs/model-preparation.md) and [blind review](docs/blind-review.md) document the implementation and limits.

The [prospective judge protocol](docs/judge-preregistration.md) applies only to future collected runs after approval, commit/push and held-out validation. Gemini 3.8 Flash uses low thinking and temperature 0, with prompt/template/settings hashes fixed before evaluation. G-Eval checks only human-type criteria; Hallucination is independently compared with `faithful`. Split the 300 saved summary answers by source prompt into 120 development and 180 held-out answers, keeping all repeats/configurations together. Unweighted held-out Cohen's kappa must reach 0.6 for each required metric; raw agreement is secondary. Assess cloud-answer agreement separately; a failing cloud stratum remains human-scored. Failed or undefined required validation means the judge is not yet reliable, summaries stay human-scored and the app demo uses maths only. Initial results are never overwritten.

New task types need 30-50 distinct human-labelled items per metric, target 50/minimum 30, and their own predeclared split. Spot-check every judged metric on 10% of each future run (within the agreed 5-10% range), independently selected. Judge calls are logged/costed separately from task-call measurements. All new priorities, post-data app rules and newly derived analyses are labelled exploratory, not pre-registered.

## 6. Status and next steps

| Status at 17 October 2026 | Evidence or next action |
| --- | --- |
| Git state | Reviewed baseline HEAD `97011111d993022ea7604a1c62da0e55355396b3` on `main`, matching `origin/main`. The final session HEAD is the docs-only commit adding `docs/next-chat-prompt.md`; resolve its exact hash with `git log -1 --format=%H -- docs/next-chat-prompt.md`. Verify live HEAD with `git rev-parse HEAD` at the next chat. |
| Session-close verification | 113 tests passed; Ruff reported zero violations. All 73 internal Markdown links resolve; six frozen blocks and all 5,398 private run files retain their hashes. Code behaviour is unchanged. |
| Initial benchmark complete | Local 1,015 calls: 1,000 measured plus five pilots and ten warm-ups. Cloud 203 completed slots: 200 measured plus one pilot and two warm-ups; 18 failed HTTP attempts retained with unknown cost. No completed checkpoint may repeat. |
| Human summary review/audit complete | 300 summary answers, one blinded author-reviewer; initial scores and raw evidence remain unchanged. [Initial results](results/2026-10-17-initial/) include the published snapshot and figures. |
| Registered findings | Maths knee 4→3 bit; summaries no knee. Criterion 1 not triggered; roughly steady cost reductions are not established. |
| Energy/memory gaps | Q6 lacks energy for 85/150 maths and 29/50 summary calls. Sampled process memory is unavailable for 255/1,000 local calls. Cloud client energy was deliberately omitted. Do not reconstruct rejected samples or lower guards. |
| Billing pending | Matching Google billed Gemini figure/export and VAT treatment. Known all-history list-price equivalent is USD 0.23373225 over 204 successful calls; 18 failed attempts have unknown usage/cost. Private ledger: `runs/gemini-cost-ledger-20261017/`. Reconcile matching scope, not an approximate balance change. |
| Judge hard cap pending | Owner must check the prepaid balance and confirm an explicit monetary cap; none is approved. Proposed 1,380 physical requests: 480 development, 900 held-out. Current token scenarios estimate USD 2.35980 / 4.20210 / 13.70340, not spending caps. |
| Judge validation awaiting approval | No judge code, dependency installation, pinned executable manifest or validation exists. The next task is the pinned judge manifest and implementation plan for owner review before any call. Required downloads/installs and all validation calls need explicit approval; the hard monetary cap is still unset. |
| Web app not started | Probe/recommendation engine and macOS web page have not been started. |
| Bonsai pending | Compatibility, thinking and runtime checks are a plan only; separate permission is needed for download, installation, inference or long tests. |
| Kill criterion 2 unmet | No actual owner-confirmed Fairy model/quantisation/local-cloud decision changed. The owner is considering a dated deferral note; none is adopted. The frozen criterion is unchanged and must not be reported as met. Record an actual decision before changing this assessment; benchmark recommendations alone are insufficient. |

Private local/cloud pointers remain `runs/LATEST-local` and `runs/LATEST-cloud`. Read the matching `status.json`, then `run.log`; checkpoints are authoritative. `runs/LATEST` is only the most recently touched run. Scored audit: `runs/audit-20261017-scored/`; blind review/import provenance: `runs/blind-review-20261017/`. Do not re-import or modify original prompts/responses. The old installed `.venv/bin/callcost` may lag checkout source; use `PYTHONPATH=src .venv/bin/python -m callcost`.

Next task: prepare the pinned judge manifest and implementation plan for owner review before any call. Separately obtain the matching billed Gemini figure and the judge monetary cap; validate only after explicit owner approval; then implement the probe/recommendation engine and web page in the existing code area. Any actual Fairy decision requires owner confirmation. Docs and code edits, short offline checks, and small commits/pushes are authorized. No model calls, downloads, installs, system-setting changes or runs longer than a few minutes without explicit owner approval. For the next chat, [report status first and wait](docs/next-chat-prompt.md).

## 7. Roadmap, WAICY requirements and do-not list

| Dates / deadline | Deliverable or constraint |
| --- | --- |
| 18 to 24 October | Refocus docs and judge pre-registration; judge implementation/validation only after the separate approvals above. |
| 25 to 31 October | Probe and recommendation engine. |
| 1 to 7 November | macOS local web page and report; AMC on 5 November. |
| 8 to 14 November | End-to-end checks; Veritas on 14 to 15 November. |
| 15 to 22 November | Slides, presentation/demo videos and 250-word texts; aim for a complete AI Showcase demo by 22 November. |
| 29 November, 23:00 Madrid | Owner-supplied WAICY 2026 submission deadline, `Europe/Madrid`; buffer after the 22 November target. |
| 4 to 6 December | Owner-supplied finals and live presentation/Q&A dates. |
| 15 December | Repository/chart freeze. |
| After December | CI budget mode and SCI units remain deferred. |

The WAICY 2026 target is AI Showcase (High School): demonstrate the single-call measurement, quality constraint and local-model recommendation, with the validated Gemini judge as the planned AI element. If summary validation fails, demonstrate maths only. Energy probes take minutes, so disclose sped-up/earlier recordings.

Owner-supplied submission requirements, recorded 17 October 2026: place all deliverables in a Google Drive folder named `Main_High_CallCost`.

| Deliverable | Requirement |
| --- | --- |
| Project description | 250 words |
| AI usage explanation | 250 words |
| Slides | PDF |
| Presentation video | 3 minutes |
| Demo video | 3 minutes |

| Rubric category | Points |
| --- | ---: |
| AI | 25 |
| Technical skills | 25 |
| Problem | 10 |
| Design | 10 |
| Ethics | 10 |
| Presentation | 10 |
| Originality | 10 |

Codex wrote the code. The owner must be able to explain it during Q&A, including the implementation, measurement choices and limitations.

Do not build the abandoned configurator, add user-defined tasks, extend long-context/tool-use evaluation, integrate Fairy code, support Windows/Linux, download models automatically, estimate cloud-server energy or implement full SCI. Do not treat vendor benchmarks as CallCost measurements, change initial scores/frozen rules, auto-publish raw runs or credentials, infer missing observations, or claim a universal local/cloud winner. No additional features are included by this reorganisation.
