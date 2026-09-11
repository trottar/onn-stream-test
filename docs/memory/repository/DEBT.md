---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Technical Debt Register

| Debt | Priority now | Intended phase / trigger |
| --- | --- | --- |
| Windows-specific native server/capture/audio/input stack | Expected prototype debt | Phase E Linux functional migration |
| Representative Linux resource/transport sizing not yet measured | Planned | Phase F after Linux baseline |
| Prototype UDP timing/duplication pathology | Deferred after deep evidence | Replay on representative Linux/network infrastructure; reopen earlier only if blocking |
| Android cleartext/exported diagnostics and companion exposure without mature auth | Security/privacy debt | Dedicated threat-model/auth/encryption/privacy work |
| WGC/FFmpeg/process-audio clean-machine bootstrap not fully represented | Portability/reproducibility debt | Phase E or earlier clean-machine requirement |
| Large `MainActivity.kt`, `emulator_manager.py`, `plugins/games.py` | Maintainability debt | Dedicated modularization after a stable regression boundary |
| Stream-profile parameters duplicated across Windows/Android paths | Active architecture debt | C1 explicit stream profiles |
| Minimal conventional CI | Medium before broader productization | Grow from deterministic probes/runtime regression as platforms expand |
| Repetitive/legacy repository-hygiene details | Low | Dedicated repo-hygiene change only |
| Remaining Live TV/EPG/guide identity and UX work | Planned product debt | Phase D |
| VOD recursive artwork/metadata cache polish | Planned product debt | Phase D |
| Game Session banner latency | Low polish | Measure first if prioritized |

Resolved items are removed from this live debt register rather than left as
active debt. Historical four-player, `companion/games` tracking and
Sunshine/Moonlight cleanup work remains in dated/deep history.
