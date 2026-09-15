---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Current Handoff


<!-- PRIVYHUB_D079_MEMORY_CHECKPOINT_LINUX_ONN_STREAM_DIAGNOSIS_2026_09_15:HANDOFF:BEGIN -->
## 2026-09-15 active handoff — first Linux/onn game E2E

Current active work is **Phase D Linux migration / integrated onn E2E**, not the
older Windows Phase-C position in stale checkpoints.

What now works in the integrated path:

- Linux runtime selection/startup;
- RetroArch launch;
- restored game/user data;
- uinput controller preflight with temporary development ACL;
- RT audio permission with temporary `RLIMIT_RTPRIO=1`;
- prior PS1 save load;
- exact managed X11 window discovery by the Linux native backend;
- VAAPI 720p60 encoding.

Two distinct remaining issues:

1. **Android handoff compatibility bug:** `MainActivity` still requires
   Windows-only `host_window_policy.window_found` before automatic native-stream
   handoff. Linux can therefore show `Game ready, stream not opened` even though
   native Linux X11 discovery subsequently succeeds. Manual banner entry reaches
   NativeStreamActivity.
2. **Transport blocker:** NativeStreamActivity then fails stabilization because
   the Linux -> onn path is delivering severe video/audio gaps. Multiple short
   runs showed thousands of UDP `SndbufErrors` and `RcvbufErrors`; video
   `sendto()` stalled for hundreds of milliseconds; the separate nonblocking
   SCHED_RR audio sender had thousands of failed sends.

Hypotheses already tested/falsified as primary cause:

- Linux exact-window capture failure — falsified.
- VAAPI encoder starvation — not supported; encoder remained near 60 fps.
- Android software-decoder fallback — falsified; hardware vendor decoder active.
- Linux socket max-buffer cap — falsified as root cause; 4 MiB ceilings did not
  improve the run.
- USB runtime autosuspend / USB 2-speed bottleneck — falsified; adapter is
  SuperSpeed 5000 Mb/s, `power/control=on`, never runtime-suspended.
- rtw88 deep-LPS — falsified as root cause.
- ordinary mac80211/NetworkManager powersave — disabling it removed rtw88 LPS
  warnings but transport failure persisted, so it is a secondary driver issue.

Important host/kernel evidence:

- adapter: Realtek RTL8822BU (`0bda:b812`), driver `rtw_8822bu`;
- repeated kernel `firmware failed to leave lps state`;
- one rtw register read timeout;
- interface TX drop/error counters did not increase during UDP failure;
- ordinary Wi-Fi powersave test suppressed LPS/register warnings while
  `SndbufErrors`/`RcvbufErrors` still rose by thousands.

Next step:

Run the preserved standalone **Linux -> onn idle UDP Test A** before touching
production transport. Use 5 ms / ~1000-byte datagrams and Android kernel receive
timestamps. Do not ask for or expose the onn IP. The first Linux wrapper attempt
failed locally at address discovery (`ONN_ADDRESS_DISCOVERY_FAILED`) before any
packets were sent, so fix only that wrapper/discovery seam first.

Also restore the PS1 `scph5501.bin` BIOS before final PS1 acceptance; it is not
the present transport root cause.

<!-- PRIVYHUB_D079_MEMORY_CHECKPOINT_LINUX_ONN_STREAM_DIAGNOSIS_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D078_HANDOFF -->
## D-078 handoff

D-078 is installed and host-validated when `logs/games/d078_linux_companion_startup_probe.txt` ends with `D078_LINUX_MEDIA_SERVER_STARTUP_READY`. Normal Linux companion startup now uses Python `range_server.py`; Windows remains on the existing PowerShell wrapper. Current next step is integrated onn/Linux SNES E2E through the normal Games UI. Live-source PowerShell runner portability is explicitly not part of D-078.

## Repository state

Authoritative local root:

`L:\Projects\onn-stream-test`

Local source is authoritative between checkpoints. GitHub is reference/history
unless a clean synchronized checkpoint is being verified.

Predecessor synchronized checkpoint for the remote-foundation promotion:

`0c31c100ec721d687aff6aedbd79bc0cf9343810`

Part 1, Part 2 and Part 3 docs/memory cleanup are checkpointed/pushed.

Part 4 top-level docs/ledgers refresh is checkpointed/pushed.

The focused docs/memory cleanup Parts 1-4 is complete.

The minor Games startup/catalog cleanup is runtime validated and checkpointed:
- startup reconciliation detected the changed library and reconciled 124/124 games;
- 39 artwork files were downloaded, 80 were reused from cache, and 5 had no usable artwork;
- a later startup returned `SKIPPED_CURRENT` with 124 discovered / 124 metadata entries;
- the player-facing `Native Streaming Alpha` catalog node is removed;
- native-stream status/start/stop endpoints and `NativeStreamActivity` remain preserved;
- normal game picture/audio/controller regression passed.

C1 schema design and its durable-memory update are checkpointed/pushed.

C1.1 static reference profile extraction is runtime validated and checkpointed/pushed.

The native-stream public-status privacy hotfix is live-endpoint validated and checkpointed/pushed.

Next work: `C3_ACTUATOR_CONTINUITY_PROBE`.

Do not rerun the completed C1 inventory unless source changes invalidate it.

## Development position

