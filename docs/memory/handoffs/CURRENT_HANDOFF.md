---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Current Handoff

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
