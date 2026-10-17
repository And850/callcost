# Prospective judge pre-registration, 17 October 2026

**Draft for owner review. Not effective, not validated, no calls authorized.** This new experiment supersedes the abandoned configurator judge proposal. Approval and commit/push must precede judge calls, score exposure to the judge and collection of any future run using the exception. The initial 17 October results remain permanently human-scored and are never rescored. Validation predictions are stored separately and never imported into original runs/reports.

## Model, controls and immutable record

- Judge model ID: `gemini-3.8-flash`, also the original cloud generator. This deliberate self-preference risk requires the cloud stratum below; it is not an independent-model judge.
- Requested thinking: `thinking_level: low`; temperature 0; maximum output 2,048 tokens per physical request, including thinking. No tools, grounding, chat history or fallback model. Temperature 0 does not guarantee identical responses. Retain returned model/version, requested settings, visible/thinking/billable tokens and raw request/response separately from benchmark measurements.
- Framework proposed for later installation: DeepEval (Apache 2.0), LLM evaluation mode only, sequential calls and explicit Gemini adapter controls. No Jev/hybrid mode, provider defaults, hidden retries, hosted dataset upload or implicit fallback. Pin an exact version and package hash before calls; none is installed or pinned by this draft. Confirm its API and metric score direction offline before approval to run. Any necessary download needs separate permission.
- Before validation, save the human checklist descriptions unchanged, manually written G-Eval evaluation steps, system instructions, Hallucination templates, output schemas, normalization and pass/fail conversion, dependency/source pins and all generation settings in a canonical UTF-8 JSON manifest (sorted keys, compact separators, no NaN). Record its SHA-256, commit and reviewer approval. Also hash each fully rendered request (without credentials), answer/source file and split manifest. Do not claim a prompt hash now: executable templates have not been implemented.
- Freeze the final prompt manifest after development and before any held-out call; no held-out prompt tuning, threshold changes, model changes or rescoring to improve agreement. Record all development revisions. Changing the frozen protocol requires a new registration and genuinely new held-out human items.
- Judge sees source input, task instruction, one answer and the relevant checklist description, never configuration ID, latency, energy, human score or other candidate answers. Treat source/answer text as data, not instructions to the judge. Keep the configuration key available only for later stratified analysis. Retain binary decisions and concise reasons; do not request private chain-of-thought.