- Phase A — Games / emulator subsystem: **COMPLETE / PUSHED**
- Phase B — Diagnostics + clean native baseline: **COMPLETE / PUSHED**
- Phase C — Adaptive native streaming: **ACTIVE**
- C1 inventory: **COMPLETE / `C1_INVENTORY_COMPLETE`**
- Part 4 docs refresh: **COMPLETE / CHECKPOINTED / PUSHED**

## C1 design direction

Reference path:

`WGC -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference behavior:

- 1280x720;
- 60 fps;
- 7000 kbps;
- GOP 15;
- B-frames 0;
- FEC group size 8;
- RTP PT 96;
- packet size 1200 bytes.

Reference profile `native_game_720p60_reference` is design-fixed as:

- `id`: `native_game_720p60_reference`
- `width`: 1280
- `height`: 720
- `fps`: 60
- `bitrate_kbps`: 7000
- `max_bitrate_kbps`: 7000
- `gop_frames`: 15
- `bframes`: 0
- `fec_group_size`: 8

Do not add `min_bitrate_kbps` in C1.1 because the validated baseline has no existing lower-bound behavior to preserve.

`fec_group_size` is portable C1 profile data and must validate to 1-8 because the current PHF1 marker mask is one byte.

Keep NVENC codec/preset/tune/RC/buffer/pixel-format policy, RTP payload type, packet size, ports, capture backend, audio, controller protocol and telemetry cadence outside the portable C1.1 profile.

C1.1 is companion-only static extraction. Preserve Android constants/startup ordering; keep existing top-level host status fields and add inspectable `profile_id` plus nested profile data. No selector, adaptation, generalized backend framework, capture/audio/input redesign or wire-format change.

## Regression contract

Representative C1 runtime validation must preserve:

- picture;
- process audio;
- controller input;
- Pause / Resume;
- Save / Load;
- End / teardown;
- validated game/profile behavior.

## Stable subsystems

Preserve unless fresh evidence requires change:

- WGC/NVENC native video;
- process-specific audio;
- UDP/FEC;
- Android hardware AVC;
- PHI1/ViGEm P1-P4;
- Save/Load/Pause/End;
- A8 profiles;
- PS1 manual Port-1-only multitap;
- Phase B diagnostics/Self-Test/support bundle/retention.

Coverage:

- PS1 — extensive;
- SNES — runtime exercised;
- NES — configured/supported, no local A9 fixture;
- Genesis — configured/supported, no local A9 fixture.

## Phase B result

Complete/runtime validated:

- health/resource model and endpoint;
- Android client health feedback;
- classifier corrections;
- bounded event history;
- Diagnostics / Self-Test GUI;
- sanitized support bundle;
- bounded/manual retention;
- Sunshine/Moonlight production/artifact removal;
- native-only regression and clean-native checkpoint.

Raw measurements outrank classifiers.

## Roadmap

`docs/ROADMAP.md` roadmap v4 is authoritative.

After C:

- D Media Library / VOD / Live TV UX
- E Linux Migration / Native Linux Baseline
- F Linux Core Resource Characterization & Optimization
- G Secure Remote Access / Portable Client Foundation
- H Extended Emulation & User-Content Import
- I Home Infrastructure / Broader Plugin Expansion
- J Local Intelligence / Voice / Privacy-Aware AI

Phase C must remain reusable for future WAN paths while WAN implementation stays
deferred to Phase G.

D-059 establishes:

- home Opal = PrivyHub trust/network domain;
- ordinary household network = upstream only;
- Tailscale = preferred first overlay candidate, not permanent contract;
- overlay transport != PrivyHub authorization;
- source/request IP != durable client identity;
- no permanent travel-router model selected yet;
- deferred UDP replay target = Linux + home Opal + onn.

Remote implementation is **PLANNED ONLY**.

The remote-foundation documentation update is **CHECKPOINTED / PUSHED**.

## Commands

Android build/install:

`.\tools\build_install_onn.ps1; cd L:\Projects\onn-stream-test`

Companion:

`python .\companion\privyhub_service.py`

Existing C1 inventory evidence:

`logs/streaming/c1_stream_profile_inventory.txt`

## Working rules

- Inspect exact current local source before patching.
- Use exact predecessor hashes/state.
- Back up changed files under `archive/patch_backups`.
- Validate deterministic output before delivery.
- Roll back exact bytes on deterministic validation failure.
- Keep install and checkpoint/push as separate stages.
- Update durable memory with meaningful work.
- Never ask for or expose network addresses in shareable diagnostics.

## C1.1 static reference profile extraction — development state

**Status:** RUNTIME VALIDATED / CHECKPOINTED / PUSHED

Implementation:
- added `companion/native_stream_profiles.py`;
- defines immutable `NativeStreamProfile`;
- defines `native_game_720p60_reference`;
- `NativeStreamManager` now derives the prior width/height/fps/bitrate/GOP/
  B-frame/FEC constants from that profile;
- FFmpeg `-maxrate` explicitly consumes `max_bitrate_kbps`;
- FFmpeg `-bf` explicitly consumes `bframes`;
- the FEC relay still uses the same 8-packet group through the profile-derived
  manager constant;
- native-stream status preserves existing top-level fields and adds
  `profile_id` plus nested `profile`.

Intentionally unchanged:
- Android source/startup ordering;
- WGC capture ownership;
- H.264 NVENC backend/preset/tune/RC/buffer/pixel format;
- RTP payload type, packet size and ports;
- FEC wire format;
- audio and controller paths;
- GUI/profile selection and adaptation.

Representative game runtime regression passed the C1.1 acceptance boundary.

## Native-stream status privacy hotfix — 2026-09-14

**Status:** LIVE ENDPOINT VALIDATED / CHECKPOINTED / PUSHED

A C1.1 runtime status review found that public native-stream status inherited the
process-audio helper's raw status object. That exposed a client network
identifier and an absolute local diagnostics path.

Root cause:
- `NativeAudioStreamer.status()` returned `_read_status()` wholesale as
  `helper_status`;
- the same method exposed its timing-log `Path` as an absolute string.

Hotfix boundary:
- raw helper JSON remains unchanged in local runtime/data storage;
- public `helper_status` is a recursively sanitized copy;
- network-address fields and valid embedded IPv4/MAC identifiers are redacted;
- helper path fields are redacted;
- public top-level `timing_log` is project-relative when available;
- public strings containing the project-root prefix use `<project-root>`.

Intentionally unchanged:
- process-audio capture/pacing/packetization and raw local diagnostics;
- video/FEC/controller behavior;
- Android;
- C1.1 profile values and stream behavior.

The live native-stream status endpoint passed the bounded privacy validator.

## Immediate continuation after remote-foundation checkpoint

Resume Phase C.

Preserve D-059:
- Phase C artifacts must remain reusable for future WAN paths;
- WAN overlay/auth/travel-router implementation remains Phase G work.

## C2 continuation

C2.1 inventory result:

`C2_INVENTORY_COMPLETE_EXISTING_FOUNDATION_WITH_GAPS`

C2.2 design classification:

`C2_DESIGN_MINIMAL_STREAM_TELEMETRY_V1` — **COMPLETE / CHECKPOINTED / PUSHED**

Implementation target:
- keep the existing 2-second client-health loop;
- add receiver RFC-style jitter;
- add previous successful health-POST control round trip;
- derive signed queue-depth change companion-side;
- instrument FEC-relay `sendto()` pressure/timing;
- assemble `privyhub_stream_telemetry_v1` companion-side;
- no adaptive bitrate/FEC controller yet.

Decision: D-060.

## C2 implementation runtime-validated state

`C2_IMPLEMENT_STREAM_TELEMETRY_V1` — **COMPLETE / RUNTIME VALIDATED /
CHECKPOINTED / PUSHED**

Evidence:
- `docs/memory/evidence/C2_STREAM_TELEMETRY_RUNTIME_VALIDATED_2026-09-14.md`;
- `C2_STREAM_TELEMETRY_RUNTIME_PASS`;
- representative gameplay regression passed.

The stale cached wireless-ADB failure path encountered during C2 installation
is also runtime validated as fixed; see
`docs/memory/evidence/ADB_STALE_CACHE_RECOVERY_RUNTIME_VALIDATED_2026-09-14.md`.

C3 is active. Next: **C3_ACTUATOR_CONTINUITY_PROBE**.

## C3 continuation

C2 is checkpointed/pushed at `da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0`.

C3.1 source/policy audit is complete under D-062.

The present FFmpeg/NVENC process has no live PrivyHub bitrate control surface.

Do not implement the automatic controller yet.

Next diagnostic: `C3_ACTUATOR_CONTINUITY_PROBE`.

Keep 7000 kbps and determine whether a narrow video-only actuator cycle can
preserve audio/controller/game lifecycle and recover Android IDR/render
continuity acceptably.

## C3 actuator continuity runtime step

`C3_ACTUATOR_CONTINUITY_PROBE` — **RUNTIME VALIDATED / INITIAL ACTUATOR
STRATEGY ACCEPTED / CHECKPOINT PENDING**

Companion-only diagnostic. No Android rebuild is required.

Runtime order:
1. restart companion;
2. launch a normal game/native stream;
3. run `python .\tools\probe_c3_actuator_continuity.py`;
4. verify process audio, controller, Pause/Resume, Save/Load;
5. End normally so Android writes the decoder-session report;
6. run `python .\tools\probe_c3_actuator_continuity.py --finalize`;
7. review `logs/streaming/c3_actuator_continuity_probe.txt`.

Do not checkpoint this development diagnostic as an accepted actuator until the
evidence is reviewed.

## C3 actuator accepted state

D-063 accepts `video_only_restart` as the initial backend-neutral C3 actuator
strategy.

Windows runtime validation passed using WGC + FFmpeg/NVENC. The exact Windows
implementation is not the Linux architecture; Linux must map the same actuator
boundary to its selected capture/encoder backend and rerun the continuity test.

Evidence:
`docs/memory/evidence/C3_VIDEO_ONLY_RESTART_RUNTIME_VALIDATED_2026-09-14.md`

Next development step after checkpoint:
**C3 fixed-bitrate characterization**.

## C3 fixed 6000 characterization runtime step

First lower candidate: **6000 kbps — VALIDATED**.

Next lower candidate: **5000 kbps — NOT YET INSTALLED**.

No Android rebuild is required for the completed 6000 validation.

Runtime:
1. restart companion;
2. launch a normal game/native stream at 7000;
3. run `python .\tools\probe_c3_fixed_6000_characterization.py`;
4. play for several focused minutes and watch image quality/stutter;
5. verify audio/controller/Pause/Resume/Save/Load;
6. End normally;
7. run `python .\tools\probe_c3_fixed_6000_characterization.py --finalize`;
8. review `logs/streaming/c3_fixed_6000_characterization.txt`.

Do not accept 6000 until technical evidence and manual quality observation are
both reviewed.

## C3 6000 validated result

D-064 validates 6000 kbps as the first lower C3 candidate.

Focused gameplay/movement was fine. Audio stutter was heard, but receiver
metrics showed severe queue burst/gap oscillation (868 stale trims, 922
concealed underruns, 104 prolonged-starvation events) with only 11 lost audio
packets. This matches the separately deferred transport/audio pathology and is
not attributed to the bitrate reduction.

Evidence:
`docs/memory/evidence/C3_FIXED_6000_VALIDATED_2026-09-14.md`

Next after checkpoint:
**C3 fixed 5000 kbps characterization**.

## Patch tooling hardening from C3 6000 acceptance

Durable installer rule: command success/failure is determined by exit code, not
by whether stdout/stderr contains text.

Specifically, `git diff --check` exit 0 with CRLF/LF warnings is PASS; warnings
are logged but are not rollback triggers. Future packages must regression-test
that case before delivery.

## C3 fixed 5000 characterization runtime step

5000 kbps is **installed as the next development-only characterization
candidate**.

Validated before this test:
- 7000 kbps;
- 6000 kbps.

Runtime:
1. restart the companion;
2. launch a normal game/native stream at the 7000 reference;
3. run `python .\tools\probe_c3_fixed_5000_characterization.py`;
4. play for several focused minutes and assess image quality, motion/stutter and
   responsiveness;
5. verify audio/controller/Pause/Resume/Save/Load;
6. End normally;
7. run `python .\tools\probe_c3_fixed_5000_characterization.py --finalize`;
8. return `logs/streaming/c3_fixed_5000_characterization.txt` plus the focused
   visual/gameplay impression.

Detailed audio burst/gap counters are emitted automatically but remain a
separate deferred issue unless the 5000 evidence shows a specific regression.

## C3 5000 result / 5500 next

5000 kbps: **RUNTIME TESTED / NOT ACCEPTED AS A LADDER CANDIDATE**.

Why:
- image looked subjectively clearer;
- initial lag persisted but later gameplay could feel good;
- however, focused extended play showed definitely more visual stutters than
  6000/7000.

Technical evidence also recorded 11 decoder drops and 11 queue-overflow drops.

Do not attribute the known audio burst/gap pathology to 5000; it remains
deferred to Linux + Home-Opal replay.

Validated candidates remain 7000 and 6000 kbps.

Current bracket: 5000–6000 kbps.
Next candidate: **5500 kbps**.

## C3 fixed 5500 characterization runtime step

5500 kbps is installed as the single midpoint bracket test.

Current state:
- 7000 validated;
- 6000 validated;
- 5000 runtime tested / not accepted;
- bracket 5000–6000.

Runtime:
1. restart companion;
2. launch a normal game/native stream at the 7000 reference;
3. run `python .\tools\probe_c3_fixed_5500_characterization.py`;
4. play for several focused minutes, including enough steady-state time after
   the initial transition to judge visual stutter/smoothness;
5. assess input responsiveness and image quality;
6. verify audio/controller/Pause/Resume/Save/Load;
7. End normally;
8. run `python .\tools\probe_c3_fixed_5500_characterization.py --finalize`;
9. return `logs/streaming/c3_fixed_5500_characterization.txt` plus focused
   gameplay/visual observations.

Detailed audio burst/gap counters are included automatically but remain a
separate deferred issue unless new causal evidence appears.

## C3 5500 accepted / fixed envelope complete

D-066 validates the Windows C3 fixed ladder:

- 7000 kbps validated max;
- 6000 kbps validated middle;
- 5500 kbps validated lower/current Windows floor;
- 5000 kbps not accepted.

5500 focused observation: initial lag for a few seconds, then gameplay ran very
well.

Important evidence nuance:
- whole-session decoder totals: 57 drops / 57 queue-overflow drops;
- six stored post-cycle telemetry intervals, session elapsed 5,502–15,536 ms:
  638 rendered-frame deltas, 0 dropped-frame deltas, 0 overflow deltas, queue
  depth 0 throughout.

Do not claim all 57 drops occurred during startup; their location outside the
sampled window is unresolved.

Audio burst/gap remains deferred to Linux + Home Opal.

Next: C3 adaptive bitrate controller over discrete 5500/6000/7000 levels.
Linux later revalidates the actuator/fixed envelope.

## C3 startup stabilization runtime validation

D-067 development patch is the gate before adaptive bitrate control.

Expected:
1. game launches paused;
2. fullscreen native stream shows `Stabilizing game…`;
3. overlay includes title, 720p60, bitrate, FEC, video/audio/controller;
4. gameplay input does not leak while stabilizing;
5. after clean readiness, game resumes automatically and overlay disappears;
6. Back returns to existing paused Game Session UI;
7. paused Game Session shows the same compact stream metadata;
8. Resume/Save/Load/End still work.

Fail closed: if readiness times out/errors, game remains paused and Back returns
to Game Session.

Automatic bitrate switching remains off.

## D-067 startup stabilization validated

Runtime result after companion restart:
- stabilization GUI appeared;
- release succeeded;
- gameplay worked well;
- no initial lag was observed.

The first failure was a stale-process artifact: new APK + old running companion.
RetroArch logs proved PAUSED then old-code resume behavior. Restarting companion
loaded the installed Python and fixed the issue without another patch.

Operational rule: restart companion after companion Python changes before
runtime validation.

Next: checkpoint D-067/D-068 and proceed to C3 adaptive bitrate controller over
5500/6000/7000.

## C3 bidirectional actuator runtime step

Current clean checkpoint before development:
`9d7da2ccc47cc78a19f7128161859a1c5f308174`.

D-069 diagnostic sequence:
`7000 -> 6000 -> 7000`.

After installation:
1. restart companion because Python changed;
2. launch a normal game and let startup stabilization release;
3. while actively playing, run
   `python .\tools\probe_c3_bidirectional_actuator.py`;
4. continue focused play briefly and note whether either transition causes
   visible stutter/input disruption;
5. End normally;
6. run
   `python .\tools\probe_c3_bidirectional_actuator.py --finalize`;
7. return `logs/streaming/c3_bidirectional_actuator_probe.txt` plus focused
   transition observation.

Automatic bitrate adaptation is still disabled.

## D-070 actuator disposition / next probe

D-069 bidirectional probe completed:
`7000 -> 6000 -> 7000`.

Both legs recovered, but restart produced ~0.84-0.95 s first-RTP gaps and focused
play observed ~1 s freeze. Final decoder max output gap was 1,059 ms.

Disposition:
- bidirectional restart works;
- not accepted for seamless automatic adaptation;
- retain as diagnostic/startup/manual/fallback only.

Next:
investigate **live bitrate reconfiguration without encoder replacement**.

Do not implement the automatic bitrate controller until that actuator question
is answered.

Companion restart remains required after Python changes.

## D-071 current roadmap / next work

Current development tree contains D-069/D-070 evidence on checkpoint
`9d7da2ccc47cc78a19f7128161859a1c5f308174`.

D-071 roadmap reorder:
- D = Linux Migration / Native Linux Baseline;
- E = Linux Core Resource Characterization & Optimization;
- F = Media Library / VOD / Live TV UX;
- G+ unchanged.

Windows-specific automatic adaptation is paused. Do not pursue NVENC-specific
live reconfiguration.

The Linux migration preserves today's working VOD/Live TV paths but does not
block on media polish.

On Linux:
1. restore normal-use parity;
2. inventory capture/encoder/audio/input backends;
3. classify bitrate actuation;
4. replay deferred transport evidence;
5. revalidate bitrate envelope;
6. then resume automatic bitrate/FEC work if supported.

Next after checkpoint: Phase D Linux baseline work.

## D-072 sequencing clarification

Next technical phase is still **Phase D Linux Migration / Native Linux
Baseline**.

However Phase C is paused, not finished.

After D is runtime validated/checkpointed, return to:
C3 controller -> C4 FEC -> C5 1080p60 -> C6 source abstraction -> C7 Phase C
checkpoint, all on Linux.

Only then move into Phase E Linux resource characterization/optimization.

Do not resume Windows/NVENC-specific adaptation work.

## D-073 Linux baseline handoff

Phase D is active.

Linux runtime validation now includes:
- VAAPI H.264 encode;
- exact X11 RetroArch capture;
- PulseAudio isolation;
- four uinput pads;
- all four required Linux libretro cores;
- real SNES content/video/audio;
- real RetroArch -> x11grab -> VAAPI capture;
- `NativeStreamManager` construction/status boundary;
- `EmulatorManager` readiness and complete real-game launch/flush/stop lifecycle.

Windows persistent RetroArch state was migrated byte-for-byte:
129 files, manifest SHA-256
`6de3fa8b67d5a0ee21ace20af9347b5cf0f5997f3a9d410fcd23d6410b18280c`.

`EmulatorManager` is no longer considered a Linux-porting blocker.

Do not resume Windows/NVENC adaptation.

Next: identify and implement the smallest Linux backend substitutions for native video, audio, controller output, and telemetry while preserving PHI1, FEC, Android decoding/audio/controller paths, and the validated emulator lifecycle.

## D-074 Linux native-video development patch

D-074 implements the validated Linux video architecture without changing the
Windows WGC/NVENC path.

Changed production scope:
- Games plugin passes the internally trusted active RetroArch PID;
- NativeStreamManager resolves the exact visible X11 window for that PID;
- Linux uses one FFmpeg x11grab -> VAAPI H.264 process;
- existing RTP/XOR-FEC relay is reused unchanged;
- stream liveness/status are backend-aware.

Still pending:
- full Android/onn E2E validation of D-074;
- Linux PulseAudio backend;
- D-076 PHI1 -> uinput runtime validation;
- Linux host telemetry;
- service/device permissions;
- migrated save/state/profile regressions.

Do not change Android or FEC for D-074 runtime validation.

## D-074 validated Linux video backend

D-074 is host-side runtime validated.

Validated production path:
`EmulatorManager PID -> exact X11 window -> x11grab -> VAAPI H.264 ->
existing NativeVideoFecRelay`.

Real-session validation observed 4,500 RTP + 680 PHF1 packets, zero skipped
packets, zero send errors, clean stream teardown, and graceful game shutdown.

Do not add a Linux WGC/raw-frame bridge.

Android video code remains unchanged; full onn E2E is still pending.

Next: Linux audio production backend.

## D-075 Linux native-audio development patch

Baselines 32-34 resolved the Linux audio architecture.

Validated concepts:
- managed RetroArch PID -> exactly one PulseAudio sink-input;
- exact stream -> dedicated 48 kHz stereo null sink;
- monitor -> useful PCM;
- hybrid monotonic 5 ms PHA1 pacer is stable;
- simple sleep pacer is rejected.

D-075 changes only `NativeAudioStreamer` plus durable memory. Windows WASAPI,
Android, PHI1, video/FEC, controller output, telemetry, and EmulatorManager are
intentionally unchanged.

D-075 runtime validation established that the Linux PulseAudio route, PCM
capture, PHA1 framing, and cleanup path are correct, but normal-scheduler
sender cadence was rejected. D-075R1 below is authoritative for production
Linux native-audio pacing.

## D-075R1 Linux native-audio RT pacer correction

D-075 functional routing/wire behavior passed, but its normal-scheduler sender
cadence failed under active RetroArch. Baselines 35-41 localized the cause to
Linux scheduling and validated the fix: only the PHA1 sender thread uses
`SCHED_RR` priority 1; the main companion thread stays `SCHED_OTHER`.

D-075R1 implements that correction without changing PulseAudio routing, FFmpeg
capture, Android/PHA1, Windows audio, video/FEC, controller output,
EmulatorManager, or telemetry. Production code does not invoke `sudo`.

D-075R1 production runtime validation passed with process-scoped
`RLIMIT_RTPRIO=1`: the sender thread verified `SCHED_RR/1`, PHA1 framing and
delivery remained clean, 5 ms sender cadence was restored under active
RetroArch, the original PulseAudio route was restored, the temporary sink was
removed, native video remained active, and RetroArch stopped gracefully.

D-076/R1/R2 host-side managed runtime validation passed without changing the
validated Linux video/audio implementations. Next: checkpoint this state, then
run full Android/onn Linux E2E.

## D-076 Linux uinput controller backend

Baselines 42-45 passed before production modification:

- exact Linux joystick mapping measured;
- PHI1/XUSB -> uinput translation passed 20/20 controls;
- P1-P4 autoconfigured in RetroArch ports 1-4;
- project-relative autoconfig directory validated.

D-076 adds the Linux uinput backend inside the existing controller bridge while
preserving Windows ViGEm, Android PHI1, video/FEC, D-075R1 audio, EmulatorManager,
and A8 gameplay-profile semantics. Existing ViGEm-named diagnostic counters are
retained as compatibility aliases.

Host-side managed RetroArch validation is complete. P1-P4 configured in ports
1-4, PHI1 live updates were clean, Pause/Resume passed, raw RetroArch logs prove
real Save/Load, normal EmulatorManager stop was graceful, and all pads cleaned up.
Durable service permissions remain a later Phase D item.

D-076 isolated production-backend runtime validation passed: Linux selected
`linux_uinput`, created four pads, processed PHI1 for P1-P4 with zero
bad/rejected packets, preserved meta-hotkey edge ordering, and removed all pads
on stop. Managed RetroArch host integration subsequently passed; full onn E2E remains pending.

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

Status: **HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING**

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

Status: **HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING**

## D-076 managed-runtime acceptance

Authoritative evidence: P1-P4 autoconfigured in ports 1-4; eight live PHI1
packets produced two updates per player with zero bad packets; Pause and Resume
changed RetroArch state correctly; RetroArch logged saving and loading the same
284304-byte `.state`; the production `EmulatorManager.stop()` path returned a
graceful SIGTERM shutdown with `SAVE_FILES` -> `OK`; cleanup removed all virtual
pads. The probe's `validated=False` was a classifier defect (`.state.png` match +
non-production `quit` requirement), not a controller failure.

## D-077 Linux platform-aware RetroArch runtime selection

**Status after successful installer validation:** NORMAL-PATH RUNTIME SELECTION VALIDATED / ONN E2E PENDING

The normal Games product path no longer depends on the Windows-only base runtime
selection when running on Linux. D-077 adds an optional `platforms.linux`
override to the existing trusted emulator descriptor and has EmulatorManager
merge it into the effective config used by both readiness and `_resolve_game()`.

Windows base paths/`.dll` cores remain unchanged. Linux selects the already
validated project AppImage plus `cores-linux`/`.so` cores. No GamesPlugin,
Android, video/FEC, audio, controller, lifecycle, telemetry or permission
behavior is changed.

Next: run the integrated onn Linux E2E through the normal Games launch path.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:HANDOFF:BEGIN -->
## Linux transport handoff update — idle Test A

Standalone Linux -> onn idle UDP Test A has now **reproduced the old transport
pathology on the representative deployment path**.

Measured 20-second result:

- 3993 successful Linux sends, 7 would-block;
- host send p95 ~5.015 ms;
- 3993 unique Android arrivals, zero unique loss;
- **2626 same-stamp duplicate Android arrivals**;
- Android kernel arrival p95 ~18.36 ms, max ~792.30 ms;
- 2116 sender-clean 4-6 ms intervals became kernel intervals <2 ms;
- 190 sender-clean 4-6 ms intervals became kernel intervals >=20 ms;
- Linux `SndbufErrors +7`, `RcvbufErrors +0`.

This isolates the base pathology from RetroArch/native-stream load. The old
2026-09-07 investigation's resume criterion is met. Its prior Android
`WIFI_MODE_FULL_LOW_LATENCY` test did not fix the forward behavior, so do not
repeat that as the next hypothesis.

Next: preserved **Test B — onn -> Linux, idle**. Use the existing Android
nonblocking DatagramChannel sender and Linux Python receiver. Discover the Linux
target address locally and never print/persist it in shareable output.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:HANDOFF:BEGIN -->
## Transport handoff — Tests A and B complete

The representative Linux acceptance replay has now reproduced the deferred UDP
problem in both directions while idle.

### Test A — Linux -> onn

- 3993/4000 successful sends;
- 7 would-block;
- 3993 unique Android arrivals;
- 0 missing unique packets;
- **2626 same-stamp duplicates**;
- Android kernel p95 ~18.36 ms, max ~792.30 ms;
- 2116 clean 4-6 ms sends became kernel <2 ms;
- 190 became kernel >=20 ms.

### Test B — onn -> Linux

- 4000/4000 Android sends successful;
- 3894 unique Linux arrivals;
- 106 missing unique packets;
- **476 same-stamp duplicates**;
- Linux receive p95 ~18.14 ms, max ~173.72 ms;
- 1312 clean 4-6 ms sends became receive <2 ms;
- 126 became receive >=20 ms;
- Linux `SndbufErrors +0`, `RcvbufErrors +120`.

Interpretation:

The transport pathology is not specific to production game streaming or a
Linux-only sender. Both directions are affected on the shared home
Opal/network/radio path.

Do not tune production bitrate/FEC/audio/decoder/relay behavior yet.

Next:
1. capability probe the locally discovered default-gateway router without
   printing the gateway;
2. if router-side capture is available, perform the deferred dual-boundary
   packet capture around one synthetic direction at a time;
3. compare unique packet identities/timing at the router boundaries with the
   endpoint summaries.

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:HANDOFF:BEGIN -->
## Router localization readiness

The default gateway was discovered locally and SSH port 22 is reachable.
`ssh` is installed on the Linux host. Batch login is unavailable, so the next
step is an interactive `ssh root@<locally discovered gateway>` capability check.

Return only sanitized capability/interface names. Do not expose addresses,
SSID, MACs, or credentials.

If `tcpdump` exists, proceed to a router-side dual-boundary UDP capture using the
preserved synthetic transport probes.

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:HANDOFF:BEGIN -->
## Opal SSH handoff update

SSH/22 is reachable, but the first interactive execution probe stopped before
authentication because the Opal offered only `ssh-rsa` as its host key.

Use one-command compatibility only:

`-o HostKeyAlgorithms=+ssh-rsa`

Do not modify global `ssh_config`. Do not add `PubkeyAcceptedAlgorithms` unless
authentication later fails for a separate RSA-signature reason.

Next: rerun the sanitized capability command with that single option and confirm
`router_shell=OK` plus `tcpdump` availability.

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:HANDOFF:BEGIN -->
## Router diagnostic handoff

Authenticated Opal shell works.

Current sanitized capabilities:

- `tcpdump=UNAVAILABLE`
- `iw=AVAILABLE`
- bridge: `br-lan`
- radios: `wlan0`, `wlan1`

Use `HostKeyAlgorithms=+ssh-rsa` only per router SSH command. Do not weaken
global SSH policy.

Next diagnostic-only step:

- identify firmware release/package manager;
- report writable overlay free space;
- show bridge member interface names;
- show wireless interface type/channel only;
- check whether package indexes already advertise `tcpdump` or `tcpdump-mini`;
- do not run package update/install yet.

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:HANDOFF:BEGIN -->
## Router capture readiness handoff

Current sanitized Opal state:

- OpenWrt/LEDE;
- `opkg` present;
- ~81 MiB free overlay;
- `libpcap` installed;
- zero cached package lists;
- no installed `tcpdump`;
- `br-lan` = `eth0.1` + `wlan0` + `wlan1`;
- `wlan0` = AP channel 1;
- `wlan1` = AP channel 40.

Next:
1. temporarily populate `opkg` indexes in RAM;
2. determine whether `tcpdump-mini`/`tcpdump` is available and its installed
   size;
3. return package-list cache to the exact prior empty state;
4. map Linux and onn to radio names without exposing IP/MAC values.

Do not install a package until that probe establishes a compatible candidate.

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:HANDOFF:BEGIN -->
## Opal SSH transport handoff

Use quoted remote commands only. A control probe confirmed:

- router shell OK;
- remote command execution OK;
- `opkg` available;
- `iw` available;
- exit code 0.

The prior heredoc/stdin form is incompatible in this environment and is not a
router diagnostic result.

Next rerun the temporary package-index/radio-membership probe using the validated
quoted-command form.

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:HANDOFF:BEGIN -->
## D080 router dual-boundary diagnostic

New diagnostic files:

- `tools/run_opal_dual_boundary_probe.sh`
- `tools/analyze_opal_dual_boundary_pcap.py`

The probe temporarily installs `tcpdump-mini`, captures the existing forward
20-second UTP1 test on both Opal radios, removes the package, verifies the
installed-package set and empty package-list cache are restored, and writes
`opal_dual_boundary_summary.txt/json`.

Raw PCAPs remain local because they contain network metadata.

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:HANDOFF:BEGIN -->
## D080 first-run correction

Do not trust the first D080 classification.

Run:
`logs/transport_probe/opal_dual_boundary_20260915_102045`

Endpoint traffic was real (2971 host successes, 2971 Android unique arrivals,
5291 Android duplicates), but both router analyses matched zero UTP1 packets.

D080R1 fixes the diagnostic classifier to fail closed and adds:
- PCAP byte size;
- total PCAP record count;
- linktype;
- matched UTP1 packet count.

Next action is local re-analysis of the existing session only. No router access
or new capture is required.

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:HANDOFF:BEGIN -->
## D080 router-capture handoff

D080R1 reanalysis proved both router radio PCAPs were header-only:

- `router_linux_radio.pcap`: 24 bytes, 0 records;
- `router_onn_radio.pcap`: 24 bytes, 0 records.

Endpoint traffic was definitely present:
- 2971 host successes;
- 2971 Android unique arrivals;
- 5291 Android duplicates.

So the current problem is router capture visibility, not UTP1 parsing.

Next diagnostic:
read only the Opal acceleration/offload state and relevant fast-path modules /
services. Do not change the router yet. If acceleration is enabled, a later
controlled experiment can temporarily disable it, repeat the idle synthetic
probe, and restore the exact prior setting.

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:HANDOFF:BEGIN -->
## D081 acceleration-off probe

Run `tools/run_opal_acceleration_off_dual_boundary_probe.sh`.

It refuses unexpected pre-state, arms a 600-second router restore watchdog,
temporarily sets flow offloading 1/1 -> 0/0, invokes D080, then explicitly
restores and verifies 1/1.

Interpret capture visibility and Android duplicate metrics separately: capture
visibility improving alone does not prove acceleration caused duplication.

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:HANDOFF:BEGIN -->
## D081 result

D081 is runtime validated and restored cleanly.

Acceleration-off test:
- UCI flow offload flags: 0/0;
- `sfhnat`: still loaded;
- host sends: 3131;
- Android unique: 2944;
- Android duplicates: 5224;
- Android missing: 187;
- both router radio PCAPs: 24 bytes / zero records.

Restore verified:
- flow_offloading=1;
- flow_offloading_hw=1.

Interpretation:
The normal OpenWrt/GL.iNet offload toggles do not expose the radio path and do
not cure the UDP failure. Next inspect Siflower `sfhnat`, switch, and wireless
driver control surfaces read-only. Do not disable/unload vendor modules until
their dependencies and restore mechanism are understood.

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:HANDOFF:BEGIN -->
## Siflower inventory handoff

Validated loaded modules:
- sf16a18_hb_fmac
- sf16a18_lb_fmac
- sf16a18_rf
- sf_eswitch
- sfax8_factory_read
- sfax8_netlink
- sfhnat

`sfhnat` module parameters: none.

The prior `siflower_packages` output is invalid due to an awk syntax error.
Ignore it.

Next:
read module file paths / metadata and identify installed package ownership with
`opkg search`; do not unload modules or restart networking.

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:HANDOFF:BEGIN -->
## D082 bridge-boundary diagnostic

New files:
- `tools/run_opal_bridge_boundary_probe.sh`
- `tools/analyze_opal_bridge_boundary_pcap.py`

The probe temporarily installs `tcpdump-mini`, captures only `br-lan` during
the existing UTP1 forward test, removes the package, verifies package state
restoration, retains raw PCAP locally, and prints a sanitized summary.

No vendor module unload, wireless restart, or acceleration change occurs.

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:HANDOFF:BEGIN -->
## D083 next diagnostic

D082:
- 3661 host successful sends;
- 3661 Android unique;
- 2371 Android duplicates;
- zero Android unique loss;
- `br-lan` PCAP = 24 bytes / 0 records.

D083 files:
- `tools/run_opal_netdev_counter_probe.sh`;
- `tools/analyze_opal_netdev_counter_probe.py`.

D083 is read-only on the router. It samples sysfs counters for `wlan0`,
`wlan1`, and `br-lan` during the existing forward synthetic test.

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:HANDOFF:BEGIN -->
## D083R1

Initial D083 failed diagnostically: counter CSV had fewer than two rows, while
the runner incorrectly returned 0.

D083R1 fixes only `tools/run_opal_netdev_counter_probe.sh`:
- nohup-detached finite sampler;
- minimum 25-line retrieval gate;
- explicit compare/analyzer failure propagation.

Analyzer hash remains unchanged. Rerun D083 after installing D083R1.

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:HANDOFF:BEGIN -->
## End-of-chat handoff — transport investigation

Resume from **D082**, not D083.

Last valid result:
`logs/transport_probe/opal_bridge_20260915_141216`

- host successful sends: 3661;
- Android unique: 3661;
- Android duplicates: 2371;
- Android missing: 0;
- `br-lan` capture: 24 bytes / 0 records;
- `wlan0` and `wlan1` had already shown the same capture blindness.

D083 is invalid:
- insufficient counter CSV;
- analyzer failed;
- runner falsely exited 0.

D083R1 is invalid:
- `nohup` was assumed without capability validation;
- router has no `nohup` command or BusyBox applet;
- setup failed before sampling with `sampler_not_running`.

Smoke-test correction:
- raw `/proc/mounts` shows `/tmp` without `noexec`;
- ignore the contradictory `tmp_noexec=YES` classifier;
- direct `sh` execution did write header + three sample rows.

Do not treat the original D083 SSH-lifetime hypothesis as established.

Next chat must first decide between:
- one clearly bounded, product-relevant diagnostic; or
- deferring the Opal/Siflower-specific path and moving on.

No further router diagnostic is authorized by this handoff by default.

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:HANDOFF:END -->
