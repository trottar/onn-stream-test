# PrivyHub

PrivyHub is a local-first home hub. A Linux host runs the **companion**: the `privyhub-companion` systemd user unit,
which starts `companion/privyhub_service.py`. The companion serves three things to the **PrivyHub Android app** on an
onn TV box:

- **games**, run in project-managed RetroArch cores and sent as a native low-latency H.264 stream;
- **TV / IPTV** channels with a guide (EPG);
- **video on demand** from local storage.

At home the onn reaches the hub over the LAN. Away from home it reaches the hub over an overlay network (the Tailscale
provider), with paired session identity (v2).

The Windows companion (Windows Graphics Capture, NVENC, `companion/process_audio/`) is kept as a reference
implementation. It is not the running server.

## The parts

- **The hub (companion).** `companion/` holds:
  - the control API;
  - the games, TV-state, EPG and IPTV plugins;
  - the HTTP range server for VOD;
  - the native stream (capture, encoder, FEC relay, audio, controller input);
  - the adopted feature modules and the diagnostics.

  See [`companion/README.md`](companion/README.md).
- **The onn app.** `PrivyHub/` is the Gradle project of the Android TV client. It covers the catalog, the TV guide, the
  VOD player, the native stream receiver (hardware AVC, the Opus decoder, controller sender), pairing, and the
  Diagnostics / Self-Test screen. See [`PrivyHub/README.md`](PrivyHub/README.md).
- **Games.**
  - NES, SNES (the Snes9x core, adopted line 3), Genesis and PlayStation.
  - 1P / 2P / 4P controller routing with the A8 input profiles ([`docs/A8_INPUT_PROFILES.md`](docs/A8_INPUT_PROFILES.md)).
  - PS1 Port-1 Multitap On/Off.
  - Save / Load, pause / resume, direct launch, metadata and art, cheats.
  - Runtime coverage is strongest on PS1, and SNES is exercised. NES and Genesis are configured, but they have no local
    fixtures, so they are not claimed as runtime validated.
- **TV.** An IPTV catalog with the TV state and a guide; the guide is served from a cached index (adopted line 2). The
  channel video goes from upstream to the onn directly. The hub's share is the TV state and the EPG
  (`docs/memory/architecture/E1_WORKLOAD_SUITE.md`).
- **VOD.** `companion/range_server.py` serves the media files with HTTP byte ranges for the app's Media3 / ExoPlayer.
- The E1 measurement suite marks some workloads **ABSENT** (`docs/memory/CURRENT.md`): Live TV (no unattended start),
  browser / camera sources, NES / Genesis, and a power meter.

## Playing at home and away

At home the onn joins the home 5 GHz Wi-Fi and the app's Hub host stays at its home value. Away from home:

1. The onn joins the local 5 GHz Wi-Fi.
2. The overlay app on the onn is switched to Connect.
3. The app's Hub host is set to the hub's overlay name.

The onn is paired with the hub once, on the home LAN. Only a paired device is accepted over the overlay, never a
legacy one ([`docs/REMOTE_TRUST.md`](docs/REMOTE_TRUST.md) §5). A session that arrives over the overlay is a
remote-class session. Adopted line 13 gives it:

- the remote ladder;
- a start at the floor rung;
- the 7000 kbps cap;
- the WAN telemetry.

A LAN session is unchanged. The user's steps are in [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

## The fourteen adopted lines

The adopted state is fourteen environment lines, listed in `tools/e1_suite.py` `ADOPTED`. Each line comes from its own
drop-in under `~/.config/systemd/user/privyhub-companion.service.d/`.

| # | Line | Drop-in | What it does |
|---|---|---|---|
| 1 | `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` | `adaptive.conf` | the live bitrate ladder |
| 2 | `PRIVYHUB_EPG_GUIDE_INDEX=cached` | `epg-index.conf` | the guide served from a cached index |
| 3 | `PRIVYHUB_SNES_CORE=snes9x` | `snes-core.conf` | SNES on the Snes9x core |
| 4 | `PRIVYHUB_RECOVERY_TRIGGER=v2` | `recovery.conf` | the stream recovery trigger, v2 |
| 5 | `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` | `snes-capture.conf` | the SNES capture fix |
| 6 | `PRIVYHUB_OVERLAY_PROVIDER=tailscale` | `overlay.conf` | the overlay provider (read-only state reads) |
| 7 | `PRIVYHUB_SESSION_IDENTITY=v2` | `session-identity.conf` | paired session identity and authorization |
| 8 | `PRIVYHUB_AUDIO_CODEC=opus` | `audio-codec.conf` | the Opus game audio |
| 9 | `PRIVYHUB_LINK_REPORT=1` | `link-report.conf` | the client's Wi-Fi link report |
| 10 | `PRIVYHUB_LINK_RECOVERY=1` | `link-recovery.conf` | the link-recovery stack (six sub-lines: the input hold, its tuning and ownership, the rewind, the stall signal and resume) |
| 11 | `PRIVYHUB_RESTART_FAST=1` | `restart-fast.conf` | the fast client restart |
| 12 | `PRIVYHUB_RESTART_FAST_UNLOCK=1` | `restart-fast-unlock.conf` | the fast restart, unlocked |
| 13 | `PRIVYHUB_REMOTE=1` | `remote.conf` | on a remote-class session only: the remote ladder, the floor start, the 7000 cap, the WAN telemetry; the LAN unchanged |
| 14 | `PRIVYHUB_STEP_IN_PLACE=1` | `step-in-place.conf` | each ladder step on the same stream (one IDR, no new SSRC) |

