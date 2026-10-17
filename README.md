# CallCost

Measure the hidden energy and memory cost of one LLM call on a constrained laptop. CallCost is a Python CLI for installed LM Studio models and a Gemini reference, measured on one Apple M1 Pro Mac with 16 GB RAM. Energy comes first, then memory and swap, latency and money; quality constrains useful work. A local macOS recommendation web app is planned, not implemented.

| Initial configuration | Encoded weight GiB | Maths median energy J (available / 150) | Summary median energy J (available / 50) | Swap-active calls / 200 |
| --- | ---: | ---: | ---: | ---: |
| Qwen 8 bit | 8.861 | 263.42 (150/150) | 119.12 (50/50) | 147/200 |
| Qwen 6 bit | 6.777 | 316.88 (65/150) | 149.51 (21/50) | 158/200 |
| Qwen 4 bit | 4.692 | 213.47 (150/150) | 109.41 (50/50) | 51/200 |
| Qwen 3 bit | 3.650 | 231.61 (150/150) | 107.92 (50/50) | 22/200 |
| Fairy's production reference | 5.541 | 225.26 (150/150) | 112.74 (50/50) | 23/200 |
| Gemini 3.8 Flash | unavailable | unavailable (0/150) | unavailable (0/50) | 7/200 |

Initial results, 16 to 17 October 2026: 30 maths problems and ten Fairy-style prompts written for the benchmark (invented texts), five repeats. Summary scores remain human-scored and unchanged. The cloud swap row measures this Mac's activity, not server memory.

Energy is **estimate, whole-machine delta**, CPU + GPU + ANE, not per-process or cloud-server energy. Encoded weight GiB is not runtime peak memory. Q4 has the lowest observed median energy among quality-eligible locals for both tasks, but missing q6 energy prevents a definitive full-data recommendation. This app-rule check and GiB presentation are exploratory, not pre-registered. Maths has a registered 4→3-bit knee; summaries have no knee found. No real Fairy deployment decision has changed.

- [PLAN.md](PLAN.md): single current plan, scope, status, approvals and roadmap.
- [Results](results/README.md): full tables, source paths, coverage, limitations and figures.
- [Frozen pre-registration and amendments](docs/preregistration.md): original rules, preserved byte-for-byte.
- [Setup and CLI commands](docs/methodology.md#reproduction), [methodology](docs/methodology.md) and [prospective judge protocol](docs/judge-preregistration.md): measurement and future validation details.
- [History](docs/log.md): dated decisions and previous handoffs.

Use checkout source: `PYTHONPATH=src .venv/bin/python -m callcost --help`. Raw runs remain private and ignored. [MIT licence](LICENSE).
