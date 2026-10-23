---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 00c7c40 (BENCH-R3's record committed; this record uncommitted)
---

# UX-R4 — the lag the user marked with a Save State: FOUND — a 41-s storm of uplink silences with downlink damage beside it, then a 5-s two-way drop the client restarted from

**The user (2026-10-23):** "playing and just had severe lag I saved at the spot".

**Classification: FOUND, read-only.**
- **The play:** one session of *The Legend of Zelda: A Link to the Past* on snes9x, 04:54:42-05:07:11Z (00:54-01:07
  EDT). There were two saves and two loads.
- **The mark is the second save, 05:01:30.1Z.** Its pause was pressed at 05:01:21.4Z, at the end of a **41-s stretch,
  05:00:40.9-05:01:20Z, of 19 uplink silences ≥ 250 ms** (9.5 s silent in all, the longest 1,378 ms).
  - Beside the silences, the downlink was damaged: post-FEC loss 284 per minute against ~30 before; rendered 57.7 fps,
    with two intervals at 43-44; output gaps to 288 ms; audio concealment ×25.
  - The host was steady: 60 frames sent every second, the rung 7000 throughout, no recovery row.
  - **Shape: both directions, uplink-dominant, beginning 05:00:40.9Z.**
  - 24 hitch seconds in the mark's −60 s / +10 s; the longest run 5 s (05:00:40-44Z).
  - 285.7 frames (~4.8 s) of game ran with the player's input not arriving.
  - The first save (04:58:08.6Z) followed 138 s of clean play (0 hitch seconds). It is listed, not the mark.
- **Then a second event, 47 s after the resume:**
  - a **4.9-s uplink silence at 05:03:39.8Z**, the downlink failing in the client's last interval (23 frames per
    second, output age 166 ms);
  - **the client restarted its stream by itself** when the link came back: no session end, no report for that
    session;
  - the new session's audio underran ~170 times a second;
  - the user paused at 05:03:54Z and **loaded the save** at 05:04:01Z.
  - This is the "death" shape UX-R3 found (a 4-s two-way drop). 280 frames (~4.7 s) of game ran without the player.
- **In force:** APK `bf5114a2…` (the last install on file; tonight's reports carry its property-empty behaviour); the
  eight adopted lines only; every property empty.
  - **So there is no RSSI and no corrupted-frame counter for this session:** the link report and the loss guard were
    off.
- **By the built mechanisms' records** (§2): the hold at H 950 would have fired 3 times. The bidirectional rule would
  have asked for one rung down at 05:01:00Z. The stall signal at 400 would not have fired. The loss guard would have
  frozen instead of corrupting. None addresses an uplink storm of mostly sub-second silences. Nothing is changed or
  proposed.

Task: `handoffs/UX-R4_SAVED_AT_THE_LAG_TASK.md`, session A, read-only, from 14:48Z 2026-10-23. **The user was not
playing at the read.** No game, RetroArch or encoder was running; the session had ended at 05:07:11Z. So the live
files were read once, complete.

## 0. Preserved, and what was in force

- **The copies** (`ux_r4_2026-10-23/session/`, `copied_at.txt` 14:49Z) were made by UX-R2's preserve script, copied
  byte for byte (`ux_r2_preserve.py`, sha256 `c40b2408…`), run with span `2026-10-22T21:53` and out
  `ux_r4_2026-10-23`. Every byte went through the project redactor, plus the client-id / token masks.
  - The ladder log + its 3 archives, the frame-size log + its 3 archives;
  - heartbeat, recovery, control-gap, host-sampler and PulseAudio logs;
  - 7 client reports (BENCH-R3's last one and tonight's 6) and 8 audio-timing files;
  - the game logs (BENCH-R3's last PS1 one and tonight's SNES one), `save_state_probe.txt`,
    `retroarch_control_probe.txt`;
  - the encoder log's span blocks; the audit and HTTP span rows; the companion journal since 21:53Z (394 lines, 0
    warnings or errors).
  - `manifest.sha256`. Nothing was moved; the sources are untouched.
  - **Not copied:** the Opal (no sampler was running, and none is taken now).
