---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Current Handoff

Continue PrivyHub / Safe IoT from baseline commit `25e9a1492a684dbaeebede90ea7ca4abd3eab1fb` on `main`, treating `L:\Projects\onn-stream-test` as authoritative between checkpoints. Never ask for IP addresses. Preserve stable video/audio/controller/meta paths. Use one narrow hypothesis -> targeted diagnostic -> fresh evidence -> one coherent patch.

Phase A A1-A8 are complete/runtime validated. The four-player extension precedes A9.

Four-player lower-layer runtime evidence is now complete:

- exact-local source audit: PHI1 v1/36-byte reusable;
- four ViGEm/XInput slots and synthetic P1-P4 routing: passed;
- four real onn-side controllers -> host slots 1-4: passed;
- fresh RetroArch startup -> Xbox ports 1-4 with xinput and no fallback: passed.

The A8 P3/P4 profile/editor extension is now runtime validated. Live schema 1 reports `player1`-`player4`; legacy P1/P2 profiles normalize safely to four; generated P3/P4 session binds are present; Android exposes Player 1-4 editors plus copy-from-another-player; the user successfully synchronized custom mappings across all four players.

The post-extension 1P regression is now runtime validated: P1 stayed on slot 1, gameplay was normal, xinput had no fallback, and normal End/Exit removed all four session slots.

The post-extension 2P regression is now runtime validated: P1/P2 stayed isolated on slots 1/2, gameplay was normal, P3/P4 did not interfere, xinput had no fallback, and normal End/Exit removed all session slots.

Next evidence is representative 4P gameplay via `tools/probe_phase_a_4p_gameplay.py`. Use Crash Bash Battle Mode with four controllers. If all four host routes are clean but gameplay exposes fewer than four players, investigate PS1 core multitap rather than reopening PHI1/ViGEm. A9 begins after real 4P gameplay passes.

Closed/deferred work stays closed absent new evidence: A4 audio/lifecycle, Prototype-1 UDP pathology (deferred), A6 artwork transient, and original P1/P2 A8 mapping/editor.

Every meaningful ZIP must update affected `docs/memory` files and set `durable_memory_updated: true`.

## 2026-09-10 4P gameplay handoff update

Representative Crash Bash gameplay proved P1-P4 host routing and RetroArch ports 1-4, but Players 3/4 remained greyed out. The probe found no explicit Beetle PSX HW multitap setting under `data/games/retroarch`. Next: inspect exact current source hashes, RetroArch core-option storage, latest log option paths, and Crash Bash `max_players` metadata. Do not modify PHI1/ViGEm/A8 unless new evidence contradicts current runtime proof.

## PS1 multitap audit result

Core-option storage is now known: the active nightly uses `runtime/emulators/retroarch-nightly-20260907/config/Beetle PSX HW/Beetle PSX HW.opt`, with both multitaps disabled. Next run the exact source-context audit and then patch only the PS1 session/game topology layer.

## Latest boundary

Exact PS1 core-option storage and post-A8 source context are captured. The active production patch reuses `controller_overrides.json` with `ps1_multitap`, writes a native content-specific Beetle `.opt` while preserving all unrelated core options, and enables Port-1 multitap for Crash Bash only. Do not reopen PHI1/ViGEm/Android/A8. After install/restart, rerun `tools/probe_phase_a_4p_gameplay.py`; if it returns `PHASE_A_4P_GAMEPLAY_REGRESSION_CONFIRMED`, proceed directly to A9.

## Latest regression / immediate next step

The first PS1 game-specific multitap development patch made Crash Bash expose Players 3 and 4, but the next 4P probe had only P1 physical input while all four host slots/RetroArch ports remained present. User reports all controllers charged and all four remain connected with the game/server session off, but only 2-3 remain connected while it is active. Treat the last patch as causally suspect. Exact rollback package `privyhub_phase_a_ps1_multitap_rollback_test_01_2026-09-10` restores the patch backup bytes and removes the generated Crash Bash `.opt`. After rollback, restart companion, launch a normal game, and rerun `tools/probe_four_player_android_assignment.py`.

## Latest comparison / next test

Rollback removed multitap but did not recover P4 physical input. P1-P3 map correctly; P4 is absent. Reapply the unchanged game-specific Crash Bash Port-1 multitap implementation, restart companion, use a different physical remote for the missing slot, then rerun the real four-controller assignment probe during the active game session before attempting the full 4P gameplay probe.

## Final four-player closure / A9 handoff

Four-player support is COMPLETE/runtime validated. Replacement-controller assignment passed exact P1-P4 mapping, and the final Crash Bash Battle Mode probe passed four-player exposure, independent gameplay, no cross-control, ports 1-4 xinput, and clean teardown. Keep the game-specific PS1 Port-1 multitap implementation. The prior dropout is a controller-specific/pairing/transient observation, not an active software regression. Immediate next step: run the A9 emulator-focused regression probe, inspect its repository-audit section, then create the clean Phase A checkpoint commit/push.

## 2026-09-10 A9 installer v1 preflight correction

