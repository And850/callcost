# Saved-call cost inventory, 17 October 2026

Draft for owner review. Offline inventory completed before the refocus edits. No inference or rescoring. The 17 October scores, reports, raw data and published aggregate are unchanged.

## Provenance and conventions

Each row below cites a source alias. All paths are relative to the repository root `/Users/andreyryzhanskiy/Documents/CallCost/callcost`:

- **L**: `runs/20261016T213431.178691Z-local/report.json` and `runs/20261016T213431.178691Z-local/calls.csv`.
- **C**: `runs/20261017T082234.706092Z-cloud/report.json` and `runs/20261017T082234.706092Z-cloud/calls.csv`.
- **A**: `docs/data/results-20261017.json` (published quality/latency).
- **S**: `runs/audit-20261017-scored/audit.json` (score counts and qualifications).

For report values, select `groups[]` by `configuration_id`, `task_type` and `cache_stratum: all`; the field names are specified per table. For CSV calculations select the report group's `call_ids`, which are completed measured calls only. Pilots and warm-ups are excluded. Each local configuration has 150 maths and 50 summary calls; cloud has the same measured counts. p50 is the median, p95 nearest rank. All report metrics retain their original availability rules.

**Exploratory, not pre-registered:** this refocus, the recommendation rule, GiB conversions, newly calculated byte/cost totals, missing-data sensitivity and energy per correct answer. Existing p50/p95 values below are copied from saved reports using the original registered definitions, not new fitted estimates. Energy is **estimate, whole-machine delta**, CPU + GPU + ANE above a loaded idle baseline, not process energy or wall-socket energy. Cloud energy and memory are unavailable, never zero. Cloud swap describes the client Mac only.

## Energy per call

Source field: `energy_j.{p50,p95,n,missing_reasons}`. Available/unavailable counts sum to the group call count.

| Configuration | Task | Median J | p95 J | Available / unavailable | Reason if unavailable | Source |
| --- | --- | ---: | ---: | ---: | --- | --- |
| local-q8 | maths | 263.417 | 507.740 | 150 / 0 | none | L |
| local-q8 | summarisation | 119.124 | 162.932 | 50 / 0 | none | L |
| local-q6 | maths | 316.881 | 654.020 | 65 / 85 | Unsupported or invalid power sample encountered: 85 | L |
| local-q6 | summarisation | 149.506 | 197.916 | 21 / 29 | Unsupported or invalid power sample encountered: 29 | L |
| local-q4 | maths | 213.473 | 481.929 | 150 / 0 | none | L |
| local-q4 | summarisation | 109.408 | 141.375 | 50 / 0 | none | L |
| local-q3 | maths | 231.605 | 761.106 | 150 / 0 | none | L |
| local-q3 | summarisation | 107.915 | 163.519 | 50 / 0 | none | L |
| fairy-production | maths | 225.262 | 425.551 | 150 / 0 | none | L |
| fairy-production | summarisation | 112.737 | 147.513 | 50 / 0 | none | L |
| cloud | maths | unavailable | unavailable | 0 / 150 | Energy collection disabled or unavailable; see metadata: 150 | C |
| cloud | summarisation | unavailable | unavailable | 0 / 50 | Energy collection disabled or unavailable; see metadata: 50 | C |

Q6: the retained collector errors include a timing-drift guard failure and no post baseline. Later estimates remain unavailable after an invalid sample; exact rejected receipt times are unavailable. Do not impute them or relax the guard. Source: `runs/20261016T213431.178691Z-local/energy-audit.json`, metadata and S. Cloud client energy was deliberately disabled because background noise limits attribution; cloud-server energy is outside scope.

## Memory

Source fields: `loaded_weight_bytes` and `memory_peak_footprint_bytes`. GiB = bytes / 1,073,741,824 (exploratory presentation conversion). Footprint is p50/p95 of valid per-call sampled process-group peaks, not the highest sample over the entire run. Static weight coverage is complete for every local measured call; cloud local weight/footprint is inapplicable.

