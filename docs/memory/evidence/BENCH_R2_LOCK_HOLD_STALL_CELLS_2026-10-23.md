---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 43a8df6 (the code under test; the record's pin patch uncommitted beside it)
---

# BENCH-R2 — the lock, the hold, the stall signal: MEASURED, 15/15 valid; the stack is NOT a candidate; APK cb0935c8 CONFIRMED

**Classification: MEASURED, all 15 cells playing and valid on suite attempt 1; host gates met in all 15.** The
pre-registered reading, applied as hashed:
- **The Wi-Fi lock did not cut the uplink silences.** a3 (`high_perf`) was −30 % against a1. a2 (`low_latency`) was
  +262 %. The bar was −80 %. **The lock is not the cause, and B6's H stands.**
  - The room changed across the A/B hour: a1 and a2 lost ~1,100-1,300 packets per minute after FEC with no impairment;
    a3 lost 19.
  - Every later cell with the lock on read 9-28 silences per 10 min, the same range as BENCH-R1 cell 8 without it
    (15.6).
- **The hold + rewind + stall stack is NOT a candidate.**
  - b1 left ~45 unattended frames per blackout (bar ≤ 5).
  - d1 had 2.6 stall pauses per 10 min (bar ≤ 2).
  - c1 met its bar: the pause landed 150-205 ms after the client's last frame in every blackout, against BENCH-R1 cell 7's
    ~2.2-2.6 s of game without a picture.
- **Beetle PSX HW's rewind is not confirmed.** Its 1,074-MB buffer initializes and costs +16.6 points of a core and
  +1.0 GB RSS. **118 of 123 rewinds failed B4's after-check** (the core read PAUSED).
  - snes9x's rewind was never exercised: no hold happened on SNES.
- **The bidirectional LAN rule: 0 asks, 0 steps on the bench** (e1-e3), which was its out-of-sample check.
- **The CONFIRMED rule:** every cell was valid, and the property-empty / host-flag-absent cells behaved as today. So
  **`cb0935c8…1080` stays on the onn and is CONFIRMED.** The pin is moved (§8).
- **No adoption question arises from the reading.** Nothing adopted. Nothing committed.

Task: `handoffs/BENCH-R2_LOCK_HOLD_STALL_CELLS_TASK.md` §2, "the record", session A, read-only from `bench_r2_2026-10-22/`.
- The launch: `BENCH_R2_LAUNCH_2026-10-22.md`.
- The pre-registration: sha256 `45046008…e2fc`, hashed 14:04:37Z, before the install.
- The driver ran 14:09:00-17:45:11Z, "all 15 cells done". The properties read empty at the close.

## 0. The read

- **The code under test is HEAD `43a8df6`.** The tree had no `companion/` or `tools/` change during the run. Every tool
  matches its pre-registration hash (`tools_at_preregistration_sha256.txt`). The readers used are the hashed ones:
  - `ux_r3_seconds.py` (`e9b2b3f7…`), B6's `gap_distribution.py` (`a93d2f57…`): their definitions exec'd unedited;
  - `tools/unattended_frames.py` (`d30a7e6b…`, with B4's `--net`).
- **The logs** (`logs_bench/`, copied first; the heartbeat log had rotated at ~16:31Z during the run): 5,117
  heartbeats, 580 control gaps, 593 recovery rows, 10,502 frame seconds, 6,560 ladder rows, over 14:09:00-17:45:12Z.
  - Each cell's client report was added under `runs/<cell>/logs_run1/decoder_sessions/`, the core's version token
    masked.
- **The reader:** `record/bench_r2_record_read.py` → `record/record_read.json`, `record/record_read_console.txt`,
  `record/unattended_<cell>[_net].json`.
- **c1's blackout times, disclosed (a reader correction):**
  - BENCH-R1's anchor (the shim's dark spans plus the b1 / b2 control-gap offset; offset range 1.7 s here, 0.57 s in
    BENCH-R1) placed c1's blackouts ~1.8 s late.
  - **c1 is anchored on the client's own ≥ 3-s output gaps**: their start = the client's last frame before the dark.
  - Expectation 4 is measured from that same point. Both anchors are kept in `record_read.json`.

## 1. Validity and the gates (every cell)

| cell | workload | shim, applied | environ at stream / load | properties set → cleared | PLAYING (attempt, s) | host gates |
| --- | --- | --- | --- | --- | --- | --- |
| a1 | PS1 | none | 10 / 10 | (none) → empty | 1, 4.1 | met |
| a2 | PS1 | none | 10 / 10 | wifi_lock=low_latency → empty | 1, 3.0 | met |
| a3 | PS1 | none | 10 / 10 | wifi_lock=high_perf → empty | 1, 3.0 | met |
| d1 | PS1 | none | 14 / 14 | low_latency, stall_signal=1 → empty | 1, 3.1 | met |
| d2 | PS1 | none | 14 / 14 | the same → empty | 1, 4.1 | met |
| b1 | PS1 | 5 dark spans 120.0 s apart; `uplink_dropped` 8,572 | 14 / 14 | the same → empty | 1, 3.1 | met |
| b2 | PS1 | 5 spans; `uplink_dropped` 8,683 | 13 / 13 | low_latency → empty | 1, 5.1 | met |
| c1 | PS1 | 5 spans; `uplink_dropped` 0 | 14 / 14 | low_latency, stall_signal=1 → empty | 1, 8.0 | met |
| e1 | PS1 | loss 0.993 % | 11 / 11 | low_latency → empty | 1, 5.0 | met |
| e2 | PS1 | loss 4.982 % | 11 / 11 | low_latency → empty | 1, 6.1 | met |
| e3 | PS1 | 35 bursts / 35 | 11 / 11 | low_latency → empty | 1, 3.0 | met |
| f1 | SNES (snes9x) | none | 10 / 10 | low_latency → empty | 1, 4.1 | met |
| f2 | SNES (snes9x) | none | 13 / 13 | low_latency → empty | 1, 3.0 | met |
| f3 | PS1 (Beetle PSX HW) | none | 10 / 10 | low_latency → empty | 1, 3.1 | met |
| f4 | PS1 (Beetle PSX HW) | none | 13 / 13 | low_latency → empty | 1, 3.1 | met |

- **The gates:** RetroArch 59.998-59.999; capture 59.995-60.047; dup+drop 0.0-0.1/min; `flags_absent` true after every
  cell.
- Every report with a lock property carried `wifi_lock_held: true` and its mode. a1's report carried no `wifi_lock_*`
  and no `stall_signal_*` key.
- **No `link_*` column in any report:** `debug.privyhub.link_report` was never set (not in the pre-registered table).

## 2. Per cell: silences, hitches, unattended frames, the client, the host

The **uplink silences** are B6's `measure` over the session, 10 s at each edge excluded.

| cell | silences ≥ 250 ms /10 min (n, longest ms) | ≥ 950 /10 min | hitch /10 min (longest run s) | unattended core-running /10 min (--net) | loss /min | rendered fps | max output gap ms | host CPU % | encoder % | RetroArch CPU % / RSS MB |
| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| a1 lock none | **41.8** (47, 692) | 0 | 84.9 (16) | 202.8 (202.8) | 1,278 | 57.79 | 1,319 | 10.18 | 36.7 | 33.3 / 256 |
| a2 low_latency | **151.6** (170, 1,879) | 8.92 | 130.4 (15) | 1,664.0 | 1,102 | 57.93 | 2,824 | 11.08 | 41.3 | 35.6 / 257 |
| a3 high_perf | **29.5** (33, 677) | 0 | 25.2 (2) | 174.9 | 19 | 59.90 | 232 | 12.39 | 44.6 | 36.0 / 257 |
| d1 stack | 16.9 (19, 523) | 0 | 20.8 (2) | 136.7 | 11 | 59.91 | 216 | 12.29 | 37.1 | 50.0 / 1,266 |
| d2 stack, stall 400 | 15.2 (17, 818) | 0 | 14.7 (3) | 108.1 | 17 | 59.90 | 217 | 12.77 | 43.6 | 50.9 / 1,267 |
| b1 blackout@both, stack | 12.5 (outside the blackouts 7.8) | 4.46 | 23.4 (3) | 242.3 (236.3) | 1,650 | 57.82 | 4,162 | 9.51 | 36.5 | 23.3 / 1,033 |
| b2 blackout@both, no stall | 7.1 (outside 2.9) | 4.46 | 14.8 (2) | 213.4 (213.4) | 1,632 | 57.81 | 4,260 | 13.24 | 36.7 | 49.5 / 1,264 |
| c1 blackout@down, stack | **125.7** (outside 127.2; 1,328) | 5.35 | 115.3 (11) | 955.8 (952.3) | 1,846 | 56.87 | 4,187 | 12.12 | 36.4 | 39.9 / 1,260 |
| e1 loss-1, bidir | 14.3 (16, 420) | 0 | 14.7 (2) | 65.6 | 75 | 59.28 | 211 | 10.65 | 36.6 | 34.2 / 256 |
| e2 loss-5, bidir | 27.7 (31, 703) | 0 | 146.5 (5) | 251.7 | 841 | 52.28 | 424 | 11.60 | 36.2 | 35.4 / 257 |
| e3 burst-50x20, bidir | 8.9 (10, 578) | 0 | 40.8 (3) | 49.7 | 159 | 59.70 | 227 | 10.84 | 40.2 | 36.3 / 256 |
| f1 snes9x, rewind off | 15.2 (17, 917) | 0 | 15.6 (6) | 135.9 | 19 | 59.85 | 291 | 8.89 | 29.7 | 9.8 / 147 |
| f2 snes9x, rewind on | 11.6 (13, 484) | 0 | 14.7 (2) | 42.3 | 48 | 59.80 | 273 | 7.27 | 27.4 | 10.1 / 176 |
| f3 PSX HW, rewind off | 9.8 (11, 437) | 0 | 11.3 (2) | 50.0 | 11 | 59.92 | 194 | 10.81 | 36.5 | 34.6 / 256 |
| f4 PSX HW, rewind on | 15.2 (17, 477) | 0 | 14.7 (2) | 56.3 | 20 | 59.90 | 305 | 14.06 | 42.6 | 51.2 / 1,264 |

The silences' length distribution, B6's bins, per cell, is in `record_read.json`.
- **a1:** 16 / 15 / 11 / 3 / 2 in 250-300 / 300-400 / 400-500 / 500-600 / 600-800.
- **a2:** 55 / 57 / 23 / 9 / 11 / 6 / 8 / 1, up to ≥ 1,500.
- **a3:** 14 / 11 / 5 / 2 / 1.
- c1, outside the blackouts: 36 / 50 / 15 / 13 / 19 / 5 / 3.

**Read with care:**
- **The room was bad in two stretches with no shim drop:**
  - 14:11-14:37Z (a1, a2): ~1,100-1,300 lost/min after FEC, 1-2.8-s output gaps;
  - 15:52-16:04Z (c1): 127 uplink silences / 10 min outside the blackouts, an encoder restart in its 5th blackout's
    window.
- In those stretches the uplink and downlink failed together, as on Sunday (UX-R1). The a-cells cannot separate the lock
  from the room. That is why the bar's comparison (a2 / a3 against a1) is confounded. The hashed result stands.

## 3. The blackout cells against BENCH-R1 (cells 5-7)

**b1 — `@both`, the whole stack** (hold H 950 via B6, rewind, stall signal, lock):

| blackout | hold (s in, age ms) | handover → `client_stall` | resumes (s after the link's return: first / last) | rewind | unattended core-running / --net / raw | new session |
| --- | --- | --- | --- | --- | --- | --- |
| 15:24:52 | +1.04, 955 | +4.06, held 3,099 | 1.93 / 2.25 | `rewind_failed` (req 2) | 49.0 / 49.1 / 227.0 | 0 |
| 15:26:52 | +0.95, 950 | +4.05, held 3,098 | 3.70 / 4.18 | `input_release` rewound 3 | 42.2 / 39.2 / 226.3 | 0 |
| 15:28:52 | +0.97, 953 | +4.03, held 3,077 | 1.78 / 5.97 (a second stall at +9.8) | failed ×2 (req 2, 6) | 43.0 / 43.0 / 225.8 | 0 |
| 15:30:52 | +1.05, 956 | +4.03, held 3,069 | 1.97 / 2.60 | rewound 4 | 47.8 / 43.8 / 225.4 | 0 |
| 15:32:52 | +1.05, 952 | +4.03, held 3,075 | 2.59 / 3.07 | failed (req 1) | 47.8 / 47.8 / 225.2 | 0 |

- **The shape, per blackout:**
  1. one hold at 0.95-1.05 s;
  2. at the link's return (+4.03-4.06 s), `input_hold_handover` → `client_stall`;
  3. a `resumed` with no via 1.8-3.7 s after the return;
  4. one in-gate `client_stall` (age 1-39 ms);
  5. `resumed via stall_end` 2.2-4.2 s after the return.
- **The rewound frames were only the stall's own 1-4.** The ~57 frames the core ran between the silence's onset and the
  hold at 950 ms were never requested: after the handover the stall owns the pause, and B7 rewinds to the client's last
  displayed frame.
- So **~45 frames per blackout ran without the player (net 39-49)**:
  - against BENCH-R1 cell 5's 85.0, which v2's desync pause then cut short; B1b now gates that desync;
  - against this cell's raw ~226, the true unheld cost.
- No new client session. The heartbeat held ~6 s, ~3,200 lost after FEC, 0-1 unrecoverable groups per blackout.

**b2 — `@both`, hold + B6 + rewind, no stall pair:**
- Every blackout:
  - the hold at +1.04-1.05 s (age 951-960 ms);
  - `rewind_failed` (requested 58-59, the pre-hold frames);
  - `resumed via input_release` (held 4,001-4,023 ms) **1.06-1.11 s after the link's return**;
  - `client_ready_after_hold` 0.8-1.1 s later.
- **Unattended frames: 47.3-47.9 per blackout, net the same.** The rewind that would have cut them failed on PSX HW.
  No new session.

**c1 — `@down`, the whole stack:**
- **The pause, every blackout:** `desync_pause client_stall` with age **150 / 153 / 157 / 152 / 205 ms**, i.e. 0.15-0.21 s
  after the client's last frame. That is ~9-12 frames of game without a picture.
  - BENCH-R1 cell 7: ~2.2-2.6 s (~140 frames) before v2's `client_output_silence`.
  - Unattended frames 0 / 1.7 / 0 / 0 / 9.8. The 5th blackout's window held the room's uplink flapping and an encoder
    restart.
- **Then:** a `resumed` with no via at +5.7-6.1 s (1.7-2.1 s after the return), one in-gate stall, and `resumed via
  stall_end` 2.3-2.6 s after the return. The 2nd and 5th blackouts trailed further stalls into the room's noise (last
  resume +9.6 / +10.9 s).
- **Outside the blackouts:**
  - **82 more stall pauses (77 per 10 min)**, at the 150-ms threshold, on that hour's flapping link;
  - **6 false holds** (silences ≥ 950 ms, the room).

## 4. The clean cells (d1, d2), and the stall threshold

- **d1** (stall at 150):
  - **1 false hold** (14:54:41Z, a 1,013-ms room silence, `rewind_failed` req 59): **0.87 / 10 min** (bar ≤ 1: met);
  - **3 stall pauses** (14:57:51, 14:59:09, 15:04:22, ages 150-157 ms): **2.60 / 10 min** (bar ≤ 2: **not met**);
  - 4 `rewind_failed`. The client sent 6 stalls and 4 ends.
- **d2** (host threshold 400, client at 150): **0 holds, 0 stall pauses**. The client sent 9 stalls and 8 ends, all under
  400 ms.

## 5. The loss cells with the bidirectional rule (e1-e3)

- **0 `lan_loss_rule` rows, 0 transitions, 7000 throughout in all three.** The rule never asked, so it wrote no
  `uplink_windows` row. The uplink was quiet (8.9-27.7 silences per 10 min).
- Against BENCH-R1 cells 2-4 (`=1`): those stepped to 5000 within 5-8 min.
- **The cost of staying at 7000 under 5 % random loss (e2):** rendered 52.3 fps, hitch 146.5 per 10 min. That is the
  case the rule is designed not to act on (LAN-R2).

## 6. The rewind rows: CPU and memory per core, and whether Beetle PSX HW rewound (f1-f4, and every hold)

| | RetroArch CPU % of a core | RetroArch RSS MB, mean / max | host CPU % | host memory available, min MB | rewind buffer (RetroArch's log) |
| --- | ---: | --- | ---: | ---: | --- |
| snes9x, off (f1) | 9.78 | 147 / 147 | 8.89 | 11,157 | — |
| snes9x, on (f2) | 10.05 (**+0.28**) | 176 / 197 (**+29**) | 7.27 | 11,087 | 53 MB |
| PSX HW, off (f3) | 34.61 | 256 / 278 | 10.81 | 11,048 | — |
| PSX HW, on (f4) | 51.18 (**+16.6**) | 1,264 / 1,327 (**+1,008**) | 14.06 | 10,052 | **1,074 MB** |

**Did Beetle PSX HW rewind at all?** Not confirmed.
- RetroArch's log reads "Initializing rewind buffer with size: 1074 MB" with no error, so serialization runs. That is
  the CPU and memory above.
- **Of 123 rewinds on PSX HW (d1, b1, b2, c1), 118 ended in `rewind_failed`.** The reason, every time: "not playing
  after the rewind: GET_STATUS PAUSED Beetle PSX HW,…". 5 small ones (3-5 frames) passed the after-check.
- B4 §7 named this limit: over the NCI the host cannot tell a refused rewind from one that ran and left the core paused.
  So the frames may or may not have been rewound. The core was resumed either way (B4: the resume never depends on it).
- **snes9x's rewind was not exercised:** f2 had no hold.
  - The pre-registration put every blackout cell on the PS1 fixture (the task's table marked only the f rows SNES).
    That was my choice, and it left the core where rewind should work untested.

## 7. The user's observation (verbatim) and the counters beside it

> "I was seeing some wild glitches/artifacts on stream. Like in one the NPC models were missing faces but everything was
> running fine (also a rainbow like bar at the top)"

- **When and what:** seen ~16:05-16:17Z. That is **cell e1**: `loss-1@post-fec,seed=1` (1 % random packet loss on the
  downlink, after FEC), PS1 (Tekken 3, Beetle PSX HW), rewind off, the lock on, the session 16:06:34-16:18:06Z.
- **Per minute in that window** (the heartbeats):
  - **50-99 packets lost after FEC**; **14-30 FEC-unrecoverable groups**;
  - 286-503 recovered by FEC;
  - rendered 59.0-59.4 fps.
- **The client's counters for the session** (11.65 min):
  - lost 871; FEC recovered 5,400; **unrecoverable groups 237**;
  - **`sequence_gap_au_drops` 454 + `incomplete_au_drops` 34**: 488 frames the client dropped because packets were
    missing, ~42 per minute;
  - `dropped_frames` 475; `sequence_resyncs` **0**; `timestamp_anomalies` **0**;
  - the decoder rendered 41,319 of 41,365 queued;
  - IDR frames 2,706 (≤ 41 frames between them); max output gap 211 ms;
  - hardware decoder `c2.realtek.video.avc.decoder`.
- **What the counters called that picture: rendered frames.** No error counter moved.
  - The client dropped the incomplete frames and kept decoding the next ones. Those referenced pictures it never
    received, so the hardware decoder drew them from stale references, up to the next IDR.
  - Missing faces and a coloured band are what such frames look like.
  - Nothing in the report marks a frame as corrupted. The only trace is the access-unit drop count.
- **This is not new with this APK.** BENCH-R1 cell 1 (`loss-1`, the previous APK `93d29b4a…`) dropped 551 + 90 access
  units with 18 resyncs. Nobody was watching the TV then.
- **A finding, not a fault of the cell:** under steady post-FEC loss the client shows corrupted pictures without counting
  them. Whether to freeze on the last good frame until the next IDR, or to count "frames decoded after a dropped
  reference", is B's question (§9).

## 8. The pre-registered expectations, the reading and the CONFIRMED rule, as hashed

| # | written beforehand | result |
| --- | --- | --- |
| 1 | a2 and/or a3 cut the uplink silences ≥ 250 ms per 10 min against a1 by ≥ 80 % | **NOT MET:** a2 +262 % (151.6 against 41.8), a3 −30 % (29.5). The room changed across the hour (§2). |
| 2 | d1: ≤ 1 false hold / 10 min and ≤ 2 stall pauses / 10 min | **NOT MET:** holds 0.87 (met), stall pauses 2.60 (not met) |
| 3 | b1: net unattended ≈ 0 (≤ 5 per blackout), one hold and one stall-end resume per blackout, no new client session | **NOT MET:** net 39-49 per blackout. One hold each. Stall-end resumes 1 / 1 / 2 / 1 / 1. No new session (met). |
| 4 | c1: the pause within 0.3 s of the client's last frame in every blackout | **MET:** 150-205 ms, all five |
| 5 | e1-e3: 0 `lan_bidir` steps when the uplink is quiet | **MET:** 0 asks, 0 steps |
| 6 | f: the CPU cost of rewind per core stated; PSX HW's answer stated | **MET (stated):** snes9x +0.3 points / +29 MB; PSX HW +16.6 points / +1.0 GB; PSX HW's rewind not confirmed (118 / 123 failed the after-check) |

**The reading, as hashed:**
- **"If a2/a3 cut the silences by ≥ 80 %":** they did not, so the Wi-Fi lock is not an adoption question. **B6's H
  (950) stands.**
- **"If b1 and c1 meet their bars with d1 clean":** b1 did not, and d1 was not clean (stall pauses). **The stack is not
  a candidate** for the user's adoption call.
  - "If d1 shows false holds": d1 showed one, within its bar. The lock result is now in, and it did not help.
- **e:** the bidirectional rule's false-trigger count on the bench is **0** (its out-of-sample check passed). It also
  never acts on random loss, as designed.
- **f:** PS1 rewind is not confirmed, so **the stack's rewind is SNES-only** until PSX HW is shown to rewind. snes9x's
  own rewind is still unexercised.

**The CONFIRMED APK (CL-B7's rule):**
- All 15 cells were valid.
- The property-empty cell a1 and the host-flag-absent cells f1 / f3 behaved as today:
  - a1's report carried no new key; its losses and its one `client_output_silence` pause were the room's (§2);
  - f1 / f3 rendered 59.85 / 59.92 fps with their gates met.
- e1's corrupted pictures are the same mechanism as the previous APK's (§7).
- **So `cb0935c8cadd5ee65a3f52f390d0994899de27ebaa5c207b547e57185e761080` stays on the onn and is CONFIRMED.**
- **Pinned** (`record/bench_r2_hash.diff`, `record/predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK`;
  - `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test.
- **Tests** (`record/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK;
  `git diff --check` clean.
- **The previous CONFIRMED `93d29b4a…` is preserved** at `PrivyHub/app/build/bench_r2_preserved/app-debug.apk`
  (gitignored).

## 9. What the data hands back to B (the user's call which; nothing here is built)

- **The hold's ownership at the return.** On `@both`, the stall takes the pause over at the link's return, so the
  hold's own ~57 pre-hold frames are never rewound, and the resume waits for the ready gate plus a second stall (2-4 s
  after the return).
  - b2 (no stall pair) resumed 1.1 s after the return.
- **PSX HW's after-check.** Either the REWIND / PAUSE_TOGGLE sequence leaves Beetle PSX HW paused (B4's method), or the
  core refuses. Neither is visible over the NCI. The rewind's +16.6 points and +1 GB are paid either way.
- **snes9x's rewind,** never exercised: the one cell where rewind should work.
- **The stall threshold.** At 150 ms, 2.6 pauses per 10 min on a clean hour and 77 per 10 min on a flapping one. At 400,
  0 on a clean hour.
- **The lock is not the cause of the silences.** The room is.
- **The corrupted pictures under loss (§7):**
  - freeze on the last good frame until the next IDR, or not;
  - a counter for frames decoded after a dropped reference.

## 10. State at the end (the user's checks)

- **`tools/e3_state.py --check`: ok** on the eight lines, **APK CONFIRMED** (`cb0935c8…`, pinned), no `e3_flag.conf`, no
  game, no RetroArch, no encoder (`record/check_end.json`).
- **The three properties read empty.** Only the companion unit is running.
- **On the onn:** `cb0935c8…1080`, CONFIRMED.

## 11. Files

- **`bench_r2_2026-10-22/`:**
  - the launch's and the driver's files, `runs/` (15 cells, each client report added);
  - `logs_bench/` (the five logs over the run, `copied_at.txt`);
  - `record/`:
    - `bench_r2_record_read.py`, `record_read.json`, `record_read_console.txt`, `unattended_*.json`;
    - the pin patch: `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `bench_r2_hash.diff`, `tests.txt`;
    - `check_end.json`, `manifest.sha256`;
  - `redact_check_record.txt`: 70 files OK. 2 HITs, `tools/e1_suite.py` and its predecessor copy, are the suite's own
    `127.0.0.1` URL (line 597, pre-existing), OK (benign) on the re-check.
- **Elsewhere:**
  - `tools/e1_suite.py`, `tools/c3_l4_nft_night.py`, `tools/test_c3_l4_nft_night.py` (the pin);
  - `docs/KNOWN_ISSUES.md` (the top item), `docs/ROADMAP.md` (§G8), `docs/memory/CURRENT.md` (Next Action);
  - `logs/bench_r2_git_status.txt`.
- No sudo, no nft, no Opal, adb only for state reads (`--check`, `getprop`).
- Nothing fetched, deleted, adopted or committed.