`privyhub_phase_a_a9_regression_probe_01_2026-09-10` correctly returned **FAILED BEFORE MODIFICATION** before installing anything because its runtime-evidence preflight compared exact reconstructed chat-log bytes to the authoritative Windows log bytes. The visible successful measurements were unchanged; the gate was too strict about byte representation. A9 v2 replaces that check with semantic validation of the required classifications and raw measurements while leaving the A9 runtime probe itself unchanged.

## Immediate handoff: PS1 multitap flag generalization

A9 first run found CTR lacks four-player exposure because only Crash Bash carries the current game-specific Port-1 multitap override. User decision: max four players; no Port-2/Both product option. Implement per-game `Multitap: On/Off` beside the existing PS1 Controller option, preserve controller profile fields, force Port 2 disabled, and show an advisory recommendation when metadata says more than two players. Do not auto-enable. Before patching, inspect exact current post-A8/post-multitap source contexts and actual PS1 candidate metadata. NES/Genesis `<unknown>` are separate A9 probe-detection misses.

## PS1 multitap flag implementation

Latest audit: 80 PS1 games, zero metadata candidates; CTR and Crash Bash both missed. Implement manual per-game Multitap On/Off only. On = Beetle Port 1, Port 2 forced disabled. Existing Crash Bash `port1` override is compatible. Patch changes emulator_manager, Games API, and Android Options UI; controller transport/video/audio remain untouched. Next runtime test: enable CTR Multitap On, launch CTR Battle, confirm P3/P4 available and independent, and return `logs/games/ps1_multitap_onoff_runtime.txt`.

## Immediate tooling blocker: wireless ADB recovery

The PS1 Multitap On/Off source patch reached the Android build/install step, but `tools/build_install_onn.ps1` stopped with `No online ADB devices found`. Treat this as a separate persistent toolchain bug. Run `tools/probe_adb_wireless_recovery.py`; inspect `logs/android/adb_wireless_recovery_probe.txt`; then patch the build script based on exact local hash/context. Never ask for or log the onn's network address.

## ADB recovery audit correction

Audit v1 probe itself failed before measurement because it could not parse
`sdk.dir`; no log was created and no ADB/device state changed. Audit v2
replaces only `tools/probe_adb_wireless_recovery.py` with a non-regex
local.properties parser and keeps the persistent build/install tooling issue
ACTIVE. Rerun v2 while the ONN is still not appearing in `adb devices`.

## Wireless ADB persistent fix

Patch changes only `tools/build_install_onn.ps1` plus durable memory. It adds
private LocalAppData target caching and bounded recovery. First successful run
seeds the cache. If the ONN currently advertises no service, the script prompts
once to toggle Wireless debugging Off/On; it never requests an address or
re-pairing. After build/install succeeds, continue CTR Multitap On validation.

## ADB recovery closed

Persistent wireless ADB recovery is runtime validated. Post-patch classification:
`ADB_TARGET_ALREADY_ONLINE`; one TLS-connect service and one online transport,
no offline/unauthorized transports. Do not spend more Phase A time on ADB unless
the patched cached-target/recovery path reproduces a failure. Immediate next step:
CTR -> Options -> Multitap -> On, Battle mode, then run
`tools/probe_ps1_multitap_onoff_runtime.py`.

## CTR multitap closed; A9 finish only

CTR returned `PS1_MULTITAP_ONOFF_CTR_CONFIRMED`: Port 1 enabled, Port 2
disabled, P3/P4 exposed, and four independent controllers. PS1 Multitap On/Off
is COMPLETE/runtime validated.

Do not rerun the already-passed A9 SNES/PS1 lifecycle/cheat/mod/input-profile
stages. Correct the A9 game-identification helper so it can fall back from an
incomplete status payload to the newest fresh RetroArch log matching the
expected system. Run finish mode for NES and Genesis only, then fresh repository
audit. If it passes, create the Phase A checkpoint.

## A9 fixture clarification

The prior NES/Genesis A9 answers are invalid as runtime evidence: no NES or
Genesis games were installed/launched. Do not chase the `<unknown>` result as an
emulator bug.

Use the coverage-aware A9 finalizer. It queries `/games?system=...` first.
Zero games => `SKIPPED_NO_LOCAL_FIXTURE` with no gameplay questions. Installed
games => a real runtime launch remains mandatory. If the available library
passes and only absent systems are skipped, proceed to the Phase A checkpoint
while preserving NES/Genesis as explicit future runtime-coverage gaps.

## Phase A final checkpoint

A9 available-library finalization passed with classification
`PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS`. NES and Genesis each had
library count 0 and are recorded as no-fixture runtime gaps, not passes.

Final checkpoint commit message:
`Checkpoint: complete Phase A emulator subsystem`

Repository evidence policy is now durable:
- commit curated memory/evidence;
- ignore live `docs/memory/evidence/raw/`;
- commit sanitized checkpoint snapshot ZIP + manifest;
- never commit user/runtime/media/game data or private network-bearing state.

After successful push, Phase A emulator development is checkpointed. Next work
should follow the roadmap rather than extending emulator scope by default.
