---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Curated Project Memory

## Mission

PrivyHub is a local-first, privacy-preserving, modular smart-home/media experiment. The current prototype uses a Windows companion/server and an inexpensive onn Android TV client on an isolated secondary network. The design is intended to evolve toward inexpensive Linux-capable server hardware and additional clients without mandatory cloud, subscriptions, or proprietary infrastructure.

## Current baseline

`25e9a14` is the clean, pushed checkpoint completing A8 input mapping and profiles. It is the immutable pre-four-player baseline.

Phase A features A1 through A8 are complete/runtime validated, including the P1-P4 controller/profile extension. Representative four-player Crash Bash gameplay with game-specific Beetle PSX HW Port-1 multitap is also complete/runtime validated. Post-extension 1P and 2P regressions passed. A9 full emulator regression/checkpoint is the only remaining Phase A gate.

## Stable Games path

Native game streaming uses Windows Graphics Capture, H.264 NVENC, 720p60, 7 Mbps, short GOP, RTP-sized packets, 8+1 XOR FEC, process-specific game audio, Android hardware AVC decoding, and a separate UDP controller transport. These working paths are preservation boundaries until evidence says otherwise.

RetroArch is the managed emulator frontend. Current cores: FCEUmm (NES), bsnes (SNES), BlastEm (Genesis), and Beetle PSX HW (PS1).

## Controller architecture

Current validated two-player path:

`Android controller state -> PHI1 UDP full-state packet -> Windows NativeControllerBridge -> persistent ViGEm VX360 devices -> RetroArch ports`.

The PHI1 packet is 36 bytes and carries one player index per packet. The exact-local source audit on 2026-09-10 classified the protocol as reusable for P3/P4: the two-player limits were sender/receiver counts and literal bookkeeping arrays, not packet structure. The four-player base patch preserves PHI1 v1 while generalizing Android assignment/sending and Windows ViGEm state to four players. Its isolated runtime probe confirmed four XInput slots, exact synthetic P1-P4 routing, 120/120 packets with zero loss/rejection/bad packets, neutral release, and clean slot teardown. Real Android four-controller assignment is runtime validated: four distinct physical controllers reached XInput slots 1-4 exactly in first-touch order, with isolated A presses, confirmed releases, four-slot continuity, and a neutral final state. RetroArch P1-P4 enumeration is also runtime validated: a fresh normal game startup configured Xbox 360 Controller in ports 1-4 with the xinput driver and no startup fallback.

All intended virtual controllers must exist before RetroArch initializes input. The A8 controller-preflight ordering fix is proven and must remain intact.

## A8 mapping

A8 sits after canonical XUSB/ViGEm semantics and before RetroArch/libretro gameplay bindings. It uses named reusable profiles and session-only RetroArch overrides. Save/Load/Pause/End are meta controls outside gameplay remapping. The editor is Xbox-oriented and enforces a complete one-to-one mapping per player.

The P3/P4 extension keeps input-profile schema 1 for backward compatibility. Existing P1/P2 profiles normalize to Player 1-4 with empty P3/P4 mappings, preserving RetroArch default autoconfiguration until those players are explicitly edited. New/reset profiles can carry complete mappings for all four players, and the Android editor derives supported players from companion capabilities. Runtime validation of this extension is complete. The live schema stayed at 1; every inspected profile exposed P1-P4 keys; legacy P1/P2 data normalized to four; generated P3/P4 bindings and four-port analog-D-pad settings were present; the Android editor exposed all four player actions and copy-from-another-player; and the user successfully synchronized custom mappings across all four players.

## Closed work

A1 controller/analog, A2 Save/Load, A3 pause/resume, A4 host coexistence/audio lifecycle, A5 direct-launch UX, A6 organization/metadata/art, A7 cheats/mods, and A8 input mapping are closed absent regression evidence.

The severe prototype UDP burst/gap/duplication investigation is deferred to representative Linux/network infrastructure unless it again becomes a blocker.

## Deferred roadmap

After four-player and A9: Phase B removes Sunshine/Moonlight legacy and proves native-only Games; Phase C generalizes streaming and adds explicit quality profiles; Phase D performs resource/Linux hardware characterization and replays the transport acceptance suite.

## Durable project rules

Canonical ROMs and normal save namespaces are protected. Cheat/mod profiles remain isolated. Diagnostics should trust raw measurements over incorrect classifiers. Runtime/log/user-content directories stay separate from source control. New work should reuse proven paths rather than create parallel implementations.

## Four-player regression closure

The post-extension 1P regression is runtime validated. In a normal PS1 session, P1 physical A reached only XInput slot 1, gameplay remained normal, no other controller took over Player 1, RetroArch stayed on xinput without fallback, and normal End/Exit removed all session XInput slots. The active regression boundary is now 2P, then representative 4P gameplay.