The selected thinking level is supported by [Google's thinking documentation](https://ai.google.dev/gemini-api/docs/thinking). [G-Eval documentation](https://deepeval.com/docs/metrics-llm-evals) supports fixed evaluation steps and binary strict mode. Provider/version settings must be checked again before any approved calls.

## Metric mapping

Maths uses the existing deterministic final-line numeric parser and declared Decimal tolerance, not a judge. Existing automatic summary checks remain deterministic in future composite quality. G-Eval evaluates one check per existing human-type checklist criterion; only those items are candidates for replacement after validation. The 930 proposed G-Eval checks on automatic criteria are removed: deterministic criteria require no judge calls and add no judge-validation value. Do not reweight the checklist or double-count diagnostic metrics.

For each G-Eval check, use manually frozen evaluation steps: (1) read source and instruction; (2) test only the exact checklist description, preserving negation, conditional clauses and scope; (3) pass only if fully satisfied, otherwise fail, with a concise reason. Use `strict_mode: true`, pass=1 and fail=0. Supply fixed steps rather than generating evaluation steps through extra model calls. No partial-credit or tuned score cutoff. Missing/malformed/truncated judgments are unavailable and block acceptance; do not count them as human failures or silently drop them.

The following mapping preserves each human-type ID and its full description from `prompts/summarisation.yaml`. H means the human-labelled validation endpoint. Automatic criteria are omitted from the judge mapping and continue to use their existing deterministic checks.

| Prompt | Criterion | Endpoint | G-Eval criterion (verbatim) |
| --- | --- | --- | --- |
| summary-01 | right_time | H | Gives 15:30 as the next session's start, not 15:40 (today's late start). |
| summary-01 | hackathon_undecided | H | If the hackathon is mentioned, says it has no date / is postponed; does not present December as fixed. |
| summary-01 | github_deadline | H | Mentions messaging Leo by Friday for the GitHub invite. |
| summary-01 | faithful | H | Adds no facts that are not in the notes. |
| summary-02 | not_old_date | H | Does not present 3 November as the deadline. |
| summary-02 | content_requirement | H | Mentions the raw data table or the uncertainty for g. |
| summary-02 | faithful | H | Adds no facts that are not in the thread; does not turn Priya's question into an instruction. |
| summary-03 | cause | H | Identifies the scheduler registering the timer again on unlock as the likely cause. |
| summary-03 | not_focus | H | Does not present Focus / Do Not Disturb as the cause. |
| summary-03 | no_fake_fix | H | Does not claim a workaround or fix exists. |
| summary-03 | on_topic | H | Does not mix in the blurry icon issue. |
| summary-04 | three_bullets | H | Exactly three bullet points. |
| summary-04 | single_ride | H | Does not claim the single-ride price changes. |
| summary-04 | on_topic | H | Does not include the unrelated council business (terraces, renaming, parking). |
| summary-05 | final_plan | H | Presents Sunday 26th as the final plan, not tomorrow or next Saturday. |
| summary-05 | tickets | H | Mentions Oscar buying the tickets. |
| summary-05 | undecided_railway | H | Does not present the rack railway as decided. |
| summary-05 | faithful | H | Adds no facts that are not in the chat. |
| summary-06 | importer_removed | H | Mentions removal of the Evernote importer. |
| summary-06 | known_issue | H | Mentions the duplicate-notes known issue. |
| summary-06 | sync_scope | H | Does not claim sync is every 2 minutes on mobile data. |
| summary-06 | bullets | H | At most four bullet points. |
| summary-07 | max_temp | H | Says to use the maximum temperature reached after switch-off. |
| summary-07 | calculation | H | Gives the formula or says energy is calculated from voltage, current and time. |
| summary-07 | safety | H | Mentions that the heater stays hot after switch-off. |
| summary-07 | faithful | H | Adds no facts or numbers that are not in the sheet. |
| summary-08 | affected | H | Makes clear the 4th-floor resident is affected by the water cut. |
| summary-08 | lift | H | Mentions the lift being out of service 08:00 to 12:00. |
| summary-08 | on_topic | H | Does not include items unrelated to 12 November (recycling, fees, painting, scooter). |
| summary-09 | limitation | H | Names at least one stated limitation. |
| summary-09 | quiet_rest | H | Does not claim quiet rest had a significant effect. |
| summary-09 | hedged | H | Does not repeat the co-author's overstatement (free grade boost, every school should) as the finding. |
| summary-09 | faithful | H | Adds no facts that are not in the press release. |
| summary-10 | from_november | H | Says the extended hours start on 1 November. |
| summary-10 | outdated_source | H | Does not present 10:00 to 20:00 as current; treats the 2023 blog as outdated or conflicting. |
| summary-10 | no_sunday | H | Does not claim the library opens on Sundays. |

### Hallucination versus `faithful`

Run DeepEval Hallucination independently on summary-01, -02, -05, -07 and -09, the five prompts with an existing human `faithful` criterion. Set `context` to the complete source text as one trusted document; `actual_output` is the saved answer and `input` the task instruction. Use LLM mode, strict binary scoring and reasons. Compare its pass/fail to that same answer's human `faithful` label, separately from G-Eval's `faithful` result. It is a validation diagnostic, not a second weighted checklist item. Prompts without `faithful` have no human Hallucination endpoint; do not invent labels from `on_topic` or another criterion.

