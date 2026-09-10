---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Current Development State

## Checkpoint

- Branch: `main`
- Baseline: `25e9a1492a684dbaeebede90ea7ca4abd3eab1fb`
- Commit message: `Checkpoint: complete A8 input mapping and profiles`
- Meaning: immutable pre-four-player baseline

## Status

Phase A is nearly complete. A1-A8 are complete/runtime validated. The four-player transport/device chain is now runtime validated end-to-end through RetroArch enumeration: four ViGEm/XInput slots, real Android P1-P4 assignment, and RetroArch ports 1-4 all passed with PHI1 v1 unchanged.

The P3/P4 extension of the existing A8 named gameplay-profile/editor layer is now runtime validated. The live schema remains 1, legacy P1/P2 profiles normalize safely to four players, P3/P4 RetroArch binds generate correctly, and the onn editor exposes/copies mappings across Players 1-4.

The 1-player regression is now runtime validated after the four-player extension: P1 remained isolated on slot 1, gameplay stayed normal, XInput did not fall back, and normal End/Exit removed the session controller slots.

The 2-player regression is now runtime validated after the four-player extension: P1 remained isolated on slot 1, P2 on slot 2, P3/P4 did not interfere, XInput did not fall back, and normal End/Exit removed all session controller slots.

Representative four-player gameplay is now COMPLETE/runtime validated. After re-enabling game-specific Beetle PSX HW Port-1 multitap and substituting a different physical controller, the real Android assignment probe again confirmed exact P1-P4 -> XInput 1-4 routing. The final Crash Bash Battle Mode probe then confirmed four human players, independent P1-P4 gameplay, RetroArch ports 1-4 through xinput without fallback, no cross-control, and clean End/Exit teardown.

The earlier physical-controller dropout is not classified as a PrivyHub multitap regression: it persisted once after exact multitap rollback and did not reproduce with the replacement controller. Treat it as a controller-specific/pairing/transient Bluetooth observation unless representative hardware reproduces it.

A9 full emulator regression/checkpoint is ACTIVE.
No known active regression requires reopening A4 audio, UDP smear, A6 artwork, or the validated P1/P2 A8 editor behavior.

## Current four-player state

Validated lower layers:

- PHI1 remains v1 and 36 bytes per player packet.
- Windows creates four persistent ViGEm VX360 devices before RetroArch launch.
- Synthetic P1-P4 routing is exact with zero packet errors in the base probe.
- Four real onn-side controllers mapped exactly to host XInput slots 1-4.
- Fresh RetroArch startup configured Xbox 360 Controller in ports 1-4 with no XInput fallback.

The A8 P3/P4 development patch keeps input-profile schema 1. Existing P1/P2 profiles remain valid; normalization adds empty P3/P4 mappings, whose semantics remain RetroArch's validated default autoconfiguration. New/reset profiles can carry complete mappings for all four players. The Android editor derives its player list from companion capabilities rather than hard-coding two players.

## Four-player acceptance sequence

1. Exact source/diagnostic audit for two-player assumptions: COMPLETE.
2. Four persistent ViGEm X360 devices before RetroArch: COMPLETE / runtime validated.
3. Synthetic P1->1, P2->2, P3->3, P4->4 routing: COMPLETE / runtime validated.
4. Real Android controller assignment: COMPLETE / runtime validated.
5. RetroArch ports/devices 1-4: COMPLETE / runtime validated.
6. P3/P4 A8 backend/editor/session-remap extension: COMPLETE / runtime validated.
7. 1-player regression: COMPLETE / runtime validated.
8. 2-player regression: COMPLETE / runtime validated.
9. Suitable 4-player gameplay regression: COMPLETE / runtime validated, including PS1 multitap and independent P1-P4 gameplay.
10. A9 full emulator regression/checkpoint: ACTIVE; close Phase A after runtime pass + repository checkpoint.

## 2026-09-10 PS1 multitap audit update

Exact-local evidence found Beetle PSX HW core options in the runtime config directory with both multitap ports explicitly disabled. The current emulator manager has no core-option/game-specific-option handling. The active next step is a source-context audit around game records, controller overrides, session config, and launch; lower controller layers remain closed.

## 2026-09-10 PS1 multitap production patch

