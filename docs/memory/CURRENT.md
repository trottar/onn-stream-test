---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: efa4240 (G-A3 and CL-B10 PART 1 committed; CL-B10 PART 2 and the record uncommitted beside it; the user commits)
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase E ACTIVE; the G track (remote) under way. G-A1 ADOPTED (2026-10-16, the user's): the overlay provider and
session identity v2 run on the host, and `identity_v2` is on in the client. **G-A2 ADOPTED (2026-10-19, the user's):
the Opus audio path. **G-A3 ADOPTED (2026-10-23, the user's): the client's link report. The adopted environ is NINE
lines.**
CL-B3 is OPEN on two G5-S1 smoke gates (NOT MET; the user decides). Everything else passed: G3-S3's hardened APK
`59f736d2…` is installed and CONFIRMED, the signed LAN path passed, and the VOD play through the range server
passed.** E1 FROZEN; E2
MEASURED; E3 CLOSED; E4 CLOSED (host side). Nothing committed since `af3ed73`.

**State (2026-10-24 04:10Z, after CL-B10): the NINE adopted lines; `--check` ok; APK `da09e154…6cf` CONFIRMED**
(CL-B10; `bf5114a2…` preserved).
- Every client property is empty. `link_report` empty means on with this APK.
- No `e3_flag.conf`, no stream. One device paired; `identity_v2` on.
- Running: `privyhub-link-n1` (nightly) only.

The nine lines:
1. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` (`adaptive.conf`);
2. `PRIVYHUB_EPG_GUIDE_INDEX=cached` (`epg-index.conf`);
3. `PRIVYHUB_SNES_CORE=snes9x` (`snes-core.conf`);
4. `PRIVYHUB_RECOVERY_TRIGGER=v2` (`recovery.conf`);
5. `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` (`snes-capture.conf`);
6. `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`overlay.conf`);
7. `PRIVYHUB_SESSION_IDENTITY=v2` (`session-identity.conf`);
8. `PRIVYHUB_AUDIO_CODEC=opus` (`audio-codec.conf`, G-A2);
9. **`PRIVYHUB_LINK_REPORT=1` (`link-report.conf`, G-A3; diagnostics only)**.

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
- **Installed (CL-B7, 2026-10-19 16:56Z): APK `93d29b4a…1624`**, CL-B7P's build: CL-B5's client plus the lean-drain flag
  `debug.privyhub.opus_decode` (absent = today). Pinned by patch `CL-B7_LEAN_APK_HASH`; CONFIRMED at 17:48Z. Before it,
  APK `043891e1…1607` (CL-B5's debug build, installed 2026-10-18 23:26Z: CL-B4's Opus decode,
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

**CL-B12: MEASURED, 3 / 3 cells valid; APK `20e3e339…563d` (B17 + B18 + B19) CONFIRMED and pinned, every client property
EMPTY** (`evidence/CL_B12_DEFAULTS_AND_UMBRELLA_2026-10-24.md`; cells 2-3 2026-10-24 16:39-17:09Z, cell 1 attended
17:09-17:24Z, all on 5 GHz; the host drop-in `PRIVYHUB_LINK_RECOVERY=1` alone).
- **The stack via the umbrella, with the client's defaults:** in 11 / 11 blackouts the resume came **108-349 ms after
  the return**, with 0 restarts, 0 v2 handovers and net 24 / 26. The picture was held 4.11-4.35 s per 4-s drop.
  **0 saves outside the blackouts;** the bye at each teardown.
- **The guard, two Home presses:** no separate stop, the end logged by the start, the start sent 96-280 ms after the
  new activity, 0 underruns after each new start.
  - Both returns took the new-instance path (`recreate`); the surface and process paths were not exercised.
  - The user: "Each home and return behaved as expected and ran well".
- **Back to B on two narrow rows:**
  - the `link_recovery_config` log line (the six logged as `explicit`; `plugins/games.py:201` logs a second
    `apply()`);
  - one 30-underrun interval at the second Home press (the activity pausing, not a return).
- **On 5 GHz:** 0 silences / 10 min in every span.
- **State:** the seven properties empty (no `setprop` in CL-B12), nine lines, `--check` ok, APK CONFIRMED, paired.
  `e2db0aa0…` is kept at `PrivyHub/app/build/cl_b11_installed/`. B's `ga4_tools.diff` passes `git apply --check` on the
  pinned tree.

1. **The user's commit:**
   - the two records (`CL_B12_LAUNCH_2026-10-24.md`, `CL_B12_DEFAULTS_AND_UMBRELLA_2026-10-24.md`) and
     `cl_b12_2026-10-24/`;
   - the pin (`tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, its test);
   - `KNOWN_ISSUES.md`, `ROADMAP.md`, this file;
   - git status: `logs/cl_b12_git_status.txt`.
2. **G-A4, the user's adoption question: the tenth line `PRIVYHUB_LINK_RECOVERY=1`.**
   - **What it does:** when the Wi-Fi drops for a few seconds, the host freezes the game the moment it notices, about
     a second in, and saves a snapshot about 0.4 s in. When the link comes back, it loads that snapshot and resumes
     within about a third of a second, so you don't die to lag you couldn't see.
   - **What it costs:**
     - you replay about 0.4 s (24-26 frames) of game from before each drop;
     - the picture stays frozen for the drop plus ≤ 0.35 s;
     - one save is written per real stall, and none when you quit.
     - The onn's half (the stall signal, the restart guard) is already on with this APK.
   - **How to turn it off:** delete `~/.config/systemd/user/privyhub-companion.service.d/link-recovery.conf`, then
     `systemctl --user daemon-reload` and `systemctl --user restart privyhub-companion`. The onn's halves go off with
     `debug.privyhub.stall_signal 0` / `debug.privyhub.restart_guard 0`.
   - **The two rows still with B** (a log line; one interval at a Home press) do not change what it does. Applying it
     is a separate prompt (B20's `patches/G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md`).
3. **The loss guard** (`PRIVYHUB_LOSS_GUARD=1` + `loss_guard=1`, BENCH-R3 a candidate). The cost:
   - freezes up to ~0.5 s in place of corrupted frames;
   - hitch s 125.7 against 68.8 per 10 min under 1 % loss, and rendered 55.2 against 57.8 fps;
   - no runtime IDR.
4. **The notice as a client default** (`link_notice` on without the property; shown, "I saw that box"). The cost: an
   on-screen line on any 2.4-GHz or weak link. The 30-s clear path is not yet exercised.
5. **To B:** the two rows, the press-1 ready 8.8 s after its start (press 2: 4.2 s), and the teardown race (the suite's
   `games/stop` before the client's stop → 503; the skip read `state_ended`).
6. **"Read LINK-N1's nights"**: nights done 1, the next 2026-10-25 04:30Z.
7. **The user's own play on 5 GHz** with everything as it is now (nine lines, `20e3e339…`, the properties empty: the
   client's defaults on, the host's stack off until G-A4).

**CL-B11: MEASURED, 3 / 3 cells valid; APK `e2db0aa0…6b33` (B15 + B16) CONFIRMED and pinned**
(`evidence/CL_B11_GUARD_AND_FAST_READY_2026-10-24.md`; cells 2-3 2026-10-24 10:33-11:02Z, cell 1 attended
15:19-15:34Z, all on 5 GHz).
- **Cells 2 / 3 (B16's fast ready): back to B with one row.** In all 10 blackouts the resume came via the client's
  ready **133-458 ms after the return** (CL-B10 427-2,130 ms), with no `encoder_restart` and no v2 handover. The stall
  save came at 429-433 ms, before the pause, and net was 24 / 26. The picture was held 4.13-4.47 s per 4-s drop.
  - **The miss:** one silence save at each session's end (~205 ms before `session_ended`), against "zero outside the
    blackouts" (CL-B10: 4).
- **Cell 1 (B15's guard): back to B with one row.** The Home press and a return through PrivyHub's menu created a new
  stream activity in the live process; the events read confirms it.
  - The old report and the stop came before the new start, with `restart_cause.trigger` `recreate` and `away_ms`
    21,356. Then 52 underruns in 441 s (CL-B10: 2,418 in 28 s).
  - **The miss:** one 2-s interval of 221 underruns before the guard's restart.
  - The user: "I had to click into the game but seemed to be at same spot".
  - Not exercised: the process-death path (CL-B10's) and the same-instance surface path.
- **On 5 GHz, cell 1:** 4.4-5.6 silences and 6.9-12.9 hitch s per 10 min (CL-B10 cell 1: 0 / 0).
- **CONFIRMED by CL-B7 §6** (all three valid). Disclosed: no cell ran with the properties empty; that path is B's
  by-construction proof.
- **State:** the properties cleared and read back empty (including `link_report`), nine lines, `--check` ok, APK
  CONFIRMED, paired. `da09e154…` is kept at `PrivyHub/app/build/cl_b10_installed/`.

1. **The user's commit:**
   - the two records (`CL_B11_LAUNCH_2026-10-24.md`, `CL_B11_GUARD_AND_FAST_READY_2026-10-24.md`) and
     `cl_b11_2026-10-24/`;
   - the pin (`tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, its test);
   - `KNOWN_ISSUES.md`, `ROADMAP.md`, this file;
   - git status: `logs/cl_b11_git_status.txt`.
2. **To B:** the two rows (the session-end save; the pre-restart underrun interval), with the record's tables.
3. **The adoption questions, for the user, each with its cost:**
   - **The hold / state / stall stack on SNES** (`PRIVYHUB_INPUT_HOLD=1 _B6=1 _B8=1 _REWIND=1 PRIVYHUB_STALL_SIGNAL=1
     PRIVYHUB_STALL_RESUME=1` + `stall_signal=1`). Back to B on one row. The measured cost:
     - 24-26 frames per drop, restored to the save;
     - a save per real stall plus one at each session's end;
     - the picture frozen 4.1-4.5 s per 4-s drop, ≤ 0.46 s past its end.
   - **The restart guard** (`restart_guard=1`). Back to B on one row. The cost:
     - a report and a stop posted at each return, and the audio rebuilt;
     - one file in `noBackupFilesDir`;
     - ~3 s more before the picture is back, with one burst of late audio before the rebuild.
   - **The loss guard** (`PRIVYHUB_LOSS_GUARD=1` + `loss_guard=1`, BENCH-R3 a candidate). The cost:
     - freezes up to ~0.5 s in place of corrupted frames;
     - hitch s 125.7 against 68.8 per 10 min under 1 % loss, and rendered 55.2 against 57.8 fps;
     - no runtime IDR.
   - **The notice as a client default** (`link_notice` on without the property; shown, the user's word "I saw that
     box"). The cost: an on-screen line on any 2.4-GHz or weak link. The 30-s clear path is not yet exercised.
4. **"Read LINK-N1's nights"**: nights done 1, the next 2026-10-25 04:30Z.
5. **The user's own play on 5 GHz** with everything in force (nine lines, `e2db0aa0…`, the properties empty). It is the
   first live read of the property-empty path, and the next marked lag will carry the link.

**CL-B10: MEASURED, 4 / 4 cells valid; APK `da09e154…6cf` CONFIRMED and pinned**
(`evidence/CL_B10_RESTART_GUARD_STATE_STALL_NOTICE_2026-10-23.md`; cells 2-3 2026-10-23 18:42-19:11Z, cells 1 and 4
attended 2026-10-24 03:32-04:09Z).
- **The band, in one hour:** 2.4 GHz gave **168 silences and 149 hitch s per 10 min**; 5 GHz gave **0 and 0-9**.
  - The user, on 2.4 GHz: "It's running like absolute shit right now".
  - After the switch: "Switched to 5 with no issues and plays significantly better".
- **Cells 2 / 3 (B12's stack): back to B.** Each met every row but one, in one blackout:
  - `@both`: the resume 2.13 s after the return;
  - `@down`: one `encoder_restart`.
- **Cell 1 (B11's guard): back to B.**
  - The Home press was found, and the client restarted itself in ~6 s ("it never paused from what I can see").
  - But there was no old report, no `session_ended` before the new start, and `restart_cause` null.
  - The new session had 2,418 underruns in 28 s.
- **Cell 4 (B14's notice):** raised on 2.4 GHz at the first heartbeat (reason 1) and cleared on 5 GHz at the new
  session's first heartbeat. **"Shown" on screen awaits the user's word** (their stage-3 message carried none).
- **CONFIRMED by CL-B7 §6** (all four valid). Disclosed: no cell ran with the properties empty, so the property-empty
  path (and the link keys with `link_report` empty) is B's by-construction proof. The user's next play is the first
  live read.

1. **The user's commit:**
   - the record, `cl_b10_2026-10-23/` (PART 2's files), the pin (`tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, its
     test);
   - `KNOWN_ISSUES.md`, `ROADMAP.md`, this file, the PART 2 task file;
   - git status: `logs/cl_b10_git_status.txt`.
2. **The user's word on the notice** (one line: seen or not, the words, a photo): it closes cell 4's gate.
3. **To B:** the guard's rows (cell 1) and the stack's two misses (cells 2 / 3), with the record's tables.
4. **The three adoption questions, for the user, each with its cost:**
   - **The hold / state / stall stack on SNES** (`PRIVYHUB_INPUT_HOLD=1 _B6=1 _B8=1 _REWIND=1 PRIVYHUB_STALL_SIGNAL=1
     PRIVYHUB_STALL_RESUME=1` + `stall_signal=1`).
     - Not a candidate yet: back to B on two misses.
     - When it is, the cost: 24 frames per two-way drop (restored to the save at 0.40 s), a save per stall including
       150-ms gate stalls, and the picture frozen 3.5-7.2 s per 4-s drop.
   - **The loss guard** (`PRIVYHUB_LOSS_GUARD=1` + `loss_guard=1`, BENCH-R3 a candidate). The cost:
     - freezes up to ~0.5 s in place of corrupted frames;
     - hitch s 125.7 against 68.8 per 10 min under 1 % loss, and rendered 55.2 against 57.8 fps;
     - no runtime IDR.
   - **The notice as a client default** (`link_notice` on without the property). The cost: an on-screen line on any
     2.4-GHz or weak link. It is raised at once and cleared on a good link; the 30-s clear path is not yet exercised.
     Pending the user's word that it shows as built.
5. **"Read LINK-N1's nights"** after a few nights. The watch is sampling tonight.
6. **The user's own play on 5 GHz** with everything in force (nine lines, `da09e154…`, the properties empty). The next
   marked lag will carry the link.

**G-A3: `PRIVYHUB_LINK_REPORT=1` ADOPTED, the ninth line** (`evidence/G_A3_LINK_REPORT_ADOPTION_2026-10-23.md`; the
user's decision, "Yes to both"; `patches/G-A3_LINK_REPORT_ADOPTED.md`). **The adopted environ is NINE lines:**
1. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` (`adaptive.conf`);
2. `PRIVYHUB_EPG_GUIDE_INDEX=cached` (`epg-index.conf`);
3. `PRIVYHUB_SNES_CORE=snes9x` (`snes-core.conf`);
4. `PRIVYHUB_RECOVERY_TRIGGER=v2` (`recovery.conf`);
5. `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` (`snes-capture.conf`);
6. `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`overlay.conf`);
7. `PRIVYHUB_SESSION_IDENTITY=v2` (`session-identity.conf`);
8. `PRIVYHUB_AUDIO_CODEC=opus` (`audio-codec.conf`);
9. **`PRIVYHUB_LINK_REPORT=1` (`link-report.conf`; diagnostics only)**.

- **The adoption:** B's prepared diff was applied, and the tools read nine (self-test OK, `test_e1_remote` 21,
  `test_c3_l4_nft_night` 33). The drop-in was written, and the companion restarted at 18:24Z. `--check` ok on nine.
- **The confirmation window** (no flag file, 5 GHz) was VALID, host gates met:
  - 346 / 346 heartbeats with all five `link_*` keys, via the property path on `bf5114a2…`;
  - silences 0.0 and hitch seconds 0.9 per 10 min (LINK-R1: 0 / 0).
- **Off:** delete `link-report.conf`, then daemon-reload + restart (`REMOTE_TRUST.md` §10).

**CL-B10 PART 1: `da09e154…` INSTALLED, two bench cells RUNNING** (`evidence/CL_B10_LAUNCH_2026-10-23.md`; the unit
`privyhub-cl-b10`, launched 18:42Z, closes itself ~19:17Z).
- **The install:** sha256 = B's pin, same signer, paired. `bf5114a2…` is preserved in
  `PrivyHub/app/build/cl_b10_preserved/`.
- **The onn:** 5 GHz. Properties `restart_guard` / `stall_signal` / `link_notice` = 1, **left for PART 2**.
- **The cells:**
  - cell 2 `blackout-4s@both`, then cell 3 `@down`;
  - both with `INPUT_HOLD=1 _B6=1 _B8=1 _REWIND=1 STALL_SIGNAL=1 STALL_RESUME=1`;
  - cell 2 was PLAYING at 18:44:35Z with 16 lines.
- **Status:** `cat ~/privyhub_cl_b10/status.txt`. **Stop: `touch ~/privyhub_cl_b10/STOP`.** The status line's own
  text names `~/privyhub_bench_r3/STOP`, a stale string, and that path does nothing.
- `--check` reads `MISMATCH` on the APK alone until the CONFIRMED rule.

1. **The user's commit:**
   - G-A3: the record, `g_a3_2026-10-23/`, the patch file, the four tools, `REMOTE_TRUST.md`, `ROADMAP.md`;
   - CL-B10: the launch record, `cl_b10_2026-10-23/` (the driver keeps writing `runs/` until it closes);
   - the task file, `_cowork_prompt.txt`, this file;
   - git status: `logs/g_a3_git_status.txt`, `logs/cl_b10_launch_git_status.txt`.
2. **CL-B10 PART 2 (attended, a later prompt):**
   - cell 1: the restart guard, Home ~5 s and back;
   - cell 4: the notice on 2.4 GHz, then back to 5 GHz (the user's hand);
   - then the properties cleared, `--check` on nine;
   - the record for all four cells, and the CONFIRMED rule for `da09e154…` (else `bf5114a2…` reinstalled).
   - The reading for cells 2 / 3 is pre-registered: both rows met → the hold / state / stall stack is a candidate on
     SNES, at ~24 frames per two-way drop, a save per stall, and the frozen picture while held.
3. **LINK-N1 keeps running** to 10-31 (first night tonight, 04:30Z): "read LINK-N1's nights".

**LINK-R1: the 5-GHz check — MEASURED, valid; 0 uplink silences ≥ 250 ms and 0 hitch seconds in 10 min**
(`evidence/LINK_R1_5GHZ_CHECK_2026-10-23.md`; one E1-SNES-STREAM 15:52-16:04Z, drop-in `PRIVYHUB_LINK_REPORT=1` only,
nine lines read back; nothing adopted). The user moved the onn to 5 GHz by hand ("I swapped to 5G").
- **The onn is on 5 GHz:** 5180 MHz, channel 36, 802.11ac in 346 / 346 heartbeats. RSSI −68 (as on 2.4 GHz); tx 195 /
  rx 117 Mbps median; no tx heartbeat ≤ 54 Mbps.
- **Silences 0.0 / 10 min** (BENCH-R3 C 22.4, BENCH-R1 cell 8 15.6). **Hitch seconds 0.0** (C 19.9). Post-FEC loss
  4.9 / min (C 33). Rendered 59.98, max output gap 120 ms, host gates met.
- **The Opal's 5 GHz radio lists the onn's station:** signal −76, retries 8.0 %, the AP's tx rate swinging 30-433 Mbps.
- **The pre-registered reading:** E2 met, so the band was most of the room-independent flapping. **Caveats:** one
  daytime window, a different drop-in from C (no stack), and 0 silences means there is no 5-GHz distribution yet to
  re-derive H from.
- **State:** eight lines, no `e3_flag.conf`, `--check` ok, APK `bf5114a2…` CONFIRMED.
  - **`debug.privyhub.link_report` LEFT at 1** on the onn (the user's say-so; diagnostics only). It clears on the
    onn's reboot; to set it again: `adb shell setprop debug.privyhub.link_report 1`.

**LINK-N1: the nightly watch is RUNNING** (`evidence/LINK_N1_LAUNCH_2026-10-23.md`). The unit `privyhub-link-n1`
(launched 16:10:56Z) samples 00:30-01:30 EDT = 04:30-05:30Z each night, with no stream, read-only:
- ping to the onn every 1 s;
- the onn's Wi-Fi over adb every 30 s;
- the Opal's `wlan1` every 60 s, redacted;
- the hub's loadavg.

It runs to the cap 2026-10-31T06:00:00Z (8 windows; the task named 7). The first is tonight, 04:30Z.
- Status: `cat ~/privyhub_link_n1/status.txt`. Stop: `touch ~/privyhub_link_n1/STOP`.
- Linger is off, so a logout or reboot ends it; the restart command is in the launch record.

1. **The user's commit:** `LINK_R1_5GHZ_CHECK_2026-10-23.md`, `link_r1_2026-10-23/`, `LINK_N1_LAUNCH_2026-10-23.md`,
   `link_n1_2026-10-23/` (the watch keeps appending to `nights/` and `summary.md` until 10-31), the task file,
   `_cowork_prompt.txt`, this file (`logs/link_r1_git_status.txt`, `logs/link_n1_launch_git_status.txt`).
2. **After 10-31 (or any morning, for a partial read): "read LINK-N1's nights."** The reading is pre-registered: a
   minute that recurs on ≥ 2 nights → name the device (the user's hand; the Opal's client list then, read-only).
   Nothing recurring → the 1-am pattern needed a stream, or was the 2.4-GHz band.
3. **The user's adoption question:** a **ninth adopted line `PRIVYHUB_LINK_REPORT=1`** (host; diagnostics only). The
   client side is already on. Without it, the host keeps no link keys outside a run's drop-in. With it, the next lag
   the user marks carries its band / RSSI / rates.
4. **The B queue:**
   - re-derive the stack's H from 5-GHz sessions, once they show silences;
   - the savestate path for snes9x (its rewind reads PAUSED, BENCH-R3);
   - the client's self-restart after a two-way drop: the lost session and the audio-underrun storm (UX-R4 §1.3);
   - the link report on by default in the client (no property).

**UX-R4: the lag the user marked with a Save State — FOUND, read-only**
(`evidence/UX_R4_SAVED_AT_THE_LAG_2026-10-23.md`; play 2026-10-23 04:54-05:07Z, Zelda on snes9x; nothing changed).
- **In force:** APK `bf5114a2…` (by the files), the eight adopted lines only, every property empty. So **no RSSI and no
  corrupted-frame counter** for this session.
- **The mark is the 05:01:30Z save.** It came after a 41-s storm, 05:00:40.9-05:01:20Z:
  - 19 uplink silences ≥ 250 ms (9.5 s silent, the longest 1.4 s);
  - the downlink's loss ×9 (284 per minute), 43-44 fps in two intervals, audio concealment ×25;
  - the host steady at 7000, 60 frames per second.
  - Shape: **both directions, uplink-dominant**. ~4.8 s of game ran without the player.
- **47 s after the resume:** a 4.9-s two-way drop (05:03:39.8Z). The client restarted its stream by itself, its audio
  then underran, and the user loaded the save.
- **Clock:** the same quarter-hour after 00:50 EDT as UX-R2's step and UX-R3's death (a coincidence in time).
- **By the records,** the hold (3 fires), the stall signal (none), the loss guard (freezes) and the bidirectional rule
  (one rung down at 05:01:00Z) would not have addressed a storm of mostly sub-second uplink silences.

1. **The user's commit:** `UX_R4_SAVED_AT_THE_LAG_2026-10-23.md`, `ux_r4_2026-10-23/` (36 MB, mostly the log
   copies), `KNOWN_ISSUES.md`, this file (`logs/ux_r4_git_status.txt`).
2. **For the user's say-so (nothing done):**
   - **The 2.4-GHz finding is the user's hand change.** BENCH-R3 measured the onn on 2.4 GHz channel 1 (802.11n,
     −68 dBm); O1 found it on the Opal's 5 GHz. Moving it back, on the Opal or on the onn, is the user's setting. An
     evening like tonight's would show whether it helps.
   - **The link report on during play.** `PRIVYHUB_LINK_REPORT=1` as a **ninth adopted line**, diagnostics only (it
     adds the RSSI / tx / rx / band to each heartbeat, no behaviour), plus `adb shell setprop debug.privyhub.link_report
     1` after each onn boot. Then the next lag the user marks carries its link.
3. **Then the BENCH-R3 items below** (the loss-guard question, the Opal's `wlan0` read, B's items).

**BENCH-R3: the stack on SNES, the loss guard, the link — MEASURED, 6 / 6 valid, host gates met in all**
(`evidence/BENCH_R3_SNES_STACK_AND_LOSS_GUARD_2026-10-23.md`; run 20:22:11-21:52:17Z on `9fd73c7`; nothing adopted).
- **The hold / rewind / stall stack is NOT a candidate on SNES** (A and B missed; C met):
  - `@both`: one hold per blackout at 0.95-0.97 s, but snes9x's hold-path rewind read PAUSED after 7 / 7 rewinds.
    That leaves 47.5-48.7 unattended frames per blackout (bar ≤ 5). The resume came 2.06-3.13 s after the return,
    via the gate's ready in 4 / 5.
  - `@down`: the pause 420-428 ms after the client's last frame in 4 / 5 blackouts, 484 in one (bar 0.40-0.46).
    Recovery v2 resumed each blackout's pause (3 encoder restarts, one step 7000→5000). 0 stall pauses outside the
    blackouts.
  - Clean: 0 false holds, 0 stall pauses.
- **PS1's savestate fallback works:** 5 / 5 loads played, net 24 frames per blackout. It joins nothing while the stack
  is not a candidate.
- **The loss guard IS a candidate:** held 3,010 = its counter's 3,010, 0 timeouts, max wait 501 ms. No watch.
- **The link:** the onn is on 2.4 GHz channel 1 (802.11n, RSSI −67…−69). The Opal sampler read the 5 GHz `wlan1`,
  which had no station in 18 rounds.
  - One coincidence in time: E-on's cluster of 42 uplink silences coincided with the onn's tx rate falling to 27-81
    Mbps.
  - The downlink loss bursts coincided with no RSSI change beyond 1 dB.
- **APK `bf5114a2…cf73` CONFIRMED (the pre-registered rule) and pinned;** `cb0935c8…` preserved. At the record:
  `--check` ok on the eight lines, APK CONFIRMED, no `e3_flag.conf`, the properties empty.

1. **The user's commit:**
   - BENCH-R3's record, `bench_r3_2026-10-22/` (`record/`, `opal/`, `runs/`, the launch files);
   - `BENCH_R3_LAUNCH_2026-10-22.md`, the task file, `_cowork_prompt.txt`;
   - the pin: `tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, `tools/test_c3_l4_nft_night.py`;
   - `KNOWN_ISSUES.md`, `ROADMAP.md`, this file (`logs/bench_r3_git_status.txt`).
2. **Adoption question (the reading gives one): the loss guard** (`debug.privyhub.loss_guard=1` on the onn +
   `PRIVYHUB_LOSS_GUARD=1` on the host). It freezes the last good frame until the next IDR instead of showing
   corrupted ones. Its costs:
   - freezes of up to ~0.5 s (501 ms here; B10 expected ≤ 250);
   - 125.7 hitch seconds per 10 min against 68.8 without it (104.3 outside a house cluster in the cell);
   - rendered 55.2 against 57.8 fps;
   - the keyframe requests force nothing (no runtime IDR path);
   - the property resets on a reboot, so making it the default is a B task;
   - nobody has watched it yet. **A look at the TV with it on and off is the cheapest next evidence**, if the user
     wants it before deciding.
   - **No question on the stack or PS1:** the reading gives none. The stack's costs, for when B returns it: the frozen
     picture during a hold; ~1 s of unattended game at H 950; snes9x's 61-MB rewind buffer; a ~1-s rewind before every
     resume.
3. **The link finding's next task (session A, read-only, ~20 min).** The onn is on the band where the Opal's `wlan0` is,
   and the sampler read `wlan1`.
   - One `iw dev wlan0 station dump` through `o1_redact.py` (is the onn on the Opal?).
   - If it is, O1's sampler on `wlan0` beside one clean stream: the onn's retries / signal / rate per 5 min next to the
     link report.
   - Then the user's call whether to try the onn on 5 GHz as a cell.
4. **For session B (the user's call which):**
   - the hold path's rewind after-check (PAUSED after 59-frame rewinds on snes9x 7 / 7; 2-3-frame `stall_end` rewinds
     pass 4 / 5);
   - the ~1-s per-frame rewind before the resume;
   - `@down`'s ownership (recovery v2 resumes the blackout's pause);
   - whether the PS1 `state` path should serve SNES too.
5. **Then the user plays,** wherever they like. The onn has the CONFIRMED `bf5114a2…`, with every flag and property
   absent: today's stream (the loss guard on only if adopted).

**BENCH-R2: the lock, the hold, the stall signal — MEASURED, 15 / 15 valid, host gates met in all**
(`evidence/BENCH_R2_LOCK_HOLD_STALL_CELLS_2026-10-23.md`; run 14:09:00-17:45:11Z on `43a8df6`; nothing adopted).
- **The Wi-Fi lock is not the cause of the uplink silences** (none 41.8, `low_latency` 151.6, `high_perf` 29.5 per
  10 min; bar −80 %). The room changed across that hour. B6's H (950) stands.
- **The hold + rewind + stall stack is NOT a candidate:**
  - `@both`: ~45 unattended frames per blackout (bar ≤ 5). The stall takes the hold over, so the pre-hold frames are not
    rewound, and the core resumes 2-4 s after the link's return.
  - Clean hour: 2.6 stall pauses per 10 min (bar ≤ 2).
  - `@down`: the pause 0.15-0.21 s after the client's last frame (met).
- **Beetle PSX HW's rewind is not confirmed:** 118 / 123 failed B4's after-check; +1 GB RSS, +16.6 points of a core.
  snes9x's rewind is untested.
- **The bidirectional LAN rule never fired** (0 asks on the three loss cells).
- **The user's glitches (16:05-16:17Z, the loss-1 cell)** are loss-corrupted frames the client decoded through: 488
  frames dropped for missing packets and no error counter. The same happens with the previous APK.
- **APK `cb0935c8…` CONFIRMED (the pre-registered rule) and pinned;** `93d29b4a…` preserved. At the record: `--check`
  ok, the eight lines, no `e3_flag.conf`, the properties empty.

1. **The user's commit:**
   - BENCH-R2's record, `bench_r2_2026-10-22/` (`logs_bench/`, `record/`, the client reports in `runs/`);
   - `BENCH_R2_LAUNCH_2026-10-22.md`, the task file, `_cowork_prompt.txt`;
   - the pin: `tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, `tools/test_c3_l4_nft_night.py`;
   - `KNOWN_ISSUES.md`, `ROADMAP.md`, this file (`logs/bench_r2_git_status.txt`).
2. **Adoption questions: none. The reading gives none.**
   - The lock did not cut the silences. Its cost if adopted anyway: battery / scan behaviour on the onn, for no measured
     gain.
   - The stack missed b1's bar and d1's. Its costs, stated for when B returns it:
     - the frozen picture during a hold;
     - ~1 s (57 frames) of unattended game at H 950 unless rewound;
     - the rewind buffer: SNES +29 MB / +0.3 points, PSX HW +1 GB / +16.6 points (and not confirmed to rewind).
3. **For session B (the user's call which):**
   - the hold's ownership at the return (rewind the pre-hold frames; resume at the return, as b2's 1.1 s);
   - PSX HW's after-check, or a SNES-only stack;
   - the stall threshold (0 at 400 on a clean hour);
   - the decode-through-loss pictures (freeze to the next IDR, or count frames decoded after a dropped reference).
   - A bench on snes9x is what would exercise rewind at all.
4. **Then the user plays,** wherever they like. The onn has the CONFIRMED `cb0935c8…`, every flag and property absent,
   i.e. today's stream.

**ML-R1: the hitch early-warning detector — MEASURED offline, NO FLAG PROPOSED**
(`evidence/ML_R1_HITCH_EARLY_WARNING_2026-10-23.md`; run 13:24:47-13:28:48Z, 4 min; nothing adopted).
- **The data:** 128 client sessions, 10-10 to 10-22 (the control-gap log starts 10-10), 49,785 labelled seconds,
  132 host-side inputs. Held out: the two evenings (UX-R1, UX-R2) and BENCH-R1 cell 5.
- **As hashed, the bar reads "met".** That is an artefact of my pre-registration's false-alarm definition: the
  chosen thresholds alarm on every second, and an always-on alarm forms one episode per session, which always holds a
  hitch. Stated, not re-scored.
- **What it really shows:**
  - The detector ranks better than every hand rule (AUPRC 0.666 against 0.398 for silence 250 ms, k = 2).
  - At a matched alarm duty it adds only +2.5 points of recall over the 250-ms silence rule (70.9 against 68.4 %;
    post hoc, labelled).
  - It mostly reads "already hitching".
  - Nothing fires ≥ 2 s before the death at any usable operating point.
- **Also disclosed:** BENCH-R1 cell 8 fell out of the run by the pre-registration's coverage-end rule (14 s past the
  gap log's last row). It was scored post hoc with the frozen models.

1. **The user's commit:** `ml_r1_2026-10-22/` (the inputs are 12 MB), the record, `tools/hitch_predictor.py`,
   `KNOWN_ISSUES.md`, `ROADMAP.md`, this file (`logs/ml_r1_git_status.txt`). BENCH-R1's record is still uncommitted too.
2. **The detector's next step: none proposed.** The fix for the death is the hold / rewind making an outage cost
   nothing, not predicting it.
   - An ML-R2 only for the user's say: a seconds-based false-alarm rule, onsets as the target, and B3's link features
     after CL-B8.
3. **BENCH-R2 after session B's queue (`QUEUE_2026-10-22C`)**, as `SESSION_B_DONE_2026-10-22B.md` §8 sketches it,
   with B5 (the Wi-Fi lock) and B6 (H = 950) folded in as B's records state.

**BENCH-R1: the loss and blackout cells — MEASURED, 8 / 8 valid** (`evidence/BENCH_R1_BLACKOUT_AND_LOSS_CELLS_2026-10-22.md`;
run 02:31:50-04:26:59Z on `b909735`, read 2026-10-22; nothing adopted).
- **The death is reproduced on the bench:** `blackout-4s@both,every=120s`, all four shape terms in 5 / 5 blackouts,
  85.0 unattended frames (core running) per blackout against the death's 83.8.
  - B1 lets the client's desync through, so v2 pauses ~1.5 s into a bench blackout. A real drop runs up to ~234 frames
    unheld.
- **The input hold (`PRIVYHUB_INPUT_HOLD=250`) is NOT a candidate until its trigger is fixed** (the hashed reading).
  - 18 holds in 11.5 min on a clean link (cell 8): the room's own ≥ 250-ms uplink silences.
  - −73 % per blackout, not ≥ 90 %: one blackout skipped by the cap, and v2 took every other hold over ~1 s in.
- **The LAN loss rule goes back to B** (the hashed reading): first step 0.9-1.5 min into the stream, not 3-4; in cell
  4, ~2 min before G8-S1's `capacity_mild` point.
  - Disclosed: on LAN-R1's own clock (from the driver's cell start), cell 2 matches. The hashed wording was applied.
- Host gates met in all eight. Cell 1 (loss-1, rule off) held 7000, with one 27.7-s recovery.

1. **The user's commit:** BENCH-R1's record, `bench_r1_2026-10-22/` (with `logs_bench/` and `record/`),
   each cell's client report under `runs/<cell>/logs_run1/decoder_sessions/`, `KNOWN_ISSUES.md`, `ROADMAP.md`, this
   file (`logs/bench_r1_git_status.txt`).
2. **Adoption questions: none.** The reading gives none: the hold is not a candidate, and the rule is back with B.
   The user may weigh the disclosed clock difference for the rule (record §6). Nothing changes unless they say so.
3. **For session B (the user's call what B takes):**
   - the hold's trigger: the false holds on an idle LAN (15-16 per 10 min at 250 ms), the 6-per-60-s cap spent by
     a flapping minute, and v2's `client_output_silence` handover (no release; the core resumes ~2 s after the link);
   - the rule's timing, which did not transfer from the replay;
   - B1: gate the client's desync request on `@both` too.
4. **Then CL-B8** (install B3's APK `e4d02354…`, one LAN window), **then BENCH-R2** as B sketched it
   (`SESSION_B_DONE_2026-10-22B.md` §8):
   - (a) `blackout-4s@both,every=120s,seed=1` + `PRIVYHUB_INPUT_HOLD=250` + `PRIVYHUB_INPUT_HOLD_REWIND=1` on snes9x.
     Expected: net unattended ≈ 0 per blackout, `rewound_frames` ≈ `requested_frames` (~17-20), no `rewind_failed`,
     the post-rewind frame = the onset's.
   - (b) plain E1 rows per core (snes9x, Beetle PSX HW), rewind on vs off, for the CPU and RetroArch's RSS.
   - (c) whether Beetle PSX HW's hardware renderer rewinds at all (if not, the flag is SNES-only).
   - (d) whether REWIND is honoured while paused.
   - Note: BENCH-R2 rides on the hold, which this reading says is not a candidate yet. Rewind's own questions (b-d)
     stand either way; (a)'s net count is only as good as the hold's trigger.
5. **The night queue `QUEUE_2026-10-19N.md` is still HELD until the user says.** The instrumented evening in the
   user's room stays the next run for their say-so.

**UX-R3: find the deaths** (`evidence/UX_R3_FIND_THE_DEATHS_2026-10-21.md`; read-only from the copies; no run, no
adb).
- The user: "It felt better but there were two memorable instances where I literally died because of lag."
- **Their standard: "This product needs to work at any house especially lan as long as the Internet is over 50mb/s."**
- **Death 1 found:** 04:54:55-04:54:59Z, halfway through Zelda. A ~4-s drop in both directions: the uplink silent
  2.65 s, output gaps 410 / 307 ms, 61 lost after FEC, frame sizes normal. The ladder saw nothing and could not have
  acted.
- **Death 2 is not distinguishable** in 04:56-05:03Z; the instruments' blind spots are named in the record.
- **Hitch seconds per 10 min:** Sunday 43.3, last night 12.9. This orders the two as the user does (a candidate metric,
  not adopted). September cannot be scored.

1. **The night queue `QUEUE_2026-10-19N.md` is still HELD until the user says.**
2. **The next run, for the user's say-so: the instrumented evening in the user's own room** (the TV and Wi-Fi path the
   two evenings used). This is UX-R1's H1 test with UX-R2's additions, plus:
   - **the Opal's view (station counters for the onn: retries, rate, signal) every 5 min, read-only, and densely around
     any user mark;**
   - **the user's clock marks:** the user says "now" (or notes the host clock) at each hitch or death, so a death has
     a second, not a 13-minute window;
   - the heartbeat and control-gap logs preserved that night (they rotate);
   - ≥ 65 min of play, 00:40-01:30 EDT, PS1 first then SNES after ~00:56;
   - the onn's `udp6` drops, `cl_b6_onn_read.py` and `cl_b7_onn_threads.py` every 5 min; `boot_count` at the start and
     the end.
3. **LAN-R1 (session B):** the loss step-down replay and design. UX-R3 §3's table is its input: no live rule acts on a
   3-5-s bidirectional drop.
4. **The user's commit:** UX-R3's record, `ux_r3_2026-10-21/`, `KNOWN_ISSUES.md`, this file, the task file and
   `_cowork_prompt.txt` (`logs/ux_r3_git_status.txt`).

**UX-R2: the second evening read** (`evidence/UX_R2_SECOND_EVENING_2026-10-21.md`, read 2026-10-21 15:31-15:45Z; nothing
run, changed or adopted).
- At the read: the eight lines, `--check` ok, APK `93d29b4a…` CONFIRMED, nothing streaming. The onn was cold-booted
  again ~15:01Z today. The user: "Ran a few games last night"; how it felt: **no report yet**.
- **Mostly clean:** 04:42-05:26Z, 43 min, Zelda (SNES) first, then three PS1 titles.
  - After the first 5 min: loss 37.5 / min, underruns 3.9 / min. No pause, no encoder restart.
  - UX-R1's damage did not repeat at its clock. R2 ended at play-minute 44, before UX-R1's damaging play-minutes 45-64.
- **The single-loss step repeated at the same clock** (04:52Z against 04:54-04:56Z; play-minute 10 against 35), under
  SNES both nights.
- **H5 CLOSED, not new:** the Pause menu ends the stream session; 2026-09-20 did the same.
- **H2 / H3 / H4 are weakened;** H1 stays first.

1. **The night queue `QUEUE_2026-10-19N.md` is still HELD until the user says.**
2. **The next task, for the user's say-so: the instrumented evening.** This is UX-R1's H1 test plus UX-R2's additions:
   - **≥ 65 min of play** (past play-minute 45);
   - **00:40-01:30 EDT on the clock, starting on PS1 and switching to SNES after ~00:56.** A step at ~00:52 on PS1
     means the clock; a step only at SNES means the content.
   - **Every 5 min:** the onn's `udp6` drops while PrivyHub runs, `cl_b6_onn_read.py`, `cl_b7_onn_threads.py`, and
     **the Opal's station counters read-only (required)**, or the link watch resumed for the evening;
   - `settings global boot_count` at the start and the end;
   - the user narrating against the host clock.
3. **Questions for the user:**
   - How did last night feel?
   - Was the onn power-cycled between 10-20 ~18:30Z and the evening?
   - Do they cold-boot the onn the day after playing? Both evenings were followed by one.
4. **The user's commit:** UX-R2's record, `ux_r2_2026-10-21/`, `KNOWN_ISSUES.md`, this file, the task file and
   `_cowork_prompt.txt` (`logs/ux_r2_git_status.txt`).

**UX-R1: the user's extended evening read; OPEN** (`evidence/UX_R1_EXTENDED_SESSION_REGRESSION_2026-10-20.md`, read
2026-10-20 18:25-18:40Z; nothing run, changed or adopted). At the read: the eight lines, `--check` ok, APK
`93d29b4a…` CONFIRMED, nothing streaming. The onn was cold-booted ~14:22Z today (after the session).
- **The files agree with the user's "horrible."** Play ran 04:19-05:22Z on the LAN: five games, 20 client sessions.
  - First 5 min: underruns 3.9 / min, post-FEC loss 26 / min, the week's clean figures.
  - After: 39.4 / 173. SNES was worst, and SNES was also the last 31 min.
  - Bursts at 05:06 / 05:10 / 05:20-21 hit both directions and ended in two silence pauses and an encoder restart.
- **Ruled out by the files:** the host, the grabs (none ran), the ladder (7000 throughout), the frame-size tail (cap
  held, ρ −0.13).
- **Loss rose with the evening (ρ 0.52) and the audio followed it (ρ 0.83).** Link vs the onn's receive side is not
  separable from the files: neither end was read, and the onn's end state is lost.

1. **The night queue `QUEUE_2026-10-19N.md` is HELD until the user says.**
2. **The next task, for the user's say-so (H1, ranked first; written, not run):** one instrumented evening.
   - The user plays the same games for ≥ 60 min, and the onn is power-cycled first.
   - Every 5 min: the onn's `/proc/net/udp6` drops, `cl_b6_onn_read.py` and `cl_b7_onn_threads.py`; the Opal's
     station counters read-only (or the link watch resumed for the evening); the user narrating against the host
     clock.
   - `udp6` drops moving with the loss → the onn. Drops at 0 while the Opal's counters move → the air.
   - Then, as the files direct: the order reversed (SNES first) and the kill switches, one per evening.
3. **Questions only the user can answer:**
   - Was the onn power-cycled between CL-B7 (~16:52Z) and the evening?
   - Did they cold-boot it today because of the evening?
   - Were the Load States in Emperor's New Groove (16 in 19 min) part of what felt bad?
4. **The user's commit:** everything since `d3a8ee3`: CL-B7's files (below) and UX-R1's.
   - The record, `ux_r1_2026-10-20/`, `KNOWN_ISSUES.md`, this file.
   - The task file and `_cowork_prompt.txt` (`logs/ux_r1_git_status.txt`).

**CL-B7: three arms on a fresh onn, all VALID** (`evidence/CL_B7_OPUS_CLIENT_THREADS_AB_2026-10-19.md`, 2026-10-19
16:55-17:48Z; host gates held; the eight lines and `--check` ok at the end; **APK `93d29b4a…1624` installed and now
CONFIRMED**, the property empty).
- **The Opus cost on the onn is located: the platform's Opus MediaCodec.** Today − PCM: the process +19.5 % of a core
  plus `media.swcodec` +11.1, ≈ 0.31 core. Three quarters of it is framework-side (`MediaCodec_loop` +9.8, binder +2.2,
  `media.swcodec`); our own threads +7.5. B's hypothesis holds.
- **Lean moved nothing** (framework / binder ~0): the per-call count is not the owner.
- **Spikes ≥ 20 / min:** PCM 70.1, today 121.0, lean 108.7 (between; one run each).
- **Underruns:** 16 / 25 / 12.
- **The user:**
  - PCM: "Sounds fine, maybe small (<1 second) stutter every 20 seconds or so";
  - Opus today: "Sounds good, no stutters noticed";
  - lean: "Sound is good, no stutters" (after the arm ended).

1. **The user's commit:** everything since `d3a8ee3`:
   - `tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, `tools/test_c3_l4_nft_night.py` (the CONFIRMED hash);
   - the record, `cl_b7_2026-10-19/`, patch `CL-B7_LEAN_APK_HASH`, `KNOWN_ISSUES.md`, this file;
   - the task file and `_cowork_prompt.txt` (`logs/cl_b7_git_status.txt`).
2. **What to build next, if anything, is the user's call.** The table names the owner as the platform codec. The
   options are fewer frames through MediaCodec (20-ms Opus frames: half the frames, +10 ms latency; host and client)
   or a decoder outside MediaCodec (libopus via JNI; no NDK on the host today). Or leave it: the user hears no problem
   on Opus, and Opus stays adopted (2026-10-19 decision).
3. **The off-site reconnect test** is held until the user says.

**G8-S5 MEASURED, 2/2 valid** (`evidence/G8_S5_CAP_CELL_ENCODER_RC_TIGHT_2026-10-19.md`, 2026-10-19 14:42-15:15Z,
the unit `privyhub-g8-s5` closed by itself and collected; at the record the eight lines, no `e3_flag.conf`, `--check` ok
with adb reconnected by hand and only read).
- G8-S3's cell 1 (cap-6000, 5000 floor) run paired: A flag absent, B `PRIVYHUB_ENCODER_RC=tight`. Both reached PLAYING
  with host gates met, and the encoder command was read back in each.
- **Before A's pause (first 235 s):** tail drop 6.52 → 4.43 %, **per-second drop p95 19.68 → 15.75 % (not halved)**,
  largest frame 89,248 B in both, rendered 53.45 → 55.12 fps, loss 2,286 → 1,534/min.
- **A went silent 235 s in** and recovery gave up (max gap 366.8 s); B held 600 s. One run each.
- **The pre-registered reading:** the p95 did not halve, so the bench did not transfer and the `tight` item closes as
  measured. **Not a candidate by the written reading; nothing adopted.**
- **The user's decision 2026-10-19:** Opus stays adopted. It is a watch item, with hands-on testing as things change
  (`KNOWN_ISSUES.md`).

1. **The user's commit:** everything since `7a1ab60` that is session A's:
   - the record and `g8_s5_2026-10-19/`;
   - ROADMAP §G8, `KNOWN_ISSUES.md` (the rate-cap item's G8-S3 / G8-S5 entry, the Opus decision line), this file;
   - the G8-S5 task file and `_cowork_prompt.txt` (`logs/g8_s5_git_status.txt`).

   Session B's CL-B7P files (`PrivyHub/…`, `tools/cl_b7_onn_threads.py`, `cl_b7p_2026-10-19/`, its task file and
   `_cowork_prompt_b.txt`) are its own.
2. **`tight`:** no adoption question by the written reading. If the user wants to pursue it anyway (the tail drop and
   loss fell by a third; only the flag-absent cell went silent), the next step is more paired runs aimed at the
   silences under the cap. Those silences are open in `KNOWN_ISSUES.md` and not located. The picture cost is
   G8-S4's −0.45 dB PSNR avg.
3. **CL-B7:** the client A/B, after session B's CL-B7P.
4. **The off-site reconnect test** (a hotspot toggle resuming over the overlay; G4-S1 run 2) is held until the user
   says.

**G4-S3 VALID** (`evidence/G4_S3_OFFSITE_4000_OPUS_2026-10-19.md`, 2026-10-19 13:49-14:12Z; the eight lines, no
`e3_flag.conf`; `--check` host fields ok, the client fields pending `adb connect` after the network change).
- **Off-site at 4000 with Opus: the tailnet wire rate is 5,299 kbit/s** (expected ~5,370 ±10 %, met; G4-S2 with PCM
  8,243): ~40 MB/min, ~2.4 GB/h, 443 MB for the run.
- Host gates met, with the RetroArch counter read (59.999). Loss 0.21/min. Underruns 34 in the window (three client
  starts); spikes ~45/min.
- The user: "Audio and visual looked good, consistent with lan".

1. **The user's commit:** everything since `1c8c2c2`:
   - the launch record and the record, with `g4_s3_2026-10-19/`;
   - ROADMAP §G4, `KNOWN_ISSUES.md` (the wire-rate item addressed, the counter item closed), this file;
   - the task file and the prompt (`logs/g4_s3_launch_git_status.txt`, `logs/g4_s3_git_status.txt`).
2. **adb:** `adb connect <onn-address>:5555` by hand after the onn's network change, then `--check` reads ok.
3. **Pending:**
   - the reconnect-over-overlay test (a hotspot toggle resuming over the overlay; G4-S1 run 2), on a true off-site
     day;
   - G8-S5 (G8-S3 cell 1 with `PRIVYHUB_ENCODER_RC=tight`);
   - the spikes item (Opus's ~0.2 core on the onn; `KNOWN_ISSUES.md`), with underruns a watch item.

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
