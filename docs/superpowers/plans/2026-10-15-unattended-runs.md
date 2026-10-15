# Unattended runs implementation plan

**Goal:** Validate memory attribution, record swap activity and make full runs recoverable from Terminal.

**Architecture:** Keep the existing sequential runner and provider APIs. Add physical-footprint sampling alongside RSS, durable JSON call checkpoints as the source for CSV recovery, and a Terminal launcher that owns preflight, sudo keepalive, caffeinate, logging and notifications. Terminal remains open; Codex can quit.

**Spec:** Andrii's 15 October 2026 request in this conversation.

## Constraints

Five measured repeats for full runs. Smoke mode uses only one held-out call per configuration and cannot count as benchmark evidence. No automatic Git commits of results. No Fairy code changes. No em dashes in documentation. Unknown swap activity excludes a call from knee analysis.

## Tasks

- [ ] Memory and swap: test counter parsing and contemporaneous footprint sums, implement the SDK-defined libproc ABI, run four short validation pilots, record findings and commit the dated README amendment before any benchmark data.
- [ ] Checkpoints and resume: test interrupted streams and crash windows, save each attempt atomically, rebuild CSV from checkpoints, skip completed schedule slots, refuse changed inputs/software and concurrent writers, maintain live status.
- [ ] Terminal launcher: test preflight failures before model loading, check credentials/charger/model inventory/RAM/disk, record clean-state facts, authenticate sudo once with noninteractive keepalive, use caffeinate and full logging, maintain LATEST and notify completion/failure.
- [ ] Reporting and documentation: report all successful calls and swap exclusions separately, preserve first-appearance/repeat strata, document memory and resume workflow.
- [ ] Verification: run tests/lint, live five-local-model smoke with a deliberate interruption and resume, verify no completed slot repeats. Cloud smoke requires a configured model, prices and environment key. Review and push small commits.

## Review focus

Crash between checkpoint and CSV write; signal during streaming or model loading; stale status after SIGKILL; two resume processes; changed files on resume; missing swap counters; no sudo credentials; leftover owned model; an unrelated loaded model; missing cloud inputs. Preflight thresholds apply before loading, not to the free RAM left after an 8-bit model has loaded.