Exact post-A8 source context is captured. Development patch `privyhub_phase_a_ps1_multitap_game_override_01_2026-09-10` adds a generic per-game `ps1_multitap` override to the existing controller override store. It preserves existing core/game option settings by deriving the native `<game>.opt` from the current game-specific file when present, otherwise from the active Beetle core options file, and changes only the two Beetle multitap keys. Crash Bash is configured for Port-1 multitap for the representative 4P validation. Production status remains development-only until the four-player gameplay probe passes.

## 2026-09-10 post-multitap rollback test

The post-patch Crash Bash run exposed four human players, proving the game-specific multitap setting took effect, but only P1 produced host input and the user observed controller connectivity degradation only while PrivyHub/game streaming was active. All controllers are charged. Restore the exact pre-multitap production bytes from the patch backup, remove the generated Crash Bash game-specific `.opt`, restart the companion, and rerun the four-controller Android assignment probe during a normal game session. If four-controller connectivity returns, treat the multitap patch as the regression trigger and redesign it before retrying gameplay.

## 2026-09-10 rollback comparison result

The exact pre-multitap rollback did not restore the previously validated four-controller physical assignment: P1->1, P2->2 and P3->3 were clean, but P4 produced no host input. Crash Bash Players 3/4 were greyed out again, confirming the rollback removed multitap. Therefore the first multitap implementation is no longer the leading cause of controller dropout. Re-enable the same validated game-specific Port-1 multitap behavior for Crash Bash and continue controller-stability testing with a different physical controller. Keep the Android/Bluetooth/session connectivity issue ACTIVE and separate from the PS1 core-option path.

## 2026-09-10 final four-player closure

Replacement-controller assignment returned `ANDROID_FOUR_CONTROLLER_ASSIGNMENT_CONFIRMED`. Final Crash Bash Battle Mode returned `PHASE_A_4P_GAMEPLAY_REGRESSION_CONFIRMED` with exact P1-P4 routing, four-player exposure, independent gameplay, no cross-control, ports 1-4 on xinput, and clean teardown. Four-player development is closed. Next: A9 emulator-focused regression and repository checkpoint.

## 2026-09-10 A9 installer v1 preflight correction

`privyhub_phase_a_a9_regression_probe_01_2026-09-10` correctly returned **FAILED BEFORE MODIFICATION** before installing anything because its runtime-evidence preflight compared exact reconstructed chat-log bytes to the authoritative Windows log bytes. The visible successful measurements were unchanged; the gate was too strict about byte representation. A9 v2 replaces that check with semantic validation of the required classifications and raw measurements while leaving the A9 runtime probe itself unchanged.

## 2026-09-10 A9 first run / PS1 multitap product gap

A9 first runtime pass was largely healthy but not classifiable as complete. NES and Genesis were user-validated as normal while the probe failed to identify their fresh logs (`<unknown>`), so those are probe-detection misses. More importantly, CTR Battle still greyed Players 3/4 because the validated PS1 multitap implementation was intentionally game-specific to Crash Bash. Product decision: support at most four local players and expose only a per-game PS1 Multitap On/Off flag; On always means Port-1 multitap enabled and Port-2 forced disabled. A checker may recommend On from existing local-player metadata but must never auto-enable. Exact current source/context plus live PS1 candidate metadata audit is ACTIVE before the production UI/API patch.

## PS1 Multitap On/Off production implementation

The source/library audit returned `PS1_MULTITAP_FLAG_SOURCE_CONTEXT_CAPTURED_NO_CANDIDATES`: 80 PS1 games were visible but neither CTR nor Crash Bash had `max_players > 2`. Automatic/recommended multitap based on current metadata is therefore deferred. The active production change is a manual PS1 `Multitap: On/Off` option. On means Beetle Port 1 enabled; Port 2 is forced disabled. Existing Crash Bash behavior is preserved. After install/build, enable Multitap for CTR and runtime-validate that Players 3/4 become available without regressing P1-P4 routing.

## Persistent wireless ADB build/install failure

The PS1 Multitap On/Off production source installed successfully, but the subsequent Android build/install workflow stopped at `tools/build_install_onn.ps1` step `[2/4] Finding physical ONN ADB target` with `No online ADB devices found`. This is a persistent tooling defect rather than a multitap runtime result. The historical build script only checks `adb devices` and aborts when the paired wireless target is not already online; it has no mDNS/server-health/reconnect recovery. A diagnostic-only wireless ADB recovery audit is ACTIVE before patching the build tool. No network addresses are requested or recorded.