- **In force during the play** (`in_force.json`):
  - **The APK.** The onn's APK was not re-read tonight (adb is `getprop`-only here). By the files it is
    **`bf5114a2…cf73`, CONFIRMED**:
    - the last install is BENCH-R3's (2026-10-22 20:19:52Z), read back at 22:45Z, and no install since;
    - tonight's reports carry the same client build (profiler 0.12.3) and no `loss_guard_*` or `stall_signal_*` key,
      which is its property-empty behaviour.
  - **The environ:** the companion has run unchanged since 2026-10-22 21:49:10Z (BENCH-R3's last teardown restart).
    - It reads **exactly the eight adopted lines**; the drop-in directory holds the eight conf files, no
      `e3_flag.conf`.
    - **No stack flag, no `PRIVYHUB_LINK_REPORT`, no `PRIVYHUB_LOSS_GUARD`.**
  - **The properties** (`getprop` now): `wifi_lock`, `stall_signal`, `link_report`, `loss_guard`, `opus_decode` all
    **empty**. They were cleared and read back empty at BENCH-R3's close.
  - **Therefore no RSSI / link rate and no corrupted-frame counter exist for this session.** No heartbeat or report
    tonight carries `link_*` or `frames_after_dropped_reference`.
  - **The fixture / core:** the user's own title, *The Legend of Zelda: A Link to the Past (USA)*, on snes9x (the same
    title as UX-R2's evening). The Opus audio path.
  - **The rung:** 7000 throughout. No ladder transition; the states moved between `REFERENCE` and `PRESSURE` only.
  - **The onn's uptime:** not carried by any report; not read.
- **The audit:** one `token_issued` (lan) at the session's setup, and the box-art media rows. Client ids and tokens are
  masked.

## 1. The mark, the ±60 s, the session

### 1.1 Every save and load (the game log + the save probe, UTC)

The game log has two "Saving state" lines to the slot file (lines 102 and 106) and two loads (lines 100 and 110). The
"Saving state RAM" lines are RetroArch's undo buffer before a load. Times come from `save_state_probe.txt`:

| # | pause pressed | request | probe row | resume | the client session it ended |
| --- | --- | --- | --- | --- | --- |
| load | 04:54:43.5 (at launch) | load-state 04:54:45.7 | `LOAD_STATE_SLOT 0` | 04:55:44.5 | — |
| **save 1** | 04:58:02.5 | **save-state 04:58:08.6** | `SAVE_STATE_SLOT 0`, file 102,303 B | 04:58:17.3 | 04:55:44-04:58:02 (138 s) |
| (pause) | 04:58:44.4 | — | — | 04:59:25.5 | 04:58:17-04:58:44 |
| **save 2 = the mark** | **05:01:21.4** | **save-state 05:01:30.1** | `SAVE_STATE_SLOT 0`, file 102,059 B | 05:02:52.7 (82 s later) | 04:59:25-05:01:21 (116 s) |
| (pause) | 05:03:44.9 | — | — | 05:03:50.8 | none: the client had restarted its stream (event 2) |
| **load** | 05:03:54.4 | **load-state 05:04:01.0** | `LOAD_STATE_SLOT 0` | 05:04:08.3 | 05:03:50-05:03:54 (4 s) |
| stop | 05:07:06.1 | — | close by SIGTERM, save flush OK | 05:07:11.4 | 05:04:08-05:07:06 |

- **The mark is save 2.** It is the only save preceded by any hitch: the 41-s stretch ends 1 s before its pause. It
  was followed by an 82-s pause, and its slot was loaded 2.5 min later, after event 2. The user's message carries no
  time, so this is the nearest by the data. The user can say otherwise.
- **The pause / save trips** show as UX-R2 §2 described: the client's `session_ended` the second the pause is
  pressed, the gap through the menu, and `session_started` at the resume. These are excluded from the hitch count by
  UX-R3's rule.

### 1.2 The per-second view, mark − 60 s → mark + 10 s

`seconds/window_save2_050130.tsv` (every column), `seconds/window_tables.md`, produced by `seconds/ux_r4_seconds.py`
with UX-R3's `evening` exec'd unedited (sha256 `e9b2b3f7…`).

**Resolutions as they are:**
- heartbeat ~2 s, credited to the second it ends in;
- control gaps per event ≥ 250 ms;
- frame sizes 1 s;
- ladder per report;
- the client report's output gaps: its top 16 for the session and its retained ≥ 50-ms events.

| UTC | hitch | rendered / s (interval) | post-FEC lost | FEC rec / unrec | control gaps ms | output gap ms | underruns / concealed | audio gap max ms | out age ms | tx frames / packets / max pk / ≥40 | ladder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 05:00:30-05:00:39 | — | 59.1-60.2 | 0-4 per interval | 0 / 0-1 | — | — | 0-1 / 0-2 | 57-68 | 2-34 | 60 / 681-984 / 31-44 / 0-4 | 7000, REFERENCE / PRESSURE |
| **05:00:40** | C | 59.8 | 0 | 0 / 0 | **366** | | 0 / 0 | 71 | 10 | 60 / 829 / 46 / 4 | 7000, REFERENCE |
| 05:00:41 | C | | | | 288 | | | | | 60 / 841 / 46 / 4 | |
| 05:00:42 | C | 58.7 | **11** | 1 / 0 | 260 | | 0 / 72 | 143 | 41 | 60 / 878 / 44 / 3 | 7000, REFERENCE |
| 05:00:43 | C | | | | 381 | | | | | 60 / 910 / 35 / 0 | |
| 05:00:44 | C | 56.7 | 12 | 2 / 2 | 538 | | 0 / 15 | 98 | 6 | 60 / 702 / 39 / 0 | 7000, PRESSURE |
| 05:00:46 | | 60.7 | 13 | 0 / 1 | | | 0 / 27 | 144 | 3 | 60 / 840 / 47 / 4 | 7000, PRESSURE |
| 05:00:48 | C | | | | 584 | | | | | 60 / 856 / 46 / 4 | |
| 05:00:49 | G | 57.1 | 4 | 0 / 1 | | 274 | 0 / 24 | 163 | 70 | 60 / 891 / 46 / 3 | 7000, PRESSURE |
| 05:00:50 | RC | **43.2** | 16 | 1 / 0 | 350 | | 0 / 130 | 128 | 81 | 60 / 749 / 46 / 3 | 7000, PRESSURE |
| 05:00:51 | C | | | | **1,378** | | | | | 60 / 839 / 47 / 4 | |
| 05:00:52 | G | | | | | 249 | | | | 60 / 832 / 47 / 4 | |
| 05:00:53 | | 51.2 | 18 | 1 / 3 | | | 0 / 126 | 207 | 7 | 60 / 832 / 46 / 3 | 7000, PRESSURE |
| 05:00:54 | L | 75.6 | 30 | 2 / 4 | | | 0 / 61 | 267 | 7 | 59 / 862 / 40 / 4 | 7000, REFERENCE |
| 05:00:56 | R | 49.7 | 6 | 7 / 1 | | | 0 / 50 | 142 | 5 | 60 / 843 / 43 / 3 | 7000, PRESSURE |
| 05:00:57 | G | | | | | 200 | | | | 60 / 848 / 36 / 0 | |
| 05:00:58 | C | | | | 502, 262, **922** | | | | | 60 / 848 / 36 / 0 | |
| 05:01:00 | | 59.6 | 4 | 1 / 2 | | | 2 / 105 | 236 | 7 | 60 / 859 / 36 / 0 | 7000, REFERENCE |
| 05:01:02 | | 63.6 | 13 | 0 / 1 | | | 0 / 22 | 176 | 0 | 61 / 796 / 46 / 4 | 7000, REFERENCE |
| 05:01:03 | C | | | | 270 | | | | | 60 / 835 / 44 / 2 | |
| 05:01:04 | | 60.2 | 3 | 0 / 1 | | | 0 / 41 | 195 | 12 | 60 / 887 / 40 / 2 | 7000, REFERENCE |
| 05:01:05 | C | | | | 446 | | | | | 59 / 847 / 43 / 2 | |
| 05:01:06 | CG | | | | 554 | 288 | | | | 61 / 775 / 43 / 3 | |
| 05:01:07 | CG | | | | **995** | 275 | | | | 60 / 853 / 43 / 4 | |
| 05:01:08 | R | **44.2** | 11 | 1 / 2 | | | 0 / 83 | 281 | 123 | 60 / 855 / 43 / 4 | 7000, REFERENCE |
| 05:01:09 | L | 58.1 (2.52 s) | **42** | 2 / 6 | | | 9 / 127 | **387** | 2 | 60 / 842 / 43 / 1 | |
| 05:01:11 | | 60.2 | 0 | 0 / 0 | | | 0 / 0 | 61 | 24 | 60 / 866 / 37 / 0 | |
| 05:01:13 | CG | 60.9 | 0 | 0 / 0 | 371 | 279 | 0 / 0 | 66 | 8 | 60 / 836 / 35 / 0 | |
| 05:01:16 | C | 56.2 | 1 | 2 / 0 | 250 | | 0 / 48 | 145 | 67 | 60 / 848 / 35 / 0 | 7000, REFERENCE |
| 05:01:17 | CG | 61.2 | 3 | 1 / 1 | 433 | 226 | 0 / 96 | 133 | 13 | 60 / 851 / 35 / 0 | |
| 05:01:19 | CG | 58.7 | 7 | 2 / 2 | 355 | 243 | 5 / 57 | 220 | 24 | 60 / 868 / 35 / 0 | |
| **05:01:21** | (pause) | | | | 87,460 (the menu) | | | | | 60 / 864 / 35 / 0 | `session_ended` |
| 05:01:24-05:01:40 | — | the menu: no stream (encoder stopped at 05:01:23.9; **the save at 05:01:30.1**) | | | | | | | | — | |

Seconds with nothing in any column are omitted from this table; the TSV has every second.

**The hitch seconds in the window, ranked** (score, then the longest control gap, the output gap, the loss):
05:01:07 CG (995 / 275), 05:01:06 CG (554 / 288), 05:01:17 CG (433 / 226), 05:01:13 CG (371 / 279), 05:01:19 CG
(355 / 243), 05:00:50 RC (350 / 43.2 fps), then the single-criterion seconds: 05:00:51 C 1,378; 05:00:58 C 922;
05:00:48 C 584; 05:00:44 C 538; 05:01:05 C 446; 05:00:43 C 381; 05:00:40 C 366; 05:00:41 C 288; 05:01:03 C 270;
05:00:42 C 260; 05:01:16 C 250; 05:00:49 G 274; 05:00:52 G 249; 05:00:57 G 200; 05:01:09 L 42; 05:00:54 L 30;
05:01:08 R 44.2; 05:00:56 R 49.7.
- **24 hitch seconds** (C 17, G 9, R 3, L 2); 0 of score ≥ 3.
- **The longest run before the mark: 5 s, 05:00:40-05:00:44Z.**
- The window's first 10 s (05:00:30-39) are clean.

**The stretch against the session around it** (`seconds/stretch_summary.txt`):

| span | s | hitch s | fps | post-FEC / min | unrec | uplink silences ≥ 250 (silent s, max ms) | output gap max | concealed | audio gap max | tx frames / s min | rung |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| session 1, 04:55:44-04:58:01 | 138 | 0 | 59.9 | 30.4 | 16 | 0 | — | 44 | 131 | 60 | 7000 |
| session 3 before, 04:59:25-05:00:39 | 75 | 1 | 59.9 | 31.2 | 10 | 0 | 203 | 35 | 203 | 60 | 7000 |
| **the stretch, 05:00:40-05:01:20** | 41 | **24** | **57.7** | **283.9** | 27 | **19 (9.5 s, 1,378)** | 288 | **1,084** | 387 | 59 | 7000 |
| session 4 before event 2, 05:02:53-05:03:37 | 45 | 0 | 59.8 | 24.0 | 5 | 0 | — | 32 | 86 | 60 | 7000 |
| **event 2, 05:03:38-05:03:50** | 13 | 3 | **42.5** | 13.8 | 1 | **1 (4.9 s)** | 282 | 921 | **1,579** | 11 (the restart) | 7000 |
| session 6, 05:04:08-05:07:05 | 178 | 3 | 59.9 | 25.6 | 16 | 3 (0.9 s, 362) | 267 | 189 | 247 | 60 | 7000 |

**The shape of the mark: both directions, uplink-dominant, beginning 05:00:40.855Z.**
- **The uplink:** the gap log (event resolution) shows the first silence at 05:00:40.855. Then 18 more in 39 s, the
  uplink silent 23 % of the stretch. The host's controller stream was not reaching it: what the player felt as lag on
  the controls.
- **The downlink:** loss began in the same 2-s heartbeat interval (05:00:40.5-42.3), 11 lost, and ran ~9× the session's
  rate. There were two intervals at 43-44 fps, output gaps 200-288 ms in 9 seconds, and audio concealment ×25.
- **Not host-side:** the encoder sent 59-61 frames every second with normal packet counts; no recovery row; no rung
  change.
- **It ended without a recovery:** the last silence was 05:01:19.4 (355 ms). The user paused at 05:01:21.1.

### 1.3 Event 2 (05:03:38-05:03:50Z), after the resume

| UTC | hitch | rendered / s | post-FEC | control gap ms | underruns / concealed | audio gap max | out age | tx frames / packets / max pk | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 05:03:35-37 | — | 59.7 | 0 | — | 0 / 0 | 52-68 | 1-53 | 60 / 727-852 / 32-43 | clean |
| **05:03:39** | RC | **23.0** (the interval 05:03:37.8-39.9) | 0 | **4,924** (05:03:39.794-05:03:44.718) | 44 / 88 | 146 | **166** | 60 / 792 / 35 | the old session's last heartbeat |
| 05:03:40-44 | — | — (no client data: the uplink was dark) | | | | | | 60 / 792-793 / 35 | the host kept sending |
| 05:03:45 | G | — | | | | | | **11** / 56 / 22 | a NEW client session (sequence 1, client clock started 05:03:44.73), output gap 282 ms |
| 05:03:46 | | | | | | | | 60 / 716 / 36 | `native-stream-start` at 05:03:46.67 (no `native-stream-stop`, no report for the old session) |
| 05:03:47 | R | 44.6 | 3 | | **377** / 457 | **1,579** | 12 | 60 / 800 / 36 | |
| 05:03:49-53 | | 59.2-60.1 | 0-3 | | **330-341 / 365-376** per interval | 53-76 | 5-32 | 60 / 792-800 | the picture fine, the audio underrunning ~170 / s |
| 05:03:54 | (pause) | | | 10,164 (the menu) | | | | 52 / 691 | `session_ended`; the load at 05:04:01.0 |
| 05:04:06-10 | | 56.0-60.6 | 0-7 | | 0 / 2-4 | 57-60 | 6-27 | 60 / 836-863 | session 6, the audio clean |

- **Shape: both directions, ~5 s.** The uplink was silent 4.9 s, and the client's picture was failing in its last
  interval (23 fps, output age 166 ms). The host was steady (60 frames per second throughout, the same packet count
  each second).
- **The client restarted its stream by itself** the moment the uplink returned. The session that began at 05:02:52Z
  ended with no `session_ended` and its report was lost.
- The new session's audio then underran ~170 times a second (1,392 in 9 s, against 0-13 in the other sessions) until
  the user paused and loaded the save.
- B2's reader: **280.4 frames of game ran without the player** in this silence (the stretch: 285.7).

### 1.4 The whole session (`seconds/counts.json`)

| client session | from-to (UTC) | s | hitch s | per 10 min | longest run s | silences ≥ 250 (max ms) | post-FEC / min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 04:55:44-04:58:02 | 138 | 0 | 0.0 | 0 | 0 | 30.4 |
| 2 | 04:58:17-04:58:44 | 27 | 0 | 0.0 | 0 | 0 | 0.0 |
| 3 | 04:59:25-05:01:21 | 116 | **25** | **129.3** | **5** | **15 (1,378)** | **120.5** |
| 4 | 05:02:52-05:03:50 (no session end) | 58 | 3 | 31.0 | 1 | 1 (4,924) | 21.7 |
| 5 | 05:03:50-05:03:54 | 4 | 0 | — | 0 | 0 | 45.0 |
| 6 | 05:04:08-05:07:06 | 178 | 3 | 10.1 | 2 | 3 (363) | 25.6 |
| **all** | 521 s of play | | **31** | **35.7** | 5 | 19 | 46.4 |

- **One event, not the end of a bad stretch:** the first 4 min of play were clean (1 hitch second, 0 silences).
  The storm began 75 s into session 3 and ended at the pause; event 2 came 47 s after the resume.
- Session 6 (the last 3 min) was clean again, at 10.1 hitch seconds per 10 min, the bench's clean range.
- For scale: BENCH-R3's clean SNES cell C read 19.9 hitch seconds and 22.4 silences per 10 min; BENCH-R2 b1 (blackout
  both ways) 23.4. Session 3 here: 129.3 hitch seconds and 94.7 silences per 10 min (B6's measure).
- **The clock:** the stretch began at 01:00:40 EDT and event 2 at 01:03:39 EDT.
  - UX-R3's "death" (a 4-s two-way drop) was at 04:54:55Z on 2026-10-20 (00:54 EDT).
  - UX-R2's single-loss step was at 04:52 / 04:54-04:56Z.
  - UX-R1's damaging bursts ran 05:04-05:21Z.
  - **The same quarter-hour after 00:50 EDT, on three different nights.** A coincidence in time, stated, not a cause.
- **The resemblance to BENCH-R3:** E-on's 21:42:20-21:43:25Z cluster of uplink silences had the same look (42 silences
  ≥ 250 ms in 65 s, the downlink mostly fine). There it coincided with the onn's tx link rate falling to 27-81 Mbps.
  Tonight there is no link report, so whether the tx rate fell cannot be said.

