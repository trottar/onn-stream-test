---
memory_schema: 1
as_of: 2026-09-15
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Current Development State


<!-- PRIVYHUB_D079_MEMORY_CHECKPOINT_LINUX_ONN_STREAM_DIAGNOSIS_2026_09_15:CURRENT:BEGIN -->
## 2026-09-15 Linux/onn integrated game-stream diagnosis

**Status:** ACTIVE DIAGNOSIS — emulator/runtime/capture path works; representative
Linux -> onn UDP transport remains the current blocker.

Validated in the normal integrated Linux/onn path:

- D-077 Linux platform-aware RetroArch runtime selection is host validated.
- D-078 Linux companion/media-server startup seam is host validated.
- Windows-backed game/user data was restored while Linux machine-local
  `retroarch.cfg` was reconstructed with `input_joypad_driver = "udev"` and
  project-relative `joypad_autoconfig_dir`.
- Temporary development permissions were sufficient for Linux uinput and the
  D-075R1 audio RT sender (`/dev/uinput` ACL plus `RLIMIT_RTPRIO=1`).
- A real PS1 session launched, loaded an existing save, created the managed
  RetroArch X11 window, and VAAPI encoded the intended 720p60 native stream.
- Linux exact-window capture therefore is not the current failure boundary.

Current blockers/findings:

1. Android auto-open still gates on the Windows-only
   `host_window_policy.window_found`. Linux reports that legacy preflight as
   unsupported/false even though the native Linux backend later finds the
   correct X11 window. Result: the GUI first shows
   `Game ready, stream not opened` and requires manual entry into the game
   banner. This is a confirmed Linux compatibility bug, separate from the
   transport failure.
2. Once NativeStreamActivity is entered, the stream does not satisfy the
   stabilization gate. Fresh Android evidence showed substantial video/audio
   loss, long decoder/output gaps, and low delivered/rendered FPS while the
   Linux encoder itself remained near 60 fps.
3. Companion telemetry localized severe pressure at Linux UDP send boundaries:
   a video `sendto()` call reached about 785 ms and audio's independent
   nonblocking RT sender accumulated thousands of failed sends.
4. `/proc/net/snmp` repeatedly showed thousands of `Udp:SndbufErrors` and many
   more `Udp:RcvbufErrors` per short integrated run while interface
   `tx_errors`/`tx_dropped` did not increase. This localizes the observable loss
   to the Linux socket/network path before ordinary interface TX accounting.
5. Raising `net.core.rmem_max` / `wmem_max` so the application actually received
   its requested 2 MiB buffers did not improve the run and made sender behavior
   worse. Socket-cap sizing is therefore not the root cause.
6. Host Wi-Fi is a USB Realtek RTL8822BU (`0bda:b812`) on `rtw_8822bu`, USB
   SuperSpeed 5000 Mb/s. USB runtime autosuspend is disabled (`power/control=on`)
   and never suspended, so USB autosuspend/link speed is not the cause.
7. `disable_lps_deep=Y` did not materially change the failure. Deep LPS is not
   the root cause.
8. Kernel logs contain repeated
   `firmware failed to leave lps state` and one register timeout. Disabling
   ordinary NetworkManager/mac80211 Wi-Fi powersave (`802-11-wireless.powersave=2`)
   removed LPS/register warnings during the controlled test, proving a real
   RTL8822BU/rtw88 power-state problem, but UDP send/receive-buffer errors and
   audio send failures remained severe. Ordinary LPS is therefore a real
   secondary driver issue, not the primary stream-collapse cause.
9. The next transport discriminator is the repository's existing standalone
   Linux -> onn idle UDP acceptance probe: 5 ms cadence, ~1000-byte datagrams,
   Android kernel receive timestamps, outside RetroArch/MediaCodec/production
   streaming. The first Linux wrapper attempt failed before sending because its
   local onn-address discovery method returned `ONN_ADDRESS_DISCOVERY_FAILED`;
   that wrapper needs correction without asking for or exposing an IP address.

Separate PS1 migration cleanup: Beetle PSX HW reported `scph5501.bin` missing in
the integrated run. The core still launched and the save loaded, so this was not
the stream-stabilization cause, but the BIOS should be restored before PS1
acceptance is considered complete.

Do not change Android stabilization thresholds, bitrate, FEC, RetroArch, or
decoder policy based on the current failure. First characterize the
representative Linux -> onn transport independently with the preserved UDP
diagnostic suite.

<!-- PRIVYHUB_D079_MEMORY_CHECKPOINT_LINUX_ONN_STREAM_DIAGNOSIS_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D078_CURRENT -->
## D-078 Linux companion startup seam

**Status:** HOST STARTUP SEAM VALIDATED / ONN E2E PENDING

The normal Linux companion no longer depends on `powershell.exe` to start the media server. Windows preserves the existing `scripts/start_server.ps1` path; Linux directly launches the existing `companion/range_server.py` with the current Python interpreter under the same managed-process lifecycle. The D-078 live probe exercised the real `PrivyHubController.start_server()` Linux branch on a loopback-only ephemeral port, confirmed HTTP readiness, and confirmed clean stop.

Next: restart the normal companion and run the integrated onn/Linux Donkey Kong Country E2E through the normal Games product path.

## Checkpoint

- Branch: `main`
- Predecessor synchronized checkpoint for the remote-foundation promotion: `0c31c100ec721d687aff6aedbd79bc0cf9343810`
- Part 1 current-state alignment: **CHECKPOINTED / PUSHED**
- Part 2 durable-memory curation/deep history: **CHECKPOINTED / PUSHED**
- Part 3 decision/investigation normalization: **CHECKPOINTED / PUSHED**
- Part 4 top-level docs/ledgers refresh: **CHECKPOINTED / PUSHED**
- Docs/memory cleanup Parts 1-4: **COMPLETE / CHECKPOINTED**
- Minor Games cleanup (startup metadata/art reconciliation + Alpha catalog removal): **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**
- Phase A: **COMPLETE / PUSHED**
- Phase B: **COMPLETE / PUSHED**
- Phase C: **ACTIVE**

C1 minimal schema design: **COMPLETE / CHECKPOINTED / PUSHED**

C1.1 static reference profile extraction: **RUNTIME VALIDATED / CHECKPOINTED / PUSHED**

Native-stream status privacy hotfix: **LIVE ENDPOINT VALIDATED / CHECKPOINTED / PUSHED**

Next work: C3 actuator continuity diagnostic under D-062.

## Active technical step

**C2 — end-to-end transport telemetry contract**

C2.1 inventory:

`C2_INVENTORY_COMPLETE_EXISTING_FOUNDATION_WITH_GAPS` — **COMPLETE**

C2.2 design:

`C2_DESIGN_MINIMAL_STREAM_TELEMETRY_V1` — **COMPLETE / CHECKPOINTED / PUSHED**

Next production step:

`C2_IMPLEMENT_STREAM_TELEMETRY_V1`

Reuse the Phase-B 2-second client-health cadence/store. Do not create a second
Android telemetry sampler and do not add adaptive bitrate yet.

## C1 reference stream

Validated path:

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Reference values:

- 1280x720;
- 60 fps;
- 7000 kbps target;
- GOP 15;
- B-frames 0;
- FEC group size 8;
- RTP payload type 96;
- packet size 1200 bytes.

Backend policy also includes NVENC `p1`, ultra-low-latency tuning, CBR, a 1000k
buffer and yuv420p. Those are not automatically portable profile semantics.

