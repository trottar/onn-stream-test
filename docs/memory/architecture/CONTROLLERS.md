---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Controller Architecture

## Validated two-player path

`Android InputDevice -> NativeControllerSender -> PHI1 UDP full-state packets -> NativeControllerBridge -> ViGEm VX360Gamepad devices -> RetroArch input`.

At baseline `25e9a14`:

- Android `NativeControllerSender` declares `PLAYER_COUNT = 2` and allocates state from that count.
- Android assigns controller descriptors to the first unused player index.
- It emits one 36-byte PHI1 v1 packet per player per send cycle.
- The packet contains a player byte, global sequence number, buttons, four stick axes, and two triggers.
- Windows `NativeControllerBridge` declares `MAX_PLAYERS = 2` and creates that many VX360 devices.
- Several receiver state arrays remain literal two-element arrays and must be generalized coherently.
- Receiver validity rejects player indexes outside `MAX_PLAYERS`.
- The receiver uses one global sequence tracker, matching the sender's global per-packet sequence progression.

## Four-player implication

Current source evidence does not require a wider or differently versioned packet merely to represent P3/P4. The narrow candidate is to preserve PHI1 v1/36-byte P1/P2 semantics and extend accepted player indexes/count-backed state to four. This must be proven with targeted diagnostics before calling transport compatibility complete.

## Preflight invariant

All intended virtual controllers must exist before RetroArch initializes input. The corrected Games launch path performs controller preflight before emulator launch. This ordering is part of the known-good baseline.

## A8 layer

A8 gameplay profiles operate after canonical XUSB/ViGEm semantics. They do not redefine PHI1. Current profile/editor state models Player 1 and Player 2, so P3/P4 profile support is a separate but related extension after physical Android assignment and RetroArch P1-P4 exposure are proven.

## 2026-09-10 four-player base development patch

The exact-local audit returned `EXPECTED_TWO_PLAYER_BASELINE_PROTOCOL_REUSABLE` with Android count 2, Windows count 2, packet size 36, and no P3/P4 profile/editor references. The resulting base patch changes only the canonical transport/device layer:

- Android allocates/assigns/sends four player states using the existing PHI1 packet.
- Windows creates four persistent ViGEm VX360 devices and sizes bridge bookkeeping from `MAX_PLAYERS`.
- Receiver validation accepts player indexes 0-3.
- PHI1 magic/version/36-byte layout and global sequence semantics remain unchanged.
- A8 profile/editor data remains P1/P2 until base-slot runtime proof succeeds.

## Base-slot runtime evidence

The isolated four-player base-slot probe returned `FOUR_PLAYER_BASE_SLOTS_CONFIRMED`. Four ViGEm/XInput slots appeared, synthetic P1-P4 reports reached slots 1-4 exactly, each player received 30 updates, all 120 packets were accepted with zero loss/rejection/bad packets, release returned all slots to neutral, and bridge stop removed all four slots.

This validates the PHI1/ViGEm/XInput base layer only. Four distinct physical Android devices and RetroArch P1-P4 behavior remain separate acceptance boundaries.

## Real Android four-controller runtime evidence

The normal production path was observed with four real controllers connected to the onn. Physical controllers 1-4 reached host XInput slots 1-4 respectively. Every isolated physical A press appeared only on the expected slot, every release was confirmed, no simultaneous-A ambiguity occurred, four-slot continuity held for every capture, and the final state was neutral.

This closes the Android device-assignment boundary. The next separate question is whether RetroArch itself enumerates and binds all four pre-existing XInput/ViGEm devices as ports 1-4 during normal emulator startup.

## RetroArch four-port runtime evidence

A fresh normal game session returned `RETROARCH_FOUR_PLAYER_PORTS_CONFIRMED`. Host XInput slots 1-4 remained live, RetroArch selected `xinput`, and Xbox 360 Controller was autoconfigured in ports 1, 2, 3, and 4 with no XInput startup fallback. This closes the transport/device-enumeration path below A8.

## A8 P3/P4 extension design