**B33 is live inside line 10.** A short drop with no loss behind it resumes without a state load. Its own off switch is
`PRIVYHUB_REWIND_NEEDS_LOSS=0`.

**The one off switch, for every line:**

1. Delete the line's drop-in.
2. Run `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`.
3. Take the name out of `tools/e1_suite.py` `ADOPTED`; each record names the diff to reverse.

Each line's adoption record (under `docs/memory/evidence/`) gives its exceptions. The G lines are written up in
[`docs/REMOTE_TRUST.md`](docs/REMOTE_TRUST.md).

## Native game-streaming baseline

The validated Linux path:

`x11grab of the managed RetroArch window -> H.264 VAAPI -> RTP-sized UDP -> 8+1 XOR FEC -> Android hardware AVC`

Windows Graphics Capture -> NVENC remains a preserved reference path.

The reference profile is `native_game_720p60_reference` in `companion/native_stream_profiles.py`:

- 1280x720 at 60 fps;
- 7000 kbps, the top of the live ladder;
- GOP 15;
- no B-frames;
- **a maximum frame size of 90,000 bytes** (Linux `h264_vaapi` only);
- 8 data + 1 XOR FEC;
- RTP payload type 96;
- a 1200-byte packet size;
- an audio cushion of 12 / 17 packets;
- audio redundancy 2 / 4 (every audio datagram sent twice, 20 ms apart).

**The live ladder** (line 1) moves the bitrate between rungs:
- **LAN:** 5000 / 5500 / 6000 / 7000. A LAN session starts at 7000.
- **Remote** (line 13): 4000 is added as the floor. A remote session starts at the floor and climbs. The cap is 7000.
- **The step** (line 14): each step still starts a new encoder, but the new encoder's packets are spliced onto the
  same stream, so the onn sees one IDR and no SSRC change.

**Audio** is Opus (line 8; `companion/audio_codec.py`): 128 kbit/s and 10-ms frames by default. Controllers take the
path PHI1 -> uinput -> RetroArch udev. Both are separate from the video transport.

**The frame cap is a transport parameter, not a quality knob.** The packet loss on the wireless hop was traced to a
per-frame micro-burst meeting the access point's per-station queue: one frame in a hundred was 80-plus packets emitted
back to back. Capping the frame bounds the burst. The cap:
- removed 100 % of the >= 80-packet frames;
- removed 7-9x of the loss;
- left the achieved bitrate, the frame rate and the encoder CPU unchanged;
- held over a three-hour soak.

The encoder is CBR, so it spends the same bits; the cap only changes when it may spend them.
`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` reproduces the uncapped behaviour for comparison. Records:
[`D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`](docs/memory/evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md),
[`D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`](docs/memory/evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md),
[`D_BASE_S3_CAP_SOAK_2026-09-22.md`](docs/memory/evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md). The D-BASE close-out
table ([`D_BASE_CLOSEOUT_2026-09-23.md`](docs/memory/evidence/D_BASE_CLOSEOUT_2026-09-23.md)) must stay met.

