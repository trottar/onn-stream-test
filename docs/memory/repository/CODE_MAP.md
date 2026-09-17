---
memory_schema: 2
as_of: 2026-09-17
---

# Repository Code Map

## Root

- `PrivyHub/` — Android TV application.
- `companion/` — companion control/media/Games/native-stream implementation.
- `scripts/` — setup/start and supporting helpers.
- `tools/` — build/install helpers, diagnostics, audits, and targeted probes.
- `docs/` — feature documentation, roadmap, investigations, and durable memory.
- operational media/game content, logs, archives, runtimes, and generated build
  output remain outside normal source tracking.

## Android

`MainActivity.kt` still owns substantial application orchestration.

TV-specific state and guide behavior are split across the TV repository/database,
EPG repository/database, TV-state sync client, and MainActivity UI/actions.

Avoid broad MainActivity refactoring while D5 behavior is still being closed.

## Companion

Important current seams include:

- `companion/privyhub_service.py` — HTTP service and plugin lifecycle;
- `companion/plugins/epg.py` — Linux EPG acquisition/cache/background warmer;
- `companion/plugins/tv_state.py` — durable Linux TV user-state authority;
- `companion/plugins/games.py` and `companion/games/` — Games/runtime stack;
- `companion/range_server.py` — media byte-range serving.

## Durable memory

`docs/memory/` is the persistent development bridge:

- `CURRENT.md` — authoritative active bootstrap;
- `MEMORY.md` — durable knowledge;
- `MAINTENANCE.md` — maintenance policy;
- `handoffs/CURRENT_HANDOFF.md` — handoff-only note;
- `architecture/`, `decisions/`, `evidence/`, `investigations/`, `patches/`,
  `repository/`, `roadmap/` — canonical specific records;
- dated files and `history/` — chronology/superseded reference.

Startup should retrieve specific records as needed rather than bulk-reading the
whole hierarchy.