## C1 ownership findings

- `companion/native_stream.py` — capture/session setup, reference
  quality constants, encoder/backend policy and RTP/FEC/session setup.
- `companion/native_fec_relay.py` — relay/FEC behavior and
  duplicated transport assumptions.
- Android `NativeStreamActivity.kt` — duplicated width/height/fps and endpoint
  constants.
- Android `RtpH264Receiver.kt` — receive/FEC buffering.

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

## First C1 acceptance boundary

The first implementation is behavior-preserving static extraction only:

- same 1280x720 @ 60 fps;
- same 7000 kbps target;
- same GOP 15;
- same 8+1 FEC contract;
- no GUI selector;
- no adaptive controller;
- no generalized backend framework;
- no capture/audio/controller/lifecycle redesign.

Representative regression must preserve picture, process audio, controller,
Pause/Resume, Save/Load, End/teardown and validated game/profile behavior.

## Runtime coverage to preserve

Runtime validated:

- extensive PS1 path;
- SNES normal Games path;
- 1P/2P/4P controller routing;
- Crash Bash/CTR Port-1-only manual multitap;
- Save/Load and prior saves;
- pause/resume/frozen preview;
- process audio / host coexistence;
- cheats/mods/A8 profiles;
- native streaming and teardown;
- Phase B diagnostics/Self-Test/support bundle/retention;
- native-only post-Sunshine/Moonlight regression.

Declared no-fixture gaps:

- NES — supported/configured, no local A9 fixture;
- Genesis — supported/configured, no local A9 fixture.

## Preservation boundaries

Do not reopen without new evidence:

- WGC capture;
- H.264 NVENC low-latency path;
- native process audio;
- UDP/FEC transport;
- Android hardware AVC decode;
- PHI1/ViGEm P1-P4;
- Save/Load/Pause/End;
- A8 profiles;
- PS1 Port-1-only multitap;
- Phase B diagnostics/support-bundle behavior.

## Roadmap

`docs/ROADMAP.md` roadmap v4 is authoritative.

- D — Media Library / VOD / Live TV UX
- E — Linux Migration / Native Linux Baseline
- F — Linux Core Resource Characterization & Optimization
- G — Secure Remote Access / Portable Client Foundation
- H — Extended Emulation & User-Content Import
- I — Home Infrastructure / Broader Plugin Expansion
- J — Local Intelligence / Voice / Privacy-Aware AI

Phase C remains active. Its profiles, telemetry, adaptation/FEC behavior and
streaming boundaries must be reusable for future WAN work without implementing
WAN overlay/auth/travel-router behavior during Phase C.

Home trust boundary: home Opal.

Ordinary household network: upstream only.

Tailscale is the preferred first overlay candidate, not the permanent contract.
No permanent travel-router model is selected yet.

Before Phase G WAN characterization, replay the deferred UDP suite on the
representative `Linux + home Opal + onn` path.

## Debugging and privacy rule

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**

Never ask the user to provide or paste network addresses. Shareable diagnostics
must avoid or redact them.

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

Representative game runtime regression confirmed picture, process audio,
controller input, Pause/Resume, Save/Load and End/teardown with the
reference profile/status values preserved.

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

The live native-stream status endpoint passed the bounded privacy validator:
no network identifiers, absolute paths or unsafe keyed values were exposed.

## Remote-foundation architecture decision

D-059 is accepted.

Remote implementation remains **PLANNED ONLY**.

Future Phase G separates client identity, session identity, reachable
media/audio/controller endpoints, overlay/path state and PrivyHub application
authorization. Source/request IP is not durable client identity.

Future WAN adaptation protects interactivity by degrading quality before
queue/buffer growth creates runaway latency.

The current reference session planning envelope is roughly 10-11 Mbps outbound;
this does not change the stable PCM audio path.

Documentation update status: **CHECKPOINTED / PUSHED**.

## Next technical work after architecture checkpoint

The remote-foundation architecture/roadmap promotion is checkpointed/pushed.

Resume deeper Phase C implementation under D-059. Do not implement WAN overlay,
remote authentication or travel-router routing in Phase C.

## C2 telemetry contract design

C2.1 confirmed that receiver Mbps/FPS, loss/FEC counters, decoder queue state,
stale/overflow drops, rendered continuity and receive/decode/output-gap timing
already exist in the production feedback path.

The remaining C2 implementation classes are:
- RTP inter-arrival jitter;
- control-path round trip from the existing health POST;
- signed queue-depth change derived on the companion;
- FEC-relay send pressure/timing.

The adaptation-facing measurement contract is
`privyhub_stream_telemetry_v1`, assembled companion-side from client health plus
native-stream/FEC-relay status.

No second sampler, pacing scheduler, explicit starvation counter, adaptive
controller, WAN plumbing or source-address identity is part of C2.2.

Decision: D-060.

Design status: **COMPLETE / CHECKPOINTED / PUSHED**.

## C2 stream telemetry v1 implementation

**Status:** COMPLETE / RUNTIME VALIDATED / CHECKPOINTED / PUSHED

D-060 is now implemented and runtime validated.

Validated measurement surfaces:
- receiver RFC-style inter-arrival jitter;
- previous successful client-health POST control round trip;
- signed decoder queue-depth delta;
- FEC-relay send bytes/calls/errors and send-call timing;
- companion-side `privyhub_stream_telemetry_v1`;
- `GET /diagnostics/stream-telemetry`;
- bounded runtime validator.

2026-09-14 live result:
- `C2_STREAM_TELEMETRY_RUNTIME_PASS`;
- reference profile active;
- receiver ~7.46 Mbps and ~61.35 FPS;
- inter-arrival jitter 2.399 ms;
- packet loss 0;
- unrecoverable FEC groups 0;
- sender errors 0;
- queue depth 0;
- control-path round trip 42 ms.

Representative gameplay regression also passed: picture, process audio,
controller input, Pause/Resume, Save/Load and End/teardown.

Intentionally unchanged:
- reference profile and encoder settings;
- RTP/FEC packet format/group semantics and packet scheduling;
- audio/controller/capture/ports/game lifecycle behavior;
- adaptive bitrate/FEC policy;
- WAN/overlay/session routing.

Next development step after checkpoint: **C3 adaptive bitrate**.

## C3 adaptive bitrate design / actuator gate

**Status:** C3.1 SOURCE/POLICY AUDIT COMPLETE / ACTUATOR DIAGNOSTIC NEXT

The synchronized C2 checkpoint is `da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0`.

Source audit found no live bitrate actuator in the current stream manager.

Next: `C3_ACTUATOR_CONTINUITY_PROBE`.

Keep bitrate at 7000 kbps and measure one prospective video-only actuator cycle
before changing bitrate or implementing automatic adaptation.

Do not add a guessed production minimum bitrate yet.

## C3 actuator continuity diagnostic implementation

**Status:** RUNTIME VALIDATED / INITIAL ACTUATOR STRATEGY ACCEPTED / CHECKPOINT PENDING

The first C3 actuator probe is companion-only and keeps the reference bitrate at
7000 kbps.

It adds a loopback-only diagnostic action that restarts only the WGC capture and
FFmpeg encoder while intentionally preserving:
- the existing FEC relay;
- process audio;
- persistent controller;
- RetroArch/game lifecycle.

The probe tool captures pre/post `privyhub_stream_telemetry_v1` and consumes the
existing Android decoder-session report after normal End. No Android change or
new telemetry sampler is required.