## Post-extension 2P regression

The 2P regression is runtime validated. In a normal Crash Bash PS1 session, P1 physical A reached only slot 1 and P2 physical A reached only slot 2; both players worked independently, P3/P4 did not interfere, RetroArch remained on xinput with no fallback, and normal End/Exit removed all session XInput slots. The only gameplay-specific gate before A9 is representative 4P gameplay.

## Representative 4P host-routing result

The Crash Bash four-player gameplay probe proved exact P1->1, P2->2, P3->3, and P4->4 routing in a normal session with RetroArch ports 1-4 present and no XInput fallback. Crash Bash nevertheless greyed out Players 3 and 4 and no explicit Beetle PSX HW multitap option was found under the managed RetroArch data tree. Therefore the active blocker is above the validated PrivyHub transport/device/A8 stack: PS1 multitap/core-option session configuration. Do not reopen lower controller layers without contradictory new evidence.

## PS1 multitap core-option storage

The active RetroArch nightly writes Beetle PSX HW options to `runtime/emulators/retroarch-nightly-20260907/config/Beetle PSX HW/Beetle PSX HW.opt`; Port-1 and Port-2 multitap are explicitly disabled. `emulator_manager.py` currently has no core-options path/game-specific options/global core-options/max-player handling. Preserve global PS1 topology; the intended fix must be session/game-specific.

## PS1 multitap architecture

Representative four-player Crash Bash host routing is runtime validated, but the game initially exposed only two players because the active Beetle PSX HW core options explicitly disabled multitap on both physical PS1 ports. The chosen architecture reuses `data/games/retroarch/controller_overrides.json`: a per-game `ps1_multitap` mode controls native content-specific Beetle core options. The generated `<game>.opt` preserves every existing game/core option and changes only `beetle_psx_hw_enable_multitap_port1` / `port2`. Managed sessions explicitly enable RetroArch content-specific core options. Ordinary PS1 sessions preserve their prior two explicit libretro-device assignments; a multitap-enabled session assigns the selected PS1 device to users 1-4. Crash Bash is the first `port1` validation record.

## PS1 multitap rollback finding

The first game-specific multitap patch made Crash Bash expose Players 3 and 4, so the core-option concept is functionally relevant. However, the same post-patch runtime had four host XInput/RetroArch ports present while physical P2-P4 produced no XInput activity, and the user observed only 2-3 charged controllers remaining connected during the active PrivyHub/game-stream session while all four stayed connected with the session off. Treat this as a causal regression candidate, not as proof of Bluetooth mechanism. The authoritative next step is exact rollback plus repeat of the previously validated four-controller assignment probe before redesigning multitap.

## Multitap rollback comparison

Exact rollback removed Crash Bash multitap as expected but did not restore four physical controllers: P1-P3 still mapped cleanly while P4 produced no host input. This weakens the causal case against the multitap implementation. The game-specific multitap path can be restored for continued 4P testing, but physical-controller stability during the active Android game-stream session remains an independent unresolved issue.

## Final four-player acceptance

A replacement physical controller restored exact Android P1-P4 -> XInput 1-4 assignment while multitap was enabled. The final Crash Bash Battle Mode probe confirmed four human-player exposure and independent in-game control for all four controllers, no cross-control, RetroArch ports 1-4 on xinput without fallback, and clean normal teardown. The prior dropout persisted once with multitap rolled back and did not reproduce with the replacement controller, so it is not evidence of a PrivyHub multitap/software regression. Preserve it as a controller-specific/pairing/transient Bluetooth observation unless it reproduces with representative devices.

## 2026-09-10 A9 installer v1 preflight correction

`privyhub_phase_a_a9_regression_probe_01_2026-09-10` correctly returned **FAILED BEFORE MODIFICATION** before installing anything because its runtime-evidence preflight compared exact reconstructed chat-log bytes to the authoritative Windows log bytes. The visible successful measurements were unchanged; the gate was too strict about byte representation. A9 v2 replaces that check with semantic validation of the required classifications and raw measurements while leaving the A9 runtime probe itself unchanged.

## PS1 four-player accessory policy

PrivyHub's supported local-player ceiling is four. For PS1, the only user-facing multitap state is On/Off. On maps to Beetle PSX HW Port-1 multitap enabled with Port-2 explicitly disabled. Port-2/Both are not product options. Metadata may recommend multitap for titles with more than two local players, but recommendations are advisory; behavior remains Off until explicitly enabled for that game. This prevents metadata errors from silently changing controller topology.

## PS1 multitap product rule

