# CallCost for LLMs

Read [docs/HANDOFF.md](docs/HANDOFF.md) first for current state, untested work and ordered next steps. Read the README pre-registration before changing the experiment. Keep current progress in HANDOFF.md, not in this file.

CallCost is a Python CLI that measures what one language-model call costs on Andrii's own Mac, alongside answer quality on a developer's task set. It compares separately installed LM Studio configurations with a Gemini cloud reference, retaining raw evidence for every reported number. It is the main technical project behind Andrii's university applications for Computer Science in 2027. Every number must survive hostile questioning, and Andrii must be able to explain every design decision himself.

## Standing rules

- Explain choices briefly. Do not make large decisions silently. Keep code readable and scope limited to the requested work.
- Ask before large downloads, system-setting changes or long runs. A handoff command is not permission to execute it.
- Work in this clone: `/Users/andreyryzhanskiy/Documents/CallCost/callcost`, repository `And850/callcost`. The parent directory is an older copy.
- GitHub account: `And850`. `gh` and `git` are already authenticated in Terminal; push to `origin` (`https://github.com/And850/callcost`).
- Use normal `git add`, `git commit`, `git push` here, with small, clear commits. Do not commit through an API. Never force-push or rewrite history.
- If Git metadata writes are blocked, stop and explain the permission issue. Do not work around it through another publishing route.
- Never auto-commit benchmark results. Run artifacts stay ignored unless the owner explicitly selects material to publish.
- No em dashes in README or documentation.
- Never claim "local beats cloud". The finding concerns task-specific quality and cost tradeoffs, not a universal winner.
- Cloud-side energy is out of scope. Label on-device energy "estimate, whole-machine delta" and state the measured domains; it is not per-process or cloud-server energy.
- Describe the summaries as "Fairy-style prompts written for the benchmark (invented texts)", not real Fairy usage. Do not send them to any model until Andrii confirms review.
- Fairy is a separate project. Do not touch its code or build an integration here.
- Missing observations are unavailable with reasons, never zero. Preserve failed/interrupted attempts and trace reported values to raw calls.
- Initial 17 October results keep human scores primary permanently. The draft prospective exception in `docs/judge-preregistration.md` is not effective until owner approval, commit/push and held-out validation; only later-collected runs may then use an LLM as primary judge. Human scores stay pending until reviewed where that exception does not apply.
- Temperature 0 does not guarantee GPU determinism. Retain and report answer variation across repeats.
- Read credentials from the environment. Never print or commit API keys. Prices come from config, not provider-code constants.

## Pre-registration

The hypothesis, knee definition, variance rule and both kill criteria live in [README.md](README.md), the authoritative specification. They are frozen once any benchmark data exists. Before that point, any change requires a dated amendment with its reason, committed and pushed before collecting benchmark data. Check the run state before assuming an amendment is still permitted. Do not reinterpret an instrumentation pilot as a task-set benchmark result.

## Decisions log