The synthetic UDP burst / gap / duplication pathology seen without game load is still **paused**. It reproduced from a
Linux sender too, but it has never been replayed on the current topology. It is not treated as a product buffering
requirement ([`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md),
[`docs/investigations/2026-09-07-udp-transport.md`](docs/investigations/2026-09-07-udp-transport.md)).

## Diagnostics

- **The keeper, `privyhub-diag`** (`tools/diag_keeper.py`; the unit file is `tools/privyhub-diag.service`). It is
  read-only on the hub.
  - Every 5 minutes it copies the hub's logs, redacted, into `~/privyhub_diag/<YYYY-MM-DD>/`.
  - Every minute it records overlay and session samples.
  - Each ended session gets a summary row in `~/privyhub_diag/sessions.jsonl`.
  - Day directories older than 30 days are removed.
- **`python3 tools/diag_check.py`** prints six lines: adopted, apk, overlay, routing, band, diag-keeper.
- **`python3 tools/diag_read.py "<range>"`** reads the keeper's copies for a range: `today`, `"last night"`, or
  `"YYYY-MM-DD HH:MM..HH:MM"` (UTC). It writes one Markdown read under `docs/memory/evidence/reads/` and prints the
  path.
- **`python3 tools/e3_state.py`** prints the adopted state as one JSON line (`"ok": true`, `"apk": "CONFIRMED"`).
- **The app's Diagnostics / Self-Test screen** calls the hub's `/diagnostics/health`, `/diagnostics/self-test` and
  `/diagnostics/bundle` (the support bundle, redacted).
- The diagnostics are described in [`docs/DIAGNOSTICS.md`](docs/DIAGNOSTICS.md).

## How to run it

**The units** (systemd user units on the hub):

```text
systemctl --user status privyhub-companion
systemctl --user restart privyhub-companion
systemctl --user status privyhub-diag
```

- The companion's unit file is `~/.config/systemd/user/privyhub-companion.service`; a copy is in
  `docs/memory/evidence/h3_2026-09-23/`. It runs `python3 -u ./companion/privyhub_service.py` from the repo.
- To see the lines the running companion has:

  ```text
  MP=$(systemctl --user show -p MainPID --value privyhub-companion)
  tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_'
  ```

**The host tests** run from the repo root, with no stream and no companion. The command is in each test file's
docstring:

```text
python3 -m unittest discover -s tests/<feature> -v
python3 -m unittest tools/test_<name>.py -v
python3 tools/e1_suite.py --self-test
python3 tools/check_memory_health.py
```

[`tests/README.md`](tests/README.md) lists the test directories.

**The APK.** The Gradle project is `PrivyHub/`. The records build it offline, in a fresh copy of the tree:

```text
cd PrivyHub
./gradlew :app:testDebugUnitTest :app:assembleDebug --rerun-tasks --offline --no-configuration-cache
```

The APK is `PrivyHub/app/build/outputs/apk/debug/app-debug.apk`. Build output is ignored by git.

**The confirmed-APK rule.**
- A new build is only a candidate. It goes on the onn for a pre-registered, attended run (HOME-1's had the user at the
  TV), and it is CONFIRMED only by that run's pre-registered rule: every cell that ran was valid (CL-B7 §6).
- A CONFIRMED build is pinned in `tools/e1_suite.py` `EXPECT_APK`.
- Otherwise the confirmed APK goes back on and the pin does not move. That happened in HOME-1:
  [`HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md`](docs/memory/evidence/HOME_1_TRIP_CLOSE_AND_QUEUE_L_CELLS_2026-11-02.md).
- Today **`fcd924c2…` is CONFIRMED** on the onn.
- Each installed copy is kept under `PrivyHub/app/build/<step>_installed/`.

## Where the records are

- [`docs/memory/CURRENT.md`](docs/memory/CURRENT.md): the state now and the next action.
- [`docs/memory/evidence/`](docs/memory/evidence/): every record, one per item, with its harness directory. Records
  are never moved or edited.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): the roadmap. [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md): the open items.
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md): the user's steps at home and away.
- [`docs/memory/handoffs/README.md`](docs/memory/handoffs/README.md): the status of every handoff.
  [`docs/memory/patches/PATCH_INDEX.md`](docs/memory/patches/PATCH_INDEX.md): every patch note.
- [`docs/memory/archive/INDEX.md`](docs/memory/archive/INDEX.md): what was archived on 2026-11-03, and where it went.
- [`docs/README.md`](docs/README.md): the documentation map. [`docs/memory/README.md`](docs/memory/README.md): the
  memory system.

## Network ports used by the current prototype

| Purpose | Port |
| --- | ---: |
| Companion control API | TCP 8765 |
| Media serving | TCP 8000 |
| Native game video | UDP 48100 |
| Native game audio | UDP 48101 |
| Native controller input | UDP 48102 |
| Local video FEC relay input | UDP 48110 on loopback only |
| Forward synthetic transport diagnostic | UDP 48120 |
| Android-local loopback diagnostic | UDP 48121 |

Diagnostic ports and implementation details may evolve; production code should not depend on diagnostic-only paths.

## Project principles

- Local-first and privacy-oriented operation.
- IoT devices isolated behind a dedicated network boundary.
- Prefer modular, replaceable, hardware-agnostic components.
- Preserve validated subsystems while testing one layer at a time.
- Prefer current local source and fresh measured evidence over stale summaries.
- Do not broaden capture from the managed game window to the desktop as a fallback.
- Do not encode quirks of the current test environment into product architecture without representative evidence.
- Keep user ROM/ISO/BIOS/firmware/keys and private network-bearing data out of Git and shareable support bundles.