The [current Hallucination documentation](https://deepeval.com/docs/metrics-hallucination) describes higher scores as greater consistency and strict-mode pass at 1. Pin and inspect the selected version before use: do not assume older examples' inverted score direction. It checks contradictions against supplied context, whereas the checklist also rejects unsupported additions. That mismatch may cause validation failure and must be reported, not repaired by relabelling human scores or claiming that contradiction checks prove full faithfulness.

## Split, seed and score isolation

Before the judge sees any score, rank the ten public prompt IDs by ascending SHA-256 of UTF-8 `20261017:<prompt_id>`. Seed string: `20261017`; no outcome stratification or search for a favourable seed. First four prompt IDs are development; remaining six held-out. Keep all six configurations and five repeats of each prompt in the same partition. The operator has seen aggregate results, so disclose that this is a prospective judge-validation split of an existing corpus, not a pristine new task set.

- Development: `summary-03`, `summary-04`, `summary-06`, `summary-02`: 120 answers, 420 human item labels; 30 `faithful` labels.
- Held-out: `summary-09`, `summary-07`, `summary-10`, `summary-08`, `summary-05`, `summary-01`: 180 answers, 660 human item labels; 120 `faithful` labels.
- Held-out cloud stratum: 30 answers, 110 human item labels; 20 `faithful` labels. Cloud membership is joined only after blinded judgments are frozen.

Only development labels may inform prompt development, via the operator; never transmit labels to the judge. Held-out labels stay out of development tools, prompt files and judge requests. Freeze predictions and their hashes before the final evaluator joins held-out labels from protected copies of the original human review. Original runs remain read-only. Save a manifest with the exact answer IDs, hashes and split assignment before implementation makes any judge calls. This document fixes the rule and IDs; it does not create or inspect a new review key.

## Acceptance and analysis

Compute unweighted Cohen's kappa on binary pass/fail: kappa = (observed agreement - chance agreement) / (1 - chance agreement), with chance agreement from the two raters' marginal pass/fail rates. Report the 2×2 confusion matrix, sample size, unavailable count, raw agreement and kappa. Raw agreement is secondary only: the old configurator's 85% gate does not apply.

Primary gate: held-out pooled human-type G-Eval decisions must have kappa >= 0.6; Hallucination versus `faithful` must independently reach kappa >= 0.6. Also report G-Eval kappa by criterion ID/type (pool repeated IDs, e.g. `faithful` / `on_topic`), prompt and local/cloud strata; flag failing subgroups and prevalence limits rather than describing pooled agreement as reliability on every criterion. These subgroup reports are diagnostics; the predeclared gates are the pooled G-Eval endpoint, Hallucination endpoint and separate cloud checks. Automatic criteria are not sent to G-Eval and do not enter judge validation. Do not blend Hallucination's `faithful` comparisons into G-Eval's overall statistic.

Cloud self-preference check: report both G-Eval and Hallucination held-out cloud kappas separately and evaluate the local-only strata independently. Below 0.6 (or undefined), the cloud row stays human-scored in future comparisons; do not infer reliability on cloud answers from pooled/local performance. Undefined kappa, including all-pass marginals, is not a passing result even with high raw agreement. Report the prevalence issue and obtain new human-labelled held-out items before claiming validation. Only six held-out source prompts and repeated answers limit generalisation; 660 labels are not 660 independent tasks. No independent reviewer or inter-rater validation is claimed.

If a required metric is below 0.6 or undefined, declare the summary judge not yet reliable. Do not judge-score summaries; use human scores and a maths-only app demo. Keep all failed validation artifacts and costs. Any development after observing held-out labels consumes that hold-out; a revised protocol needs new held-out labels and fresh approval. The existing 17 October results remain human-scored in every outcome. A passing validation permits prospective use only after explicit approval, not this week's calls by implication.

## New task types and ongoing checks

For first validation of each metric on a new task type, obtain 30-50 distinct human-labelled items before evaluation (target 50; minimum 30), including pass/fail cases and task diversity. Repeats of one input do not fill that minimum. Predeclare a prompt-group split; do not tune on held-out labels. This existing-summary exercise is a limited calibration with ten source prompts, not proof of transfer to new tasks.

For every future judge-scored run, human-spot-check 10% of judged answers, at least one, selected by a fixed hash-ranking seed recorded before scoring; check every judged metric on that sample. This chooses the upper end of the planned 5-10% range. Keep selection independent of judge outcomes and include candidate configurations; enlarge the sample when necessary for configuration coverage. Report disagreements, kappa where defined and raw agreement. A failed or undefined reliability check triggers human review/additional labels and suspends automated summary recommendations; never rewrite initial scores. Judge tokens, latency, requests and list-price cost are logged separately and excluded from measured task-call energy/latency/money.

## Request count and cost proposal, not authorization

This budget evaluates all 300 saved answers without new generator calls. Each answer keeps all repeats; no outcome deduplication.

| Partition | G-Eval evaluations (human-type items only) | Hallucination evaluations | Physical Gemini requests assumed |
| --- | ---: | ---: | ---: |
| Development, one pass | 14 human criteria × 30 answers per prompt = 420 | 30 | 420 + 2 × 30 = 480 |
| Held-out, once after freeze | 22 human criteria × 30 = 660 | 120 | 660 + 2 × 120 = 900 |
| Total | 1,080 | 150 | 1,380 |

The G-Eval count contains only the 1,080 human-endpoint checks. Automatic criteria incur zero judge requests. Physical-call estimate assumes fixed G-Eval steps need one score/reason request, and Hallucination with reasons needs a verdict request plus a reason request. This is based on the inspected [G-Eval source](https://github.com/confident-ai/deepeval/blob/main/deepeval/metrics/g_eval/g_eval.py) and [Hallucination source](https://github.com/confident-ai/deepeval/blob/main/deepeval/metrics/hallucination/hallucination.py); inspect and pin a release before approval to execute. If the selected version makes extra extraction, step-generation, schema repair or retry calls, revise the count/budget before any call. No automatic retry or repeat development pass is included.

At the [Google standard list price](https://ai.google.dev/gemini-api/docs/pricing), checked 17 October 2026, input is USD 0.75 per million tokens and billable output including thinking is USD 3.75 per million through 31 December 2026. Cost = requests × (input_tokens × 0.75 + billable_output_tokens × 3.75) / 1,000,000; no assumed cache discount, tax or provider-billing reconciliation.

| Assumed average tokens per request, input / billable output | Development USD | Held-out USD | Total USD |
| --- | ---: | ---: | ---: |
| 1,000 / 256 | 0.82080 | 1.53900 | 2.35980 |
| 1,500 / 512 | 1.46160 | 2.74050 | 4.20210 |
| 3,000 / 2,048 (stress allowance) | 4.76640 | 8.93700 | 13.70340 |

These are planning assumptions, exploratory, not pre-registered measurements or a guaranteed spending cap. Thinking can dominate output; prompt lengths and framework calls are unmeasured. Approval envelope: one development pass, one held-out pass and at most 1,380 physical requests, subject to a separate hard monetary cap that the owner will confirm after checking the prepaid balance. The cap is currently unset; there is no approved monetary allowance and no calls may start. The stress estimate is not the cap. Once confirmed, record the exact cap, currency and accounting scope in the run manifest and approval record. Reserve a conservative worst-case request cost before each request and stop before exceeding either cap; never silently raise a cap or treat prepaid balance as permission to spend it. Count failed requests too and stop on unknown billing usage until reviewed. A repeated development pass, a changed prompt/package or any extra calls requires a revised estimate and approval. Before asking to run, prepare the exact pinned prompt manifest and an offline length/budget check; this draft is not executable authorization. Download/install and any run longer than a few minutes also require separate owner approval.
