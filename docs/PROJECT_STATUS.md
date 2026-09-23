# Project status — 2026-09-22

<!-- PRIVYHUB_D_BASE_STATUS:PROJECT_STATUS:BEGIN -->
## 2026-09-22 baseline stream health update

This section supersedes every older statement below where it conflicts,
including the 2026-09-16 block. Its authority is the evidence directory:
`docs/memory/evidence/`, one record per item, listed in
`docs/memory/CURRENT.md`.

**The production topology is the Linux host wired directly into the Opal,
onn wireless, one hop** (`D-BASE-B2`, 2026-09-21). Everything measured
before that date ran host -> Windows PC -> Opal -> onn, and that machine's
transport pathology is a **separate, still-open note** — see
`KNOWN_ISSUES.md`.

**The loss on that path is explained and fixed.** The mechanism, in two
sentences: the CBR encoder emits one frame in a hundred as an 80-plus
packet micro-burst at line rate, and that burst overflows the wireless
hop's per-station queue, which the client sees as a forward gap. Capping
the encoder's largest frame bounds the burst — `D-BASE-P6` (2026-09-21)
did it by intervention and removed **100 % of the >= 80-packet frames and
7-9 x of the packet loss, twice**, with achieved bitrate, fps, encoder CPU
and GPU power unchanged.

**`max_frame_size_bytes = 90,000` is a declared field of the reference
profile** since `D-BASE-P6a` (2026-09-22), in force with nothing set in
the environment, adopted after the user's own perceptual check. `D-BASE-S3`
(2026-09-22) held it for three hours: **5.4 losses/min**, zero resyncs,
zero client socket drops, fps 59.96, and **the residual tracks nothing**
(every Spearman under 0.08) — the loss column is closed at this level.
The loss mechanism's records are `D_BASE_P5_WHICH_QUEUE_2026-09-21.md`
(which queue) and `D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md` (the
control).

**Phase C is SUSPENDED** until the baseline-stream-health target table in
`docs/memory/investigations/BASELINE_STREAM_HEALTH.md` is met or the
attempt is formally abandoned. Decision:
`docs/memory/decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`.

### What is runtime validated, and by what

| item | state | record |
| --- | --- | --- |
| Linux host on the production path | measured | `B2_HOST_ON_OPAL_2026-09-21.md` |
| 90 KB frame cap as profile default | RUNTIME VALIDATED | `D_BASE_P6A_CAP_ADOPTED_2026-09-22.md` |
| Audio redundancy 2 / 4 as profile default (`P10`) | ADOPTED by the user 2026-09-23 — warm audio loss −96-98 %, +1.6 Mbps | `D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md` |
| Audio cushion 12 / 17 as profile default (`P9`, `P9a`, `T2` Part 0) | ADOPTED by the user 2026-09-23 — +33.5-37.9 ms, starvation -98-99.5 % | `D_BASE_P9A_CUSHION_INTERLEAVED_2026-09-23.md` |
| the cap over three hours | SOAK VALIDATED | `D_BASE_S3_CAP_SOAK_2026-09-22.md` |
| recovery state machine (`GIVE_UP_MS` path, backoff, `.state.recovery`) | RUNTIME VALIDATED on real link failure | `D_BASE_R3_*`, `D_BASE_R3A_*`, `D_BASE_S2_*` |
| heartbeat loss counters (schema v2, now v3) | RUNTIME VALIDATED | `D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md` |
| heartbeat audio counters, schema **v3** | RUNTIME VALIDATED | `D_BASE_P7_STARVATION_COUNTER_2026-09-22.md` |
| terminal-stall report fields | RUNTIME VALIDATED | `D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md` |
| host thermal telemetry; the onn reports **status only** | RUNTIME VALIDATED / absence recorded | `D_BASE_T1_*_2026-09-21.md` |
| per-frame packet and byte counters | RUNTIME VALIDATED | `D_BASE_P5_*`, `D_BASE_P6_*` |
| audio startup hold | **DEVELOPMENT-ONLY**, not reverted | `D_BASE_P2A_*`, `D_BASE_P2B_*` |
| `prolonged_starvation_events` | CHARACTERIZED — a jitter rate, not a fault | `D_BASE_P7_*_2026-09-22.md` |
| host display / boot path before the headless cutover | INVENTORY RECORDED | `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md` |