The A8 backend already validates, serializes, exposes capabilities, and generates RetroArch bindings by iterating `INPUT_PROFILE_PLAYERS`. The backward-compatible extension therefore keeps schema 1 and expands that player tuple to `player1` through `player4`. Old profiles containing only P1/P2 remain valid; normalization supplies empty P3/P4 maps, which preserve normal RetroArch autoconfiguration.

The Android editor must read `capabilities.players` instead of hard-coding P1/P2. Create/reset actions build complete Default mappings for all supported players; profile actions expose each supported player; copy/sync can choose any other player. Generated analog-D-pad session settings must also cover all four ports. PHI1, ViGEm semantics, meta controls, and validated P1/P2 mapping behavior remain unchanged.

## A8 P3/P4 runtime evidence

The schema-1 P3/P4 extension returned `A8_FOUR_PLAYER_PROFILE_EDITOR_CONFIRMED`. The live companion exposed Player 1-4, existing two-player profiles normalized without migration, generated session configuration included all four analog-D-pad settings plus explicit P3/P4 binds, and user profile storage was unchanged by the probe. The onn UI exposed all four player editors and copy-from-another-player; the user successfully synchronized custom mappings across all four players.

This closes the mapping/editor layer. Remaining acceptance is gameplay regression only: 1P, 2P, then a representative 4P core/game path.

## Post-extension 1P regression

`PHASE_A_1P_REGRESSION_CONFIRMED`: a normal Crash Bash PS1 session kept Player 1 on XInput slot 1 with no cross-controller takeover, xinput remained active with no fallback, and normal End/Exit removed all four session virtual controllers. This proves the four-device baseline does not disturb ordinary 1P control/session teardown. Next regression boundary: P1/P2 independence in ordinary 2P gameplay.

## Post-extension 2P regression

`PHASE_A_2P_REGRESSION_CONFIRMED`: a normal Crash Bash PS1 session kept P1/P2 on XInput slots 1/2 with clean releases, no cross-control, no P3/P4 interference, xinput active without fallback, and clean normal End/Exit teardown. This closes the original two-player regression. The final controller/gameplay gate is representative real 4P gameplay; PS1 multitap capability is a core/game layer above the already-validated four host routes.

## Representative 4P host-routing result

`PHASE_A_4P_HOST_ROUTING_CONFIRMED_GAMEPLAY_NOT_CONFIRMED`: all four real controllers reached the expected XInput slots during normal Crash Bash gameplay; RetroArch autoconfigured ports 1-4 with no fallback, but Crash Bash kept Players 3/4 unavailable. No explicit Beetle PSX HW multitap setting was observed under the managed RetroArch data tree. The next investigation is core-options/session topology only. PHI1, Android assignment, ViGEm, enumeration, and A8 remain preservation boundaries.

## PS1 multitap / four-player game topology

Four XInput/RetroArch frontend ports do not by themselves create four emulated PlayStation controller sockets. Beetle PSX HW exposes native multitap core options. PrivyHub now keeps this accessory topology game-specific through the existing controller override record (`ps1_multitap`: `off`, `port1`, `port2`, or `both`). The runtime adapter uses the active RetroArch executable's `config/Beetle PSX HW` directory, preserves an existing content-specific option file when present (otherwise starts from the current core option file), changes only the two multitap keys, and atomically writes `<content-stem>.opt`. A managed session adds `game_specific_options = "true"`. Only enabled multitap sessions extend explicit PS1 libretro-device assignment to users 1-4; non-multitap PS1 behavior is unchanged.

## Post-multitap connectivity regression, 2026-09-10

The first PS1 multitap development patch did not modify Android controller transport, PHI1, or ViGEm, but the first runtime after that patch coincided with a loss of physical P2-P4 input while four host XInput slots remained present. The user also observed fewer physical controllers remaining connected during the active PrivyHub/game-stream session. Because the previously validated four-controller assignment boundary had passed before this patch, do not reinterpret the lower layers as broken without rollback evidence. Exact rollback and repeat assignment testing is the active diagnostic.

