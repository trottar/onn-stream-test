---
memory_schema: 1
as_of: 2026-10-21
status: UX-R3 READ (session A, read-only, from UX-R2's and UX-R1's preserved copies; no run, no adb). One moment in last night's Zelda stands out, and the instruments saw it on both directions at once: 04:54:55-04:54:59Z, 12.3 min into a 26.4-min session ("halfway"). The uplink went silent for 2.65 s of 4 s (five control gaps, 967 ms the longest); the downlink had the session's two largest output gaps (410 and 307 ms); audio arrival stopped for 406 ms; 61 packets were lost after FEC; and a heartbeat was held ~1.5 s. Frame sizes were normal and the ladder read "clean". A SECOND moment is not distinguishable: the user's window 04:56-05:03Z holds only five small hitches (control gaps 277-297 ms, output gaps 215 / 223 ms). The hitch count orders Sunday and last night the way the user does (43.3 against 12.9 per 10 min). September cannot be scored the same way (its logs have rotated), and by the measures its reports allow it is not cleaner. live could not have stepped down in any of last night's top seconds. Nothing changed; nothing committed
---

# UX-R3 — find the deaths

Task: `handoffs/UX-R3_FIND_THE_DEATHS_TASK.md`. Files: `ux_r3_2026-10-21/`. Read from `ux_r2_2026-10-21/session/` and
`ux_r1_2026-10-20/session/`.

**The user (2026-10-21), verbatim:**
> "It felt better but there were two memorable instances where I literally died because of lag. That is completely unacceptable especially over LAN."
>
> Where: "Zelda and no idea probably halfway through to last third of the playthrough."
>
> **The standard: "This product needs to work at any house especially lan as long as the Internet is over 50mb/s."**

Both evenings were played on a different TV from the usual test TV: a different room, so a different Wi-Fi path to
the same router.

## The answer, plainly

- **One death candidate is clear: 04:54:55-04:54:59Z.** That is 12.3 of 26.4 minutes into Zelda, the "halfway" end of
  the user's estimate. Every per-second instrument that covers it moved, in **both directions at once**:
  - **uplink:** five control gaps in 4 s (967, 350, 342, 546, 442 ms): **2.65 s of the 4 s with no controller input
    reaching the host**;
  - **downlink:** the session's two largest output gaps (410 ms at 04:54:56, 307 ms at 04:54:57). The heartbeat was
    held about 1.5 s (a 3.52-s interval arriving one second after the previous one), carrying 61 packets lost after
    FEC, 7 unrecoverable groups, 308 concealed underruns and a 406-ms audio arrival gap;
  - **not the content:** the frame sizes before and during were normal (max 72-76 packets, 3-4 frames ≥ 40 / s, 0 over
    the cap);
  - **not the host:** no recovery row, no ladder action. The ladder read `REFERENCE / clean`; its samples stopped while
    the heartbeat was held, and the next read fps 89.5 (catch-up).
  - It has the signature of UX-R1's bursts at about a tenth of their size: the link, or the onn's radio, dropping both
    ways for ~3-4 s.
- **A second moment is not distinguishable.** The user's window 04:56-05:03:59Z holds five hitch seconds, all small:
  - control gaps 297 (04:57:26), 286 (05:00:28) and 277 ms (05:01:06);
  - output gaps 215 (04:59:57, ladder fps 42) and 223 ms (05:03:10, ladder fps 38, 208 concealed).
  - The next-largest anywhere in Zelda is 04:55:53 (control gap 399 ms plus output gap 202 ms), 54 s after the first.
  - **Either the second death was one of these small events, or the instruments did not see it** (see "What the
    instruments cannot see").
- **The hitch count orders the evenings the way the user does for the two October evenings.** Sunday: 43.3 per 10 min,
  longest run 28 s. Last night: 12.9 per 10 min, longest run 11 s (the start-up); in mid-play 7.8 per 10 min, longest
  run 5 s, which is the death.
  - **September cannot be scored on the definition:** its heartbeat and control-gap logs have rotated out.
  - By the per-report measures it does carry, September is not cleaner (§2).
- **live could not have stepped down** in any of last night's top seconds. Every rule needs 4 of 5 two-second reports
  bad. The death was one report long (§3).

## 1. The per-second view

`ux_r3_seconds.py` reads the copies only and writes:
- `seconds_r2.tsv` / `seconds_r1.tsv` (every second, every column);
- `ranked.txt` (counts, every control gap, report coverage, top-15 tables with every column);
- `counts.json`, `counts_extra.json`.

**Each log's real resolution.** Nothing is interpolated; a value sits in the second its row carries.

| log | resolution | in the Zelda window |
| --- | --- | --- |
| heartbeat (rendered, loss, FEC, unrec, underruns, concealed, audio arrival gap max, output age) | ~2 s intervals, cumulative; credited to the second the interval ends in | 809 rows, median 2,010 ms, max 4,045 ms |
| `native_stream_ctrl_gaps.log` | every uplink silence ≥ 250 ms, start and length | 29 gaps (one is the pause) |
| `native_frame_sizes.jsonl` (frames, packets, bytes, max packets, frames ≥ 40) | 1 s | every second |
| ladder samples / states | per client report (~2 s) | 808 samples |
| recovery log | per event | start / end only |
| client report: 16 largest output gaps | whole session, per event, by the client's elapsed clock | all 16 |
| client report: ≥ 50-ms slow events | last 1,024 only | **from 05:03:48 only: the user's window is NOT covered** |
| client report: audio tick series | first 400 ticks only | the first ~200 s (to 04:45:57) |
| client report: audio arrival holes | last 300 only | the last ~15 s |

The client's elapsed clock was mapped to UTC per client session: the median of (heartbeat received − heartbeat
elapsed).