**Deferred or not yet run:** `D-BASE-R3b` (nftables loss injection — the
sudoers rule is in place, the session classifier refuses the write, so it
is a by-hand item), `END_MS` and the `GIVE_UP_MS` recovery save, thermal
thresholds, the `host_link` report field, `B1`/`B3`, and the cause of the
55-60 ms audio arrival hole `P7` could not locate.

**Next:** the SSH console (`H1`, the user's step — `openssh-server` is not
installed) and then the headless cutover (`H2`) once the DisplayPort dummy
plug is installed.
<!-- PRIVYHUB_D_BASE_STATUS:PROJECT_STATUS:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:PROJECT_STATUS:BEGIN -->
## 2026-09-16 Linux controller checkpoint update

This section supersedes older status language below where it conflicts.

- Phase D is **ACTIVE**, not "NEXT".
- The normal Linux Games path now launches and streams successfully on the HP
  EliteDesk Linux server.
- Linux gameplay input is runtime validated across three games and three input
  profiles after D-084/D-085.
- The current Games controller backend is native Linux
  `PHI1 -> uinput -> RetroArch udev`; Windows/ViGEm remains a preserved reference
  backend, not the active Linux implementation.
- The next D4 issue is PS1 multiplayer/multitap parity. The feature was
  previously runtime validated on Windows but currently does not work on Linux.
- Remaining Phase C work stays paused until the Phase-D Linux baseline is
  sufficiently complete.

The next diagnostic should classify multitap override/core-option/frontend/game
topology before any multiplayer production change.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:PROJECT_STATUS:END -->

## Goal

PrivyHub is an experiment in building a local-first smart-home/media environment
inside a dedicated PrivyHub network/trust domain.

The home Opal is that domain boundary. The ordinary household router/Wi-Fi is
upstream connectivity only. Trusted server/client/device infrastructure belongs
behind the Opal.

The current implementation is an onn Android TV client and a **Linux
companion** on the HP EliteDesk reference host. The Windows companion is
**history**: it is a preserved reference implementation, not the running
server. The roadmap continues to move remaining server responsibilities
onto the Linux host while preserving validated client/application
behavior, and later adds an optional secure remote/portable-client
foundation.

## Current development position

| Phase | Status |
| --- | --- |
| A — Games / emulator subsystem | COMPLETE / checkpointed |
| B — Diagnostics + clean native baseline | COMPLETE / checkpointed |
| C — Adaptive native streaming | **SUSPENDED** pending baseline stream health (`D-BASE`) |
| D — Linux Migration / Native Linux Baseline | **ACTIVE** — Linux games path launches and streams; D4 multitap parity open |
| E — Linux Core Resource Characterization & Optimization | Planned after D |
| F — Media Library / VOD / Live TV UX | Planned after E |
| G — Secure Remote Access / Portable Client Foundation | Future after F |
| H — Extended Emulation & User-Content Import | Future after G |
| I — Home Infrastructure / Broader Plugin Expansion | Future |
| J — Local Intelligence / Voice / Privacy-Aware AI | Future |

Predecessor synchronized checkpoint for this documentation promotion:

`0c31c100ec721d687aff6aedbd79bc0cf9343810`

**C1 explicit stream profiles are done.** The old "next technical work is
`C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`" line is superseded: the
reference profile lives in `companion/native_stream_profiles.py` as
`native_game_720p60_reference`, its parameters are declared fields
(including `max_frame_size_bytes` since `D-BASE-P6a`), and
`native-stream-status` reports the profile and any environment override.
What replaced C1 as the active item is **baseline stream health**
(`D-BASE`), not adaptation.

**The active technical work is `D-BASE` baseline stream health**, with
Phase C suspended behind it. Phase C must still be developed with explicit
future-remote reuse in mind, and it does not implement WAN
overlay/auth/travel-router behavior.

## Current topology

```text
Internet / ordinary household upstream
              |
          home Opal  <-- Linux hub wired in directly (D-BASE-B2)
   PrivyHub trust/network domain
      |                   |
companion / Linux hub    onn / PrivyHub devices  (one wireless hop)
```

**Since `D-BASE-B2` (2026-09-21) the Linux host is wired directly into the
Opal** and the onn is one wireless hop away. Every measurement taken
before that date ran through an intervening Windows PC and must be read
with that in mind.

Older Prototype-1 split-network evidence is historical test topology, not the
current product trust model.