| Configuration | Task | Weight bytes / GiB | Footprint p50 / p95 GiB | Footprint available / unavailable | Source |
| --- | --- | ---: | ---: | ---: | --- |
| local-q8 | maths | 9,514,412,544 / 8.8610 | 11.0155 / 11.4111 | 90 / 60 | L |
| local-q8 | summarisation | 9,514,412,544 / 8.8610 | 11.1524 / 11.6121 | 41 / 9 | L |
| local-q6 | maths | 7,276,227,072 / 6.7765 | 9.2991 / 10.1147 | 95 / 55 | L |
| local-q6 | summarisation | 7,276,227,072 / 6.7765 | 9.6791 / 10.2978 | 48 / 2 | L |
| local-q4 | maths | 5,038,041,600 / 4.6920 | 7.2138 / 8.0818 | 108 / 42 | L |
| local-q4 | summarisation | 5,038,041,600 / 4.6920 | 7.4255 / 8.2940 | 45 / 5 | L |
| local-q3 | maths | 3,918,948,864 / 3.6498 | 5.9226 / 6.7311 | 116 / 34 | L |
| local-q3 | summarisation | 3,918,948,864 / 3.6498 | 6.1913 / 6.7192 | 43 / 7 | L |
| fairy-production | maths | 5,950,062,560 / 5.5414 | 8.4827 / 8.9047 | 115 / 35 | L |
| fairy-production | summarisation | 5,950,062,560 / 5.5414 | 8.7501 / 9.0910 | 44 / 6 | L |
| cloud | maths | unavailable | unavailable | 0 / 150 | C |
| cloud | summarisation | unavailable | unavailable | 0 / 50 | C |

All local missing footprint values have report reason `Incomplete process group or failed memory sample`; raw `footprint_missing_reason` and `memory_missing_reason` in calls.csv retain details, including incomplete process coverage and sampler errors. Cloud reason: `Local process memory is not applicable to Gemini`. Weight bytes omit headers/support files and do not measure runtime cache/activation allocations. Fairy retains 912,020,960 encoded vision-weight bytes (source: `docs/data/fairy-production-weight-components.json` and README memory amendment).

## Swap

Report fields: `swapped_calls`, `swap_known_calls`, `swap_unknown_calls`, `swapped_share_known`, `swap_volume_bytes.p50`. All rows have zero unknown counters. Median volume includes known zero-volume calls and is swap-in plus swap-out, not swap-storage growth. In/out columns are **exploratory, not pre-registered** sums of CSV `swapins_bytes` / `swapouts_bytes` over the group's `call_ids`. These counters are whole-machine observations.

| Configuration | Task | Swapped / known (%) | Median volume bytes | Total swap-in bytes | Total swap-out bytes | Source |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| local-q8 | maths | 119/150 (79.33%) | 253,952 | 368,541,696 | 0 | L |
| local-q8 | summarisation | 28/50 (56.00%) | 65,536 | 61,472,768 | 0 | L |
| local-q6 | maths | 126/150 (84.00%) | 450,560 | 441,761,792 | 346,292,224 | L |
| local-q6 | summarisation | 32/50 (64.00%) | 131,072 | 62,570,496 | 0 | L |
| local-q4 | maths | 41/150 (27.33%) | 0 | 27,951,104 | 0 | L |
| local-q4 | summarisation | 10/50 (20.00%) | 0 | 8,601,600 | 0 | L |
| local-q3 | maths | 21/150 (14.00%) | 0 | 13,516,800 | 0 | L |
| local-q3 | summarisation | 1/50 (2.00%) | 0 | 1,015,808 | 0 | L |
| fairy-production | maths | 18/150 (12.00%) | 0 | 55,263,232 | 0 | L |
| fairy-production | summarisation | 5/50 (10.00%) | 0 | 8,355,840 | 0 | L |
| cloud | maths | 5/150 (3.33%) | 0 | 655,360 | 0 | C |
| cloud | summarisation | 2/50 (4.00%) | 0 | 458,752 | 0 | C |

