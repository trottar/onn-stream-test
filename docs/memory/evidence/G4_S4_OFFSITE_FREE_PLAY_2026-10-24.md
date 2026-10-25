---
memory_schema: 1
as_of: 2026-10-25
baseline_commit: 13ccff5 (the user's commit of the launch and the close)
---

# G4-S4 — off-site free play at a friend's house (Part 2, the record)

**Classification: MEASURED.** There were 100.1 min of play in 13 client sessions over the tailnet at a friend's house
(5-GHz Wi-Fi there, 5240 MHz in every heartbeat). **71.1 min were under the four WAN lines** (20:02:56-21:21:02Z).
The rest was on the ten adopted lines alone.
- **The link-recovery stack's first WAN exposure: 0 false holds.** 2 holds fired, both at the user's Home presses
  (real drops by the rule).
- **0 uplink silences ≥ 250 ms in play.** The only 3 control gaps were the user's own exits.
- **Hitch seconds: 2.2 / 10 min over the whole play, 1.8 under the four lines.** That is below the 5-GHz LAN's 3.9-9.9
  (CL-B12 cell 1).
- **The path was direct throughout the sampled play.** It read relayed only around idle spans.
- The ladder climbed 4000 → 7000 in every long session, with no step-down and no clamp.
- **The user: playable**, "pretty damn good … maybe better than lan".

Measurement only. Nothing adopted; nothing committed.

Task: `handoffs/G4-S4_OFFSITE_FREE_PLAY_TASK.md` Part 2, session A; the prompt is `_cowork_prompt_offsite.txt`. The
launch, the misread close and the relaunch are in `G4_S4_LAUNCH_2026-10-24.md` §1-8. Every number here comes from
`g4_s4_2026-10-24/`:
- `copies/` (`g4_s4_assemble.py`);
- `samples/` (the driver's);
- `g4_s4_read.py` → `sessions.tsv`, `bins_10min.tsv`, `stack_rows.tsv`, `seconds.tsv`, `counts.json`,
  `read_console.txt`.

## 1. What ran, and the state

- **The four lines:**
  - `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_REMOTE_RUNG_CAP=7000`, `PRIVYHUB_WAN_TELEMETRY=1`;
  - fourteen lines read back at 20:02:56Z (attempt 2);
  - removed at 21:21:02Z on the user's "Stop": `flags_absent` true, ten lines (`g4_s4_state.json`).
- **Attempt 1:** the drop-in was in from 19:37:07Z (fourteen, ok). I closed it at 19:42:29Z on a misreading (§10), with
  no play under it.
- **The record's state** (`check_record.json`, 2026-10-25 17:4xZ):
  - **`--check` ok on ten**: adb true after `adb connect` from the host, APK CONFIRMED;
  - no `e3_flag.conf`, no game;
  - **the onn on 5 GHz at home: 5180 MHz** (`band_record.json`; the frequency only).
  - The onn's first LAN setup was at 17:42:40Z (`routing_evidence: lan`).
- **The span read:** 2026-10-24T19:15Z to 2026-10-25T17:40Z, everything before the onn came home.
  - `copies/assemble_check.json`: every row of the driver's raw copies (19:27:32-21:21:12Z) is in the assembled copy (0
    missing).
  - The assembled copy has 248 more heartbeat rows in that span: 19:42-19:56Z, when no driver ran.

## 2. The play: 13 client sessions (`sessions.tsv`; heartbeat-window figures)

| # | UTC | play min | core | lines | path (sampled) | rung(s) kbit/s | rendered | post-FEC /min | resyncs | hitch s | silences | holds |
| --- | --- | ---: | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 19:24:35-19:25:23 | 0.81 | Beetle PSX | 10 | not sampled | 7000 | 60.04 | 53.4 | 0 | 0 | 0 | 0 |
| 2 | 19:25:34-19:27:01 | 1.44 | Beetle PSX | 10 | not sampled | 7000 | 59.90 | 44.4 | 0 | 0 | 0 | 0 |
| 3 | 19:27:36-19:28:11 | 0.57 | Snes9x | 10 | direct | 7000 | 59.75 | 10.5 | 0 | 0 | 0 | 0 |
| 4 | 19:29:00-19:35:14 | 6.23 | Snes9x | 10 | direct | 7000 | 59.75 | 33.7 | 0 | 0 | 0 | 0 |
| 5 | 19:35:42-19:36:29 | 0.80 | Beetle PSX | 10 | direct | 7000 | 59.77 | 17.4 | 0 | 0 | 0 | 0 |
| 6 | 19:47:22-19:54:33 | 7.18 | Beetle PSX | 10 | **not sampled** (no driver) | 7000 | 59.83 | 4.5 | 0 | 3 | 0 | 0 |
| 7 | 19:55:57-20:01:12 | 5.23 | Beetle PSX | 10 | direct | 7000 | 59.80 | 70.0 | 0 | 3 | 0 | 0 |
| 8 | 20:04:49-20:13:46 | 8.94 | Beetle PSX | **14** | direct | 4000→5000→5500 | 59.89 | 23.0 | 4 | 4 | 0 | 0 |
| 9 | 20:14:17-20:17:03 | 2.78 | Snes9x | **14** | direct | 4000 | 59.93 | 6.8 | 0 | 0 | 0 | 0 |
| 10 | 20:21:14-21:02:46 | **41.40** | Beetle PSX | **14** | direct (relayed ≤ 38 s at its start, §5) | 4000→…→**7000** | 59.93 | 6.8 | 10 | 1 | 0 | 1 (Home) |
| 11 | 21:02:50-21:04:46 | 1.78 | Beetle PSX | **14** | direct | 4000 | 59.50 | 1.1 | 2 | 0 | 0 | 1 (Home) |
| 12 | 21:04:51-21:21:03 | 16.22 | Beetle PSX | **14** | direct | 4000→…→**7000** | 59.86 | 2.8 | 8 | 5 | 0 | 0 |
| 13 | 01:20:57-01:27:45 (10-25) | 6.75 | Snes9x | 10 | **not sampled** (no driver) | 7000 | 59.92 | 5.2 | 0 | 2 | 0 | 0 |

- **The core is from the client report's capture line:** Beetle PSX = PS1, Snes9x = SNES.
- **Session 12's report is the post-stop tail.** It was sent at 21:42:08Z, 21 min after the closing restart. The
  client sat "reconnecting" with no audio until then: 152,647 underruns, a 1,265-s max output gap. As in G4-S3 §6,
  that tail is excluded, and the heartbeat window is the figure.
- **The user's actions** (the companion's request log; titles not written):
  - 9 launches and 9 stops;
  - **4 saves and 6 state loads.** Two loads were at a launch (19:24:28Z, 19:47:15Z) and two came from the tile at a
    relaunch (20:14:13Z, 20:17:12Z). One was the recovery Resume (`recovery-resume` 20:04:44Z, after the drop-in's
    restart).
  - **Pauses:** 4 `input_hold_skipped_paused` rows, each at a session's end while paused.
  - The cues Pause/Resume and Save/Load were met.