This is not production adaptation. No minimum bitrate, bitrate ladder,
controller, hysteresis or adaptive FEC is implemented.

Runtime result is required before choosing restart-based actuation.

## C3 actuator acceptance

D-063 accepts backend-neutral `video_only_restart` as the initial C3 bitrate
actuator strategy.

Windows runtime validation used the current WGC + FFmpeg/NVENC video pair while
FEC, process audio, persistent controller and the RetroArch/game session
remained alive.

The receiver recorded one sequence resync and one SSRC change, reacquired IDR in
17 ms, dropped zero packets while waiting for IDR, and ended with
`waiting_for_idr=false`. Decoder rendered 2,131 frames with zero decoder drops
and zero queue-overflow drops. Audio/controller error counters remained zero.

The session recorded a 791 ms maximum output gap and 800 ms maximum
receive-to-decode time. These measurements are retained; the transition is not
classified as mathematically seamless.

Focused play for several minutes felt normal. Possible slight stutter could not
be distinguished from existing occasional baseline stutter. No clear freeze,
black frame, audio interruption or controller stall was observed.

Linux is not runtime validated. Phase E must implement the same backend-neutral
video-only actuator boundary using the selected Linux capture/encoder backend
and rerun equivalent continuity validation.

**Next:** fixed-bitrate characterization. Establish validated lower bitrate
levels before adding a production minimum, bitrate ladder or automatic
controller.

## C3 fixed-bitrate characterization

**Status:** 5500 KBPS VALIDATED / FIXED LADDER 5500-6000-7000 / NEXT ADAPTIVE CONTROLLER

The actuator checkpoint is `20a1112831f47b0c44104d547123395a89964b8a`.

The first lower fixed test point is 6000 kbps. This is not yet a production
ladder entry.

The diagnostic starts from the normal 7000 kbps reference, uses the accepted
video-only restart boundary to move video to 6000, leaves all other stream
parameters/lifecycles unchanged, then records C2 telemetry plus the existing
Android decoder-session report.

Next evidence required: focused play at 6000, normal End, finalized probe log.

## C3 6000 kbps runtime acceptance

D-064 accepts 6000 kbps as the first validated lower C3 bitrate candidate.

Technical evidence:
- session duration 51,477 ms;
- one expected sequence resync and one SSRC change;
- resync-to-IDR 52 ms;
- zero packets dropped while waiting for IDR;
- receiver not waiting for IDR at session end;
- 2,823 decoder-rendered frames;
- one decoder drop and one queue-overflow drop;
- max output gap 1,016 ms;
- max receive-to-decode 1,025 ms;
- zero audio write errors;
- zero controller send errors.

Focused play: movement and gameplay were fine. Audio was audibly somewhat
stuttery.

Detailed audio evidence showed queue oscillation rather than an average-bandwidth
failure: 868 stale drops/smooth latency trims, queue depth 8/8, 922 concealed
underruns, 104 prolonged-starvation events, and only 11 lost audio packets.

The accepted 7000 actuator session already exhibited substantial audio
loss/underrun totals. Therefore the audio burst/gap pathology is not attributed
to the 6000 bitrate change and remains deferred for representative Linux +
Home-Opal replay.

Next: characterize exactly one lower candidate, 5000 kbps. No production minimum
or automatic controller is defined yet.

## Patch validation hardening — command warnings vs failures

A 2026-09-14 C3 acceptance installer rolled back even though `git diff --check`
succeeded, because the installer treated non-empty command output as failure.
The output contained only Git line-ending warnings.

Durable rule:
- subprocess success/failure is determined by the process exit code;
- stdout/stderr text is evidence/logging, not a failure predicate by itself;
- warnings must be retained in logs and classified separately;
- `git diff --check` fails only when its exit code is nonzero;
- every installer using command validation must regression-test both:
  - exit 0 with warnings => PASS;
  - nonzero exit => FAIL.

This rule applies to future patch/install/checkpoint tooling, not only C3.

## C3 fixed 5000 kbps characterization implementation

**Status:** DEVELOPMENT DIAGNOSTIC INSTALLED / RUNTIME EVIDENCE PENDING

Synchronized predecessor: `6e4563f7109f6dd1b4227a264e96e2acbd7e112d`.

Validated fixed levels remain:
- 7000 kbps reference/max;
- 6000 kbps validated lower candidate.

5000 kbps is the next single diagnostic candidate. It is not yet a validated
ladder level or production minimum.

The checkpointed 6000 video-cycle implementation is now shared internally by
both the 6000 and 5000 loopback-only wrappers. The existing 6000 external
diagnostic interface remains available as a regression surface.

5000 preserves:
- 1280x720;
- 60 fps;
- GOP15;
- B-frames0;
- FEC8;
- process audio;
- persistent controller;
- game/emulator lifecycle.

The final 5000 evidence log includes detailed audio queue/starvation counters,
but those known burst/gap counters do not classify the bitrate candidate unless
new evidence establishes a bitrate-specific regression.

Next evidence: focused 5000 gameplay/visual observation, normal End, finalized
5000 characterization log.

## C3 5000 kbps runtime disposition

D-065 records 5000 kbps as **not accepted as a ladder candidate in the current
test environment**.

Positive evidence:
- 17 ms resync-to-IDR;
- zero packets dropped while waiting for IDR;
- receiver recovered and remained active;
- image was subjectively clearer;
- after the initial lag period, gameplay could feel good and smooth.

Disqualifying focused observation:
- after settling, visual stutters were definitely more frequent than at the
  validated 6000/7000 settings.

Technical findings retained:
- 3,080 rendered frames;
- 11 decoder drops;
- 11 decoder queue-overflow drops;
- 1,010 ms max output gap;
- 1,019 ms max receive-to-decode;
- 100 lost video packets;
- 15 unrecoverable FEC groups.

Possible slightly worse input lag was observed but was not certain and is not
used as the rejection criterion.

Audio burst/gap behavior remains the separately deferred Linux + Home-Opal
issue and is not used to reject 5000.

The fixed-bitrate floor is now bracketed between 5000 and 6000 kbps.

Next: characterize exactly one midpoint candidate, 5500 kbps. No production
minimum or automatic controller is defined yet.

## C3 fixed 5500 kbps characterization implementation

**Status:** DEVELOPMENT DIAGNOSTIC INSTALLED / RUNTIME EVIDENCE PENDING

Synchronized predecessor: `0f0f58ef24646a72ff1aa6b769395d8d8dd06a1b`.

Current evidence:
- 7000 kbps: validated reference/max;
- 6000 kbps: validated lower candidate;
- 5000 kbps: runtime tested / not accepted because extended focused play showed
  definitely more steady-state visual stutters;
- lower-bound bracket before this test: 5000–6000 kbps.

5500 kbps is the single midpoint candidate. It is not yet a validated ladder
level or production minimum.

The existing shared fixed-bitrate video-only actuator now accepts 6000, 5000 and
5500 wrappers. No actuator-body fork was added.

5500 preserves:
- 1280x720;
- 60 fps;
- GOP15;
- B-frames0;
- FEC8;
- process audio;
- persistent controller;
- game/emulator lifecycle.

The final 5500 evidence output retains the detailed audio queue/starvation
counters, but the known burst/gap pathology remains a separate deferred Linux +
Home-Opal issue and is not an automatic bitrate rejection criterion.

Next evidence: focused 5500 gameplay/visual smoothness observation, normal End,
and finalized 5500 characterization log.