## Latency, payload and money

Source fields: `latency_s`, `swap_free_latency_s`, `request_payload_bytes`, `response_payload_bytes`, `list_price_cost`; p50/p95 in each pair. Payloads include API/stream framing, exclude headers and transport overhead. Cloud latency covers successful attempts, not failed-attempt duration or retry waits. List-price equivalent excludes tax, electricity and hardware. Money totals are **exploratory, not pre-registered** CSV sums.

| Configuration | Task | All p50 / p95 s | Swap-free p50 / p95 s (n) | Request p50 / p95 bytes | Response p50 / p95 bytes | USD p50 / p95; total | Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| local-q8 | maths | 17.089 / 33.695 | 15.924 / 29.421 (31) | 387.5 / 682.0 | 22167.5 / 41814.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q8 | summarisation | 6.654 / 9.631 | 6.366 / 9.077 (22) | 1579.5 / 2088.0 | 6940.0 / 11565.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q6 | maths | 13.456 / 28.710 | 12.689 / 27.927 (24) | 387.5 / 682.0 | 21972.5 / 44991.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q6 | summarisation | 6.210 / 8.153 | 6.141 / 8.105 (18) | 1579.5 / 2088.0 | 6854.0 / 11629.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q4 | maths | 10.484 / 23.844 | 9.844 / 23.818 (109) | 387.5 / 682.0 | 21798.0 / 50532.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q4 | summarisation | 5.148 / 6.937 | 5.073 / 6.926 (40) | 1579.5 / 2088.0 | 6725.0 / 12577.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q3 | maths | 10.575 / 34.257 | 9.701 / 34.093 (129) | 387.5 / 682.0 | 20678.5 / 71547.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| local-q3 | summarisation | 4.833 / 7.398 | 4.835 / 7.398 (49) | 1579.5 / 2088.0 | 6138.5 / 12892.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| fairy-production | maths | 10.450 / 19.918 | 10.420 / 19.934 (132) | 368.5 / 663.0 | 22526.0 / 42219.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| fairy-production | summarisation | 5.191 / 6.804 | 5.163 / 6.804 (45) | 1560.5 / 2069.0 | 6772.5 / 12201.0 | 0.000000000 / 0.000000000; 0.000000000 | L |
| cloud | maths | 3.893 / 9.152 | 3.877 / 8.976 (145) | 415.5 / 710.0 | 4668.5 / 6755.0 | 0.001160625 / 0.002195250; 0.183540000 | C |
| cloud | summarisation | 3.410 / 8.017 | 3.410 / 7.449 (48) | 1607.5 / 2116.0 | 2298.5 / 5761.0 | 0.000639750 / 0.002625750; 0.049327500 | C |

Latency, payload and cost have complete coverage (150 maths / 50 summaries per configuration). Local API money is zero by definition, not an energy/hardware-cost estimate. Cloud measured-call total is USD 0.232867500; pilots/warm-ups bring the pass to USD 0.23358825; the all-history ledger including earlier smoke is USD 0.23373225. The 18 failed HTTP attempts have unknown usage/cost. Pass and all-history scopes differ. Sources: C CSV/report, S `runs[]`, and `runs/gemini-cost-ledger-20261017/ledger.json`. Provider billing/VAT remains pending.

## What was registered before collection

| Metric / convention | Evidence committed before the benchmark |
| --- | --- |
| Latency, payload bytes, list-price money, energy per call; per-task p50/p95 and counts | `5bcabd3` initial README; `da06118` measurement method (median / nearest-rank p95, energy baseline and domains). |
| Loaded tensor payload bytes; sampled footprint/RSS secondary | `397d830` memory fallback, then `d3bf74e` quality-only knee and `c534937` method clarification. |
| All-call and swap-free latency, swapped share, unknown counts, median swap-in+out volume, storage and compressor before/after | `4b7f7e1` dated 16 October amendment; implementation `c5c9671`. |
| Delta power interval reconstruction, coverage/drift rejection and receipt-anchor uncertainty | `c56cba0` dated 16 October amendment before benchmark collection. |
| Human summary quality / exact maths scoring, equal prompt weights and knee/variance rules | `5bcabd3`; quality-only knee `d3bf74e`; approved summaries `6f6de97`; `4b7f7e1` swap inclusion. |
| Thinking controls and dated cloud token prices | `3f4ebc1`, `ca047dd`; cloud client energy omission documented in `d4ee06c` before cloud collection. |

