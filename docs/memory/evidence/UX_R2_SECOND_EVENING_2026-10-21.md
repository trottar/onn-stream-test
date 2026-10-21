---
memory_schema: 1
as_of: 2026-10-21
status: UX-R2 READ (session A, read-only) — the second evening (2026-10-21 04:42-05:26Z, 00:42-01:26 EDT, 43 min, four games, SNES first) read mostly CLEAN. No pause, no encoder restart, no burst like UX-R1's. After the first 5 minutes, post-FEC loss was 37.5/min (UX-R1: 173), underruns 3.9/min (39.4), concealed 120/min (328). The single-loss (FEC-recovered) step came again, at 04:52Z, against UX-R1's 04:54-04:56Z. That is the same wall-clock time at a different play-minute (10 against 35), and SNES was on screen both times. UX-R1's damaging stretch (play-minutes 45-64, 05:04-05:21Z) did not recur at the same clock; the second evening ended at play-minute 44, so that play-minute range is untested. SNES played first was fine. H5 answered: a pause ending the client session is NOT new; 2026-09-20's play did the same. The onn was cold-booted again ~15:01Z today; its uptime at the first frame is unknown (14 h 20 m if not cycled). User's report: no report yet. Nothing changed, restarted or adopted; nothing committed
---

# UX-R2 — the second evening: the read

Task: `handoffs/UX-R2_SECOND_EVENING_READ_TASK.md`. Files: `ux_r2_2026-10-21/`. Read beside
`UX_R1_EXTENDED_SESSION_REGRESSION_2026-10-20.md`.

**The user's words (2026-10-21):** "Ran a few games last night." **How it felt: no report yet.**

## The answer, plainly

- **The second evening was mostly clean.**
  - The first 5 minutes against the rest held level: post-FEC loss 26.6 → 37.5 / min, underruns 5.8 → 3.9 / min.
  - No `client_output_silence`, no encoder restart, no resync, and no acted ladder step.
  - Max output gap 534 ms.
  - The one rough stretch is Soul Reaver's first ~2 minutes (05:12Z): loss 141, 65 underruns, 876 concealed in one
    minute. Then it settled.
- **One feature repeated: the single-loss step, by the clock.**
  - FEC-recovered losses rose from ~5 to 20-38 / min at **04:52Z**. On UX-R1 the same step came at **04:54-04:56Z**.
  - That is the same wall-clock time (00:52-00:56 EDT) at different play-minutes (10 against 35). SNES was on screen
    both times.
  - On the second evening the level fell back to 10-15 / min once PS1 took over (05:11Z).
  - Two evenings cannot split the clock from SNES content.
- **UX-R1's damage did not repeat at the same clock.** UX-R1's bursts came at play-minutes 45-64, 05:04-05:21Z. The
  second evening covered 05:04-05:26Z cleanly, but by play-minute it ended at 44.
  - **Not the clock** for the bursts.
  - **Time-in-session past ~45 minutes is untested** by this evening.
- **H5 answered: not new.** On 2026-09-20 (PCM, before October) every pause ended the client session (pause image
  `saved`), and Resume started a new one 6-45 s later. It is the same behaviour now.
  - It is a pause, not a restart cost: the host pauses RetroArch, the client stops the stream and shows the menu, and
    the gap is the time the user spends in the menu.
- **The instrumented evening stays the next test**, with what this evening adds (§3).

## 0. Preserved, and the state now

**Copies** (`session/`, `ux_r2_preserve.py`: UX-R1's preserve script, parameterised by span and directory; copied at
`session/copied_at.txt`). Copies only, redacted and masked as in UX-R1.
- Every ladder log, with the archive (no rotation since UX-R1).
- The frame-size log and its archive.
- The heartbeat, recovery, control-gap, host-sampler and audio-encoder logs.
- The 6 decoder reports, 6 audio-timing records and 4 game logs.
- The encoder log's blocks in the span.
- The audit rows (1 `token_issued` at 04:41:59Z, `routing_evidence` **lan**) and the HTTP rows.
- The journal from 18:31Z 10-20.