## 2026-09-10 ADB recovery audit v1 diagnostic defect

The first ADB recovery probe failed before measurement because its Python
`local.properties` parser double-escaped the `sdk.dir` regex. This is a
diagnostic-tool defect, not evidence that ADB is absent: the existing
PowerShell build/install tool had already found ADB before failing at the
no-online-device gate. Corrected audit v2 is the active next step; it replaces
only the diagnostic probe and leaves production/ADB pairing untouched.

## Persistent wireless ADB recovery production patch

The corrected audit remained `ADB_TLS_CONNECT_SERVICE_NOT_DISCOVERED` after a
PC-side ADB server restart: ADB 37.0.1, mDNS enabled via LIBADBMDNS, zero
TLS-connect services, and zero transports while the ONN still lists this PC as
paired.

`tools/build_install_onn.ps1` now owns bounded recovery: private last-known
target, current online transport, mDNS, offline reconnect, one server restart,
then one user-assisted Wireless debugging Off/On retry without re-pairing.
Successful targets are cached only under current-user LocalAppData and are never
printed or written to repository logs.

Next: runtime-validate the normal build/install command, then resume CTR
Multitap On validation.

## Wireless ADB recovery runtime validated

Post-patch audit returned `ADB_TARGET_ALREADY_ONLINE`. The patched build/install
tool no longer contains the immediate no-online-device failure path, exposes
mDNS/reconnect recovery, and the host measured one TLS-connect service plus one
online transport with zero offline/unauthorized transports. Mark the persistent
ADB tooling fix COMPLETE/runtime validated. Resume CTR Multitap On validation.

## PS1 Multitap On/Off runtime validated

CTR runtime probe returned `PS1_MULTITAP_ONOFF_CTR_CONFIRMED`: per-game `port1`
override, Port 1 enabled, Port 2 disabled, XInput slots 1-4 live, Players 3/4
available, and four independent controllers. Mark the manual PS1 Multitap On/Off
product gap COMPLETE/runtime validated.

A9 is now the only Phase A gate. Its first full run passed every substantive
stage except NES/Genesis machine identification; both games were user-confirmed
normal but the probe status lookup returned `<unknown>`. Install the corrected
A9 finish probe and rerun only NES + Genesis identification with fresh-log
fallback, then perform a fresh repository audit.

## A9 coverage correction — no NES/Genesis fixtures installed

User clarification established that the NES and Genesis prompts in both A9 runs
were answered without actual games being launched because no local NES or
Genesis game fixtures are currently installed. Those answers are invalid as
runtime evidence and must not be counted as either pass or failure.

A9 acceptance is corrected to be coverage-aware:
- systems with installed games must be runtime exercised;
- supported systems with zero local games are recorded
  `SKIPPED_NO_LOCAL_FIXTURE`;
- skipped systems are not claimed runtime validated;
- SNES/PS1 and the rest of the already-passed A9 matrix remain valid;
- NES/Genesis runtime coverage remains pending until games are actually added.

The corrected finish probe first queries library counts and only prompts for a
real launch when a fixture exists.

## Phase A emulator subsystem checkpoint ready

A9 coverage-aware finalization returned
`PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS`.

Validated available-library state:
- prior substantive A9 stages preserved with zero missing required lines;
- CTR Multitap On/Off evidence preserved and runtime validated;
- repository HEAD remained the immutable A8 baseline before checkpoint;
- `git diff --check` clean;
- current library contains zero NES games and zero Genesis games.

NES and Genesis are explicitly `SKIPPED_NO_LOCAL_FIXTURE` and remain not runtime
validated. This is a declared coverage gap, not a failure or a pass.

Phase A emulator work is ready for the repository checkpoint. Repository policy:
curated durable memory is committed, live raw evidence remains local/ignored, and
a sanitized compressed evidence snapshot plus manifest is committed at major
checkpoints.

After the checkpoint push, advance to the next roadmap phase. Reopen Phase A
only for a regression or to close NES/Genesis runtime coverage when real content
is added.