The original metrics were registered; the new energy-first priority and app rule were chosen after viewing the results. They do not retrospectively become registered findings. HTTP retry policy `1b98743` was adopted during cloud collection, not before all data. Length-exclusion sensitivity `09cb620` was post-collection and remains secondary. Frozen rules and initial human-scored results are unchanged.

## Exploratory energy per correct maths answer

**Exploratory, not pre-registered.** Sum energy across all calls with available energy (including wrong/unparseable answers), divided by the number correct among that same subset. This is energy spent per successful outcome in the observed batch, not mean energy restricted to correct calls, and not median energy divided by full-set accuracy. Sources: L/C CSV `energy_j`, report `quality.call_scores` matched by `call_id`; S verifies original correctness counts.

| Configuration | Observed energy sum J | Energy-observed calls / 150 | Correct among those | J per correct outcome | Source |
| --- | ---: | ---: | ---: | ---: | --- |
| local-q8 | 42060.482 | 150/150 | 135 | 311.559 | L |
| local-q6 | 23737.961 | 65/150 | 61 | 389.147 | L |
| local-q4 | 36235.160 | 150/150 | 135 | 268.409 | L |
| local-q3 | 41510.997 | 150/150 | 85 | 488.365 | L |
| fairy-production | 35298.097 | 150/150 | 140 | 252.129 | L |
| cloud | unavailable | 0/150 | unavailable | unavailable | C |

Q6 is a partial-subset estimate, not comparable as a complete-run cost per correct answer. Cloud is unavailable, not zero.

## Exploratory app-rule check

**Exploratory, not pre-registered.** Candidate pool is all five local configurations, including Fairy as a separate reference. Quality uses the unchanged initial primary scores in A/L. Eligibility is inclusive: quality >= best local quality minus 0.05. Choose the lowest available median energy among eligible; flag swap only when strictly above 50%. This check does not change a production deployment or satisfy kill criterion 2.

| Task | Best local quality | Eligibility floor | Eligible | Observed energy pick | Swap warning for pick |
| --- | ---: | ---: | --- | --- | --- |
| maths | 93.3333% | 88.3333% | local-q8, local-q6, local-q4, fairy-production | local-q4, 213.473 J | no, 27.33% |
| summarisation | 90.1905% | 85.1905% | local-q8, local-q6, local-q4, fairy-production | local-q4, 109.408 J | no, 20.00% |

Q3 is excluded for both tasks. Q8 and q6 exceed the swap-warning threshold on both tasks. Missing energy does not change the observed-data pick when q6 is excluded for incomplete coverage: q4 still wins. But q6 lacks more than half of its energy observations in each task (85 maths, 29 summaries), so its full-sample median could be below q4; no definitive full-data winner is established. Available-case q6 medians (316.881 / 149.506 J) are higher than q4, but are not a bound on the missing values. Do not impute zero, fill from latency or issue an unqualified recommendation. Cloud is outside the local pool and lacks comparable energy. Excluding Fairy also leaves the observed pick unchanged.

## Single-call scope check

All 1,000 local measured saved requests contain string `input`, `store: false` and no previous-response link; all 200 cloud measured saved requests have one `contents` entry. Sources: each CSV `raw_request` path and its request JSON, plus `src/callcost/providers/lmstudio.py` / `gemini.py`. These are independent, empty-history calls, not long-chat measurements. Server/cache state is not proved empty by conversation storage settings. Longer-chat energy/memory is unmeasured; a universal numerical lower-bound claim is not established by this dataset.