**Host, now** (`state_now/host_state_now.txt`, 15:32Z):
- Up 28 d; load 0.20; 12.4 GB available; swap 679 MB used (system-wide); disk 34 %.
- The companion has run since 2026-10-19 17:47:59Z: RSS 86 MB (HWM 87), 2 threads, 5 fds, VmSwap 0. The cgroup holds
  316.5 MB, with a peak of 521.6 MB (page cache included; RSS is the process figure).
- No RetroArch, encoder or grab. Journal since 18:31Z: 1,352 lines, **0 warning or worse**, 0 EPG / grab lines.

**The onn, now** (`state_now/onn_*`). adb was connected by hand on the pinned port; the endpoint was never printed.
- **Uptime 31 min: cold-booted again ~15:01Z today.** Boot reason `cold`.
  - The boot-reason history holds reasons only, no times.
  - `dumpsys dropbox` is empty.
  - `boot_count` reads 77, but UX-R1 did not read it, so the boots in between cannot be counted.
- PrivyHub is not running; the screensaver is up.
- Busy 24 %; thermal status 0; cpu-thermal 55 °C (screensaver load).
- MemAvailable 796 MB; swap 353 MB used.
- **`/proc/net/udp6`: 7 sockets, drops 0 on every row.** This is post hoc: PrivyHub's socket is gone with the app, so
  it says nothing about last night.
- `getprop debug.privyhub.opus_decode` is empty.
- `cl_b7_onn_threads.py state_now`: "PrivyHub not running".

**Also read:**
- **`--check`:** ok on eight, adb true, APK **CONFIRMED** (`93d29b4a…`), no RetroArch / encoder.
- HEAD `7f2f990` (UX-R1 committed).
- `git status`: `state_now/git_status.txt` and `logs/ux_r2_git_status.txt`.

## 1. The timeline, and the pairing with UX-R1

`ux_r2_timeline.py` is UX-R1's script parameterised by the span; "first 5 minutes" is measured from the first frame.
Its output is `timeline.txt` / `timeline.json`. The pairing is in `ux_r2_pair.py` → `pair.txt` / `pair.json`.

**The games** (the client opened at 04:41:59Z; LAN). **The order was the reverse of UX-R1's: SNES first, then PS1.**

| start (UTC) | system / core | title | client sessions | minutes | "Loading state" lines |
| --- | --- | --- | ---: | ---: | ---: |
| 04:42:26 | SNES / snes9x | Zelda: A Link to the Past | 2 | 27.4 | 2 |
| 05:10:38 | PS1 / Beetle PSX HW | Disney's The Emperor's New Groove | 1 | 1.1 | 1 |
| 05:12:22 | PS1 / Beetle PSX HW | Legacy of Kain: Soul Reaver | 1 | 2.2 | 1 |
| 05:17:02 | PS1 / Beetle PSX HW | Castlevania: Symphony of the Night | 2 | 8.9 | 3 |

- **Recovery rows: none** besides session start / end.
- **The ladder:** `live`, 7000 throughout; 0 acted rows.
- **Grabs:** none (0 `epg/refresh`, 0 grabber lines).
- **`wan` class:** not adopted.
- **Mid-play pauses: 2.** Each ended and restarted the client session:
  - Zelda, 05:08:58 → 05:09:21 (22.5 s);
  - Symphony of the Night, 05:22:54 → 05:23:06 (11.7 s; the probe shows pause → save-state slot 1 → resume).
- The other session ends are title changes. Each game's first "Loading state" is its launch resume.

**The first 5 minutes against the rest, with UX-R1 beside** (heartbeat, per minute):