## C3 5500 kbps runtime acceptance

D-066 validates 5500 kbps as the lowest accepted fixed bitrate in the current
Windows C3 environment.

Fixed C3 ladder for controller implementation:
- 7000 kbps: validated reference/max;
- 6000 kbps: validated middle level;
- 5500 kbps: validated lower level / current Windows floor;
- 5000 kbps: runtime tested / not accepted.

5500 runtime evidence:
- 76,085 ms final decoder session;
- one expected sequence resync and SSRC change;
- resync-to-IDR 44 ms;
- zero packets dropped waiting for IDR;
- receiver not waiting for IDR at end;
- 4,088 decoder-rendered frames;
- 57 whole-session decoder drops and 57 queue-overflow drops;
- 1,026 ms max output gap;
- 1,036 ms max receive-to-decode;
- zero audio write errors;
- zero controller send errors.

The characterization tool captured six fresh post-cycle telemetry intervals from
session elapsed 5,502 through 15,536 ms. Across those intervals:
- 638 rendered frames;
- zero decoder dropped-frame deltas;
- zero queue-overflow-drop deltas;
- decoder queue depth remained zero.

The 57 whole-session decoder drops are retained as unresolved whole-session
evidence. They are not falsely attributed to the transition or erased. The
sampled post-cycle window itself was clean, and focused play reported the
initial lag recovering after a few seconds followed by excellent gameplay.

The known audio burst/gap pathology remains separately deferred to representative
Linux + Home-Opal replay.

Fixed-bitrate characterization is complete for the Windows C3 controller
prototype. Do not continue binary-searching below 5500 in this environment.

Next: implement the C3 adaptive bitrate controller over the discrete
5500/6000/7000 ladder. Linux migration must revalidate the actuator/fixed
envelope before treating these thresholds as portable constants.

## C3 startup stabilization foundation — D-067

**Status:** DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING

Authoritative predecessor: `b2f752223d0bd7617a7f7ef75c9618202d2372fa`.

Before automatic bitrate control, native startup now uses the existing paused
game as a readiness gate. Android shows `Stabilizing game…` plus basic stream
metadata and releases gameplay only after six consecutive clean 500-ms local
checks. A 15-second ceiling fails closed. Back retains the existing paused-frame
lifecycle and MainActivity reuses the same compact status model.

Windows ladder remains 5500/6000/7000; 5000 remains excluded. Automatic bitrate
switching remains disabled.

Next: runtime validate D-067 before controller implementation.

## C3 startup stabilization runtime validation — D-068

**Status:** RUNTIME VALIDATED / STARTUP LAG HIDDEN

After a clean companion restart, D-067 worked as designed: stabilization GUI
appeared, release succeeded, gameplay ran normally, and the previously observed
initial lag was not present.

The earlier `Release failed` result was caused by stale companion Python, not by
the installed D-067 source. RetroArch lifecycle evidence showed real PAUSED then
PLAYING/resume behavior matching the old running Games plugin. Restarting the
companion loaded the new `native-stream-ready` contract and resolved the issue
without another source change.

Durable rule: after companion Python changes, restart the companion before
runtime judgment.

Next: checkpoint D-067/D-068, then continue C3 adaptive bitrate controller work
over 5500/6000/7000.

## C3 bidirectional actuator validation — D-069

**Status:** DEVELOPMENT DIAGNOSTIC / RUNTIME EVIDENCE PENDING

Authoritative predecessor: `9d7da2ccc47cc78a19f7128161859a1c5f308174`.

Startup stabilization is runtime validated and the Windows fixed ladder remains
5500/6000/7000.

Before automatic policy, validate the missing actuator direction:
`7000 -> 6000 -> 7000`.

The existing shared video-only restart implementation is generalized in place;
existing 6000/5000/5500 characterization wrappers retain their reference-start
semantics.

The new transition surface is loopback-only and diagnostic. Automatic bitrate
control remains disabled.

Next evidence: run the bidirectional probe during normal gameplay, End normally,
finalize the probe, and review raw telemetry/decoder evidence plus focused
transition smoothness observation.

Restart the companion after installing this Python-side diagnostic.

## C3 bidirectional actuator disposition — D-070

**Status:** BIDIRECTIONAL RECOVERY VALIDATED / VIDEO-ONLY RESTART NOT ACCEPTED FOR AUTOMATIC ADAPTATION

D-069 completed `7000 -> 6000 -> 7000`.

Both legs recovered, but first RTP was absent for about 953 ms on the downshift
and 837 ms on the upshift. Focused play observed an approximately one-second
freeze during one shift. Final decoder evidence recorded a 1,059-ms max output
gap and 1,074-ms max receive-to-decode.

The downshift sampled recovery was clean. The first fresh upshift interval
recorded one decoder drop + one queue-overflow drop, followed by clean intervals.

Conclusion: the existing `video_only_restart` actuator is bidirectionally
functional but too disruptive for silent automatic gameplay adaptation.

Retain it as diagnostic/startup/manual/fallback capability.

Automatic controller remains blocked.

Next: determine whether the active encoder can change bitrate without replacing
the encoder process.

## D-071 Linux-first phase reorder

**Status:** ROADMAP UPDATED / WINDOWS-SPECIFIC C3 ADAPTATION PAUSED

Authoritative checkpoint beneath the current development tree:
`9d7da2ccc47cc78a19f7128161859a1c5f308174`.

D-070 remains authoritative:
- `video_only_restart` works bidirectionally;
- ~0.84–0.95 s first-RTP interruption;
- focused play observed ~1 s freeze;
- restart is retained for diagnostic/startup/manual/fallback use;
- it is not accepted for transparent automatic gameplay adaptation.

Do not pursue a Windows/NVENC-specific live-bitrate workaround.

Roadmap order is now:
- **D — Linux Migration / Native Linux Baseline**
- **E — Linux Core Resource Characterization & Optimization**
- **F — Media Library / VOD / Live TV UX**
- G onward unchanged.

Phase D preserves the currently working media/VOD/Live TV baseline while
migrating; it does not wait for Phase F polish.

Automatic bitrate/FEC continuation resumes on Linux after the real backend is
known. Revalidate the Windows bitrate envelope there before treating 5500 as a
production floor.

Next technical work after checkpoint: **Phase D Linux migration baseline**.

## D-072 Phase C resume point

**Current next work:** Phase D Linux Migration / Native Linux Baseline.

Phase C is **PAUSED / NOT COMPLETE** at the Windows boundary.

After the Phase D Linux baseline checkpoint, resume the remaining Phase C work
on Linux before Phase E:
- C3 automatic bitrate controller;
- C4 adaptive FEC or evidence-backed deferral;
- C5 1080p60 characterization;
- C6 generalized source abstraction;
- C7 final Phase C checkpoint.

Then proceed to Phase E Linux characterization/optimization, followed by Phase F
media/VOD/Live TV UX.

## D-073 Linux baseline — emulator/runtime boundary validated

**Status:** PHASE D ACTIVE / CORE LINUX EMULATOR LIFECYCLE RUNTIME-VALIDATED

The Debian host now has a validated project-owned RetroArch 1.22.2 Linux runtime with all four required cores.

Validated Linux foundations:
- Renoir VAAPI H.264 encode;
- exact X11 RetroArch window capture;
- mapped-window lifecycle requirement;
- PulseAudio isolated-capture architecture;
- four simultaneous uinput gamepads;
- RetroArch udev enumeration/autoconfig;
- real SNES video/audio runtime;
- real-game 720p60 VAAPI capture;
- current native/emulator Python modules import on Linux;
- existing `EmulatorManager` launch/control/flush/stop lifecycle works unchanged on Linux.