Future remote clients use a travel-router trusted LAN plus a secure overlay back
to the Linux hub. Overlay transport remains separate from PrivyHub application
authentication/authorization.

## Working application areas

### TV / IPTV

The existing TV stack is stable enough to preserve while streaming work
continues. Phase F owns the remaining channel normalization, EPG matching/cache,
guide diagnostics and UX work. Basic playback must not depend on guide success.

### Local sources and VOD

The companion supports local live/browser/camera sources and dynamically scanned
VOD media. Control and media planes remain separate. Recursive local-first
artwork/metadata work is scheduled for Phase F.

### Games / emulation

Managed cores:

- NES — FCEUmm;
- SNES — bsnes;
- Genesis — BlastEm;
- PlayStation — Beetle PSX HW.

Phase A is complete.

Runtime coverage:

- PS1 — extensive;
- SNES — runtime exercised;
- NES — supported/configured, no local A9 fixture;
- Genesis — supported/configured, no local A9 fixture.

NES and Genesis are not runtime validated merely because configuration exists.

## Native game-streaming baseline

Validated path, **Linux** (the production one):

`x11grab of the managed RetroArch window -> H.264 VAAPI (h264_vaapi, Mesa
radeonsi) -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Preserved reference path, **Windows** (not running):

`Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

The capture source on Linux is a **window id**, not the screen: the
companion fails closed rather than broadening to the whole desktop if the
managed RetroArch window cannot be found.

Reference behavior:

- 1280x720 at 60 fps;
- 7000 kbps target/max;
- GOP 15;
- no B-frames;
- **maximum frame size 90,000 bytes** (adopted 2026-09-22 on `D-BASE-P6`
  evidence; Linux `h264_vaapi` path only — see below);
- FEC group size 8;
- process-specific PCM audio; **client audio cushion 12 / 17 packets**
  (`audio_queue_target_packets` / `audio_queue_capacity_packets`, 5 ms
  each; adopted by the user 2026-09-23 after `D-BASE-P9`/`P9a`). The
  capacity sets the audio latency: **+33.5-37.9 ms of queue residence**
  over the old 3 / 8 (≈ 30.6 → ≈ 66 ms), for **98-99.5 % fewer
  starvation episodes**; underruns inside the 3/8 noise band.
  `PRIVYHUB_AUDIO_QUEUE_{TARGET,CAPACITY}_PACKETS` overrides per session.
  Decision: `docs/memory/decisions/D-BASE-P9_AUDIO_CUSHION.md`;
- **audio redundancy 2 copies, offset 4 packets** (adopted 2026-09-23,
  `D-BASE-P10`): each audio datagram sent twice 20 ms apart, the client
  keeps the first. Warm-state audio loss −96-98 % for +1.6 Mbps, no added
  latency. `PRIVYHUB_AUDIO_REDUNDANCY_{COPIES,OFFSET_PACKETS}` overrides
  per session. Decision:
  `docs/memory/decisions/D-BASE-P10_AUDIO_REDUNDANCY.md`;
- PHI1 -> uinput -> RetroArch udev controller path on Linux (PHI1/ViGEm is
  the preserved Windows reference).

