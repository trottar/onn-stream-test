---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: dfa1626 (CL-B6 uncommitted beside it; the user commits)
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase E ACTIVE; the G track (remote) under way. G-A1 ADOPTED (2026-10-16, the user's): the overlay provider and
session identity v2 run on the host, and `identity_v2` is on in the client. **G-A2 ADOPTED (2026-10-19, the user's):
the Opus audio path. The adopted environ is EIGHT lines.**
CL-B3 is OPEN on two G5-S1 smoke gates (NOT MET; the user decides). Everything else passed: G3-S3's hardened APK
`59f736d2…` is installed and CONFIRMED, the signed LAN path passed, and the VOD play through the range server
passed.** E1 FROZEN; E2
MEASURED; E3 CLOSED; E4 CLOSED (host side). Nothing committed since `af3ed73`.

**State (2026-10-19 02:05Z, after G-A2): the EIGHT adopted lines; nothing running; `--check` ok on eight** (adb
connected, **APK `043891e1…1607` CONFIRMED**). No `e3_flag.conf`, no stream, no game; one device paired, `identity_v2`
on. The eight lines:
1. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` (`adaptive.conf`);
2. `PRIVYHUB_EPG_GUIDE_INDEX=cached` (`epg-index.conf`);
3. `PRIVYHUB_SNES_CORE=snes9x` (`snes-core.conf`);
4. `PRIVYHUB_RECOVERY_TRIGGER=v2` (`recovery.conf`);
5. `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` (`snes-capture.conf`);
6. `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`overlay.conf`);
7. `PRIVYHUB_SESSION_IDENTITY=v2` (`session-identity.conf`);
8. **`PRIVYHUB_AUDIO_CODEC=opus` (`audio-codec.conf`, G-A2)**.

**G-A2** (`evidence/G_A2_OPUS_ADOPTION_2026-10-19.md`): the confirmation run, Opus by the drop-in alone, was VALID
with host gates held (`sig_v` 3 / opus, 8,994 kbit/s and 1,177 pkt/s at 7000, net audio loss 10 ms). **But underruns
were 78**, against CL-B5's Opus 11 / 13. ≥ 50-ms spikes 138; two > 1-s ctrl gaps; not located. No listen. CL-B5
(`evidence/CL_B5_…`): the paired A/B and the listen run, all valid; the user, on Opus: "No visual or audio problems".

**Earlier (2026-10-17 18:51Z, after the G8-S3 record):** the G8-S3 unit ended by itself (18:21:36Z,
all 3 cells done) and was collected. **G8-S3 MEASURED: 3 of 3 valid**
(`evidence/G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md`):
- cap-6000 at the 5000 start reached PLAYING, rules off and on, with host gates met;
- the ladder held 5000 at the floor;
- the tail drop was 6.75 % / 9.18 %, against the bench's ~2 %;
- cell 2 went silent 417 s in, and recovery gave up;
- cap-4500 was `no_play` (27.76 % dropped), as predicted.

**G4-S1 MEASURED: 2 of 3 valid** (`evidence/G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md`):
- runs 1 and 2 PLAYING over the overlay; gates 1-2 met, gate 3 not evaluable;
- run 2's hotspot toggle ended the session, and the stream came back after a LAN setup;
- run 3 not started.

**G8-S1 MEASURED: 18 of 22 valid** (`evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md`, superseding the 10-16
partial): the four rate-cap cells never reached PLAYING (open, `docs/KNOWN_ISSUES.md`). From cell 6 the companion ran
session B's flag-absent G5-S3 / G5-S4 edits (disclosed, §3).

- **Ten adoptions stand:**
  - live adaptive (C);
  - the guide index, Snes9x, recovery v2 (E3);
  - the SNES capture fix (E4-S5D);
  - the overlay provider and session identity v2 (G-A1, host);
  - `identity_v2` on (G-A1, client);
  - the Opus audio path (G-A2, 2026-10-19);
  - the CONFIRMED APK (CL-B5 since 2026-10-18; CL-B4's and CL-B3's before it).
- **Built behind flags, not adopted:** G5-S1 WAN telemetry (`PRIVYHUB_WAN_TELEMETRY`); G4-P1's `--remote` row and
  the hotspot runbook; G8-S4's
  `PRIVYHUB_ENCODER_RC`.
- **The link watch is stopped** (E4-S4C); the LAN loss row is parked (remote first). The LAN read clean today:
  60-80 loss/min.
- **ABSENT:** Live TV, browser / camera sources, NES / Genesis, a power meter.

## Current Work Item

**`G-A1_ADOPTION_AND_CL-B3_TASK.md` (session A)**, after session B's G3-S3
(`evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`: setup canon v2, the port binding, the media token and the
range-server gate, `diagnostics`, the Hub host setting; built and tested, the APK built).

- **G-A1 ADOPTED** (`evidence/G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`):
  - `overlay.conf` and `session-identity.conf` were written by the user by hand (this session's write was refused
    by its permission check);
  - seven lines read back; `e1_suite.ADOPTED` and the preflight have seven (patch
    `G-A1_OVERLAY_AND_IDENTITY_ADOPTED`);
  - `/status` shows the overlay object (connected, `no-peer`); `/session/status` reads v2, 1 paired device;
  - the reverts are in the record.
- **CL-B3 OPEN** (`evidence/CL_B3_HARDENED_APK_LAN_2026-10-16.md`):
  - The APK is installed, and the pairing survived `-r`. Its hash is pinned (patch `CL-B3_HARDENED_APK_HASH`).
  - **R1** (PS1-STREAM 10 min, signed path): every host gate held.
    - Host CPU 11.57 % at 7000-7000, reported only.
    - `sig_v` 2, `native-stream-start?port=48100` → 200 (the binding), no `legacy_setup`, `media_token_live` true.
  - **W** (`PRIVYHUB_WAN_TELEMETRY=1` per run): host gates held, and `wan` was live on `/status` and the telemetry
    with eleven measures and a class per window. The flag came off, and `/status` was byte for byte equal except
    `server.pid`. **NOT MET:**
    - companion CPU +0.633 point (≤ 0.5; two runs, not paired arms);
    - no `logs/wan_sessions.jsonl` line (G5-S1 writes it only when a next session starts; `docs/KNOWN_ISSUES.md`).
  - **VOD PASSED** (19:58Z): `media_session` for the paired device with the header (`media_token_used` false), on
    `lan`; the range server answered 200 / 206, and the movie streamed to the onn.
- Git status: `logs/g_a1_git_status.txt`, `logs/cl_b3_git_status.txt`.

## Verified State

**The E4 reference** (E4-S1, 20-min means): idle 1.2 % host CPU / 5.3 W;
PS1 streamed 10.9 % / 20.1 W (stack 95 % of a core, 354 MB); PS1 + grabs
21.4 % / 25.7 W (172 %, 856 MB); SNES 7.4 % / 15.2 W.

**The baseline, cold and warm, on the adopted build** (close-out,
2026-09-23; target / cold / warm): spikes ≥ 20 ms/min < 200 / **32.8** /
**26.0**; rendered fps ≥ 59.5 / **59.90** / **59.91**; stale drops/min
< 20 / 1.1 / 0.8; video loss/min (post-FEC) < 10 / **8.7** / **8.4**;
audio underruns 17 / 14 per session; max output gap ≤ 100 / **163** /
**110** ms — the transport's open row. Frames < 20 ms rx→output 99.1-99.3 %.
**Transitions on it** (`C3.L3a` smoke, 2026-09-24): telemetry settled within
one to two client reports (≤ ~4 s); each costs one 125-211 ms gap
(`codec_ms` 7-11) — the restart's ~152 ms RTP silence.
**`C3.L3a-S1` transition soak** (2026-09-24): each bitrate-only restart costs
one gap, median 186.5 ms (128-225); a sized (rung) switch costs 287-649 ms
(C5-M5 / C5-M5B).

- **The PS1 source, since 2026-10-01 (`C5-M4A`): a 1920×1080 window at
  internal resolution 4x.** It is set by the Beetle PSX HW core override
  (`dc4d6019…`) and the line in the base and six per-title `.opt`. The
  stream downscales it to the profile below. The revert is in
  `TOOLS.md`. SNES is untouched.
- **Profile** `native_game_720p60_reference`
  (`companion/native_stream_profiles.py`), all `source: profile`,
  `any_override: false`: 1280x720@60, 7 Mbps, GOP 15, no B, 8+1 FEC,
  **cap 90,000 B** (`P6a`), **cushion 12/17** (`P9`), **audio redundancy
  2/4** (`P10`). Env overrides exist for comparison sessions only
  (`TOOLS.md`, including `C5-M1`'s `PRIVYHUB_NATIVE_PROFILE_ID`); none set.
- **Installed**: **APK `043891e1…1607`** (CL-B5's debug build, installed 2026-10-18 23:26Z: CL-B4's Opus decode,
  now on its own thread; `sig_v` 3 declares `audio_codecs: ["opus"]`). Its hash is pinned in `tools/e1_suite.py`
  `EXPECT_APK` and `tools/c3_l4_nft_night.py` (patch `CL-B5_DECODE_THREAD_APK_HASH`), and it read CONFIRMED at
  23:59Z. The host's `session_identity.py` verifies `sig_v` 3 (since CL-B4). `audio_codec.py` records a v3 client's
  overlay host (CL-B5).
  - **`identity_v2` is on; the Hub host is empty (LAN).** One device is paired, and its stored permissions are
    games, tv, vod, diagnostics.
  - Rollback, written and not applied: `adb install -r PrivyHub/app/build/cl_b5_preserved/app-debug.apk`
    (`8e10497e…`, CL-B4), plus the predecessors in `evidence/cl_b5_2026-10-18/predecessors/`. Before it:
    `cl_b4_preserved/` (`59f736d2…`, CL-B3), with `evidence/cl_b4_2026-10-18/predecessors/`. Then:
    `g3_s3_preserved/` (`77011eef…`, CL-B2), with `evidence/cl_b3_2026-10-16/predecessors/`. Older APKs:
    `g3_s2_preserved/` (`de072762…`, CL-B1) and `runtime/c4_m1/` (`f31b1c18…`).
  - The companion is the systemd user unit `privyhub-companion` (`H3`);
    restart it with `systemctl --user restart`.
  - **Live adaptive bitrate by default, since 2026-10-01 13:07Z**
    (the ladder 5000-7000 at 720p), through the drop-in
    `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`
    (`Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`). The unit file
    is unchanged.
    - `adaptive_bitrate.mode live`, `configured_mode live`, `acts true`.
    - Kill switches: delete the drop-in + `daemon-reload` + restart
      (off); `POST /plugins/games/adaptive-bitrate/disable` (shadow, one
      session).
  - **The cached guide index by default, since 2026-10-07 04:15:49Z
    (E3-S6A)**: its own drop-in `epg-index.conf` beside `adaptive.conf`
    (`Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached`). Grabs read
    `data/epg/metadata/guides_index.json` (3,268,095 bytes at the end;
    rebuilt once per 24-h metadata refresh) instead of parsing the 25.6
    MB file. Kill switch: delete `epg-index.conf` + `daemon-reload` +
    restart, revert the state-check diff (`TOOLS.md`).
  - **The Snes9x core by default, since 2026-10-07 22:52:28Z (E3-A2)**:
    `snes-core.conf` (`Environment=PRIVYHUB_SNES_CORE=snes9x`); SNES
    runs on `snes9x_libretro.so` (Snes9x 1.63, `9b2b6ea9…7a31`, licence
    "Non-commercial"), not bsnes; `emulators.json` unchanged. Saves and
    states per core (`Snes9x/` vs `bsnes/`). Kill switch: delete
    `snes-core.conf` + `daemon-reload` + restart (`TOOLS.md`).
  - **Recovery v2 by default, since 2026-10-09 04:50:43Z (E3-A3B)**:
    `recovery.conf` (`Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`). It
    gives the gap log (`logs/games/native_stream_ctrl_gaps.log`), the
    5-s two-check controller trigger, and the controller-return exit.
    Kill switch: delete `recovery.conf` + `daemon-reload` + restart,
    reverse the state-check diff (`TOOLS.md`, "Recovery v2").
  - **The SNES capture fix by default, since 2026-10-15 20:56Z
    (E4-S5D)**: `snes-capture.conf`
    (`Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`). The encoder's
    output rate is `-r 60`, not x11grab's probed `tbr`. Kill switch:
    delete `snes-capture.conf` + `daemon-reload` + restart, and take the
    line out of `tools/e1_suite.py` `ADOPTED`.
  - **The overlay provider and session identity v2 by default, since 2026-10-16 17:23:17Z (G-A1):** `overlay.conf`
    (`Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale`) and `session-identity.conf`
    (`Environment=PRIVYHUB_SESSION_IDENTITY=v2`). Kill switch: delete the drop-in(s) + `daemon-reload` + restart,
    and take the name(s) out of `tools/e1_suite.py` `ADOPTED` (G-A1 record §4).
  - **The Opus audio path by default, since 2026-10-19 01:48:30Z (G-A2):** `audio-codec.conf`
    (`Environment=PRIVYHUB_AUDIO_CODEC=opus`, 128 kbit/s, 10 ms). A client without `audio_codecs` is refused at
    stream start, with the reason. Kill switch: delete `audio-codec.conf` + `daemon-reload` + restart, and take
    `AUDIO_CODEC` out of `tools/e1_suite.py` `ADOPTED` (`docs/REMOTE_TRUST.md` §9).
  - **The adopted environ is exactly eight `PRIVYHUB_*`** (live, the index, Snes9x, recovery v2, output_rate, the
    overlay provider, identity v2, Opus) in **eight drop-ins** (`adaptive.conf`, `epg-index.conf`, `snes-core.conf`,
    `recovery.conf`, `snes-capture.conf`, `overlay.conf`, `session-identity.conf`, `audio-codec.conf`). The manager
    has none. Last checked 2026-10-19 02:05Z (G-A2's end, `check_end.json`).
    - `d7_regression.py` and `c3_l4_nft_night.py` (`ADOPTED_E3`) still list four lines. They were not run or
      changed.
    - `tools/e1_suite.py` (`ADOPTED`, eight, with a preflight key per drop-in), `e3_state.py` and `e1_remote.py`'s
      preflight check it. Since
      E4-S2 they also require no `e4_constraint.conf`.
  - The companion tree carries the live controller through `C3-L4-N2`,
    the C5 selector profiles (dormant), **the 1080p rung behind
    `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`** (C5-M5; entry 415 since
    C5-M5B; since C5-CLOSE its window skips non-PLAYING reports; absent =
    the closed ladder; NOT ADOPTED) and **the PS1 look behind
    `PRIVYHUB_PS1_LOOK`** (C5-M5B; absent or `4x` = nothing written; NOT
    ADOPTED). Both flags off and absent.
  - The other E3 flags' code is dormant and absent (`TOOLS.md`, "The E3
    flags"): `frame_spin`, `RECOVERY_GAP_LOG` (alone), `EPG_GRAB_NET=paced`
    + `EPG_GRAB_DELAY_MS` (S7, S7B), `GRAB_NONET`. **E4's, dormant and
    absent:** `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1` (`epg.py`, E4-S4),
    (`PRIVYHUB_SNES_CAPTURE_FIX=output_rate` is adopted since E4-S5D.)
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); after a host reboot `adb connect <onn-address>:5555`.

## Next Action

**CL-B6: the A/B repeated after an onn power-cycle, both VALID** (`evidence/CL_B6_AB_REPEAT_AFTER_RESTART_2026-10-19.md`,
2026-10-19 02:32-03:06Z; the adopted state unchanged: the eight lines, no `e3_flag.conf`, `--check` ok).
- **Underruns:** Opus (adopted, fresh onn) 22 / 13 and PCM (override) 11 / 8. G-A2's 78 was not repeated, which is
  consistent with the onn's state after a long evening, not the codec (the pre-registered reading).
- **Spikes:** still Opus over PCM, 104.7 against 61.4 / min. The onn's PrivyHub process used 107 % against 85 % of a
  core.
- **The wire:** −2,916 kbit/s.
- **The user:** "It sounds fine" (PCM); "Both are fine".
- One disclosed tool patch: `e1_suite.expected_environ()`, so a run drop-in can override an adopted key.

1. **The user's commit:** everything since `dfa1626`:
   - `tools/e1_suite.py`;
   - the record + directory, `KNOWN_ISSUES.md`, this file;
   - the task file and the prompt (`logs/cl_b6_git_status.txt`).
2. **G4-S3, the 4000 hotspot run with Opus** (predicted ~5.4 Mbit/s on the tailnet, ~2.4 GB/h). The underrun
   question reads settled by CL-B6's reading, a watch item with the onn's uptime beside each session. If the user
   does not take it as settled, the adoption is the user's call (off: delete `audio-codec.conf`, restart;
   `docs/REMOTE_TRUST.md` §9).
3. Open: the spikes (the Opus decode's ~0.2 core on the onn, the measured candidate); `KNOWN_ISSUES.md`.

**G-A2: `PRIVYHUB_AUDIO_CODEC=opus` ADOPTED, the eighth line** (`evidence/G_A2_OPUS_ADOPTION_2026-10-19.md`,
2026-10-19 01:47-02:05Z; the eight lines, no `e3_flag.conf`, `--check` ok).

1. **The user's commit:** everything since `263c26d`:
   - `tools/e1_suite.py`, `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`;
   - `docs/REMOTE_TRUST.md` §9, `docs/CAPABILITY_MODEL.md`;
   - the record + directory, patch `G-A2_OPUS_ADOPTED`, ROADMAP §G4, `KNOWN_ISSUES.md`, this file;
   - the task file and the prompt (`logs/g_a2_git_status.txt`).

   The drop-in lives outside the repo.
2. **G4-S3, the off-site run at 4000 with Opus** (predicted ~5.4 Mbit/s on the tailnet, ~2.4 GB/h). A v3 client's
   overlay host is recorded (CL-B5). `e1_remote.py`'s preflight now requires the eight lines.
3. **Underruns and spikes** (`KNOWN_ISSUES.md`): the confirmation run's underruns were 78 against CL-B5's 11 / 13,
   with ≥ 50-ms spikes 138, not located. The spikes item stays open. Proposed: a paired PCM / Opus A/B after an onn
   restart, or watch the next sessions' underruns. If the user prefers PCM meanwhile: delete the drop-in, restart
   (`docs/REMOTE_TRUST.md` §9).

**Earlier — CL-B5: the paired A/B both VALID** (`evidence/CL_B5_OPUS_DECODE_THREAD_AB_2026-10-18.md`, 2026-10-18
23:23-23:59Z; the flag removed, the seven lines, APK `043891e1…` CONFIRMED).

1. **The user's commit:** everything since `f9a8260`:
   - `OpusDecodePipeline.kt` + its test, `NativeAudioReceiver.kt`, `NativeStreamActivity.kt`, `OpusAudioDecoder.kt`;
   - `companion/audio_codec.py` (one line) + its test;
   - the three pinned-hash files;
   - the record + directory, patch `CL-B5_DECODE_THREAD_APK_HASH`, CL-B4's §5, ROADMAP §G4, `KNOWN_ISSUES.md`, this
     file;
   - the task file and the prompt (`logs/cl_b5_git_status.txt`).
2. **The adoption question (the user's call):** `PRIVYHUB_AUDIO_CODEC=opus` as the eighth line. The paired numbers
   (A PCM / B Opus):
   - underruns 19 / 11 (≤ 20);
   - net audio loss 135 / 300 ms (2.3 / 2.6 holes/min);
   - the LAN −2,909.5 kbit/s (−1.31 GB/h) and −200.7 pkt/s;
   - decoder spikes 100 / 144 per min, max output gap 180 / 227 ms;
   - companion CPU 24.8 / 21.3 % of a core;
   - the user's lines: A "Sound is fine"; B "Run B nothing is running so I can't determine sound" (given after B
     ended); **L (Opus, listened to while it played) "No visual or audio problems"** — L's underruns 13, the wire
     −2,907 kbit/s against A, decode queue max 20 / 0 drops, spikes 137 / min.

   Not adopted here.
3. **Then the off-site run at 4000 with Opus** (predicted ~5.4 Mbit/s on the tailnet, ~2.4 GB/h). The v3 overlay
   capture is fixed (CL-B5), so an Opus start over the overlay is no longer refused.
4. Open: B's decoder spikes over A's on the same evening (not located; the onn's CPU not read).

**G4-S2 PARTIALLY MEASURED: 1 of 2 valid** (`evidence/G4_S2_OFFSITE_REMOTE_LADDER_2026-10-17.md`, 2026-10-18
17:55-18:12Z; unit collected, `flags_absent` true, the seven lines). Run 1 (cap 4000, floor) held 4000 over the overlay,
7.75 loss/min; **the wire rate at 4000 is 8.29 Mbit/s (~62 MB/min)**, not ~4.65 — known issue. Run 2 not run (the
user's phone data). `--check` reads ok false on adb only until the onn is back on the LAN.

1. **The user's commit:** everything since `49d1667` (G4-S2 launch + record + directory, ROADMAP §G4/§G5,
   `KNOWN_ISSUES.md`, this file, the two task files; `logs/g4_s2_git_status.txt`).
2. **Pending:** G8-S4 (the encoder's rate-control headroom, session B) — and now the per-rung wire overhead (the
   ~4.3 Mbit/s excess) before any further cellular session; G4-S2 run 2 (the climb from 4000 off-site); the reconnect
   test on a true off-site day.

**G8-S3 MEASURED** (`evidence/G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md`, 2026-10-17 17:38-18:21Z; driver collected).
- **Cells 1 and 2** (cap-6000, `PRIVYHUB_START_RUNG=floor`, rules off / on): PLAYING in 9.1 s / 7.1 s, host gates met.
  - The ladder held 5000: down refused `at_floor`, and no clean reports to go up.
  - Cell 1 stayed up for the window: 2,379 loss/min, 53.1 fps, 6.75 % tail-dropped.
  - Cell 2 went silent on the client 417 s in, and recovery gave up after 5 restarts.
- **Cell 3** (cap-4500): `no_play`, 27.76 % dropped, as predicted.
- 5000's wire rate: 6,039 kbit/s mean, as the bench; the drop is ~3× the bench's (the spread, §3). Playability: the
  user's.

1. **The user's commit:** everything since `0093b7c` (G8-S3 launch + record + directory, ROADMAP §G8, this file, the
   two task files; `logs/g8_s3_record_git_status.txt`).
2. **Options, not decided here (the user's call):**
   - **(a) G4-S2 off-site with G5-S3 + G8-S2** (`PRIVYHUB_REMOTE_LADDER=1` + `PRIVYHUB_START_RUNG=floor`). On the
     remote path the floor is 4000. This is the first real test of a 4000 start; G8-S2's bench put 4000 under
     cap-4500 at 5.5-5.8 % dropped.
   - **(b) A wire-overhead measurement task for session B:** the per-rung wire rate and spread, measured, not the
     1.18 ratio (G8-S3: parity 0.178 per data packet, not 0.125; frames up to 89 KB).
   - **(c) Whether a LAN rung below 5000 should exist.** C5-M3 screened 720p/4000 as passing transport. The LAN list
     stops at 5000 by C3-L4's validation.

Nothing adopted; nothing committed.

0. **G5-S3 / G5-S4 LAN smoke: PASSED on the LAN** (`evidence/G5_S3_LAN_SMOKE_2026-10-17.md`, 2026-10-17
   15:56-16:10Z).
   - One 10-min PS1-STREAM with `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_REMOTE_RUNG_CAP=4000` and
     `PRIVYHUB_WAN_TELEMETRY=1`. Host gates met.
   - `path_class` `lan` on every ladder row; the cap's configuration row once; no 4000; 7000 held on a lossy link.
   - Flags removed. Not adopted.
   - **Next, the user's:**
     - **G4-S2 off-site with the flags** (G5-S3 + G5-S2 + the cap): the first run where `path_class` reads `remote` and
       4000 can be actuated. The user judges 4000's picture.
     - **G8-S2 from session B** (`handoffs/G8-S2_START_RUNG_TASK.md`): the cap follow-up from G8-S1
       (`evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §5, §8). Session B starts after session A has exited.
   - Still open from G8-S1: (b) a re-run of the on-arm cells on committed code, if the user wants it.
1. **The user's commit:** everything since `80f3fc4`: the smoke record, `g5_s3_smoke_2026-10-17/`, the status lines
   in `docs/WAN_ADAPTATION_RULES.md`, ROADMAP §G5, this file (`logs/g5_s3_smoke_git_status.txt`).
   - Still the user's call from CL-B3: the two W gates not met.
   - After the onn next changes networks, adb needs `adb connect <onn-address>:5555` by hand.
2. **G4-S2, as the draft frames it** (`handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md`, "What G4-S2 would gate"):
   - the D-BASE table on the remote path at the remote ladder's level (720p/4000 is the lowest screened rung, R3.2);
   - the reconnect gated: a hotspot toggle resumes within the recovery bound;
   - the §G4 list gated item by item, for NES / SNES / Genesis / PS1.
   - G4-S1 found two things to settle first (`docs/KNOWN_ISSUES.md`): the remote row cannot read the host gate (no
     RetroArch FPS counter, no encoder progress), and the toggle's session came back over the LAN, not the overlay.
3. **Later tasks:**
   - **G5-S3:** make 720p/4000 actuatable, the remote floor `floor_4000`, recorded and never actuated. The data
     volume: ~5.1 GB/h at 7000 (11.42 Mbit/s measured on the overlay) against ~2.3 GB/h at 4000 (C5-M3's
     5.02 Mbit/s).
   - **G8-S1:** measured (item 0).
   - **G5-S2's open items:** the per-session line at stream stop / shutdown, the live recovery state, the unclassified
     measures' thresholds, an isolated cost A/B.

**Open, not blocking:**

- the SNES 59-fps fault is FIXED and adopted (E4-S5D); the sampler's first-to-last capture fps
  (E4 uses a segment-aware one); the pass rule's kill gates are
  window-scoped (E4-S3B's addendum reads the run span);

- the false pause: fixed and adopted (v2); the client's own 1-3-s
  output stalls stay open; **the link lossy since 10-09** (a LINK
  item, `docs/KNOWN_ISSUES.md`; 10-10: 39-863 loss/min, 0 of 4 clean
  controls): use same-night controls;
- the max output gap; `host_link`; the thermal flag; `CTRL-L1`; the
  slow-event ring; the mild step's ~120 s bound;
- **the onn's 1080p decode jitter**; the overlay's constant size text;
- `C6-D1`'s list; B3a's two clauses; C5-M4's R3; `encoder_command` is the
  full start's only;
- **adaptive-off measurements need the drop-in out** (`TOOLS.md`);
- **G5-S1 WAN telemetry** (CL-B3 W): no session line on a one-session run, and the CPU cost over its bar; `docs/KNOWN_ISSUES.md`;
- **the host-CPU band gate** (CL-B2 R3): FAILED by 0.06 on the encoder's
  share (46.65 vs ~36 % of a core) at the same 7000 rung as the
  reference. The cause is not located. A BAR item in
  `docs/KNOWN_ISSUES.md`: report the encoder with its rung;
- E5-S2 (a second machine, the alpha candidate) is not on this Next Action list.

## Success Criteria

Phase C: met (C7, `docs/ROADMAP.md`). **Phase E** (`docs/ROADMAP.md`):

- E1 froze the workload suite before any measurement.
- Every later change is measured with that suite
  (`architecture/E1_WORKLOAD_SUITE.md`) and against the D-BASE close-out
  table, which must stay met.
- No perceptual gate unless the user sets one.

## Do Not Reopen Without New Evidence

- **`D-BASE` is closed** — reopen only if the close-out table fails on the
  adopted profile. Its settled findings (curated in `MEMORY.md`): client
  latency (`C3.L2c`, `P1`), the audio startup burst (`P2a`), the loss is
  the frame-size tail (`P6`/`P6a`; not pacing, the air or the onn's
  receive path), the audio holes are the path's (`P7`/`P8`), the
  warm-state loss is between the ends (`T3`). **Do not derive loss as
  host-sent minus client-received** (`P4`); use `R5`'s counters.
- The adopted values: cap 90 KB (60 KB and VBV measured, not rejected —
  reopen on a picture complaint), cushion 12/17, redundancy 2/4.
- The host display path (`H2-PREP`/`H2`): the plug is X `DisplayPort-1`
  = DRM `card0-DP-2`, 1920x1080@60 by EDID; re-run the inventory, don't
  re-derive.
- The synthetic UDP pathology is **PAUSED** (`M1`), never seen post-`B2`.
- The onn's thermal zones / radio counters are absent (`T1`, `P4`); its
  status is 0 always; its CPU temperature is `dumpsys thermalservice`.
- D4/D5 restoration; the Windows-era C3 record; `C3.L3a` Part 1 (chained
  ladder transitions are clean).
- **C5 is closed** (C5-CLOSE, 2026-10-05): the rung and `remaster` not
  adopted, the 4x source adopted. Reopen only with a 1080p-detail source
  or a different client. **Phase C is closed.**
- **`C3.L3a` is closed** (four sessions, the user's reading): single
  transitions are not reliably noticed, ramps are. Do not re-run the gate;
  build to the decision. **C4 is closed** for Phase C (8+1 stays).

## Relevant References

- G (remote): `evidence/CL_B3_HARDENED_APK_LAN_2026-10-16.md`, `G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`, `G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`, `CL_B2_IDENTITY_APK_AND_LAN_SMOKE_2026-10-16.md`, `G1_S2_…`, `G3_S2_…`, `G3_S1_…`, `G1_S1_…`, `G5_S1_…`, `G4_P1_…`, `E4_S4C_LINK_WATCH_2026-10-16.md`; `docs/REMOTE_TRUST.md`, `docs/WAN_ADAPTATION_RULES.md`; `handoffs/QUEUE_2026-10-16.md`, `QUEUE_2026-10-16B.md`; `patches/CL-B2_IDENTITY_APK_HASH.md`.
- E4: `evidence/E4_S1_…`, `E4_S2_…` (10-09), `E4_S3_MEMORY_FLOOR_CLOSE_…`, `E4_S4_GRAB_DEFERRAL_…`, `E4_S5_SNES_CAPTURE_59FPS_…`, `E4_S3B_MEMORY_FLOOR_1G_SWAPOFF_…`, `E4_S5B_SNES_CAPTURE_PROBE_BENCH_…`, `E4_S4B_GRAB_DEFERRAL_CLEAN_LINK_…` (10-10); `handoffs/QUEUE_2026-10-09.md`, `QUEUE_2026-10-10.md`, `QUEUE_2026-10-10B.md`; `patches/E4-S2_…` … `E4-S5_…`, `E4-S3B_RUNNER_REFRESH_BACKOFF.md`.
- E3: `evidence/E3_A3B_…`, `E3_A3_…` (10-09), `E3_R2_…`, `E3_S7B_…`, `E3_R1_…`, `E3_S7_…` (10-08), `E3_A2_…`, `E3_S*`; `handoffs/QUEUE_2026-10-06.md` … `-08B`; `TOOLS.md` ("The E3 flags", the drop-ins).
- `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md` (E2); `architecture/E1_WORKLOAD_SUITE.md` (the frozen suite); `evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`.
- `evidence/C5_CLOSE_2026-10-05.md`, `decisions/C5_1080P60_CAPABILITY_2026-09-28.md` — C5 and Phase C closed; `evidence/C7_D8_CHECKPOINT_2026-09-30.md`.
- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the baseline table.
- `docs/ROADMAP.md` (the E3 status tables); `handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `docs/KNOWN_ISSUES.md`; `evidence/RUNTIME_VALIDATION.md`; `patches/PATCH_INDEX.md`.