## 2. Against what we have built, by the record (nothing changed, nothing proposed)

For the seconds that scored, what each mechanism **would have done, by its record's measured behaviour**:

- **The hold at H 950** (B6; BENCH-R2 / R3: fires at 0.95-1.05 s of uplink silence; snes9x's hold-path rewind not
  confirmed, PAUSED after 7 / 7):
  - **It would have fired 3 times:** 05:00:51.3 (1,378 ms), 05:01:07.0 (995 ms, at the edge of its measured 0.95-1.05
    s) and 05:03:39.8 (4,924 ms). The other 17 silences in the stretch were < 950 ms and below it.
  - Cost: the picture frozen from ~0.95 s until the link returned (~0.4 s, ~0 s, ~3.9 s). The ~57 frames before each
    hold still ran unattended, with no rewind confirmed.
  - **It would have cut event 2's 280 unattended frames to ~57, and the stretch's 286 by only ~20-30.** Most of the
    stretch's silences were 250-950 ms.
- **The PS1 `state` path** (BENCH-R3 D: saved at 0.40 s, loaded and playing, net 24 frames; **measured on PS1 only,
  not on snes9x**):
  - By that record it would save at 0.40 s into every silence ≥ 400 ms (9 in the stretch, 1 in event 2: 10 saves of
    ~0.8 MB on SNES) and load at the hold's release (3 loads).
  - Net ~24 frames per hold.
  - Cost: a save in each of 10 silences; after each load, the client's gate stalls for 1.8-11.8 s (D); on snes9x,
    unmeasured.