**The frame cap is a transport parameter, not a quality tuning knob.** The
loss on the wireless hop is a per-frame micro-burst meeting the AP's
queue, so the burst *is* the frame: capping it at 90,000 bytes removed
100 % of the >= 80-packet frames and **7-9x of the packet loss**, with
achieved bitrate, fps, encoder CPU and GPU power unchanged. Adopted after
the user's own perceptual check. `PRIVYHUB_ENC_MAX_FRAME_SIZE` overrides
it and **`=0` runs uncapped**. Decision:
`docs/memory/decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

Reference profile:

`native_game_720p60_reference`

C1.1 made the reference stream parameters explicit without changing
validated behavior, and `D-BASE-P6a` added the first parameter adopted from
transport evidence rather than inherited from the Windows build.

Phase C is **suspended**; when it resumes it continues with
telemetry/adaptation/generalization, and its contracts must remain reusable
by future Phase G WAN operation.

## Phase C remote-readiness rule

Future Phase G depends on Phase C producing reusable:

- named profiles and capability gates;
- goodput/loss/FEC/jitter/RTT/pacing/queue telemetry;
- explainable adaptation decisions;
- source/capture -> profile/encoder -> transport/FEC -> decoder boundaries.

Do not implement remote overlay/auth/travel-router routing in Phase C.

For future WAN adaptation, degrade quality before allowing queue/buffer growth
to create runaway latency.

The current reference session is roughly 10-11 Mbps outbound as a planning
estimate once video, 8+1 parity, PCM16 stereo audio and packet/tunnel overhead
are considered. This does not change the stable audio path.

## UDP transport: the Windows-era note and the Linux-path resolution

**These are two different things and the 2026-09-22 reading separates
them.** Detail in `KNOWN_ISSUES.md`.

**1. The synthetic burst/gap/duplication pathology — PAUSED.** Severe
packet timing transformation and **same-stamp duplication** in both
directions, reproduced by synthetic probes without game load. **It is not
a Windows-only artifact**: it was replayed from a Linux sender and
reproduced bidirectionally while idle (D083 closeout), with Opal capture
points zero-record during confirmed traffic. But that replay ran with the
**Windows PC still in the path**, and `D-BASE-B2` could neither implicate
nor exonerate the PC — the two arms overlapped. **The suite has never been
replayed on the current post-`B2` topology**, and duplication in
particular is untested there. Preserve the validated native path and
diagnostics; **do not tune product buffering around it.**

**2. The Linux-path loss — resolved.** Identified by intervention
(`D-BASE-P6`), adopted as a profile parameter (`P6a`) and held for three
hours (`S3`). Not the air, not the Opal's forwarding, not the onn's
receive path, not sender pacing — a per-frame micro-burst at the wireless
hop. The residual after the cap **correlates with nothing measured**, so
the column is closed at this level. Reopen conditions are listed under
"Do Not Reopen Without New Evidence" in `docs/memory/CURRENT.md`.

## Linux and remote direction

Phase D establishes Linux-native functional parity on the HP EliteDesk 805 G6
reference machine.

Phase E optimizes and characterizes PS1-and-below, then selects cheaper
Prototype 2 hardware from evidence.

Phase F resumes Media Library / VOD / Live TV UX work on the representative
Linux foundation.

Phase G establishes secure optional remote access and portable clients on that
mature Linux/Core baseline before heavier emulator families are introduced.

Tailscale is the preferred first overlay candidate, not the permanent contract.
No permanent travel-router model is selected yet.

Phase H then adds user-content import and N64/GameCube/PS2 characterization.
Users supply ROM/ISO/BIOS/firmware/keys; PrivyHub keeps that content outside Git
and support bundles.

## Security boundary

Future remote operation separates:

- secure network transport/overlay;
- PrivyHub client/session identity;
- application authentication/authorization;
- reachable media/audio/controller endpoints;
- overlay/path state.

Source/request IP is not durable client identity.

Remote access must not flatten or expose the ordinary household LAN.

## Current constraints and debt

Open/deferred work that does not invalidate the current baseline includes:

- Windows-specific server/capture/audio implementation, preserved as
  reference;
- older-network UDP pathology pending representative Linux + home Opal +
  onn replay (see above — moot for the current host, not disproved);
- **no SSH server on the Linux host** and **no autologin**, both required
  before the headless cutover (`H2-PREP`, 2026-09-22);
- nothing starts the companion at boot; it is launched by hand;
- Android cleartext/exported diagnostic surfaces and immature companion auth;
- minimal conventional CI;
- large orchestration files;
- remaining Phase F media/EPG/guide UX work;
- all Phase G remote functionality, which is planned only.

See `KNOWN_ISSUES.md` and durable memory for detailed evidence/state.

## Architecture checkpoint state

The remote-foundation topology/roadmap promotion is **CHECKPOINTED /
PUSHED**.

Git HEAD is the authoritative synchronized checkpoint.

**Next technical work is `D-BASE` baseline stream health, not Phase C
under D-059** — that line is superseded by the 2026-09-22 block above.

## Linux-first sequencing clarification

Phase C is not complete. The Windows implementation reached a portability
boundary and deliberately stopped before the remaining adaptive-streaming work.

Next execution sequence:

`Phase D Linux baseline -> D-BASE baseline stream health -> remaining Phase C on Linux -> Phase E -> Phase F`

`D-BASE` was inserted in front of the remaining Phase C work by decision
`docs/memory/decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`: adaptation
is not built on a baseline that is not healthy.

The remaining Phase C items are automatic bitrate control, adaptive FEC
disposition, 1080p60 characterization, generalized source abstraction and the
final Phase C checkpoint.