Windows durable RetroArch state was migrated byte-for-byte:
129 files, manifest SHA-256
`6de3fa8b67d5a0ee21ace20af9347b5cf0f5997f3a9d410fcd23d6410b18280c`.

Do not port or replace `EmulatorManager` without new evidence.

Remaining Linux production surfaces:
1. platform-aware runtime/config selection;
2. X11/VAAPI native video backend;
3. PulseAudio native audio backend;
4. PHI1 -> uinput controller backend — D-076/R1/R2 host-side managed runtime validated; onn E2E pending;
5. Linux host telemetry;
6. persistent service-user/device permissions;
7. save/state/profile regression validation through the migrated project data.

Next technical work: checkpoint D-076/R1/R2 host-side validation, then run full onn Linux E2E.

## D-074 Linux native-video backend development patch

**Status:** SUPERSEDED — SEE HOST-SIDE RUNTIME VALIDATION BELOW

D-074 adds the first production Linux native-video seam while preserving the
validated Windows path.

Linux video shape:
`EmulatorManager PID -> exact owned X11 window -> one FFmpeg x11grab/VAAPI
process -> existing RTP/XOR-FEC relay -> unchanged Android receiver`.

The managed RetroArch PID is supplied only by the internal Games plugin after
`EmulatorManager.status()` reports an active game. Linux window discovery
remains fail-closed and never falls back to desktop capture.

Intentionally unchanged:
- Android video/audio/controller code;
- PHI1 protocol;
- FEC wire format and relay;
- Windows WGC/NVENC start path;
- RetroArch lifecycle manager;
- Linux audio, controller output and host telemetry.

Next runtime validation: launch a managed game, start the Linux native stream
against a loopback receiver, verify active/status/FEC/bootstrap behavior, then
stop normally and inspect `logs/games/native_video_alpha.log`.

## D-074 Linux native video backend

**Status:** HOST-SIDE RUNTIME VALIDATED

Production Linux native video now uses the trusted EmulatorManager-owned
RetroArch PID to select an exact visible X11 window, then runs one FFmpeg
x11grab -> Renoir VAAPI H.264 process into the existing RTP/FEC relay.

Runtime validation with real SNES content passed:
- active x11grab/VAAPI stream;
- 4,500 RTP packets;
- 680 PHF1 parity packets;
- zero skipped relay packets;
- zero relay send errors;
- clean managed stream teardown;
- graceful RetroArch shutdown.

No Linux WGC-equivalent capture bridge is required.

Full Android/onn E2E remains pending.

Next Phase D production seam: Linux audio.

## D-075 Linux native-audio backend development patch

**Status:** DEVELOPMENT-ONLY / INSTALL VALIDATED / RUNTIME E2E PENDING

Baselines 32-34 established the production Linux audio boundary:
- the EmulatorManager-owned RetroArch PID resolves to exactly one PulseAudio
  sink-input;
- that exact stream can be moved into a dedicated 48 kHz stereo PrivyHub sink;
- the dedicated monitor supplies useful PCM;
- a simple sleep pacer was rejected due burst/gap scheduling jitter;
- the hybrid monotonic 5 ms pacer produced 1,000/1,000 packets with no malformed
  packets, sequence gaps, sub-2 ms bursts, or >=8 ms gaps.

D-075 implements only the Linux audio backend inside `NativeAudioStreamer`:
`managed PID -> exact PulseAudio sink-input -> dedicated sink -> monitor ->
FFmpeg PCM16 -> hybrid 5 ms PHA1 sender`.

Windows WASAPI process-loopback remains unchanged. Android audio, PHI1,
video/FEC, controller output, telemetry, and EmulatorManager remain unchanged.

Next runtime validation: start the real native stream through the existing
paused stabilization flow, verify Linux audio is active while paused, resume the
game, observe valid/non-silent PHA1 traffic and timing metrics, then verify route
restoration and clean teardown.
## D-075R1 Linux native-audio RT pacer correction

**Status:** RUNTIME VALIDATED

D-075's Linux audio route and PHA1 framing are functionally validated, but the
first production runtime exposed sender cadence jitter under active RetroArch.
Baselines 35-39 rejected video/FEC, PulseAudio routing, PCM lock contention,
Python switch-interval tuning, and wait-primitive tuning as root causes.

Baselines 40-41 established the correction:
- active RetroArch makes a normal `SCHED_OTHER` 5 ms userspace pacer unreliable;
- `SCHED_RR` priority 1 restores stable sender timing;
- only the PHA1 sender thread needs promotion; the main companion thread remains
  `SCHED_OTHER`;
- Baseline 41 delivered 1,000/1,000 packets with p95 5.0318 ms, max 5.116 ms,
  zero sub-2 ms intervals, and zero >=8 ms intervals.

D-075R1 promotes only the Linux PHA1 sender thread to `SCHED_RR/1`, verifies the
policy before sending, and exposes scheduler state in timing/status evidence.
Production code never invokes `sudo`. Runtime permission must be scoped to the
PrivyHub process/service with `RLIMIT_RTPRIO=1`; persistent service configuration
remains a later Phase D task.

Next: runtime-revalidate the full native stream with a temporary process-scoped
`RLIMIT_RTPRIO=1`, then record acceptance before committing.

## D-076 Linux uinput controller backend

**Status:** HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING

Baselines 42-45 established the Linux controller contract before production
modification: exact Linux button/axis layout, 20/20 PHI1/XUSB-to-uinput control
translation, deterministic four-pad RetroArch port ordering, and a validated
project-relative udev autoconfig path.

D-076 preserves Android PHI1 and the Windows ViGEm backend while adding a Linux
`python3-evdev`/uinput backend inside the existing `NativeControllerBridge`.
P1-P4 are created before RetroArch through the already-validated controller
preflight edge. Existing `vigem_updates*` status fields remain compatibility
aliases while backend-neutral update fields and a Linux backend identifier are
reported.

Runtime acceptance still requires real managed gameplay, trigger behavior,
Save/Load/Pause/End hotkeys, four-player ordering, cleanup, and confirmation that
the validated Linux video/audio paths remain unaffected. Durable `/dev/uinput`
permission is still a later service-permission item; production code does not
invoke `sudo`.

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

## D-076 authoritative host-side managed runtime result

D-076/R1/R2 are host-side managed-runtime validated. Fresh managed RetroArch
evidence established P1-P4 in ports 1-4, eight live PHI1 packets with zero bad
packets and two updates per player, Pause -> PAUSED, Resume -> PLAYING, a real
284304-byte slot-0 `.state` save, loading of that same 284304-byte `.state`,
`SAVE_FILES` -> `OK`, graceful SIGTERM shutdown with return code 0, and complete
virtual-pad cleanup.

The managed probe's final `validated=False` is a diagnostic-classifier defect:
it matched `.state.png` as the saved state and incorrectly required the optional
controller `quit` chord. The normal production End path is
`EmulatorManager.stop()` and passed gracefully. Do not reopen D-076 host-side
controller architecture without contradictory runtime evidence. Full Android/onn
Linux E2E remains pending.

## D-077 Linux platform-aware RetroArch runtime selection

**Status after successful installer validation:** NORMAL-PATH RUNTIME SELECTION VALIDATED / ONN E2E PENDING

