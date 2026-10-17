# CallCost refocus plan (agreed 17 Oct 2026)

Status: agreed between Alex and the reviewer. Not yet sent to Codex.

## Thesis
- CallCost measures the hidden energy and memory cost of a single LLM call on a constrained laptop.
- Priority: 1) on-device energy estimate per call, 2) memory: GiB the model occupies and how much is swapped, 3) latency and money, 4) answer quality (secondary).
- Scope: single calls in a fresh, empty chat. Longer chats cost more energy and memory per call; results are a lower bound for chat use and representative of single-task use.
- Lead finding to report: on a 16 GB Mac, 8-bit and 6-bit swapped on 73.5% / 79.0% of calls (4-bit: 25.5%) and were slower than 4-bit with no quality gain. Whole-machine counters cannot prove inference alone caused the swapping.

## Existing results (17 Oct)
- Initial results. Human scores stay primary; never rescored. Knee results kept unchanged as the registered secondary result.
- README refocus is a dated presentation note, not a pre-registration amendment.
- Stale wording to fix: README line 251 (resume), line 61 (point to 17 Oct 500/503 retry decision), HANDOFF line 110.
- Limitation to add: summary texts were invented; existing datasets and frameworks (e.g. DeepEval) were not used.

## Quality evaluation (new runs)
- Dated amendment: an LLM judge may be primary for runs collected after the amendment, once validated.
- Framework: DeepEval (Apache 2.0). Judge model: Gemini 3.8 Flash; settings and prompt hash fixed before validation; judge calls logged and costed separately.
- Metrics:
  - Maths: exact match (deterministic, no judge).
  - Summaries: G-Eval, one check per existing checklist criterion.
  - Summaries: DeepEval Hallucination, validated against the human "faithful" criterion.
  - Not used now: DeepEval Summarization (overlaps), JSON Correctness and agentic metrics (no tasks yet).
- Validation: the 300 human-scored summaries, split by prompt into development and held-out sets before the judge sees any score. Cohen's kappa (unweighted, labels are yes/no) >= 0.6 on held-out. Raw agreement reported as secondary only.
- Self-preference check: kappa reported separately on the cloud answers; below threshold, the cloud row stays human-scored.
- First validation of any metric on a new task type: minimum 30-50 human-labelled items. Afterwards: 5-10% human spot check of every judged run, for every judged metric.
- If kappa < 0.6: summaries are not judge-scored and the app demo runs on maths only.

## App (truncated version for WAICY)
- Question it answers: which local model should this computer use for this task, given energy and memory cost.
- Local web page (Streamlit or similar). macOS only for the demo; other PCs are the stated next step.
- Flow: read machine (chip, RAM, free memory, swap) -> pick task type (maths or summaries, existing sets) -> pick installed LM Studio models -> probe -> score quality -> recommend.
- Run modes (config): Quick 5 prompts x 2 repeats (labelled "rough"), Standard 10 x 3, Full 30 x 5. Report states the mode.
- Recommendation rule (app defaults, chosen after seeing 17 Oct data; disclosed; user-adjustable):
  - Eligible: quality within X = 5 points of the best local candidate.
  - Choose: lowest median energy per call among eligible.
  - Warning: swap on more than Y = 50% of calls.
  - On 17 Oct data this excludes 3-bit for both tasks.
- AI element: the validated Gemini judge. Optional: Gemini writes a plain-language explanation using only measured numbers.
- Out of scope: Windows/Linux, model downloads, tool use, long contexts, user-defined tasks.
- Known limits: energy needs sudo (powermetrics); probes take minutes, so the demo video uses a sped-up or earlier recording.

## Not doing
- Self-built configurator. Context-length experiment (no time). Tool-use task set (no tasks yet).

## Timeline
- 18-24 Oct: README refocus, judge pre-registration, validation on the 300 scores.
- 25-31 Oct: probe and recommendation engine.
- 1-7 Nov: web page and report (AMC 5 Nov).
- 8-14 Nov: end-to-end test (Veritas 14-15 Nov).
- 15-22 Nov: slides, presentation and demo videos, 250-word texts. Buffer to 29 Nov.

## Still pending
- Gemini billed figure from Google Cloud billing report.
- Kill criterion 2 (a real Fairy decision) remains unmet.
