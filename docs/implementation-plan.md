# CallCost implementation plan

**Goal:** Deliver an auditable comparison of per-call cost and task quality on one Mac.

**Architecture:** A small Python package coordinates sequential experiments. Provider adapters return a shared per-call record. Independent measurement collectors retain raw samples, and reporting reads saved artifacts without rerunning inference.

**Specification:** [README and pre-registration](../README.md), [measurement method](methodology.md).

## Constraints

- Forty scored prompts: 30 pinned GSM8K test problems and ten owner-supplied summaries.
- Five measured calls per prompt per configuration, with additional excluded warm-ups.
- No family selection before showing the installed variants to the owner.
- Fixed Gemini thinking setting and config-supplied prices.
- No invented measurements, hidden retries, LLM primary judge or Fairy code changes.
- No em dashes in README or documentation.
- Small commits, no force-pushes and no history rewriting.

## Repository foundation

- [x] Publish the README, MIT licence, measurement specification and example input formats.
- [x] Record the installed model inventory without claiming file sizes are runtime memory.
- [ ] Add a reproducible 30-problem GSM8K selection with pinned source, row IDs and licence.

## Milestone 1: runners and logging, 25 October 2026

Files: `src/callcost/cli.py`, `schemas.py`, `experiment.py`, `storage.py`, `providers/lmstudio.py`, `providers/gemini.py`, and `measurements/{machine,memory,energy}.py`.

- [ ] Implement strict YAML/JSON validation before provider requests. Test duplicate IDs, unknown fields, repeats below five, missing scoring rules, unresolved prices and missing thinking settings.
- [ ] Define one typed per-call record with explicit units, missing-value reasons, statuses, provider usage and load-event references. Test CSV escaping and metadata round trips.
- [ ] Implement LM Studio discovery, explicit variant loading and streamed text/statistics. Test fragmented streaming events, empty events, truncated streams and unexpected model identity using recorded API fixtures.
- [ ] Implement Gemini streaming with explicit thinking controls. Test thinking-token accounting, missing usage, rate limiting and payload byte counts.
- [ ] Implement machine metadata and sampled process RSS. Test process exits, ambiguous worker identity and contemporaneous sums rather than sums of separate peaks.
- [ ] Add optional powermetrics collection and raw preservation. Test units, overlapping intervals, incomplete coverage, baseline drift and negative deltas.
- [ ] Implement seeded sequential scheduling, held-out warm-ups and first-appearance/repeat labels. Test that every configuration sees every prompt exactly five measured times.
- [ ] Verify with offline fixtures, then a clearly labelled smoke run once model settings and access are available. Commit each independently verified component.

## Milestone 2: aggregation

- [ ] Implement p50, nearest-rank p95, IQRs and observation counts from saved CSV. Test hand-calculated samples, missing metrics and load-event deduplication.
- [ ] Render one row per configuration/task with adjacent quality and cost metrics, and separate first-appearance/repeat reporting when cache reuse cannot be disabled.
- [ ] Test incomplete and failed runs so missing data cannot become zero-cost successes.

## Milestone 3: blind review, 8 November 2026

- [ ] Implement numeric final-line, substring, regex and JSON checks with hand-scored fixtures.
- [ ] Implement anonymous shuffled review with resumable checklist decisions. Test that configuration, filenames and performance data do not leak into the review display.
- [ ] Aggregate prompt scores with equal prompt weights, preserving pending review status.

## Milestone 4: results and charts, 22 November 2026

- [ ] Verify all dataset rules and configuration choices are committed before the first full run.
- [ ] Run the real 40-prompt experiment and complete blind review.
- [ ] Apply registered knee and variance rules with boundary tests at 10 points, twice the prior drop, 20% savings and 5 points.
- [ ] Produce a chart per task type with a named cost axis, quantisation points, a cloud reference and visible uncertainty.
- [ ] Publish limitations and either the observed knee or `no knee found`, plus the actual decision the tool changed or its failure to change one.

## Milestone 5: CI budget mode and freeze, 15 December 2026

- [ ] Compare against a stored previous-commit baseline under matched task/configuration/machine definitions.
- [ ] Test configured budget boundaries and non-zero exit status for regressions; reject incomparable or incomplete baselines.
- [ ] Freeze the repository and charts without rewriting their history.

## Review focus

Tests must protect measurement meaning, especially streaming chunks mistaken for tokens, duplicated thinking-token charges, missing workers presented as low memory, changed cache state hidden in pooled measurements, and incomplete human review presented as a final quality score.