The source audit found that the normal `GamesPlugin` constructs
`EmulatorManager(project_root)` while the tracked base descriptor still names
the Windows RetroArch executable and `.dll` cores. Earlier Linux host probes
supplied temporary descriptors, so they did not close this product-path seam.

D-077 keeps the Windows descriptor fields as the default contract and adds a
trusted `platforms.linux` override for the already validated Linux AppImage,
`cores-linux` directory and four `.so` cores. `EmulatorManager` now builds one
effective config before readiness and launch resolution. This is required because
`_resolve_game()` reads the selected core from `runtime["config"]["systems"]`.

The D-077 installer runs both an isolated Linux/Windows selection fixture and a
read-only live normal-path probe. It remains installed only if
`EmulatorManager(project_root)` reports the Linux runtime ready with all four
Linux cores present.

Intentionally unchanged: Games launch ordering, emulator lifecycle,
Save/Load/Pause/End, cheat/mod/profile behavior, D-074 video, D-075R1 audio,
D-076 controller output, Android, FEC/wire formats, host telemetry and persistent
service/device permissions.

**Next:** integrated onn Linux E2E using the normal product path.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:CURRENT:BEGIN -->
## Linux -> onn idle UDP Test A — reproduced transport pathology

**Status:** RUNTIME DIAGNOSTIC VALIDATED / BLOCKING TRANSPORT INVESTIGATION

The repository's preserved Linux acceptance Test A was run idle, outside
RetroArch/MediaCodec/production native streaming:

- 20 s requested;
- 5 ms cadence;
- 4000 planned ~1000-byte UDP datagrams;
- Linux nonblocking sender;
- Android kernel receive timestamps.

Result:

- host successful sends: 3993/4000;
- host `would_block`: 7;
- host send p95: ~5.015 ms;
- host send-call max: ~128.8 us;
- Android unique arrivals: 3993;
- host-success packets missing on Android: 0;
- Android duplicate arrivals: **2626**, all same host packet stamp;
- Android kernel arrival p95: ~18.36 ms;
- Android kernel arrival max: ~792.30 ms;
- sender-clean 4-6 ms -> Android kernel <2 ms: 2116 intervals;
- sender-clean 4-6 ms -> Android kernel >=20 ms: 190 intervals;
- Linux UDP `SndbufErrors`: +7;
- Linux UDP `RcvbufErrors`: +0.

Interpretation:

The transport pathology exists on the representative Linux + home Opal + onn
path even while idle. Linux sender pacing is clean, all successfully sent unique
packets arrive, but the external path converts the cadence into strong
burst/gap behavior and delivers a very large number of same-stamp duplicates
before the Android kernel receive boundary.

This satisfies the 2026-09-07 deferred transport investigation's explicit Linux
resume criterion. Production-stream socket errors are load-amplified symptoms,
not a prerequisite for the underlying pathology.

Do not rerun the Android low-latency Wi-Fi lock as the next step merely because
Test A reproduced: the prior transport investigation already tested
`WIFI_MODE_FULL_LOW_LATENCY` and found no meaningful forward-path improvement.

**Next:** run preserved Test B — onn -> Linux idle reverse UDP — using the
existing Android nonblocking `DatagramChannel` sender and Linux receiver. This
will determine whether the representative Linux path is again bidirectionally
distorted/duplicating before any production-stream change.

<!-- PRIVYHUB_D079R1_MEMORY_CHECKPOINT_LINUX_IDLE_UDP_TEST_A_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:CURRENT:BEGIN -->
## onn -> Linux idle UDP Test B — bidirectional pathology confirmed

**Status:** RUNTIME DIAGNOSTIC VALIDATED / ROUTER-BOUNDARY LOCALIZATION NEXT

The preserved reverse idle UDP probe was run on the representative
Linux + home Opal + onn path with no game/native-stream load.

Result:

- Android sender attempts: 4000;
- Android successful sends: 4000;
- Linux unique arrivals: 3894;
- missing unique packets on Linux: 106;
- Linux duplicate arrivals: 476;
- same-stamp duplicates: 476;
- Android send-completion p95: ~6.275 ms;
- Android send-completion max: ~29.424 ms;
- Linux receive p95: ~18.143 ms;
- Linux receive max: ~173.722 ms;
- sender-clean 4-6 ms -> Linux receive <2 ms: 1312 intervals;
- sender-clean 4-6 ms -> Linux receive >=20 ms: 126 intervals;
- Linux UDP `SndbufErrors`: +0;
- Linux UDP `RcvbufErrors`: +120.

Combined with Test A, the representative path now reproduces the old transport
pathology in **both directions while idle**:

- Linux -> onn: clean sender, zero unique loss, 2626 same-stamp duplicates,
  severe kernel burst/gap transformation.
- onn -> Linux: all Android sends succeeded, 106 unique packets missing,
  476 same-stamp duplicates, severe Linux receive burst/gap transformation.

This satisfies both explicit Linux resume criteria from the 2026-09-07 deferred
transport investigation. The current primary boundary is no longer production
streaming, RetroArch, Linux video/audio implementation, or a Linux-only sender.
The shared unresolved region is the home Opal/network path plus endpoint
Wi-Fi/radio/driver internals.

Do not change bitrate/FEC/decoder/audio/relay policy to mask this environment
before localizing the shared path.

**Next narrow diagnostic:** determine whether the home Opal exposes a usable
router-side packet-capture boundary (SSH/tcpdump or equivalent) using only the
locally discovered default gateway. Do not ask for or print router/client IP
addresses. If router capture is available, run the previously deferred
dual-boundary capture to determine whether duplicates/timing distortion are
already present on the router-facing ingress/egress sides.

<!-- PRIVYHUB_D079R2_MEMORY_CHECKPOINT_LINUX_REVERSE_IDLE_UDP_TEST_B_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:CURRENT:BEGIN -->
## Opal router capability checkpoint

**Status:** ROUTER BOUNDARY LOCALIZATION AVAILABLE IN PRINCIPLE

From the Linux host, the locally discovered default gateway was validated without
printing or persisting its address. Results:

- default-gateway discovery: OK;
- local SSH client: available;
- TCP/22 on the gateway: reachable/open;
- noninteractive batch login: not authorized / unavailable.

Interpretation:

The next router-boundary diagnostic is not blocked by network reachability.
Authentication is required before confirming whether the Opal shell exposes
`tcpdump` and the relevant bridge/radio interface names.

Next step is one interactive SSH capability command using the router password
locally. Do not request, print, or persist the password, gateway address, SSID,
or MAC addresses.

<!-- PRIVYHUB_D079R3_MEMORY_CHECKPOINT_OPAL_SSH_CAPABILITY_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:CURRENT:BEGIN -->
## Opal SSH negotiation finding

The first authenticated-shell attempt did not reach authentication. The Linux
OpenSSH client rejected the router's offered host-key algorithm:

`no matching host key type found. Their offer: ssh-rsa`

This is a client/server algorithm-negotiation issue, not a credential failure.

Next probe: enable `ssh-rsa` only for the single diagnostic invocation using
`-o HostKeyAlgorithms=+ssh-rsa`. Do not weaken global SSH configuration and do
not add `PubkeyAcceptedAlgorithms` unless a later, distinct user-authentication
error specifically requires it.

<!-- PRIVYHUB_D079R4_MEMORY_CHECKPOINT_OPAL_SSH_RSA_NEGOTIATION_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:CURRENT:BEGIN -->
## Opal authenticated capability result