**The hitch definition** (written in the script's header before any ranking; one definition for every evening). A UTC
second is a hitch second if any of these holds:
- **R:** the heartbeat interval ending in it rendered < 50 fps;
- **C:** a host control gap ≥ 250 ms starts in it;
- **G:** an output gap ≥ 200 ms is recorded in it (a client-report row, or the ladder sample's `output_gap_ms`);
- **L:** the heartbeat interval ending in it lost ≥ 30 packets after FEC.

The user's own pauses (a control gap containing a `session_ended`) are excluded. Score = criteria met. Ties go by the
longest control gap, then the output gap, then the loss.

**Zelda (04:42:26-05:09:21Z): 35 hitch seconds in 26.2 min.**
- 15 are the stream's start-up (04:42:40-04:42:57, the first 11 s after `session_started`).
- 20 are in mid-play, at: 04:43:45, :50, 04:44:26, :49, :57, 04:47:33, 04:52:37, 04:52:56, **04:54:55-59**, 04:55:53,
  04:57:26, 04:59:57, 05:00:28, 05:01:06, 05:03:10, 05:07:38.

**Top 15 seconds of Zelda** (selected columns; every column in `ranked.txt`):

| UTC | criteria | rendered / interval | post-FEC | ctrl gaps (ms) | output gap (ms, source) | concealed | audio arrival gap | tx max packets / ≥ 40 | ladder fps / state |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |
| 04:42:47 | R C | 97 / 2.06 s (47.2 / s) | 24 | 921 | — | 84 | 161 | 77 / 4 | 45.0 PRESSURE (start-up) |
| 04:55:53 | C G | 115 / 2.01 s | 0 | 399 | 202 (top16) | 16 | 61 | 77 / 4 | — |
| **04:54:56** | C G | (held) | — | 350 | **410** (top16) | — | — | 73 / 4 | (no sample) |
| **04:54:57** | C G | (held) | — | 342 | **307** (top16) | — | — | 73 / 4 | (no sample) |
| **04:54:59** | R L | 166 / **3.52 s** (47.2 / s) | **61** | — | — | 308 | **406** | 50 / 2 | 89.5 REFERENCE clean |
| **04:54:55** | C | — | — | **967** | — | — | — | 72 / 3 | — |
| 04:42:54 | C | — | — | 777 | — | — | — | 73 / 3 | — (start-up) |
| 04:42:52 | C | 166 / 2.57 s | 6 | 705 | — | 68 | 185 | 77 / 4 | — (start-up) |
| 04:42:57 | C | — | — | 669 | — | — | — | 77 / 4 | — (start-up) |
| 04:42:46 | C | — | — | 546, 638 | — | — | — | 77 / 5 | `session_started` |
| **04:54:58** | C | 119 / 2.01 s | 7 | **546, 442** | — | 23 | 112 | 76 / 4 | — |
| 04:42:49 | C | — | — | 497 | — | — | — | 77 / 4 | — (start-up) |
| 04:42:53 | C | — | — | 337, 443 | — | — | — | 77 / 4 | — (start-up) |
| 04:42:51 | C | — | — | 407 | — | — | — | 77 / 4 | — (start-up) |
| 04:42:45 | C | — | — | 398 | — | — | — | 14 / 0 | — (start-up) |

**±5 s around the death (04:54:52-04:55:02):**
- 04:54:53: heartbeat clean (124 frames, loss 7). The ladder sample read fps 59.8, clean.
- An earlier sample at 04:54:51 read receiver fps 42.
- 04:54:55-04:54:58: the uplink gaps.
- 04:54:56-57: the output gaps.
- 04:54:58: a heartbeat arrives late, then 04:54:59 another (3.52-s interval, loss 61, concealed 308, arrival gap
  406 ms).
- 04:55:01: clean again (135 frames, loss 0).
- Host transmit, every second: 782-898 packets, 829-970 KB, max 50-76 packets; 04:55:02 dipped to 622 packets (31 max).
- **Recovery log: nothing. The ladder: nothing.**

**The whole evening's top 15** (`ranked.txt`) adds Soul Reaver's start (05:12:34-05:12:46: output gaps 441 / 349 /
339 / 302 ms, rendered 39.8 / s) and 05:17:38 (control gap 398 ms plus output gap 255 ms, Symphony of the Night's
first minute). UX-R1's top seconds are its 05:06-05:11 and 05:20-21 bursts (scores 3-4), for comparison.

## What the instruments cannot see (and so cannot rule out)

- **Controller-to-screen latency.** Nothing measures the time from a button press on the onn to its effect on screen.
  The control-gap log sees only uplink silences ≥ 250 ms. Input that arrived late but within 250 ms, or arrived
  bunched, is invisible.
- **The client's input queue and send timing.** No client-side record of when each controller packet was sent.
- **Per-second output gaps on the client across the whole session.** The report keeps the 16 largest and the last
  1,024 slow events, so 04:56-05:03:48 has only the top-16 rows. A 150-199-ms gap there would be unseen.
- **The Wi-Fi link's own retries and rate.** No Opal read was taken. The onn exposes no retry counter (MEMORY.md).
- **The game's frame on the host.** RetroArch's own frame pacing per second and the moment of the death are not
  logged.
- **A mark from the user.** No clock mark exists for either death, so "halfway to last third" is a 13-minute window.

## 2. The hitch view, counted

The definition is as in §1, once. Per 10 minutes of play, with the longest run:

| evening | user's report | hitch s | per 10 min | longest run | excl. client start-ups (first 15 s) | output-gap-only (G) per 10 min |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| **UX-R1**, 2026-10-20, 57.9 min | "horrible … not good to terrible" | 251 | **43.3** | **28 s** | 243 (42.0 / 10 min) | 12.3 |
| **UX-R2**, 2026-10-21, 39.7 min | "felt better but … two memorable instances where I literally died because of lag" | 51 | **12.9** | 11 s (start-up) | 31 (7.8 / 10 min); mid-play longest run **5 s = the death** | 5.5 |
| **2026-09-20** play, 18.3 min (PCM) | "earlier" (remembered as good) | **cannot be computed** | — | — | — | (see below) |

By criterion:
- UX-R1: C 213, G 71, R 30, L 23.
- UX-R2: C 31, G 22, R 5, L 3.

**What September's reports allow** (`per_report_like_for_like.txt`, `counts_extra.json`):
- Its heartbeat and control-gap logs have rotated out, so R, C and L cannot be computed.
- Its reports carry no top-16 list. The slow-event list held 64 rows, about the last 16 s of each session.
- So only each report's largest output gap and the latency-spike counters compare like for like:

| | reports with largest gap ≥ 200 ms | largest gaps (ms) | frames ≥ 250 ms late / min | frames ≥ 80 ms late / min |
| --- | --- | --- | ---: | ---: |
| 2026-09-20 | 5 / 8 | 99-521 | 0.88 | 71.2 |
| UX-R1 | 7 / 20 | 87-4,923 | 0.14 | 4.6 |
| UX-R2 | 3 / 6 | 109-534 | 0.35 | 2.3 |

**Does the count order the evenings the way the user does?**
- **For the two October evenings, yes:** Sunday 43.3 against last night 12.9, longest run 28 s against 5 s mid-play.
  It is a candidate gameplay metric for every record from here (proposed, not adopted). It needs the heartbeat and
  control-gap logs, which rotate (LOG_KEEP 3), so a record must preserve them the night they are made.
- **For September, it cannot say.** By the measures September's reports carry, it was not cleaner. Its frames ran late
  far more often (the pre-C3.L2c client), and 5 of 8 sessions had a gap ≥ 200 ms.
- **What the count misses:**
  - It cannot weigh one long freeze against many short ones. One 5-s run killed the user twice; 51 scattered seconds
    did not register.
  - It does not see input latency (the uplink below 250 ms).
  - It cannot know what the game was doing in the second.
  - **A death is a property of the moment in the game, not of the count.** Last night had one 5-s run; Sunday had many
    longer ones.

## 3. The ladder, in those seconds

`ux_r3_ladder.py` → `ladder_table.txt`. live's step-down rules use the last 5 evaluated reports (10 s):
- `capacity_mild` (one rung): fps < 57 on ≥ 4 of 5 AND loss ≥ 50 on ≥ 3 of 5;
- capacity: fps < 50 on all 5 AND loss ≥ 50 on ≥ 3 of 5;
- queue / gap FALLBACK: fps < 50 on all 5 AND (queue ≥ 2 on ≥ 3 OR gap > 250 on ≥ 2);
- ROUTINE: fps < 57 on ≥ 4 AND queue ≥ 1 on ≥ 3;
- none before 60 s of session age; stale, blackout and resync reports do not count.

| evening / second | state / reason at or before | last act this evening | 5 samples from it: fps < 57 / loss ≥ 50 / gap > 250 | what `capacity_mild` needed |
| --- | --- | --- | --- | --- |
| R2 04:42:47 (start-up) | PRESSURE / pressure_sample | none | 3 / 0 / 0 | 1 more slow report, 3 more lossy ones |
| **R2 04:54:56 / 04:54:59 (the death)** | **REFERENCE / clean** | none | **1 / 0 / 0** | 3 more slow, 3 more lossy |
| R2 04:55:53 | PRESSURE / pressure_sample | none | 0 / 0 / 0 | 4 more slow, 3 more lossy |
| R2 04:59:57 | PRESSURE / pressure_sample | none | 1 / 0 / 0 | 3 more slow, 3 more lossy |
| R2 05:03:10 | PRESSURE / pressure_sample | none | 1 / 0 / 0 | 3 more slow, 3 more lossy |
| R2 05:12:46 (Soul Reaver start) | PRESSURE / pressure_sample | none | 2 / 0 / 0 | 2 more slow, 3 more lossy |
| R2 05:17:38 | PRESSURE / pressure_sample | none | 2 / 0 / 0 | 2 more slow, 3 more lossy |
| R1 05:06:04 | PRESSURE / pressure_sample | none | 2 / 0 / 0 | 2 more slow, 3 more lossy |
| R1 05:10:05 (the 4.9-s gap) | PRESSURE / resync_ignored | none | 1 / 2 / 0 (resync, blackouts) | 3 more slow, 1 more lossy |
| **R1 05:10:55** | PRESSURE / pressure_sample | none | **4 / 4 / 0** | **met**; the ladder acted at 05:11:01 (7000 → 6000, `capacity_mild`) |
| R1 05:20:50 | REFERENCE / clean | 05:11:01 → 6000 (reset to 7000 at the next session) | 1 / 1 / 0 | 3 more slow, 2 more lossy |
| R1 05:21:43 | PRESSURE / pressure_sample | 05:11:01 → 6000 (reset) | 2 / 2 / 0 | 2 more slow, 1 more lossy |

**The death fit inside one report.**
- live's window is 10 s and needs 4 of 5 reports bad. During the death the heartbeat itself was held, so the ladder
  had no sample in the worst 3 seconds. The first sample after read fps 89.5 (catch-up) and loss 39.
- **No rule of the adopted ladder can act on a 3-5-s bidirectional drop.** A step down also would not prevent a link
  that stops both ways.
- No change is proposed here. That is session B's LAN-R1.

## 4. Record

- This file.
- `ux_r3_2026-10-21/`:
  - `ux_r3_seconds.py`, `seconds_r2.tsv`, `seconds_r1.tsv`, `ranked.txt`, `ranked_console.txt`;
  - `counts.json`, `counts_extra.json`, `per_report_like_for_like.txt`;
  - `ux_r3_ladder.py`, `ladder_table.txt`;
  - `redact_check.txt`, `manifest.sha256`.
- `docs/KNOWN_ISSUES.md`: the top item.
- `logs/ux_r3_git_status.txt`.
- `CURRENT.md` Next Action.

Constraints held:
- No sudo, no nft, no adb. The Opal was not touched.
- Nothing fetched, deleted or moved. No restart, no run.
- No change outside `docs/` and `logs/`. Nothing adopted; nothing committed.
