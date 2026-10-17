# CallCost for LLMs

Read [PLAN.md](PLAN.md) first for current state, untested work and ordered next steps. Read [docs/preregistration.md](docs/preregistration.md) before changing the experiment. Edit current state in PLAN.md; append historical decisions to [docs/log.md](docs/log.md), not this file.

These are Codex working rules. Keep code readable, retain evidence for every reported number, and make design decisions explainable by the project owner. Purpose, scope, status and deadlines live in PLAN.md.

## Standing rules

- Explain choices briefly. Do not make large decisions silently. Keep code readable and scope limited to the requested work.
- Ask before large downloads, system-setting changes or long runs. A handoff command is not permission to execute it.
- Work in this clone: `/Users/andreyryzhanskiy/Documents/CallCost/callcost`, repository `And850/callcost`. The parent directory contains only this clone after the approved cleanup.
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

The hypothesis, knee definition, variance rule and both kill criteria live in [docs/preregistration.md](docs/preregistration.md), the authoritative specification. They are frozen once any benchmark data exists. Before that point, any change requires a dated amendment with its reason, committed and pushed before collecting benchmark data. Check the run state before assuming an amendment is still permitted. Do not reinterpret an instrumentation pilot as a task-set benchmark result.

## History

The decisions log and all former HANDOFF sections are in [docs/log.md](docs/log.md). Current state lives only in [PLAN.md](PLAN.md).

## Key paths

- `src/callcost/`, `scripts/`, `tests/`, `configs/`, `prompts/`, `datasets/`: existing implementation and inputs. Do not duplicate the code area.
- `results/README.md`: result-set index; `results/2026-10-17-initial/`: the unchanged initial aggregate, figures and cost inventory.
- `docs/preregistration.md`: frozen initial rules and dated amendments; preserve exact bytes.
- `docs/judge-preregistration.md`: prospective judge protocol, not call authorization; the monetary hard cap remains unset.
- `docs/log.md`: chronological history; `docs/archive/`: superseded plans and preparation notes.
- `docs/data/`: preparation and runtime evidence, including the retry-upgrade record read by `src/callcost/experiment.py`.
- `runs/LATEST-local`, `runs/LATEST-cloud`, `runs/LATEST-precheck`: private run pointers. Read the matching `status.json`, then `run.log`; checkpoints are authoritative. Never repeat completed checkpoints on resume.