Authenticated router shell access is now confirmed using a per-invocation
`HostKeyAlgorithms=+ssh-rsa` compatibility exception.

Sanitized capability result:

- router shell: OK;
- `tcpdump`: unavailable;
- `iw`: available;
- bridge: `br-lan`;
- wireless interfaces: `wlan0`, `wlan1`;
- visible network interfaces include `br-lan`, `eth0`, VLAN interfaces,
  `wlan0`, and `wlan1`.

No router configuration was changed.

Router-side dual-boundary capture remains the next localization target, but
capture-tool installation must not be assumed. First inspect the actual
firmware/package-manager state, writable free space, bridge membership, and
sanitized radio roles. Only after that evidence should a temporary
`tcpdump`/`tcpdump-mini` install be considered.

<!-- PRIVYHUB_D079R5_MEMORY_CHECKPOINT_OPAL_AUTH_CAPABILITIES_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:CURRENT:BEGIN -->
## Opal capture readiness — package/topology state

Authenticated read-only router inspection established:

- firmware identifies as OpenWrt / LEDE;
- package manager: `opkg`;
- writable overlay: ~88,996 KiB total / ~82,976 KiB free;
- cached package lists: 0;
- `libpcap` already installed;
- `tcpdump` not present and no candidate can be inferred from an empty cache;
- `br-lan` members: `eth0.1`, `wlan0`, `wlan1`;
- `wlan0`: AP, channel 1 (2.4 GHz);
- `wlan1`: AP, channel 40 (5 GHz).

No router configuration or package state was changed.

Next diagnostic may temporarily run `opkg update`, inspect `tcpdump` /
`tcpdump-mini` candidates, and restore the package-list cache to its prior empty
state. In the same run, map the Linux and onn endpoints to `wlan0`/`wlan1`
without printing their addresses or MACs.

<!-- PRIVYHUB_D079R6_MEMORY_CHECKPOINT_OPAL_CAPTURE_READINESS_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:CURRENT:BEGIN -->
## Opal SSH command-transport compatibility

The prior combined package/radio probe failed with SSH exit 255 when the remote
script was supplied through stdin/heredoc. A narrow control probe using the same
router, authentication method and `ssh-rsa` host-key compatibility but a quoted
remote command succeeded:

- `router_shell=OK`
- `remote_command_transport=OK`
- `opkg=AVAILABLE`
- `iw=AVAILABLE`
- `ssh_exit_code=0`

Therefore the router/authentication path is healthy. The failed probe was an SSH
invocation-shape problem, not router reachability, credentials, `opkg`, or `iw`.

Use quoted remote commands for subsequent Opal diagnostics. Avoid stdin/heredoc
remote-script transport on this router/client combination.

<!-- PRIVYHUB_D079R7_MEMORY_CHECKPOINT_OPAL_SSH_COMMAND_TRANSPORT_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:CURRENT:BEGIN -->
## Opal package/radio mapping and dual-boundary probe

Validated router package/radio probe:

- temporary `opkg update`: success;
- both `tcpdump-mini` and `tcpdump` available in configured feeds;
- package-list cache restored from 0 files back to 0;
- Linux endpoint associated with `wlan0`;
- onn endpoint associated with `wlan1`;
- endpoints therefore cross the Opal bridge between different radio interfaces.

D080 adds a diagnostic-only dual-boundary forward probe. It captures UTP1
traffic separately on the Linux-facing and onn-facing Opal radios and compares
those captures with the existing Android receiver result. Raw PCAPs remain
local; the shareable output is sanitized.

<!-- PRIVYHUB_D080_OPAL_DUAL_BOUNDARY_PROBE_01_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:CURRENT:BEGIN -->
## D080 first router capture — classification invalidated

The first D080 runtime capture completed end-to-end and restored router package
state, but its localization classification is **invalid**.

Measured endpoint result during the run:

- host successful sends: 2971/4000;
- Android unique arrivals: 2971;
- Android duplicates: 5291;
- Android missing successful unique sends: 0.

However both router PCAP analyses reported **zero matched UTP1 packets**:

- Linux-facing radio unique UTP1 sequences: 0;
- onn-facing radio unique UTP1 sequences: 0.

Therefore `ROUTER_BOUNDARIES_CLEAN_DUPLICATION_DOWNSTREAM_OF_ONN_FACING_BOUNDARY`
was a fail-open classifier error and must not be used as evidence.

D080R1 changes only the analyzer so router localization fails closed when either
boundary has zero UTP1 or insufficient coverage. It also reports raw PCAP byte
size, total PCAP record count, linktype, and matched UTP1 count.

**Next:** re-run the corrected analyzer against the existing
`logs/transport_probe/opal_dual_boundary_20260915_102045` session. Do not run
another network capture yet. The immediate question is whether the PCAPs are
header-only/empty or contain packets the UTP1 parser did not recognize.

<!-- PRIVYHUB_D080R1_OPAL_DUAL_BOUNDARY_ANALYZER_FAIL_CLOSED_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:CURRENT:BEGIN -->
## D080R1 reanalysis — router PCAPs were truly empty

Existing session:
`logs/transport_probe/opal_dual_boundary_20260915_102045`

Corrected analyzer result:

- host successful sends: 2971;
- Android unique arrivals: 2971;
- Android duplicates: 5291;
- Android missing successful unique sends: 0;
- Linux-facing Opal PCAP: 24 bytes, 0 records, Ethernet linktype 1;
- onn-facing Opal PCAP: 24 bytes, 0 records, Ethernet linktype 1;
- classification:
  `INVALID_ROUTER_CAPTURE_NO_UTP1_AT_ONE_OR_BOTH_BOUNDARIES`.

Therefore the first router capture did not merely fail to parse UTP1; both PCAPs
were header-only and observed no frames at the selected per-radio AF_PACKET /
libpcap boundaries.

The previous downstream-of-router classification is withdrawn and superseded.

**Next narrow hypothesis:** Opal flow/network/hardware acceleration or another
proprietary fast path may bypass ordinary per-radio Linux capture visibility.
First inspect acceleration/offload state read-only. Do not disable or change
router acceleration until the actual current state is measured.

<!-- PRIVYHUB_D080R2_MEMORY_CHECKPOINT_EMPTY_OPAL_PCAPS_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:CURRENT:BEGIN -->
## Opal acceleration state and D081 controlled experiment

Read-only acceleration inspection established:

- `firewall.@defaults[0].flow_offloading=1`;
- `firewall.@defaults[0].flow_offloading_hw=1`;
- kernel modules include `sfhnat` and `cls_flow`.

Together with D080R1's header-only radio PCAPs, active acceleration / fast-path
forwarding is the leading hypothesis for capture blindness. It remains only a
hypothesis for duplicate/burst behavior itself.

D081 temporarily sets both offload flags to 0, repeats the existing D080 probe,
and restores exact prior 1/1 state. A 600-second router-side restore watchdog is
armed before the change.

<!-- PRIVYHUB_D081_OPAL_ACCELERATION_OFF_DUAL_BOUNDARY_PROBE_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:CURRENT:BEGIN -->
## D081 acceleration-off result — UCI offload flags falsified

D081 completed and restored the exact original Opal acceleration state.

Temporary test state:
- `flow_offloading`: 1 -> 0;
- `flow_offloading_hw`: 1 -> 0;
- `sfhnat` remained loaded.