| | R2 first 5 (04:42-04:46) | R2 after (04:47-05:26) | R1 first 5 (04:19-04:23) | R1 after (04:24-05:22) |
| --- | ---: | ---: | ---: | ---: |
| rendered fps | 59.82 | 59.66 | 59.88 | 59.24 |
| post-FEC loss / min | 26.6 | **37.5** | 26.1 | **173.2** |
| FEC recovered / min | 4.5 | 21.0 | 5.7 | 23.2 |
| FEC unrecoverable / min | 3.51 | 7.83 | 5.45 | 9.67 |
| resyncs | 0 | 0 | 0 | 17 |
| underruns / min | 5.77 | **3.90** | 3.86 | **39.42** |
| concealed underruns / min | 87.9 (550 in the start-up minute) | **119.9** | 37.3 | **327.8** |
| prolonged starvation / min | 8.8 | 12.1 | 4.5 | 27.2 |
| audio lost (net) / min | 0 | 0.55 | 0 | 1.18 |
| audio arrival gap max | 222 ms | 406 ms | 142 ms | 1,434 ms |
| host ctrl gaps > 1 s | 0 | 2 (both pauses) | 1 | 24 (loads + bursts) |
| silence pauses / encoder restarts | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 1 |
| max output gap (reports) | — | 534 ms | 259 ms | 4,923 ms |
| frames ≥ 40 packets / min | 218 | 213 | 116 | 232 |
| frames ≥ 80 packets | 0 | 0 | 0 | 0 |
| wire kbit/s | 7,012 | 6,751 | 6,267 | 6,700 |