- **The stall signal at 400** (B7 / B9; BENCH-R3 B: the pause 420-484 ms after the client's last frame; on a two-way
  blackout it arrives only at the return):
  - **The stretch: it would not have fired.** The client's output gaps were 200-288 ms, all under 400.
  - **Event 2:** the client's signal could not cross the dark uplink. The hold would already own the pause.
  - Cost here: none.
- **The loss guard** (BENCH-R3 E-on: holds every frame decoded from a lost reference, 0 timeouts, freezes ≤ 501 ms;
  +57 hitch seconds per 10 min on the bench):
  - The stretch had 194 post-FEC losses and 27 unrecoverable groups in 41 s. The guard would have replaced the
    corrupted frames that followed them with freezes of up to ~0.5 s each.
  - How many frames: unknown tonight, because the counter was off.
  - Cost: more freezes in a stretch already stuttering.
- **The bidirectional loss rule** (LAN-R2 `bidir`: two 5-report windows, each ≥ 4 unrecoverable groups AND ≥ 2 uplink
  silences ≥ 400 ms):
  - Replayed offline on tonight's heartbeats and gap log (`seconds/bidir_replay.py`; the condition only, not the
    controller), **it would have asked 9 times, first at 05:01:00Z** (windows 4 / 9 unrec, 2 / 3 silences), 20 s into
    the stretch. Event 2: not at all.
  - Cost: one rung down (7000 → 6000) for the rest of the session. A lower rate does not cure uplink silences: the
    rule's own record calls it a guard, not a fix.

