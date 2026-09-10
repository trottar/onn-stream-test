---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Runtime Validation Ledger

| Area | Status | Key runtime evidence |
| --- | --- | --- |
| A1 Controller/analog | COMPLETE / runtime validated | Digital, analog, two ViGEm X360 devices, 2P behavior, PS1 controller modes. |
| A2 Save/Load | COMPLETE / runtime validated | Slots, persistent state, integrity/nonzero/hash checks, real RetroArch control path, graceful flush. |
| A3 Pause/Resume | COMPLETE / runtime validated | Frozen-frame pause, stream stop/restart, emulator remains alive, controls remain available. |
| A4 Host coexistence/audio | COMPLETE / runtime validated | Host remains usable; process audio reaches TV, local duplicate suppressed, crash-safe restoration validated. |
| A5 Direct launch | COMPLETE / runtime validated | Companion launch/readiness flow proceeds directly to gameplay and fails closed. |
| A6 Metadata/art | COMPLETE / runtime validated | Catalog, stable IDs, metadata/art, organization; transient post-reinstall art cache recovered. |
| A7 Cheats | COMPLETE / runtime validated | Exact cheat activation, isolated profile saves/states, normal namespace protected. |
| A7 Mods | COMPLETE / runtime validated | Deterministic IPS derived ROM, visible DKC mod, Save/Load/reopen, canonical ROM protected. |
| A8 Backend/adapter | COMPLETE / runtime validated | Profile CRUD/assignment, generated session binds, assignment-boundary probes, no XInput startup fallback. |
| A8 Android editor | COMPLETE / runtime validated | Xbox-only Current/Change UI, directional mapping, conflicts/unmapped validation, sync; user changed many games without issue. |
| Four-player base transport/ViGEm | COMPLETE / runtime validated | PHI1 v1/36-byte preserved; four XInput slots; exact synthetic P1->1 through P4->4; 120 packets, zero loss/rejected/bad; neutral release and clean teardown. |
| Four-player physical Android assignment | COMPLETE / runtime validated | Four real onn-side controllers reached four distinct XInput slots exactly 1->1 through 4->4; isolated A presses/releases were unambiguous, slots remained continuous, final state neutral. |
| Four-player RetroArch enumeration | COMPLETE / runtime validated | Fresh normal game log: xinput driver selected; Xbox 360 Controller configured in ports 1-4; no XInput startup fallback. |
| Four-player A8 P3/P4 profiles/editor | COMPLETE / runtime validated | Live schema 1; P1-P4 capabilities/profile keys; legacy P1/P2 normalization; explicit P3/P4 binds; four-port analog-D-pad settings; Android P1-P4 editor/copy UI; user synchronized all four custom mappings. |
| Post-four-player 1P regression | COMPLETE / runtime validated | Crash Bash PS1: P1 isolated on slot 1, gameplay normal, no takeover, xinput no fallback, clean normal End/Exit teardown. |
| Post-four-player 2P regression | COMPLETE / runtime validated | Crash Bash PS1: P1->slot 1, P2->slot 2, normal independent gameplay, no P3/P4 interference, xinput no fallback, clean End/Exit teardown. |
| Four-player gameplay regression | ACTIVE | Representative real 4P gameplay is next. Keep PrivyHub four-slot routing distinct from PS1 core/game multitap support. |
| A9 full regression | PENDING | Begins after four-player acceptance. |

Runtime validation outranks stale status headings in older documents.

## Four-player gameplay gate

- Host routing: COMPLETE / runtime validated in representative Crash Bash session.
- RetroArch ports 1-4: COMPLETE / runtime validated.
- Four-human-player exposure: NOT YET CONFIRMED. Crash Bash P3/P4 remained greyed out.
- Active hypothesis: Beetle PSX HW multitap/core-options session configuration absent.

## PS1 multitap audit

- Active Beetle PSX HW `.opt` discovered under runtime config.
- Port-1 multitap: disabled.
- Port-2 multitap: disabled.
- `emulator_manager.py`: no core-option/game-specific-option support.
- Live Crash Bash metadata response did not expose max-player count.

| PS1 multitap core-options/source-context | COMPLETE / diagnostic | Exact local source hashes and launch/config/controller-override context captured. Active Beetle `.opt` has both multitap ports disabled; no existing manager adapter. |
| PS1 game-specific multitap fix | DEVELOPMENT PATCH / runtime pending | Existing controller override store drives native `<game>.opt`; Crash Bash configured for Port-1 multitap. Must rerun representative 4P gameplay before A9. |

## Post-multitap runtime regression — 2026-09-10

`PHASE_A_4P_GAMEPLAY_NOT_CONFIRMED`: Crash Bash exposed four human players after the game-specific multitap patch, and RetroArch still enumerated Xbox ports 1-4 without XInput fallback. However, only physical P1 produced host XInput activity; P2-P4 produced none. The user separately observed only 2-3 charged controllers staying connected while the PrivyHub/game-stream session was active, with all four stable when it was off. This supersedes any claim that the multitap development patch is runtime-safe. Exact rollback test is ACTIVE.

## Multitap rollback comparison — 2026-09-10

After exact rollback, `ANDROID_FOUR_CONTROLLER_ASSIGNMENT_NOT_CONFIRMED`: slots 1-4 existed; P1->1, P2->2 and P3->3 were isolated and stable; P4 produced no captured input. Crash Bash P3/P4 were greyed out again. The controller-connectivity regression therefore persists without multitap and is not currently attributable to the game-specific core-option patch.

## Final four-player gameplay — 2026-09-10

`ANDROID_FOUR_CONTROLLER_ASSIGNMENT_CONFIRMED` with replacement controller: exact P1->1 through P4->4, clean releases, four-slot continuity, neutral final A state.

`PHASE_A_4P_GAMEPLAY_REGRESSION_CONFIRMED`: Crash Bash Battle Mode exposed four human players; P1-P4 each routed to slots 1-4 and independently controlled the intended player; no cross-control; RetroArch configured Xbox controllers on ports 1-4 through xinput with no fallback; normal End/Exit left companion inactive and removed session XInput slots. Representative 4P gameplay is closed.

## A9 first run — 2026-09-10

`PHASE_A_A9_EMULATOR_REGRESSION_NOT_CONFIRMED`. SNES, ordinary PS1 2P/lifecycle, cheat, mod, custom input-profile, teardown, final 4P evidence, HEAD and diff hygiene passed. NES and Genesis were reported `<unknown>` only at the probe's fresh-log identification check while the user marked their actual launch/gameplay/analog/coexistence/End behavior normal. CTR exposed a genuine remaining product gap: Players 3/4 remain greyed without a per-game multitap setting. See `A9_FIRST_RUN_2026-09-10.md`.

## PS1 multitap flag source/library audit — 2026-09-10

`PS1_MULTITAP_FLAG_SOURCE_CONTEXT_CAPTURED_NO_CANDIDATES`: exact current source hashes were captured and the companion catalog exposed 80 PS1 games, but zero had `max_players > 2`; CTR and Crash Bash were both missed. This invalidates metadata-driven automatic multitap for the current library. Manual On/Off production implementation is the next runtime gate.
