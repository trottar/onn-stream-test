# PrivyHub documentation

This directory contains the project’s architectural, operational, diagnostic and
roadmap documentation.

## Current authority

For current development state, use this order:

1. current local source and fresh runtime evidence;
2. `memory/evidence/`, `memory/decisions/`, `memory/architecture/` and other
   specific durable records;
3. `memory/CURRENT.md`, `memory/handoffs/CURRENT_HANDOFF.md`, and
   `memory/MEMORY.md`;
4. dated memory / patch history;
5. `memory/history/` superseded snapshots.

Older top-level documents are reference only when they conflict with newer
validated state.

## Main documents

- **ROADMAP.md** — authoritative Linux-first roadmap v3.
- **PROJECT_STATUS.md** — current architecture, completed phases and active work.
- **KNOWN_ISSUES.md** — unresolved/deferred issues and technical debt.
- **DIAGNOSTICS.md** — diagnostic inventory and repeatable transport tests.
- **A4_AUDIO_RECOVERY.md** — validated game-audio recovery/lifecycle details.
- **A8_INPUT_PROFILES.md** — controller-profile architecture and behavior.
- **investigations/2026-09-07-udp-transport.md** — detailed deferred UDP
  transport investigation.

Durable development memory lives under **memory/**. It is the cross-chat
continuation layer and includes current state, curated facts, decisions,
investigations, evidence, patch history, repository maps, roadmap status and
superseded history snapshots.

## Current development position

- Phase A Games/emulator subsystem: complete.
- Phase B diagnostics + clean native baseline: complete.
- Phase C adaptive native streaming: active.
- C1 stream-parameter inventory: complete.
- Next technical step after the docs cleanup checkpoint:
  `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`.

## Documentation rule

When an experiment is deliberately deferred, record:

1. the symptom;
2. what was actually measured;
3. what was ruled out;
4. what remains unresolved;
5. the condition that should cause the investigation to resume;
6. the diagnostic tools needed to resume without repeating old work.

Do not record private network addresses, MAC addresses, device GUIDs,
credentials, ROM filenames, or other environment-specific secrets in shareable
project documentation.