- 2026-10-15: Independently convert official `Qwen/Qwen3.5-9B` weights to text-only MLX at 3/4/6/8 bit. Source revision: `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; mlx-lm 0.32.0; affine quantisation; group size 64. Exact commands and provenance are in the model-preparation docs.
- 2026-10-15: Fairy's existing production MLX 4-bit model is a fifth local reference, outside the four-level knee sequence. It retains vision weights, so memory and load comparisons require that caveat.
- 2026-10-15: Thinking is off locally. Verify zero reasoning tokens and no reasoning content or `<think>` tags, not just the requested setting.
- 2026-10-15: Cloud reference is `gemini-3.8-flash`, `thinking_level: low`. Thinking cannot be disabled for this model. Record thinking tokens separately and count them once in billable output; free-tier usage is reported at configured list-price equivalent.
- 2026-10-15: Dataset is 30 GSM8K test problems with pinned revision, original row IDs and reproducible selection, plus 10 invented-text summaries. N=5 measured repeats; temperature 0; pilots and warm-ups are additional and excluded.
- 2026-10-15: Descriptive memory metric is exact encoded tensor payload bytes in the loaded safetensors files, excluding headers and support files. It is not runtime peak memory. Measured physical footprint and RSS are secondary labelled observations.
- 2026-10-15: Knee amended to quality-only. Cost is reported per step, not a gate. Exact criteria and reasons are in the README.
- 2026-10-16: Superseding swap amendment: all completed calls contribute to quality/knee and the unchanged variance rule. All-call latency is primary; swap-free latency is secondary. Record swap-in/out bytes, before/after vm.swapusage and compressor memory; report swapped share, unknown counts and median swap volume. Swap is a configuration cost on this 16 GB Mac, with whole-machine attribution limits.
- 2026-10-16: Local (five configurations) and cloud (one reference) are independently resumable passes. Cloud quota/rate-limit errors stop without automatic retries. Confirm paid-tier evidence after the owner enables billing and before cloud collection.


- 2026-10-17: Cloud HTTP 500/503 calls may retry the same call up to four times with 10/30/90/270-second backoff. Log every failed attempt; latency covers only the successful attempt. Quota, billing, exhausted balance and auth errors stop immediately without retries; exhausted transient retries also stop cleanly with checkpoints preserved.
- 2026-10-17: Summary deviation handling: the 6f6de97 tight instructions and 50-90-word max_words checks actually ran; the intended longer-limit revision did not. Preserve identical collected prompts/responses, disclose the dated deviation, retain max_words in primary scoring and report excluding-only-max_words sensitivity separately. No reruns; primary scores alone determine knees and variance.
- 2026-10-17: Blind human summary review was completed by the project author with configuration labels hidden, then imported and checked. Disclose the single author-reviewer and AI-assisted summary prompt drafting; no independent reviewer or inter-rater measurement exists. No LLM was the primary quality judge.
- 2026-10-17: Applying the frozen quality-only knee and variance rules gives maths a 4→3-bit knee and summaries no knee found. This is consistent with the registered hypothesis on this task set, not proof; cost reductions are not uniformly steady. Kill criterion 1 is not triggered. Kill criterion 2 remains unmet pending a Fairy-style maths test and an actual recorded production decision change; no new model calls are authorized by this log.
- 2026-10-17: Owner selected aggregate results, charts and README for publication together in 70aab5d. Raw run/review artifacts stay private. Provider-billing reconciliation awaits the matching billed figure; VAT applicability is unconfirmed.

- 2026-10-17: Owner refocuses CallCost on single-call energy first, then model GiB/swap, latency/money and secondary quality; the agreed plan is copied to docs/plan-2026-10-17.md. The configurator plan is superseded. Initial human scores and frozen experiment rules remain unchanged. App recommendations and new derived metrics are exploratory, not pre-registered. DeepEval/Gemini judge policy is a draft prospective exception only; no code, inference, downloads or system changes are authorized. The owner reviewed the week-1 drafts and authorizes small documentation commits/pushes after the requested corrections; CI budget mode and SCI units wait until after December.

- 2026-10-17: Owner removes automatic-criterion G-Eval calls: validation proposal is 1,380 physical requests, with a hard monetary cap still awaiting owner confirmation after a prepaid-balance check. PrismML Ternary Bonsai 2 27B is a demo-only candidate outside the initial benchmark/knee sequence; compatibility, thinking controls and runtime caveats are planning items in docs/plan-2026-10-17.md. No download, model call or adapter code is authorized. Vendor benchmark numbers are not CallCost results.

## Key paths

- `configs/experiment.yaml`: experiment configurations, thinking controls and dated prices.
- `prompts/`: prompt files and preregistered scoring rules; private combined inputs belong under `prompts/private/`.
- `scripts/run_full.sh`: unattended launcher, currently subject to the readiness checks in HANDOFF.md.
- `runs/LATEST-local`, `runs/LATEST-cloud`, `runs/LATEST-precheck`: independent run pointers. `runs/LATEST` is only the most recently touched run. Read the matching `status.json`, then `run.log`; checkpoints are authoritative. Never repeat completed checkpoints on resume.
- `docs/HANDOFF.md`: current state and first read for each new chat.
- `docs/model-preparation.md`: model pins, conversions, production-reference caveats and instrumentation evidence.

## Device and deadlines

- One Mac: Apple M1 Pro, 16 GB RAM. The 8-bit model is close to the memory limit. Passing a preflight threshold does not prove swap-free inference or comfortable headroom.
- Real results ready: 22 November 2026.
- WAICY 2026, AI Showcase track: submission closes 29 November 2026 at 23:00 Madrid time (`Europe/Madrid`).
- Finals: 4 to 6 December 2026, live presentation and Q&A.
- Repository and chart freeze: 15 December 2026.
