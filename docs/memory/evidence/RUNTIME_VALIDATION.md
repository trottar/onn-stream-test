---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Runtime Validation Ledger

This ledger records what is actually runtime validated. Configuration/support
alone is not validation. Newer specific evidence overrides older intermediate
failure states preserved elsewhere.

| Area | Status | Key runtime evidence |
| --- | --- | --- |
| A1 Controller/analog | COMPLETE / runtime validated | Digital/analog behavior, PS1 controller modes and multi-controller routing validated. |
| A2 Save/Load | COMPLETE / runtime validated | Slots, persistent state, integrity checks, RetroArch control path, graceful flush and prior-save preservation. |
| A3 Pause/Resume | COMPLETE / runtime validated | Frozen preview, stream stop/restart, emulator remains alive, controls remain available. |
| A4 Host coexistence/audio | COMPLETE / runtime validated | Process-specific game audio reaches TV, local duplicate suppressed, host remains usable, crash-safe restoration validated. |
| A5 Direct launch | COMPLETE / runtime validated | Companion launch/readiness goes directly to gameplay and fails closed when readiness fails. |
| A6 Metadata/art | COMPLETE / runtime validated | Stable IDs, catalog metadata/art and normal organization path exercised. |
| A7 Cheats | COMPLETE / runtime validated | Exact activation, isolated cheat-profile saves/states, normal namespaces protected. |
| A7 Mods | COMPLETE / runtime validated | Deterministic IPS-derived ROM path, visible mod, Save/Load/reopen, canonical ROM protected. |
| A8 input profiles | COMPLETE / runtime validated | Profile CRUD/assignment, P1-P4 capabilities, generated session binds, Android editor/copy UI, conflict validation and user mapping tests. |
| Four-player transport / ViGEm | COMPLETE / runtime validated | PHI1 v1 preserved; four slots/devices; exact P1->1 through P4->4 routing; neutral release/teardown. |
| Four-player physical Android assignment | COMPLETE / runtime validated | Four real controllers reached four distinct host slots with isolated presses/releases. |
| RetroArch ports 1-4 | COMPLETE / runtime validated | XInput selected; Xbox controllers configured on ports 1-4 with no startup fallback. |
| Four-player gameplay | COMPLETE / runtime validated | Crash Bash four-human Battle Mode; P1-P4 independently controlled intended players; clean teardown. |
| PS1 manual Multitap On/Off | COMPLETE / runtime validated | Port-1-only product rule validated with Crash Bash and CTR; Port 2 remains disabled. |
| A9 Phase A regression/checkpoint | COMPLETE / checkpointed | PS1/SNES exercised, 1P/2P/4P lifecycle and major Phase A features preserved. NES/Genesis had no local fixtures. |
| Phase B health/diagnostics | COMPLETE / runtime/manual validated | Health endpoint, client feedback, decoder/network classifier correction, event history, Diagnostics/Self-Test and support-bundle path validated. |
| Phase B retention | COMPLETE / runtime validated | Bounded/manual retention, protected-file behavior and blocker semantics validated. |
| Sunshine/Moonlight removal | COMPLETE / runtime validated | Production edge, repository artifacts and device package removed; focused native-only regression passed. |
| Native game streaming baseline | COMPLETE / runtime validated | WGC -> H.264 NVENC -> RTP UDP -> 8+1 XOR FEC -> Android hardware AVC; process audio/controller/lifecycle preserved. |
| C1 stream-parameter inventory | COMPLETE / diagnostic | `C1_INVENTORY_COMPLETE`; ownership/duplication captured with no inventory failures. |
| C1 explicit profile implementation | NOT STARTED / next technical work | Next classification is `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`. |

## Emulator-family coverage boundary

- **PS1:** extensive runtime coverage.
- **SNES:** runtime exercised.
- **NES:** configured/supported but no local A9 fixture; not runtime validated.
- **Genesis:** configured/supported but no local A9 fixture; not runtime validated.

Do not upgrade NES/Genesis status without representative fixture evidence.

## Current native reference

Reference stream behavior:

- 1280x720;
- 60 fps;
- 7000 kbps target;
- GOP 15;
- B-frames 0;
- FEC group size 8;
- RTP payload type 96;
- 1200-byte packet size;
- WGC capture of the managed game window;
- Android hardware AVC decode.

C1 must first reproduce this behavior through an explicit static profile before
adaptive behavior is introduced.

## Deferred transport evidence

The current Windows/network environment can show severe UDP timing
transformation/duplication outside normal application pacing. That investigation
is deferred until representative Linux/network infrastructure exists unless it
becomes a blocker first.

This does not invalidate the native baseline. Do not enlarge production buffers
or otherwise encode the current environment’s pathology as a product
requirement without representative evidence.

## Evidence integrity rule

Raw measurements outrank classifiers when they disagree.

A compile/build/install result is not runtime validation. A development patch
remains development-only until the requested runtime/E2E evidence passes.