PrivyHub's PS1 local-player ceiling is four. The supported user-facing multitap control is therefore On/Off only. On always means Beetle PSX HW Port 1 multitap enabled and Port 2 disabled. Port 2/Both are not valid PrivyHub modes. Multitap is a manual per-game setting because the 2026-09-10 audit found zero `max_players > 2` candidates across 80 PS1 entries, including known four-player CTR and Crash Bash. Do not auto-enable from current metadata.

## Wireless ADB build-tool rule

`tools/build_install_onn.ps1` must not assume a paired wireless-debugging device is already present in `adb devices`. Wireless ADB discovery/reconnection is an expected transient lifecycle. The build/install tool should eventually own bounded recovery using ADB-supported mDNS/server state, without asking the user for or logging network addresses. Do not persist or expose discovered endpoints.

## ADB diagnostic rule

Do not infer that ADB is absent from the 2026-09-10 v1 wireless-recovery probe
failure. That probe failed to parse `PrivyHub/local.properties` because its
`sdk.dir` regex was double-escaped. The PowerShell build script had already
located ADB in the same session. Use the corrected non-regex parser in audit
v2 and preserve the v1 event as a diagnostic-tool failure.

## Wireless ADB recovery rule

Do not fail immediately when `adb devices` is empty. The validated failure state
had healthy ADB/mDNS but zero services/transports despite intact pairing.

Recovery order:
1. private last-known target from LocalAppData;
2. existing online physical transport;
3. ADB mDNS TLS-connect discovery;
4. `adb reconnect offline`;
5. one local ADB-server restart plus bounded retry;
6. one user-assisted Wireless debugging Off/On retry, preserving pairing.

Network-bearing target data stays outside the repository under LocalAppData and
must never be printed, logged, or copied into durable memory.

## Wireless ADB recovery validated state

The 2026-09-10 persistent wireless-ADB recovery patch is runtime validated:
post-patch audit classified `ADB_TARGET_ALREADY_ONLINE`, with one TLS-connect
service, one online transport, and no offline/unauthorized transports. Treat
`tools/build_install_onn.ps1` cached-target/mDNS/reconnect recovery as the
current authoritative build/install path. Reopen only if the new path itself
fails in a future representative run.

## CTR Multitap validation

`PS1_MULTITAP_ONOFF_CTR_CONFIRMED` on 2026-09-10 establishes that the manual
PS1 Multitap On/Off feature works beyond Crash Bash. CTR launched with Port 1
enabled, Port 2 disabled, all four XInput slots live, Players 3/4 exposed, and
four independent controllers. The feature is COMPLETE/runtime validated.
Metadata-driven recommendation remains deferred.

## A9 identification rule

The first A9 full regression passed all user/runtime stages except NES and
Genesis machine identification. Those two titles were `<unknown>` because the
probe relied on `/plugins/games/status` providing a game id/system before
locating the RetroArch log. Corrected A9 identification may fall back to the
newest fresh RetroArch game log whose `System:` field matches the expected
family, then validate port-1 XInput autoconfig and no startup fallback.
Do not require users to repeat already-passed A9 stages merely to repair this
diagnostic gap.

## Runtime-test evidence integrity

Never treat a yes/no gameplay prompt as runtime evidence when no game was
actually launched. On 2026-09-10 the user clarified that no NES or Genesis games
were installed during the A9 attempts; those yes responses are invalidated.

A9 is coverage-aware: a family with zero current library entries may be
`SKIPPED_NO_LOCAL_FIXTURE`, but that family remains explicitly **not runtime
validated**. When a game is later added, run its normal launch/input/teardown
regression before upgrading its runtime status.

Current coverage:
- SNES: runtime exercised in A9;
- PS1: runtime exercised broadly, including 1P/2P/4P, lifecycle, profiles,
  cheats, and multitap;
- NES: configured/development path present; no current runtime fixture;
- Genesis: configured/development path present; no current runtime fixture.

## Repository evidence boundary

Commit source, configuration, durable engineering memory, reusable diagnostics,
and curated evidence. Keep operational/user/runtime data out of Git.

`docs/memory/evidence/raw/` is a local working-evidence store and is ignored.
At major checkpoints, create a sanitized immutable compressed snapshot under
`docs/memory/evidence/snapshots/` with a manifest containing per-file SHA-256
and byte size. Snapshot construction fails closed on detected network
identifiers/secrets or excessive size.

Do not commit ROMs/ISOs, saves/states, emulator runtime trees, media libraries,
ordinary logs, patch backups, APK/build output, private ADB target cache, or
other user/runtime data.

## Phase A checkpoint acceptance

A9 final state is `PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS`.
Available-library regression is complete. NES and Genesis have zero local
fixtures and remain explicitly not runtime validated. SNES and PS1 have actual
runtime coverage; PS1 includes validated 1P/2P/4P routing, lifecycle, profiles,
cheats/mods, Crash Bash/CTR Port-1 multitap, and teardown.
