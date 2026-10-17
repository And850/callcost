| Result set | Scope / interpretation |
| --- | --- |
| 17 October 2026 initial | Six configurations on one Apple M1 Pro, 16 GB Mac; collected 16 to 17 October. Initial human scores unchanged. |
| Independent task units | 30 pinned GSM8K maths problems and ten Fairy-style prompts written for the benchmark (invented texts); five measured repeats. Repeats are not independent tasks. |
| Quality | Maths deterministic exact answer; summary automatic checks plus one blinded author-reviewer. No independent reviewer/inter-rater measurement. Existing summary datasets and DeepEval were not used. |
| Summary sensitivity | Primary includes max_words. Secondary removes only max_words; post-collection exploratory sensitivity, not re-registration or new answers. Tight original instructions/50-90-word limits ran; intended longer-limit revision did not. |
| Energy scope | Estimate, whole-machine delta; CPU + GPU + ANE above a loaded idle baseline. Not process energy, wall-socket power or cloud-server energy. |
| Memory / swap | Weight bytes are static encoded tensor payload, not runtime peak. Footprint is sampled process-group peak per call. Swap counters cover the whole Mac, including cloud client calls; no causal process attribution. |
| Missing observations | Unavailable with reasons, never zero; availability counts refer to completed measured calls. |
| Quantiles | Original report p50 median / p95 nearest rank; swap-free latency uses known zero swap-in and swap-out calls. Successful-attempt cloud latency excludes failed attempts/backoff. |
| Post-data presentation | GiB conversions and newly derived app-rule/energy-per-correct analyses are exploratory, not pre-registered. This page transcribes saved aggregate values; it does not rescore answers. |
| Registered findings | Maths knee 4→3 bit; summaries no knee. Criterion 1 not triggered; roughly steady cost reductions not established. Criterion 2 remains unmet: no actual Fairy decision changed. |
| Limitations | Single device and small/public task sample; local/cloud collection windows and thinking differ. Initial receipt-anchor uncertainty and q6 collector timing drift limit energy attribution. |
| Files | [Published aggregate](data.json), [cost inventory](cost-inventory.md), [figures](figures/), [frozen rules](../../docs/preregistration.md), [current plan](../../PLAN.md). |

| Source | Existing aggregate path (repository-relative) | Selection / fields |
| --- | --- | --- |
| A | `results/2026-10-17-initial/data.json` | `tasks[task].points[]`, selected by configuration_id; original published file moved unchanged. |
| L | `runs/20261016T213431.178691Z-local/report.json` | Private local aggregate, not a published raw run. `groups[]` selected by configuration_id, task_type and cache_stratum=all. |
| C | `runs/20261017T082234.706092Z-cloud/report.json` | Private cloud aggregate, same group selection. |
| S | `runs/audit-20261017-scored/audit.json` | Private scored aggregate; `variance[]`, `knee_findings`, `runs[]`. |
| I | [cost-inventory.md](cost-inventory.md) | Existing aggregate inventory, moved with path-only fixes; detailed provenance, registration commits and exploratory energy per correct maths answer. |
| Raw evidence | `runs/` (private, ignored) | Retained unchanged; no raw response or review identity is published here. |

| Configuration | Task | Primary quality % | Without max_words % | Calls / unique prompts × repeats | Source |
| --- | --- | --- | --- | --- | --- |
| local-q8 | maths | 90.00 | not applicable | 150 / 30 × 5 | A: quality, quality_without_max_words, calls |
| local-q8 | summarisation | 90.19 | 92.33 | 50 / 10 × 5 | A: quality, quality_without_max_words, calls |
| local-q6 | maths | 93.33 | not applicable | 150 / 30 × 5 | A: quality, quality_without_max_words, calls |
| local-q6 | summarisation | 89.29 | 92.33 | 50 / 10 × 5 | A: quality, quality_without_max_words, calls |
| local-q4 | maths | 90.00 | not applicable | 150 / 30 × 5 | A: quality, quality_without_max_words, calls |
| local-q4 | summarisation | 89.23 | 92.33 | 50 / 10 × 5 | A: quality, quality_without_max_words, calls |
| local-q3 | maths | 56.67 | not applicable | 150 / 30 × 5 | A: quality, quality_without_max_words, calls |
| local-q3 | summarisation | 82.62 | 81.00 | 50 / 10 × 5 | A: quality, quality_without_max_words, calls |
| fairy-production | maths | 93.33 | not applicable | 150 / 30 × 5 | A: quality, quality_without_max_words, calls |
| fairy-production | summarisation | 89.46 | 92.90 | 50 / 10 × 5 | A: quality, quality_without_max_words, calls |
| cloud | maths | 98.00 | not applicable | 150 / 30 × 5 | A: quality, quality_without_max_words, calls |
| cloud | summarisation | 94.57 | 98.47 | 50 / 10 × 5 | A: quality, quality_without_max_words, calls |