Synthetic Linux->onn result while both UCI offload flags were disabled:
- host successful sends: 3131 / 4000;
- Android unique arrivals: 2944;
- Android duplicates: 5224;
- Android missing successful unique sends: 187.

Router radio captures remained header-only:
- Linux-facing PCAP: 24 bytes, 0 records;
- onn-facing PCAP: 24 bytes, 0 records.

Restore:
- `flow_offloading=1`;
- `flow_offloading_hw=1`;
- explicit restore verified;
- D081 completed with exit 0.

Conclusion:
The OpenWrt software/hardware flow-offload UCI flags are not sufficient to
restore per-radio capture visibility and are not the primary explanation for
the UDP duplicate/burst pathology. Do not use disabling these flags as a
PrivyHub mitigation.

Next target is the Siflower/vendor forwarding path (`sfhnat`, Siflower switch /
Wi-Fi drivers, and any proprietary fast-path control surfaces). Inspect it
read-only before attempting another reversible change.

<!-- PRIVYHUB_D081R1_MEMORY_CHECKPOINT_ACCELERATION_OFF_FALSIFIED_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:CURRENT:BEGIN -->
## Siflower fast-path inventory checkpoint

Read-only Opal inventory established these valid facts:

Loaded vendor modules:
- `sf16a18_hb_fmac`;
- `sf16a18_lb_fmac`;
- `sf16a18_rf`;
- `sf_eswitch`;
- `sfax8_factory_read`;
- `sfax8_netlink`;
- `sfhnat`.

`sfhnat` exposes no entries under `/sys/module/sfhnat/parameters`.

Other valid observations:
- `/sys/module/sfhnat/drivers/platform:sf_hnat` exists;
- standard `bridge` userspace command is unavailable;
- no vendor script references were returned by the limited grep probe.

The `siflower_packages` subsection from this probe is **invalid** because its
awk command had a quoting/syntax error (`Unexpected end of string`). Do not use
that subsection as evidence.

Next narrow step:
map the actual loaded Siflower `.ko` files to installed package ownership and
module metadata with `opkg search` / `modinfo`. Keep this read-only.

<!-- PRIVYHUB_D081R2_MEMORY_CHECKPOINT_SIFLOWER_INVENTORY_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:CURRENT:BEGIN -->
## D082 Opal bridge-boundary probe

Validated Siflower ownership discovery established:

- `sfhnat.ko` -> `kmod-sf_hnat`;
- `sf_eswitch.ko` -> `kmod-sf_eswitch`;
- `sfax8_netlink.ko` -> `kmod-sf_netlink`;
- `sf16a18_rf.ko` -> `kmod-sf_smac`;
- `sfax8_factory_read.ko` -> `kmod-sfax8-factory-read`;
- high/low-band FMAC modules are loaded but not present as standalone `.ko`
  files through the normal module lookup;
- RF/factory modules are held by the Wi-Fi stack.

Because the Wi-Fi stack is coupled and per-radio tcpdump is blind, do not
unload Wi-Fi/RF modules.

D082 adds one narrow diagnostic: capture the existing Linux->onn UTP1 probe on
`br-lan` only.

Interpretation:
- populated `br-lan` + empty radio captures -> per-radio/vendor-driver capture
  limitation;
- empty `br-lan` too -> much stronger evidence that the Siflower forwarding
  path bypasses the ordinary Linux bridge observation point.

<!-- PRIVYHUB_D082_OPAL_BRIDGE_BOUNDARY_PROBE_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:CURRENT:BEGIN -->
## D082 result and D083 netdev-accounting probe

D082 runtime result:

- host successful sends: 3661;
- Android unique arrivals: 3661;
- Android duplicates: 2371;
- Android missing successful unique sends: 0;
- `br-lan` PCAP: 24 bytes, zero packet records;
- classification: `BRIDGE_CAPTURE_EMPTY`.

Combined with D080/D081:
`wlan0`, `wlan1`, and `br-lan` are all AF_PACKET/tcpdump-blind while the
synthetic traffic reaches Android.

D083 adds a read-only counter probe. It samples standard sysfs netdev counters
for `wlan0`, `wlan1`, and `br-lan` once per second while the same synthetic
traffic runs. No router package, module, wireless, firewall, or acceleration
setting is changed.

Purpose:
distinguish packet-capture hook bypass from forwarding that also bypasses normal
Linux netdev accounting.

<!-- PRIVYHUB_D083_OPAL_NETDEV_COUNTER_PROBE_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:CURRENT:BEGIN -->
## D083 first runtime failure and D083R1 fix

D083's first runtime attempt did not produce valid netdev-counter evidence.

Observed:
- host synthetic sender completed 3780 / 4000 sends;
- router sampler setup initially reported OK;
- retrieved counter CSV contained fewer than two data rows;
- analyzer correctly refused the insufficient file;
- outer runner nevertheless returned exit 0.

Source inspection found two deterministic diagnostic defects:
1. the router sampler was a plain background subshell tied to the SSH setup
   session and was not protected from session teardown;
2. analyzer failure was not propagated, so later cleanup caused an incorrect
   successful runner exit.

D083R1 changes only the diagnostic runner:
- launch the finite 32-sample router sampler under `nohup`;
- require at least 25 CSV lines before accepting retrieval;
- fail closed on comparison or analyzer failure;
- leave the analyzer and production code unchanged.

The failed D083 run is diagnostic-only and provides no counter-path conclusion.

<!-- PRIVYHUB_D083R1_NETDEV_SAMPLER_LIFETIME_FIX_2026_09_15:CURRENT:END -->

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:CURRENT:BEGIN -->
## D083 diagnostic closeout — investigation paused

D083 and D083R1 produced **no valid netdev-accounting evidence** and must not
be used to reason about the transport path.

Authoritative last valid transport localization result remains D082:

- session: `logs/transport_probe/opal_bridge_20260915_141216`;
- host successful sends: 3661;
- Android unique arrivals: 3661;
- Android duplicate arrivals: 2371;
- Android missing successful unique sends: 0;
- `br-lan` PCAP: 24-byte global header, zero packet records;
- prior `wlan0` and `wlan1` captures were likewise zero-record PCAPs.

D083 first run:
- sender completed 3780 / 4000;
- retrieved router counter CSV had fewer than two rows;
- analyzer rejected it;
- runner incorrectly returned exit 0.
No counter-path conclusion is valid.

D083R1 first rerun:
- setup failed immediately with `counter_setup=FAILED:sampler_not_running`;
- runner correctly returned exit 1;
- no network measurement was produced.

Follow-up smoke test established:
- `nohup` command: unavailable;
- BusyBox `nohup` applet: unavailable;
- direct `sh` sampler control wrote four CSV lines (header plus three samples);
- the raw `/proc/mounts` line for `/tmp` is
  `tmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0`;
- therefore the smoke probe's derived `tmp_noexec=YES` classification
  contradicted raw evidence and is **invalid**.

The earlier D083R1 memory statement that the original D083 sampler died because
it was tied to SSH session teardown was a hypothesis, not a proven result.
Supersede it with this closeout.

Current project state:
- transport issue remains unresolved;
- Siflower/Opal investigation is **paused at D082 evidence**;
- do not run or extend D083/D083R1 without first deciding whether another
  bounded router diagnostic is worth the product-level value;
- do not begin proprietary Siflower reverse engineering by default.

<!-- PRIVYHUB_D083_CLOSEOUT_INVALID_DIAGNOSTICS_2026_09_15:CURRENT:END -->