- **VOD (the user's first test, "the simplest") was not measured:**
  - the host-side VOD source started at 19:20:36Z and 19:22:43Z, before the driver (19:27:32Z);
  - once more at 20:01:30Z: the driver's range-port count read 1 connection at 20:01:52Z, 0 a minute later;
  - three starts at 06:20-06:24Z on the 25th, over the overlay, no driver.
  - No VOD data rate exists: the tailnet was sampled only 19:27-19:42Z and 19:56-21:21Z.
  - 198 media checks were logged in the span. VOD titles are not written.

## 3. The ladder (the four lines): the rung history and the clamps

- **Start rung `floor` = 4000, `path_class` remote**, in all 5 client sessions under the four lines (`start_rung` rows
  20:04:46Z … 21:04:5xZ; active list 4000/5000/5500/6000/7000).
- **10 transitions, all `increase_increase`, one rung every ~3 min 07 s, no decrease:**
  - 20:07:48 4000→5000, 20:10:55 →5500 (session 8, which ended at 5500);
  - 20:24:13 →5000, 20:27:19 →5500, 20:30:26 →6000, **20:33:33 →7000** (session 10, held at 7000 for its last
    29 min);
  - 21:07:51 →5000, 21:10:58 →5500, 21:14:05 →6000, **21:17:11 →7000** (session 12).
- **Clamps: 0 `remote_cap` refusals.** The cap 7000 is the top of the list.
- **Cost of the floor start:** each new client session starts at 4000. The Home at 21:02:36Z took the stream from 7000
  to 4000, and it was back at 7000 at 21:17:11Z: ~14.5 min below 7000, at 5.3-7.7 Mbit/s instead of 8.85.
- **On the ten lines** (sessions 1-7, 13), the stream ran at the adopted profile's 7000 from the start.

## 4. The wire and the data (`samples/fast_10s.jsonl`: the hub's tailnet `tx_bytes` every 10 s, decimal)

| | G4-S1 run 1 (7000, PCM, hotspot) | G4-S3 (4000, Opus, hotspot) | **G4-S4 (Opus, friend's broadband)** |
| --- | --- | --- | --- |
| tailnet tx at 4000 (kbit/s, median) | — | 5,299 | **5,322** (84 samples) |
| at 5000 / 5500 / 6000 | — | — | **6,532 / 7,115 / 7,678** (56 / 55 / 37) |
| tailnet tx at 7000 (kbit/s, median) | 11,420 (KiB-based; 11,698 decimal) | — | **8,849** (271) |
| GB per hour at 7000 / at 4000 | ~5.1-5.3 / — | — / ~2.4 | **~4.0 / ~2.4** |

- **The four lines' span** (20:03:02-21:21:00Z, 1.30 h, 71.1 min of it play): **4,041 MB tx, 82.5 MB rx, ~3.1 GB per
  hour of span.**
- **Attempt 1's sampled span** (19:27-19:42Z, ten lines at 7000): 534.5 MB.
- **The whole sampled tx** is ~4.9 GB, 19:27-19:42Z and 19:56-21:21Z. Not sampled: sessions 1-2 and 6, the evening
  session 13, the VOD.
- **Opus at 7000 over the WAN:** 8,849 against G4-S1's 11,698 with PCM, **−2,849 kbit/s**. The LAN's Opus saving was
  −2,916 (CL-B6).
- **Video payload alone** (`native_frame_sizes`, the whole play): ~2,336 MB per play hour.

## 5. The link side

- **Rendered 59.88 fps over the whole play** (59.92 under the four lines). Every session read 59.50-60.04.
- **Post-FEC loss 13.2 / min** over the whole play:
  - **7.8 / min under the four lines**, 33.0 on the afternoon's ten-line sessions at 7000, 5.2 in the evening session;
  - the 5-GHz LAN: 28.8 (CL-B12 cell 1).
- **The `wan` block at the end of the four lines** (481 reports, 96 windows):
  - post-FEC 2.3 / min, pre-FEC 13.3 / min;
  - FEC recovered 176, unrecoverable groups 14;
  - goodput 5,601 kbit/s (mean, mixed rungs);
  - jitter p50 / p95 0.76 / 1.50 ms;
  - windows: **clean 78, lossy 14, starved 1, path-changed 4**; class at the end `path-changed`.
- **RTT** (the client's control echo, the `wan` block's running percentiles): **p50 58-68 ms, p95 331-342 ms** after
  the first session. The first sample (20:04:52Z) read p95 768. G4-S3 on the hotspot: median 123.
- **Resyncs:** 24, all under the four lines (sessions 8, 10, 11, 12). Sessions 8, 10, 11 had 2, 4, 1 stream
  discontinuities in their reports.
- **The overlay path** (`samples/slow_60s.jsonl`, every 60 s, while the driver ran):
  - 19:27 direct; **19:37:33 relayed; 19:38:33-19:45:50 no-peer (the onn off the tailnet; 1 device online at
    19:45:50Z)**;
  - 19:56:52 direct; 20:03:52 relayed (the drop-in's restart, idle); 20:04:52 direct;
  - **20:18:52-20:20:52 relayed (idle between sessions 9 and 10)**; 20:21:52 direct to the end.
  - **Every relayed reading was in an idle span**, or within the first ≤ 38 s of session 10. That session started at
    20:21:14Z; the last relayed reading was at 20:20:52Z and the next, direct, at 20:21:52Z.
  - **Read:** the path drops to relayed when the stream is idle and returns to direct with traffic.
  - **Not sampled:** session 6 (19:47-19:54Z) and the evening session 13 (01:21-01:28Z).
- **The onn's Wi-Fi at the friend's:** 5240 MHz in every heartbeat; RSSI median −56 dBm.

## 6. The stack's rows (`stack_rows.tsv`): every hold tagged

| at | event | tag | cause | gap | cost to the player |
| --- | --- | --- | --- | ---: | --- |
| 21:02:36.687 | `state_saved` (silence, +402.7 ms) | — | — | — | — |
| 21:02:37.323 | **`desync_pause`** (`input_hold`, age 954 ms) | **REAL DROP** | the user's Home (the gap contains a `session_ended`) | 9,811 ms | the game ran **~1.06 s** without input before the pause; held 4,313 ms at the handover; away 9.8 s; **no rewind** (the return was a new client session); the rung reset to 4000 |
| 21:02:41.535 | `input_hold_handover` (`controller_silence`, 5,267 ms) | | | | |
| 21:02:46.079 | `hold_return_armed` (`input_release`) → `session_ended` → new session 21:02:50 | | | | |
| 21:04:34.357 | `state_saved` (silence, +403.0 ms) | — | — | — | — |
| 21:04:34.991 | **`desync_pause`** (`input_hold`, age 955 ms) | **REAL DROP** | the user's Home | 12,517 ms | the same: ~1.06 s unattended; held 4,311 ms; away 12.5 s; no rewind; the rung reset |
| 21:04:39.202 | `input_hold_handover` | | | | |
| 21:04:46.452 | `hold_return_armed` → `session_ended` → new session 21:04:51 | | | | |

- **False holds: 0 in 100.1 min (0 / 10 min).** The link was never silent ≥ 250 ms in play, so nothing reached H 950
  or the 400-ms stall.
  - Under the four lines that is 71.1 min.
  - A zero over ~100 min bounds the rate at **< ~0.3 / 10 min (95 %)**, on this one direct path and evening.
- **The other rows are the ends' bookkeeping:**
  - `state_save_skipped` ×10 (`state_ended` ×7, `client_bye` ×3) and `input_hold_skipped_paused` ×4, at session ends;
  - **0 saves outside the two holds**; no stall pause, no `rewind_*`, no `resumed` row.
- **The user on the Home behaviour, verbatim:**
  - "I just hit home and  it didn't pause";
  - after the explanation: "No seems about right, I'm use to at home where the pause screen shows up".
  - The game came back where it was left. There is no pause screen on the return: the hold releases and the new
    session resumes.
  - **Likely the stack's design since G-A4 (adopted the same day), not the WAN.** Before it, the older recovery path
    showed the pause screen and waited for the user. Not verified on the LAN since G-A4 (§10).

## 7. Hitch seconds and silences (UX-R3 §1's definition, unchanged; `seconds.tsv`, `bins_10min.tsv`)

| span | play min | hitch s | **per 10 min** | R / C / G / L | silences ≥ 250 ms / 10 min |
| --- | ---: | ---: | ---: | --- | ---: |
| **whole play** | 100.1 | 22 | **2.2** | 8 / 0 / 7 / 7 | **0** |
| under the four lines | 71.1 | 13 | **1.8** | 2 / 0 / 7 / 4 | **0** |
| ten lines, afternoon (sessions 1-7) | 22.3 | 7 | 3.1 | 4 / 0 / 0 / 3 | 0 |
| ten lines, evening (session 13) | 6.7 | 2 | 3.0 | 2 / 0 / 0 / 0 | 0 |
| *5-GHz LAN (CL-B12 cell 1, for comparison)* | | | *3.9-9.9* | | *0* |

- **The 22 seconds:**
  - 19:48:58 / :00 / :02 (R);
  - 19:56:23 / :33 / :39 (L);
  - 20:05:14 / :18 / :38 (L);
  - 20:10:55 (G, at a rung step);
  - 20:35:21 (L);
  - 21:02:48 (R) and 21:04:47 / :49 (G, R): **the Home returns**;
  - 21:05:50, 21:06:33, 21:07:52, 21:08:56, 21:14:05 (G; 21:07:52 and 21:14:05 at rung steps);
  - 21:21:04 (R): **the closing restart**;
  - 01:23:24 / :26 (R).
- **Four of the 22 are the user's own actions or the close:** two Home returns (3 s) and the restart (1 s). Without
  them it is 18 hitch seconds, **1.8 / 10 min**.
- **The per-10-min bins** (`bins_10min.tsv`):
  - the worst bin was 21:00-21:10Z, at 7.4 / 10 min, holding both Home presses and their returns;
  - every bin from 20:10Z to 20:59Z read 0-1.5;
  - post-FEC per bin was 1.6-44.8 / min. The high bins (19:20-20:09Z) were the ten-line sessions starting at 7000.
- **Excluded by rule:** 647 heartbeat intervals (21.9 min) outside any client session. These are the client
  "reconnecting" after a stream ended, chiefly 21:21-21:42Z after the closing restart. Their 152,365 underruns are not
  play.

## 8. Audio and spikes

| span | play min | underruns (heartbeat) | per min |
| --- | ---: | ---: | ---: |
| whole play | 100.1 | 1,077 | 10.8 |
| under the four lines | 71.1 | 571 | 8.0 |
| ten lines, afternoon | 22.3 | 450 | 20.2 |
| evening (session 13) | 6.7 | 56 | 8.4 |

- **Underruns are above G4-S3's 3.4 / min** (34 in its 10-min window) and well above CL-B12 cell 1's.
  - The onn ran all afternoon (power-cycled at hand step 0, ~19:1xZ).
  - Uptime was not read (adb off-LAN).
- **Audio packets lost** (the client reports' `audio.lost_packets`): **38 / 30 / 11** in sessions 7 / 8 / 10, 0 in
  the other ten. The ten-line session 7 was at 7000; the four-line session 8 started at 4000 and session 10 reached
  7000. G4-S3: 0. **The watch item stays open.**
- **Decoder spikes ≥ 20 / ≥ 50 ms per min, per client report:**
  - session 10 (41 min, mostly at 7000): **85.1 / 2.1**; sessions 8-9 and 11 (4000-5500): 53-73 / 3.2-12.8;
  - the short ten-line sessions at 7000: 126-608 / 6-51, dominated by their start-ups (0.6-7 min each);
  - **the LAN at 7000 with Opus: 105-163** (CL-B5 / CL-B6 / G-A2).
- **Max output gap per report:** 86-232 ms. Session 12's 1,265 s is the post-stop tail.

## 9. The user's words (verbatim; nothing perceptual is a gate; `user_report.tsv` and the launch record §7-8)

> "Say stop" / "First test is with vod since this is the simplest" (with the launch line)
>
> "At home in onn now" (the onn on its home screen; misread, §10)
>
> "What are you talking about were specifically doing off site testing?"
>
> "I've been playing for like 45 minutes"
>
> "At home" · "Home screen" · "Game is running"
>
> **"Performance has been pretty damn good. I'm shocked how well it's performed, like maybe better than lan. Hard to
> tell. I'm going to keep a game running for further diagnostics on your end"**
>
> "Do you think it's better to let running? How useful is the data?"
>
> "I just hit home and  it didn't pause" · "Tried another" · "No seems about right, I'm use to at home where the pause
> screen shows up"
>
> "Stop"
>
> "I'm at my friend's all night. We are leaving to go out then playing when we get back later tonight. So testing can
> continue while we're gone, if it doesn't seem necessary then we can just diagnose the play later tonight"

**Playable: yes, by the user's word.** The numbers agree: 1.8 hitch s / 10 min and 0 silences under the four lines,
against the LAN's 3.9-9.9.

## 10. What failed, and where

1. **I closed attempt 1 on a misreading.**
   - "At home in onn now" meant the onn's home screen, the cue I had just given. I read it as the user being back
     home, and touched STOP at 19:42:29Z.
   - Cost: sessions 6 and 7 (19:47-20:01Z, 12.4 min) were played on the ten lines. Session 6 was not sampled at all
     (no driver, 19:42-19:56Z).
   - **I also told the user "19:37-19:55Z: nothing" from the driver's samples.** The hub's logs hold session 6
     (19:47:22-19:54:33Z). The samples stopped with the driver, and the onn was off the tailnet only ~19:38-19:46Z.
     Corrected to the user at the record's start.
   - Saved as a feedback memory: only the exact stage words change the stage.
2. **The idle wait kept the four lines out of 44 min of the afternoon** (19:24-20:01Z).
   - The user went from game to game, so the restart waited.
   - The pre-registered rule (no restart over a game) held, at the cost of the ten-line sessions 1-7.
3. **The onn dropped off the tailnet for ~8 min** (no-peer 19:38:33-19:45:50Z; it set up again at 19:46:18Z).
   - It began ~1 min after the onn went idle, and ~26 s after attempt 1's companion restart (19:37:07Z).
   - The second restart (20:02:56Z) was followed only by a brief relayed reading, and no drop.
   - The cause is not in the hub's files (the onn's side unread off-LAN). **Open.**
4. **The evening session (01:20:57-01:27:45Z) and the VOD at 06:20Z ran with no driver.**
   - The user did not type "launch" again, and I had recommended relaunching only then.
   - So no four lines, no path and no tailnet sampling. Only the companion's own logs.
5. **VOD, the user's first test, has no measurement.** It started before the driver, and the driver samples games
   only.
6. **Home does not show the pause screen any more.**
   - The hold releases into the new client session and the game resumes, with no rewind. The game ran ~1.06 s without
     input before each pause.
   - The ladder restarts at the floor at the new session (~14.5 min back to 7000).
   - Both are design questions for B, not link faults. Whether G-A4 changed the LAN's Home behaviour too is to be read
     on the LAN (the user's "at home the pause screen shows up" predates G-A4).
7. **The launch's own disclosures** (G4_S4_LAUNCH §1, §3, §5):
   - `session_status_before.json` first held client ids; it was rewritten within the minute;
   - the invocation ID was shown once in my console;
   - a `__pycache__/` was left by my dry import.
8. **`--check` at the record needed `adb connect`** (the known item; G4-S1 "also seen").
   - I did it from the host, with the onn's LAN address taken from the companion's request log in a pipe, never
     printed or stored.
   - adb was then used for `--check` and one `dumpsys wifi` frequency read only.

## 11. State at the end

- The unit `privyhub-g4-s4` is collected (inactive since 21:21:12Z).
- **Ten adopted lines; no `e3_flag.conf`; no game; `--check` ok; APK CONFIRMED; the onn at home on 5 GHz (5180 MHz).**
- Nothing adopted; nothing committed (`logs/g4_s4_git_status.txt`).

## 12. Files

`g4_s4_2026-10-24/`:
- the launch's files (the launch record §5);
- `g4_s4_assemble.py`, `copies/` (the merged logs, `assemble_check.json`);
- `g4_s4_read.py`, `sessions.tsv`, `bins_10min.tsv`, `stack_rows.tsv`, `seconds.tsv`, `counts.json`, `read_console.txt`;
- `check_record.json`, `band_record.json`, `user_report.tsv`;
- `redact_check.txt`, `manifest.sha256`.

The driver's raw copies stay at `~/privyhub_g4_s4/logs/`, outside the repo.

No sudo, no nft, the Opal untouched, adb for `--check` and the band read only, no address or identifier. Nothing
fetched, nothing deleted, nothing adopted, nothing committed.