| Configuration | Task | Energy median / p95 J | Available / unavailable | Unavailable reason | Source |
| --- | --- | --- | --- | --- | --- |
| local-q8 | maths | 263.417 / 507.740 | 150 / 0 | none | L: energy_j |
| local-q8 | summarisation | 119.124 / 162.932 | 50 / 0 | none | L: energy_j |
| local-q6 | maths | 316.881 / 654.020 | 65 / 85 | Unsupported or invalid power sample encountered: 85 | L: energy_j |
| local-q6 | summarisation | 149.506 / 197.916 | 21 / 29 | Unsupported or invalid power sample encountered: 29 | L: energy_j |
| local-q4 | maths | 213.473 / 481.929 | 150 / 0 | none | L: energy_j |
| local-q4 | summarisation | 109.408 / 141.375 | 50 / 0 | none | L: energy_j |
| local-q3 | maths | 231.605 / 761.106 | 150 / 0 | none | L: energy_j |
| local-q3 | summarisation | 107.915 / 163.519 | 50 / 0 | none | L: energy_j |
| fairy-production | maths | 225.262 / 425.551 | 150 / 0 | none | L: energy_j |
| fairy-production | summarisation | 112.737 / 147.513 | 50 / 0 | none | L: energy_j |
| cloud | maths | unavailable / unavailable | 0 / 150 | Energy collection disabled or unavailable; see metadata: 150 | C: energy_j |
| cloud | summarisation | unavailable / unavailable | 0 / 50 | Energy collection disabled or unavailable; see metadata: 50 | C: energy_j |

| Configuration | Task | Encoded weight bytes | Weight GiB (exploratory conversion) | Available / unavailable | Source |
| --- | --- | --- | --- | --- | --- |
| local-q8 | maths | 9514412544 | 8.8610 | 150 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q8 | summarisation | 9514412544 | 8.8610 | 50 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q6 | maths | 7276227072 | 6.7765 | 150 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q6 | summarisation | 7276227072 | 6.7765 | 50 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q4 | maths | 5038041600 | 4.6920 | 150 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q4 | summarisation | 5038041600 | 4.6920 | 50 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q3 | maths | 3918948864 | 3.6498 | 150 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| local-q3 | summarisation | 3918948864 | 3.6498 | 50 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| fairy-production | maths | 5950062560 | 5.5414 | 150 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| fairy-production | summarisation | 5950062560 | 5.5414 | 50 / 0 | L: loaded_weight_bytes; GiB=bytes/2^30 |
| cloud | maths | unavailable | unavailable | 0 / 150 | C: loaded_weight_bytes; GiB=bytes/2^30 |
| cloud | summarisation | unavailable | unavailable | 0 / 50 | C: loaded_weight_bytes; GiB=bytes/2^30 |

| Configuration | Task | Sampled footprint p50 / p95 GiB | Available / unavailable | Unavailable reason | Source |
| --- | --- | --- | --- | --- | --- |
| local-q8 | maths | 11.0155 / 11.4111 | 90 / 60 | Incomplete process group or failed memory sample: 60 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q8 | summarisation | 11.1524 / 11.6121 | 41 / 9 | Incomplete process group or failed memory sample: 9 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q6 | maths | 9.2991 / 10.1147 | 95 / 55 | Incomplete process group or failed memory sample: 55 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q6 | summarisation | 9.6791 / 10.2978 | 48 / 2 | Incomplete process group or failed memory sample: 2 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q4 | maths | 7.2138 / 8.0818 | 108 / 42 | Incomplete process group or failed memory sample: 42 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q4 | summarisation | 7.4255 / 8.2940 | 45 / 5 | Incomplete process group or failed memory sample: 5 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q3 | maths | 5.9226 / 6.7311 | 116 / 34 | Incomplete process group or failed memory sample: 34 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| local-q3 | summarisation | 6.1913 / 6.7192 | 43 / 7 | Incomplete process group or failed memory sample: 7 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| fairy-production | maths | 8.4827 / 8.9047 | 115 / 35 | Incomplete process group or failed memory sample: 35 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| fairy-production | summarisation | 8.7501 / 9.0910 | 44 / 6 | Incomplete process group or failed memory sample: 6 | L: memory_peak_footprint_bytes; exploratory GiB conversion |
| cloud | maths | unavailable | 0 / 150 | Local process memory is not applicable to Gemini: 150 | C: memory_peak_footprint_bytes; exploratory GiB conversion |
| cloud | summarisation | unavailable | 0 / 50 | Local process memory is not applicable to Gemini: 50 | C: memory_peak_footprint_bytes; exploratory GiB conversion |