**Per report:**
- Opus decode average 3.2-3.4 ms throughout. Spikes ≥ 50 ms / min: 2.3 (Zelda) up to 30.6 (Soul Reaver's 2 min).
- **Decode queue depth max 64 / wait 278 ms in Zelda's 26-minute session, with 5.0 underruns / min.** Depth 64 also
  appeared on UX-R1's bad SNES sessions. **The depth by itself is not the damage.**
- Thermal status 0 in every report.

**By play-minute, both evenings** (5-minute blocks from each first frame; `pair.txt`):

| play-min | R1 UTC / system | R1 loss / FEC rec / concealed / underruns / fps | R2 UTC / system | R2 loss / FEC rec / concealed / underruns / fps |
| --- | --- | --- | --- | --- |
| 00-04 | 04:19 PS1 | 26.1 / 5.7 / 37 / 3.9 / 59.88 | 04:42 SNES | 26.6 / 4.5 / 88 / 5.8 / 59.82 |
| 05-09 | 04:24 PS1 | 13.8 / 9.7 / 55 / 1.8 / 59.80 | 04:47 SNES | 13.9 / 8.1 / 74 / 2.2 / 59.88 |
| 10-14 | 04:29 PS1 | 24.8 / 13.7 / 416 / 283.6* / 59.12 | **04:52 SNES** | 41.0 / **28.2** / 162 / 5.4 / 59.68 |
| 15-19 | 04:34 PS1 | 111.4 / 11.3 / 149 / 0.9 / 59.50 | 04:57 SNES | 39.9 / 30.2 / 108 / 0.8 / 59.70 |
| 20-24 | 04:39 PS1 | 12.6 / 6.5 / 42 / 2.0 / 59.90 | 05:02 SNES | 39.1 / 30.4 / 80 / 1.0 / 59.70 |
| 25-29 | 04:44 PS1 | 32.0 / 5.0 / 71 / 2.0 / 59.80 | 05:07 SNES / PS1 | 45.8 / 30.1 / 114 / 4.5 / 59.65 |
| 30-34 | 04:49 PS1 / SNES | 22.5 / 6.2 / 74 / 1.0 / 59.75 | 05:12 PS1 | 97.8 / 14.8 / 416 / 30.0 / 58.87 |
| 35-39 | **04:54 SNES** | 40.6 / **27.9** / 140 / 0.7 / 59.66 | 05:17 PS1 | 30.2 / 12.7 / 79 / 0.2 / 59.72 |
| 40-44 | 04:59 SNES | 51.0 / 27.8 / 315 / 3.6 / 59.48 | 05:22 PS1 | 25.8 / 10.2 / 83 / 1.3 / 59.83 |
| 45-49 | 05:04 SNES | 132.3 / 34.2 / 574 / 29.8 / 59.12 | — | — |
| 50-54 | 05:09 SNES | 1,423 / 52.2 / 953 / 82.3 / 56.12 | — | — |
| 55-59 | 05:14 SNES | 34.6 / 31.0 / 178 / 1.8 / 59.70 | — | — |
| 60-64 | 05:19 SNES | 412.5 / 65.8 / 1,382 / 144.0 / 57.87 | — | — |

\* UX-R1 04:31: a 1,062-underrun burst inside an 8-s load session.

- **Where the step comes:**
  - The FEC-recovered step is at play-minute 35 / 04:54-04:56Z on R1, and play-minute 10 / 04:52Z on R2.
  - **That matches the wall-clock time, not the play-minute.** SNES was on screen at the step both nights.
  - On R2 the level fell to 10-15 / min when PS1 followed. R1 never returned to PS1.
- **The damage:** UX-R1's damage (loss > 100 / min, underruns 30-144 / min) sits at play-minutes 45-64 and
  05:04-05:21Z.
  - The second evening covered that clock time cleanly, so the damage is **not the clock**.
  - It ended at play-minute 44, so **play-minute ≥ 45 is untested**.
- **Onn uptime at the step:** R1's onn was ~12.0 h up. R2's is unknown; see below.

**The onn's uptime at the first frame (04:42Z):** not determinable from the device.
- It was up at UX-R1's read (4 h 09 m at 18:31Z 10-20; cold boot ~14:22Z).
- It was cold-booted again at ~15:01Z 10-21, after the evening.
- **14 h 20 m if it was not power-cycled in between; anything less if it was.** Only the user can say.
- Both evenings ended with a cold boot of the onn on the following day.

**SNES against PS1, and the order:**

| | SNES (26.7 min, played FIRST) | PS1 (11.7 min, played last) |
| --- | ---: | ---: |
| fps | 59.74 | 59.56 |
| post-FEC loss / min | 33.8 | 42.3 (Soul Reaver 97.8; SotN 28.3) |
| FEC recovered / min | 22.3 | 12.6 |
| underruns / min | 2.89 | 6.86 (Soul Reaver 30.0; SotN 0.69) |
| concealed / min | 105.8 | 141.2 (Soul Reaver 415.8; SotN 80.9) |
| loss per frame ≥ 40 packets | 0.15 | 0.22 |

**SNES played first read clean.** UX-R1's H3 (SNES itself) loses weight: on UX-R1 SNES was bad when last, and here it
was fine when first.

**The Spearman set** (full minutes):

| pair | R2 (36 min) | R1 (50 min) |
| --- | ---: | ---: |
| post-FEC loss vs frames ≥ 40 | 0.200 | −0.134 |
| post-FEC loss vs max packets | 0.042 | 0.003 |
| FEC recovered vs frames ≥ 40 | 0.410 | −0.08 |
| post-FEC loss vs minute of the evening | 0.103 | **0.516** |
| concealed vs minute of the evening | −0.209 | **0.684** |
| concealed vs post-FEC loss | 0.499 | **0.826** |

- The second evening has **no trend with time**.
- Loss still does not follow the frame-size tail (the cap held; 0 frames ≥ 80). FEC recoveries follow it weakly
  (0.41).

## 2. H5: is the pause / load stream end-and-restart new? **No.**

- **What happens now** (second evening, `save_state_probe.txt`; the probe keeps only the last game, so UX-R1's could not
  show this). Symphony of the Night at 05:22:54Z:
  - the host logs `PAUSE_TOGGLE` and lifecycle `pause`, and the client's `session_ended` comes the same second;
  - at 05:22:58 `save-state` slot 1; at 05:23:06 `resume`, then `session_started` 0.15 s later.
- **The client session ends at the Pause menu, not at the load.** The gap is the time in the menu. UX-R1's 16 short
  sessions were 16 trips through the Pause menu, mostly to load.
- **September** (`h5_sept20_reports.txt`; reports read in place; the journal for the date has rotated out; the recovery
  log starts 09-20 21:37Z). The user's play on **2026-09-20 05:59-06:20Z** was King's Field II (4 "Loading state"),
  Emperor's New Groove (3) and Soul Reaver (2). Those are the same titles as the October evenings, on PCM, before every
  October adoption.
  - 8 client reports in 21 minutes, **every one ending with the pause image `saved`**.
  - Gaps from one session's end to the next start: 6.1-18.5 s within a title, 30-45 s across a title change.
  - **The same behaviour.** H5 is not an October change and is struck from the regression's list.
- **Beside it, for the record only** (not like for like: PCM, the pre-October client and audio path). That September
  play read fps 56.79, post-FEC loss 58.2 / min, underruns 60.2 / min, concealed 563.7 / min.
  - Every report includes its start-up burst (~110-140 underruns per start).
  - **By these counters the September play was not cleaner than either October evening.** What the user remembers as
    better is not visible in these counters. The counters may not capture it, or the "earlier" session was a
    different one; none other is on file with loads.

## 3. The reading (from the two evenings)

Taking §3's three cases in turn:
- **"The same step at a similar play-minute regardless of uptime or clock":** **no.** The single-loss step came at
  play-minute 10 against 35.
- **"The same wall-clock hour":** **partly.**
  - The single-loss step came at 04:52Z and 04:54-04:56Z. That is the same quarter-hour (00:52-00:56 EDT), and both
    times under SNES.
  - But UX-R1's damaging bursts did not come back at their clock (05:04-05:21Z was clean on R2).
  - Something on the home network around 00:50 EDT **moves up** as a candidate for the step, not for the damage. The
    Opal's view, read-only, joins the instrumented evening as a required read, not an option.
- **"Clean throughout":** **mostly.** Apart from Soul Reaver's first two minutes, the second evening reads like the
  clean windows.
  - UX-R1's damage (play-minutes 45-64) is **one event so far, not a trend**.
  - It is also **untested past play-minute 44**: this evening stopped before the point where UX-R1 went bad.

**The hypotheses after two evenings:**
- **H1 (receive path, link or onn) stays first.** It is the only one consistent with both nights:
  - a clock-aligned rise in single losses;
  - a late, bidirectional collapse on one night only.
- **H2 (the onn's time / sessions) is weakened.** If the onn was not cycled, R2 ran on a longer uptime (~14 h) and was
  cleaner. The user's answer on the power-cycles decides how much weight to drop.
- **H3 (SNES) is weakened.** SNES first was clean. The clock-aligned step under SNES on both nights leaves a residue
  that two evenings cannot split.
- **H4 (Opus) is weakened.** The same codec was clean on R2.
- **H5 is closed** (not new).
- **The time-of-day candidate is new:** the network around 00:50 EDT, for the step only.

**The next test: the instrumented evening.** As UX-R1 wrote it (the onn's `udp6` drops while PrivyHub runs,
`cl_b6_onn_read.py` + `cl_b7_onn_threads.py` every 5 min, the user narrating against the host clock), plus what this
evening adds:
1. **Play ≥ 65 minutes**, to reach UX-R1's play-minutes 45-64. The second evening stopped at 44.
2. **Span 00:40-01:30 EDT on the clock**, to cover the 00:52-00:56 step.
   - **Start on PS1 and switch to SNES after the step time.** If the single losses step at ~00:52 on PS1, it is the
     clock. If they step only when SNES starts, it is the content.
3. **The Opal's station counters every 5 minutes, read-only** (O1's read), or the link watch resumed for the evening.
   Required, not optional.
4. **Read `settings global boot_count` at the start and the end**, so any power-cycle is countable. Power-cycle the onn
   at the start only if the user chooses H2's arm; otherwise record its uptime.

## 4. Record

- This file.
- `ux_r2_2026-10-21/`:
  - `session/` (the copies) and `state_now/`;
  - `ux_r2_preserve.py`, `ux_r2_timeline.py`, `timeline.txt|json`, `ux_r2_pair.py`, `pair.txt|json`;
  - `h5_sept20_reports.txt`, `redact_check.txt`, `manifest.sha256`.
- `docs/KNOWN_ISSUES.md`: the top item updated.
- `logs/ux_r2_git_status.txt`.
- `CURRENT.md` Next Action.

Constraints held:
- No sudo, no nft. The Opal was not touched. adb was used for state reads only.
- Nothing fetched, deleted or moved. No restart, no power-cycle, no run.
- No change outside `docs/` and `logs/`. Nothing adopted; nothing committed.
