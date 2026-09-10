---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Games Architecture

RetroArch is the managed emulator frontend with project-owned config/save/state/system storage. Current systems use FCEUmm, bsnes, BlastEm, and Beetle PSX HW.

The Games subsystem now includes controller/analog support, Save/Load slots and integrity checks, pause/resume with frozen preview, host coexistence, direct launch, metadata/art, cheat profiles, deterministic mod profiles, and named input profiles.

Cheat and mod profiles use isolated save/state namespaces. Canonical ROMs and normal save/state namespaces are protected. Deterministic IPS handling creates and hashes a derived ROM without modifying the canonical source.

Game lifecycle controls reuse proven endpoints/hotkeys rather than inventing parallel mechanisms. If readiness/preflight fails, the system should fail closed rather than blindly proceeding.

## PS1 core-option boundary

Beetle PSX HW core options are persisted in the RetroArch runtime config tree, not the PrivyHub managed data config. Both multitap options are currently disabled. PrivyHub has no existing core-option session adapter. Four-player host routing is already validated; only PS1 core/game topology remains active.

## Game-specific emulator accessories

The existing project-local controller override store is also the control plane for game-specific PS1 accessory topology. This avoids a second settings database. The first supported field is `ps1_multitap`; it is consumed only for PS1/Beetle PSX HW launches and is validated fail-closed. RetroArch's native content-specific `.opt` mechanism remains the storage/application layer so unrelated core settings are preserved.

## PS1 multitap rollback test, 2026-09-10

Crash Bash exposed four human player slots after the game-specific Port-1 multitap patch, confirming that the Beetle game-specific option reached the game layer. The same run suffered a new physical-controller connectivity/input regression. The development patch is therefore rolled back to its exact predecessor for causal isolation before any revised multitap implementation. The generated Crash Bash-specific `.opt` is removed during rollback so the test returns to the audited pre-patch runtime state.

## Multitap re-enable after rollback comparison

Rollback returned Crash Bash to the expected two-player-visible state (P3/P4 greyed out) but did not restore the fourth physical controller. The game-specific Port-1 multitap implementation is therefore re-enabled unchanged for further representative testing; the physical-controller connectivity issue is tracked separately.

## Final PS1 multitap acceptance, 2026-09-10

The game-specific Beetle PSX HW Port-1 multitap implementation is runtime validated with Crash Bash Battle Mode. It changes the guest controller topology only for the configured game, exposes all four human players, preserves four independent PrivyHub controller routes, and leaves normal End/Exit teardown clean. Ordinary PS1 topology remains a required A9 regression check using a non-Crash-Bash title.

## PS1 multitap product control refinement

The accessory control is intentionally limited to four-player topology. User-facing state is `Multitap: On/Off`; On means Port 1 enabled and Port 2 forced disabled. The same project-local per-game controller override record stores this accessory flag alongside `controller_profile`. Existing metadata (`max_players` plus provenance) can drive an advisory recommendation, but never automatic activation.

## PS1 Multitap On/Off control

The existing game-specific Beetle core-options adapter remains the execution mechanism. The user-facing/API abstraction is reduced to a Boolean per-game control. Off keeps the title on normal PS1 topology; if explicitly selected after On, PrivyHub writes that title's content-specific `.opt` with both multitap ports disabled. On enables Port 1 only and forces Port 2 disabled.

The per-game controller override record may contain both `controller_profile` and `ps1_multitap`; setters must preserve unrelated fields.

The metadata checker is deferred rather than authoritative. The 2026-09-10 local audit found no >2-player PS1 metadata candidates even for known four-player titles, so no automatic enablement is permitted.