| Configuration | Task | Swap-active / known calls | Swapped share % | Unknown calls | Median swap volume bytes (known n) | Source |
| --- | --- | --- | --- | --- | --- | --- |
| local-q8 | maths | 119 / 150 | 79.33 | 0 | 253952 (150) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q8 | summarisation | 28 / 50 | 56.00 | 0 | 65536 (50) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q6 | maths | 126 / 150 | 84.00 | 0 | 450560 (150) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q6 | summarisation | 32 / 50 | 64.00 | 0 | 131072 (50) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q4 | maths | 41 / 150 | 27.33 | 0 | 0 (150) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q4 | summarisation | 10 / 50 | 20.00 | 0 | 0 (50) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q3 | maths | 21 / 150 | 14.00 | 0 | 0 (150) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| local-q3 | summarisation | 1 / 50 | 2.00 | 0 | 0 (50) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| fairy-production | maths | 18 / 150 | 12.00 | 0 | 0 (150) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| fairy-production | summarisation | 5 / 50 | 10.00 | 0 | 0 (50) | L: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| cloud | maths | 5 / 150 | 3.33 | 0 | 0 (150) | C: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |
| cloud | summarisation | 2 / 50 | 4.00 | 0 | 0 (50) | C: swapped_calls, swapped_share_known, swap_unknown_calls, swap_volume_bytes |

| Configuration | Task | All-call p50 / p95 s (n) | Swap-free p50 / p95 s (n) | Source |
| --- | --- | --- | --- | --- |
| local-q8 | maths | 17.089 / 33.695 (150) | 15.924 / 29.421 (31) | L: latency_s, swap_free_latency_s |
| local-q8 | summarisation | 6.654 / 9.631 (50) | 6.366 / 9.077 (22) | L: latency_s, swap_free_latency_s |
| local-q6 | maths | 13.456 / 28.710 (150) | 12.689 / 27.927 (24) | L: latency_s, swap_free_latency_s |
| local-q6 | summarisation | 6.210 / 8.153 (50) | 6.141 / 8.105 (18) | L: latency_s, swap_free_latency_s |
| local-q4 | maths | 10.484 / 23.844 (150) | 9.844 / 23.818 (109) | L: latency_s, swap_free_latency_s |
| local-q4 | summarisation | 5.148 / 6.937 (50) | 5.073 / 6.926 (40) | L: latency_s, swap_free_latency_s |
| local-q3 | maths | 10.575 / 34.257 (150) | 9.701 / 34.093 (129) | L: latency_s, swap_free_latency_s |
| local-q3 | summarisation | 4.833 / 7.398 (50) | 4.835 / 7.398 (49) | L: latency_s, swap_free_latency_s |
| fairy-production | maths | 10.450 / 19.918 (150) | 10.420 / 19.934 (132) | L: latency_s, swap_free_latency_s |
| fairy-production | summarisation | 5.191 / 6.804 (50) | 5.163 / 6.804 (45) | L: latency_s, swap_free_latency_s |
| cloud | maths | 3.893 / 9.152 (150) | 3.877 / 8.976 (145) | C: latency_s, swap_free_latency_s |
| cloud | summarisation | 3.410 / 8.017 (50) | 3.410 / 7.449 (48) | C: latency_s, swap_free_latency_s |