## Rollback comparison

After exact rollback of the PS1 multitap patch, four ViGEm/XInput slots were still present and physical P1-P3 mapped correctly, but P4 was absent. Therefore controller dropout persists without the multitap code. Do not attribute this failure to RetroArch topology alone. Continue investigating the Android physical-device/session boundary, with a different controller as the next representative hardware check.

## Final P1-P4 acceptance, 2026-09-10

After substituting a different physical controller, the Android assignment probe again confirmed exact P1->1, P2->2, P3->3, P4->4 routing with clean release, four-slot continuity, and neutral final state during an active game session. The final 4P gameplay probe confirmed the same mapping in Crash Bash. The earlier P4/dropout episode persisted once with multitap rolled back and disappeared with the replacement controller, so it is not attributed to PHI1, ViGEm, or the multitap code. Treat as controller-specific/pairing/transient Bluetooth behavior unless reproduced across representative devices.

## Linux production backend (D-076)

Linux retains the same canonical Android/PHI1 state and replaces only the final
host output stage:

`Android InputDevice -> NativeControllerSender -> PHI1 UDP full-state packets -> NativeControllerBridge -> evdev.UInput P1-P4 -> RetroArch udev input`

The Linux backend creates all four pads before RetroArch input initialization.
Project-owned udev autoconfig profiles bind those pads in ports 1-4. Windows
continues to use the existing ViGEm VX360 path. Save/Load/Pause/End remain
companion-injected meta controls outside gameplay-profile remapping.

## D-076R1 managed RetroArch autoconfig-path correction

D-076 isolated runtime validation passed, but the first real managed RetroArch
probe exposed a session-path issue rather than a controller-mapping failure.
All four Linux uinput pads existed before launch and RetroArch selected the udev
joypad driver, but P1-P4 were reported `not configured`.

Fresh evidence established the cause: the persistent config kept the portable
relative setting `joypad_autoconfig_dir = "data/games/retroarch/autoconfig"`,
while EmulatorManager launches RetroArch with `cwd=executable.parent`. RetroArch
therefore resolved that relative path below the AppImage directory, where no
autoconfig profiles exist. The project-owned autoconfig directory itself was
present and contained all four D-076 profiles.

D-076R1 keeps the persistent config portable. On Linux, only the generated
per-launch session config rewrites the single validated project-relative
`joypad_autoconfig_dir` to its absolute project-owned path. Windows behavior,
PHI1, uinput mapping, Android, video/FEC, audio, and emulator process cwd remain
unchanged.

Status: **DEVELOPMENT PATCH / MANAGED RETROARCH RUNTIME REVALIDATION PENDING**

## D-076R2 missing `sys` import correction

The first D-076R1 managed RetroArch revalidation failed before RetroArch launch.
Linux controller preflight succeeded (`linux_uinput`, four players), but the new
D-076R1 session-config branch referenced `sys.platform` without importing the
standard-library `sys` module. Cleanup removed all virtual pads correctly.

D-076R2 adds only the missing top-level `import sys` to
`companion/games/emulator_manager.py`. The D-076R1 autoconfig path-resolution
logic, D-076 uinput backend/mapping, PHI1, Android, video/FEC, D-075R1 audio,
RetroArch persistent config/profiles, process cwd, and runtime descriptor are
unchanged.

Status: **DEVELOPMENT PATCH / MANAGED RETROARCH RUNTIME REVALIDATION PENDING**

## D-076/R1/R2 managed Linux runtime status — 2026-09-15

**Authoritative over earlier pending-runtime notes.** Host-side managed RetroArch
validation passed: P1-P4 configured in ports 1-4, PHI1 live updates were clean,
Pause/Resume worked, RetroArch logged a real 284304-byte `.state` save and load,
normal `EmulatorManager.stop()` was graceful with `SAVE_FILES` -> `OK`, and all
virtual pads were removed. The prior probe final `False` was a classifier defect
(`.state.png` match plus a non-production `quit` requirement). Full onn E2E and
durable `/dev/uinput` service permission remain pending.
