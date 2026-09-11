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

## Startup library reconciliation and native-stream catalog cleanup — 2026-09-11

Games metadata/art reconciliation is now a companion-start responsibility, but it
must not block service startup.

`GamesPlugin` launches a daemon reconciliation worker. The worker compares
discovered stable game IDs with `data/games/metadata.json`. A full existing
metadata update runs when the library changed, metadata is missing/invalid, or a
previous provider/artwork failure is old enough for the existing provider-cache
TTL retry window.

Rules:
- reuse `games.metadata_importer.run_metadata_update`;
- do not force provider-cache refresh on every start;
- download artwork for matched games;
- full reconciliation naturally removes stale metadata records for removed
  games;
- do not automatically populate cheats;
- do not automatically delete orphan artwork;
- metadata/provider work is background-only and failure must not stop the
  companion;
- write `logs/games/game_metadata_startup_reconcile.txt` and `.json` with
  count-only shareable startup status;
- invalidate the Games scan cache after a successful metadata update.

The old player-facing `games_native_stream` / `Native Streaming Alpha` catalog
node is removed. This does **not** remove native streaming. The
`native-stream-status`, `native-stream-start`, and `native-stream-stop` companion
actions and Android `NativeStreamActivity` production path remain intact.

## Startup reconciliation runtime validation — 2026-09-11

The startup metadata/art reconciliation path is runtime validated.

First changed-library startup:
- result `RECONCILED`;
- reason `library_changed`;
- 124 discovered games;
- 84 metadata entries before reconciliation;
- 4 incomplete entries before reconciliation;
- 124 games scanned and 124 matched;
- 0 ambiguous, unmatched, or provider-unavailable results;
- 39 artwork files downloaded;
- 80 artwork files reused from cache;
- 5 matched games had no usable artwork;
- Games catalog cache invalidated.

A subsequent startup returned `SKIPPED_CURRENT` with 124 discovered games and
124 metadata entries, confirming unchanged libraries do not trigger a provider
update.

Operator runtime validation also confirmed:
- `Native Streaming Alpha` is absent from the Games UI;
- newly added games display metadata/cover art where available;
- a normal game still has picture, process audio, and controller input.

The five missing artwork results are provider/artwork availability gaps, not a
startup-reconciliation failure.