| Configuration | Task | Request payload p50 / p95 bytes (n) | Response payload p50 / p95 bytes (n) | Source |
| --- | --- | --- | --- | --- |
| local-q8 | maths | 387.5 / 682.0 (150) | 22167.5 / 41814.0 (150) | L: request_payload_bytes, response_payload_bytes |
| local-q8 | summarisation | 1579.5 / 2088.0 (50) | 6940.0 / 11565.0 (50) | L: request_payload_bytes, response_payload_bytes |
| local-q6 | maths | 387.5 / 682.0 (150) | 21972.5 / 44991.0 (150) | L: request_payload_bytes, response_payload_bytes |
| local-q6 | summarisation | 1579.5 / 2088.0 (50) | 6854.0 / 11629.0 (50) | L: request_payload_bytes, response_payload_bytes |
| local-q4 | maths | 387.5 / 682.0 (150) | 21798.0 / 50532.0 (150) | L: request_payload_bytes, response_payload_bytes |
| local-q4 | summarisation | 1579.5 / 2088.0 (50) | 6725.0 / 12577.0 (50) | L: request_payload_bytes, response_payload_bytes |
| local-q3 | maths | 387.5 / 682.0 (150) | 20678.5 / 71547.0 (150) | L: request_payload_bytes, response_payload_bytes |
| local-q3 | summarisation | 1579.5 / 2088.0 (50) | 6138.5 / 12892.0 (50) | L: request_payload_bytes, response_payload_bytes |
| fairy-production | maths | 368.5 / 663.0 (150) | 22526.0 / 42219.0 (150) | L: request_payload_bytes, response_payload_bytes |
| fairy-production | summarisation | 1560.5 / 2069.0 (50) | 6772.5 / 12201.0 (50) | L: request_payload_bytes, response_payload_bytes |
| cloud | maths | 415.5 / 710.0 (150) | 4668.5 / 6755.0 (150) | C: request_payload_bytes, response_payload_bytes |
| cloud | summarisation | 1607.5 / 2116.0 (50) | 2298.5 / 5761.0 (50) | C: request_payload_bytes, response_payload_bytes |

| Configuration | Task | List-price equivalent USD p50 / p95 per call | Available / unavailable | Source |
| --- | --- | --- | --- | --- |
| local-q8 | maths | 0.000000000 / 0.000000000 | 150 / 0 | L: list_price_cost |
| local-q8 | summarisation | 0.000000000 / 0.000000000 | 50 / 0 | L: list_price_cost |
| local-q6 | maths | 0.000000000 / 0.000000000 | 150 / 0 | L: list_price_cost |
| local-q6 | summarisation | 0.000000000 / 0.000000000 | 50 / 0 | L: list_price_cost |
| local-q4 | maths | 0.000000000 / 0.000000000 | 150 / 0 | L: list_price_cost |
| local-q4 | summarisation | 0.000000000 / 0.000000000 | 50 / 0 | L: list_price_cost |
| local-q3 | maths | 0.000000000 / 0.000000000 | 150 / 0 | L: list_price_cost |
| local-q3 | summarisation | 0.000000000 / 0.000000000 | 50 / 0 | L: list_price_cost |
| fairy-production | maths | 0.000000000 / 0.000000000 | 150 / 0 | L: list_price_cost |
| fairy-production | summarisation | 0.000000000 / 0.000000000 | 50 / 0 | L: list_price_cost |
| cloud | maths | 0.001160625 / 0.002195250 | 150 / 0 | C: list_price_cost |
| cloud | summarisation | 0.000639750 / 0.002625750 | 50 / 0 | C: list_price_cost |

| Money / reliability scope | Existing observation | Source |
| --- | --- | --- |
| Local API money | USD 0 API charge; electricity and hardware are not priced as zero. | L: list_price_cost |
| Full cloud pass, including pilots/warm-ups | USD 0.23358825 known list-price equivalent; 203 completed slots; 18 failed HTTP attempts with unknown usage/cost. | S: runs[] |
| Retries | 16 cloud calls needed 17 automatic retries; one prior failed attempt stopped the pass. No local call failed to respond (1,015 completed slots). | S: runs[].retry_summary and collection |
| Provider billing | Pending matching provider export and VAT treatment; list prices exclude tax. | C: billing_reconciliation |
| Request payload scope | Serialized bodies/stream framing; excludes headers and transport overhead. | Original measurement definitions |

| Task | Registered step | Quality drop pp | Latency p50 / p95 saving % | Weight-byte saving % | Indistinguishable | Knee step | Calls per configuration | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| maths | local-q8 → local-q6 | -3.33 | 21.26 / 14.79 | 23.52 | yes | no | 150 | S: variance[] |
| maths | local-q6 → local-q4 | 3.33 | 22.09 / 16.95 | 30.76 | yes | no | 150 | S: variance[] |
| maths | local-q4 → local-q3 | 33.33 | -0.87 / -43.67 | 22.21 | no | yes | 150 | S: variance[] |
| summarisation | local-q8 → local-q6 | 0.90 | 6.68 / 15.35 | 23.52 | yes | no | 50 | S: variance[] |
| summarisation | local-q6 → local-q4 | 0.06 | 17.09 / 14.92 | 30.76 | yes | no | 50 | S: variance[] |
| summarisation | local-q4 → local-q3 | 6.61 | 6.12 / -6.65 | 22.21 | no | no | 50 | S: variance[] |
