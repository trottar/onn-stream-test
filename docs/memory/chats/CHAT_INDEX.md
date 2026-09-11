---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Project Chat Index

This is a distilled navigation index of major project-chat themes. It is not a
raw transcript archive and is not authoritative over current local source or
durable evidence.

| Period | Theme | Durable outcome |
| --- | --- | --- |
| 2026-08-25 | Smart-home infrastructure | Established isolated IoT-network direction, inexpensive onn client and local-first/no-mandatory-cloud philosophy. |
| 2026-08-26 | Architecture/portability | Control on 8765, media on 8000, dynamic media sources, future Linux/storage/server direction. |
| 2026-09-02 | Companion/network troubleshooting | Reinforced privacy rule: never ask for IPs; prefer narrow diagnostics. |
| 2026-09-04 | TV/IPTV maturity | TV catalog/EPG/provider UX became a stable subsystem; remaining product polish moved to later media work. |
| 2026-09-05 to 09-07 | Native streaming / transport | WGC/NVENC/audio/controller baseline established; bidirectional UDP pathology isolated and deferred. |
| 2026-09-08 to 09-09 | Phase A features | Save/Load, pause, host coexistence/audio lifecycle, direct launch, metadata/art, cheats and mods completed. |
| 2026-09-09 to 09-10 | A8 controller profiles | Backend/session/editor work validated and extended to P1-P4. |
| 2026-09-10 | Four-player + PS1 multitap | Four real controllers, RetroArch ports 1-4, Crash Bash/CTR Port-1-only Multitap On/Off and Phase A checkpoint validated. |
| 2026-09-10 to 09-11 | Phase B | Health/resource model, classifier corrections, Diagnostics/Self-Test, support bundle, retention, Sunshine/Moonlight removal, native-only regression and clean checkpoint. |
| 2026-09-11 | Roadmap v3 | Linux-first D-I roadmap, HP EliteDesk Linux reference, PS1-and-below Phase F sizing, user-content import and privacy-aware optional AI direction. |
| 2026-09-11 | C1 inventory | Explicit stream-parameter ownership/duplication captured; `C1_INVENTORY_COMPLETE`; schema design next. |
| 2026-09-11 | Durable-memory cleanup | Current-state alignment, curated MEMORY/AGENTS, deep-history snapshots, unique decision IDs and current-only investigations. |

## Chat-derived rules

Recurring high-value rules:

- one narrow hypothesis -> one targeted probe -> fresh evidence -> one coherent
  patch;
- current local source and fresh runtime measurements outrank stale summaries;
- raw measurements outrank classifiers;
- deterministic generated code is validated before the user runs it;
- installation and checkpoint/push are separate validation stages;
- checkpoint scope uses an explicit allowlist, never broad `git add .`;
- never ask for or expose network addresses in shareable diagnostics;
- preserve stable video/audio/controller/lifecycle paths for unrelated work.

Chats are navigation/context. Curated durable memory and specific evidence are
the continuation authority.
