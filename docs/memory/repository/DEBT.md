---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Technical Debt Register

| Debt | Priority now | Intended phase / trigger |
| --- | --- | --- |
| Stale top-level project status/roadmap headings | Medium documentation risk | Address through `docs/memory` now; reconcile old docs at a later docs cleanup. |
| Large `MainActivity.kt`, `emulator_manager.py`, `plugins/games.py` | Low during Phase A | Dedicated modularization after stable Phase B baseline, not opportunistically. |
| Sunshine/Moonlight scripts/integration | Deferred by design | Phase B. |
| Broad/cleartext prototype control-plane exposure and exported diagnostics | Security debt, not four-player blocker | Phase B / remote-access security hardening with threat model. |
| Windows-specific/ignored runtime dependencies | Expected prototype debt | Phase D/Linux/bootstrap work or earlier clean-machine requirement. |
| Minimal conventional CI | Medium before productization | Grow from deterministic probes after Phase A/B. |
| Repetitive `.gitignore` patterns | Low | Cleanup only with a dedicated repo-hygiene change. |
| Prototype UDP timing pathology | Deferred after deep evidence | Replay on representative Linux/network infrastructure; reopen earlier only if blocking. |
| Game Session banner latency | Low polish | Dedicated measured latency investigation only if prioritized. |
| Four-player support | Active feature gap | Current task before A9. |
