---
memory_schema: 1
as_of: 2026-11-03
---

# Technical Debt Register

Today's debt, from `docs/KNOWN_ISSUES.md`'s debt sections and
`evidence/DOCS_AUDIT_2026-11-02.md`. The 2026-09-11 register is in git
history.

| Debt | State | Source |
| --- | --- | --- |
| Android cleartext networking; exported diagnostic / probe activities; service logs that may carry requester information | Open, security / privacy | KNOWN_ISSUES "Security/privacy debt" |
| Companion authentication | Partly paid: session identity v2 with the media token is adopted (lines 6-7, G-A1; G3-S3's hardening in force). The unpaired legacy LAN path is the transition rule in `docs/REMOTE_TRUST.md` §5 | REMOTE_TRUST §5, §8 |
| Large central files: `MainActivity.kt` 15,938 lines, `games/emulator_manager.py` 8,687, `plugins/games.py` 4,526, `native_stream.py` 2,672 (`wc -l`, 2026-11-03) | Open, maintainability; refactor only with its own objective and regression boundary | KNOWN_ISSUES "Maintainability / test debt" |
| Minimal conventional CI: the suites are run by hand per task; the four `tools/` tests fail in a copy of the tree at every baseline | Open | KNOWN_ISSUES; `evidence/B28_REMOTE_UMBRELLA_2026-10-28.md` §2 |
| Dormant code behind default-off flags: B32, B34, B35 in the tree; B27 and B29 not in the confirmed APK; G-A8's loss guard prepared and never applied; G-A6 shelved | Open, by decision | audit §0 |
| Windows-only modules still in `companion/` (`native_wgc_bridge.py`, `process_audio/`, two C3 probes), selected by platform and failing closed on Linux | Low; the Windows stack is long out of the live path (the Linux hub since Phase D; the Windows scripts archived under `archive/windows-scripts/`). KNOWN_ISSUES' "Windows/Linux portability debt" section is stale on this | audit §1.8; `archive/memory/TOOLS_HISTORY_2026-11-02.md` |
| 62 historical `tools/probe_*` scripts beside the live tools | Low; `docs/memory/TOOLS.md` names the live ones | audit §2.2 |
| Legacy `memory_schema: 2` front matter in a few memory files | Low; normalized when rewritten (`MAINTENANCE.md`) | audit §1.8 |
| The synthetic UDP timing pathology | Paused (`M1`) | `MEMORY.md`, D-BASE |
| The launcher's NOW PLAYING banner does not reconcile when the companion is unreachable | Open, low (client UX) | KNOWN_ISSUES, 2026-09-20 |

Resolved items are removed rather than left as active debt.