**None of these addresses tonight's main symptom,** an uplink storm of mostly sub-second silences. The hold catches
only the ≥ 950-ms ones; the rest are under every trigger.

## 3. What this hands on (the user's say-so; nothing done here)

- **The 2.4-GHz finding is the user's hand change.**
  - BENCH-R3 measured the onn on 2.4 GHz channel 1 (802.11n, −68 dBm). O1 (2026-09-21) found it on the Opal's 5 GHz.
  - Moving it back, on the Opal or on the onn, is a setting only the user changes. Tonight's storm is the kind of event
    that would show whether it helps.
- **The link report on during play:** `PRIVYHUB_LINK_REPORT=1` as a **ninth adopted line**, plus
  `adb shell setprop debug.privyhub.link_report 1` after each onn boot.
  - It is diagnostics only: it adds the RSSI, tx / rx link rate and band to each heartbeat, and changes no behaviour
    (B3; BENCH-R3 carried it in every cell).
  - So the next lag the user marks carries the link beside it. Tonight's two events have none.

## 4. Files

- **`ux_r4_2026-10-23/`:**
  - `ux_r2_preserve.py` (UX-R2's, byte for byte), `copied_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`,
    `in_force.json`;
  - `session/` (the copies, `logs/games/…`, `logs/session_audit.span.jsonl`, `logs/server.span.log`,
    `journal_privyhub_companion.span.txt`);
  - `seconds/`:
    - `ux_r4_seconds.py`, `seconds_all.tsv`, the three `window_*.tsv`, `window_tables.md`, `ranked.txt`,
      `counts.json`, `stretch_summary.txt`;
    - `bidir_replay.py` / `.json` / `_console.txt`;
    - `unattended.json` (B2's reader, sha256 `d30a7e6b…`, on the copies);
  - `redact_check.txt`, `manifest.sha256`.
- **`logs/ux_r4_git_status.txt`.**
- **Not done:** no sudo, no nft; the Opal not read. adb was used only for `getprop` of the five properties. No restart,
  no power-cycle, no run.
- **Not written:** no address or identifier.
- **Nothing** fetched, deleted, moved, adopted or committed. No change outside `docs/`, `logs/` and the evidence
  directory.
