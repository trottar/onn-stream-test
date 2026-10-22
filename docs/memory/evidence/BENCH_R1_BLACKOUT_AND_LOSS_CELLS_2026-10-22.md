---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: b909735 (the code under test, all eight cells); the tree at the read was 144e5c7 (B4 on top), clean
---

# BENCH-R1 — the loss cells and the blackout cells, the hold off and on: MEASURED, 8/8 valid

**Classification: MEASURED, all 8 cells playing and valid, host gates met in all 8.**
- **The reading, applied as hashed: the hold is NOT a candidate until its trigger is fixed.** Cell 8, on a clean link,
  held 18 times. Cell 6 also missed its bar: −73 % per blackout, not ≥ 90 %.
- **The LAN loss rule goes back to B.** Cells 2-4 did not step as LAN-R1 §3 predicted. The rule stepped earlier,
  0.9-1.5 min into the stream, and in cell 4 ~2 min before G8-S1's `capacity_mild` point.
- **The death is reproduced on the bench** (cell 5, all four shape terms in all five blackouts). It is harsher than
  the death, with the same core-running count: 85.0 per blackout against 83.8.
- Nothing adopted, nothing committed.

Task: `handoffs/BENCH-R1_BLACKOUT_AND_LOSS_CELLS_TASK.md` §2, "the record", session A, read-only from
`bench_r1_2026-10-22/`. The launch: `BENCH_R1_LAUNCH_2026-10-22.md`. The pre-registration: `bench_r1_preregistration.txt`,
sha256 `d7de4da0…e41d`, hashed 02:31:42Z. The driver ran 02:31:50-04:26:59Z ("all 8 cells done"), with no repeat and
no busy skip, and every cell PLAYING on suite attempt 1.

## 0. The code under test, and the read

**The code under test is `b909735` for all eight cells.**
- During and after the run, HEAD moved to `d4c9870`, then `144e5c7`:
  - `d4c9870` (02:39:51Z, during cell 1) holds evidence files only. `git diff b909735 d4c9870 -- companion tools PrivyHub`
    is empty.
  - `144e5c7` is session B's B4. Its five `companion/` files and `tools/unattended_frames.py` carry a 04:35:57Z mtime,
    9 min after the driver closed. B's done note (`SESSION_B_DONE_2026-10-22B.md` item 9) says it wrote nothing under
    `companion/` while the unit was active.
- Each of the six files B4 did not touch still matches its pre-registration hash: `impairment.py`, `lan_loss_rule.py`,
  `adaptive_bitrate_live.py`, `native_stream.py`, `e1_suite.py`, the driver.
- **The two readers used are the hashed ones:**
  - `ux_r3_seconds.py` (`e9b2b3f7…`), unchanged. Its `evening` / `counts` are exec'd unedited from the file, pointed
    at each cell's logs.
  - `tools/unattended_frames.py` as of `b909735`, from `git show` into `record/unattended_frames_at_b909735.py`,
    sha256 `c18e4554…`, the pre-registration's hash. B4's `--net` came later and is not used.

**The logs** (`logs_bench/`, copied first; they rotate):
- The heartbeat, control-gap, recovery, frame-size and ladder logs over 02:31:50-04:27:00Z, from the live files and
  `stream_log_archive/*.1`. The heartbeat log had rotated at ~02:59Z during the run.
- 2,749 / 383 / 131 / 5,609 / 3,458 rows; addresses masked.
- The driver's own per-cell copies (`runs/<cell>/logs_run1/`) are what the reader reads.
- Each cell's client report was added to those copies (`decoder_sessions/`). The only address-like token in a report
  (the core's version in `capture_description`) is masked.

**The reader:** `record/bench_r1_record_read.py` → `record/record_read.json`, `record/unattended_<cell>.json`,
`record/record_read_console.txt`.
- **Blackout times:**
  - Cells 5-6: from the ~4.0-s control gaps.
  - Cell 7 (`@down`, the uplink live): from the shim's dark spans, anchored by the offset measured on cells 5-6. The
    offset is −7.15 s, with a range of 0.57 s over 10 spans.
  - Cell 7's own ~4.1-4.2-s client output gaps fall inside each window.
- **A blackout's window** is [start − 1 s, start + 10 s]; its recovery rows run to + 15 s.

## 1. Validity (every cell)

| # | cell | shim, applied | environ at stream / under load | `flags_absent` |
| --- | --- | --- | --- | --- |
| 1 | `loss-1` | 0.991 %, no other drop | 10 / 10 | true |
| 2 | `loss-1` + rule | 0.984 % | 11 / 11 | true |
| 3 | `loss-5` + rule | 4.975 % | 11 / 11 | true |
| 4 | `burst-50x20` + rule | 35 bursts of 50 against 35 expected | 11 / 11 | true |
| 5 | `blackout-4s@both` | 5 dark spans (5 lines each), 120.0 s apart; `uplink_dropped` 10,599; 2.82 % of packets | 10 / 10 | true |
| 6 | the same + hold | 5 spans, 120.0 s apart; `uplink_dropped` 9,101; 2.84 % | 11 / 11 | true |
| 7 | `blackout-4s@down` | 5 spans, 120.0 s apart; `uplink_dropped` **0**; 2.90 % | 10 / 10 | true |
| 8 | `none` + hold | no drop of any kind | 11 / 11 | true |

The shim was live under load in every cell. PLAYING came on suite attempt 1 every time, in 4.1-10.2 s.

## 2. Per cell

Over the client session (11.5 min each). Hitch seconds are UX-R3's definition and code (R / C / G / L), per 10 min,
with the longest run. Unattended frames are B2's reader, the core-running count, per 10 min.

| # | rung path (acted) | hitch /10 min (longest run, s) | unattended core-running /10 min | loss /min | rendered fps | resyncs | max output gap ms | client pauses / recovery | host CPU % | encoder % core |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | 7000 throughout | 48.6 (6) | 57.8 | 1,531 | 57.25 | 15 | **11,370** | 1 / 2 desync (`client_output_silence`), 1 encoder restart; **one 27.7-s recovery from 02:38:35Z** | 10.31 | 36.3 |
| 2 | 7000→6000→5500→5000, all `lan_loss` | 19.1 (3) | 143.8 | 85 | 59.32 | 4 | 272 | 0 | 11.70 | 37.0 |
| 3 | 7000→6000→5500→5000, all `lan_loss` | 179.6 (5) | 280.0 | 957 | 52.01 | 4 | 451 | 0 | 10.39 | 36.2 |
| 4 | 7000→6000→5500→5000, all `lan_loss` | 127.4 (6) | 612.6 | 502 | 57.44 | 4 | 606 | 0 | 10.98 | 43.7 |
| 5 | 7000 throughout | 164.7 (**14**) | 1,705.7 | 2,094 | 55.54 | 6 | 4,643 | 5 / 5 desync (`client_output_silence`) | 10.29 | 36.7 |
| 6 | 7000 throughout | 46.8 (5) | 291.0 | 1,719 | 57.63 | 7 | 4,148 | 1 / the hold's rows (§4) + 1 desync | 10.68 | 37.2 |
| 7 | 7000→5000 `recovery_escalation` (FALLBACK, 8.1 min in) | 26.9 (3) | 26.2 | 1,275 | 57.67 | 13 | 4,247 | 5 / 5 desync, 3 encoder restarts | 10.89 | 39.1 |
| 8 | 7000 throughout | 26.0 (2) | 55.9 | 111 | 59.69 | 0 | 395 | 0 / the hold's rows (§4) | 11.52 | 36.8 |

- **Host gates: met in all eight.**
  - RetroArch 59.999;
  - capture 59.948-59.999;
  - dup+drop 0.0-0.1/min;
  - `flags_absent` true (teardown and final).
- The companion took 23.1-25.6 % of a core. The shim took 2.5-3.0 %.
- **Read with care:**
  - **Cell 5's room was worse than the others, outside the blackouts.** It had 154 control gaps ≥ 250 ms over the
    session, against 11 in cell 1, 18 in cell 8 and 41 in cell 6. They were spread across the whole 120-s cycle,
    including 20 in the 97 s before the first blackout.
  - Of its 1,967 core-running unattended frames, only 425 fall inside the five blackout windows. The rest, 1,542, is
    the room's uplink during that cell, not the shim: its gate drops only on the schedule.
  - The per-blackout tables (§3) compare like with like. The per-10-min column does not.
- **Cell 1, the control, held 7000 and had a 27.7-s recovery pause** at 02:38:35Z, inside the window:
  - `client_output_silence` → encoder restart → `resumed`;
  - the client's longest output gap was 11.37 s.
  - Recorded, not explained.

## 3. The blackouts, per blackout (cells 5-7), against UX-R3's death

The death (UX-R3, 04:54:55-59Z):
- the uplink silent 2.65 s of 4 s in five gaps, the longest 967 ms;
- output gaps 410 / 307 ms;
- a heartbeat held ~1.5 s;
- 61 lost after FEC;
- **83.8 unattended frames** (B2's reader).

| cell, blackout (UTC) | uplink gaps (n, longest ms) | client output gap max ms | heartbeat max inter-arrival s | post-FEC lost / unrec groups | unattended core-running (raw) | recovery rows, s after the blackout's start |
| --- | --- | ---: | ---: | --- | ---: | --- |
| 5 b1 03:33:35 | 5, 4,064 | 4,204 | 6.13 | 3,392 / 6 | **96.4** (238.0) | 1.71 desync `client_output_silence`; 6.43 resumed |
| 5 b2 03:35:35 | 2, 4,043 | 4,205 | 6.49 | 3,281 / 8 | **72.7** (227.9) | 1.46 desync; 7.28 resumed |
| 5 b3 03:37:35 | 3, 4,001 | 4,643 | 5.79 | 3,276 / 12 | **87.5** (232.3) | 1.65 desync; 7.30 resumed |
| 5 b4 03:39:35 | 4, 4,051 | 4,171 | 6.02 | 3,247 / 9 | **82.9** (243.2) | 1.38 desync; 8.00 resumed |
| 5 b5 03:41:35 | 2, 4,068 | 4,098 | 6.25 | 3,449 / 11 | **85.7** (231.0) | 1.65 desync; 6.36 resumed |
| 6 b1 03:47:54 | 2, 4,045 | 4,148 | 6.16 | 3,179 / 1 | **7.0** (229.4) | 0.34 **hold**; 1.57 handover → `client_output_silence` (held 1,314); 6.28 resumed; 8.41 hold; 8.54 release (278 ms) |
| 6 b2 03:49:54 | 1, 4,016 | 4,114 | 6.16 | 3,235 / 0 | **5.6** (226.0) | 0.34 hold; 1.26 handover (1,005); 5.98 resumed |
| 6 b3 03:51:54 | 3, 4,018 | 4,146 | 6.12 | 3,412 / 1 | **88.7** (235.4) | **no hold (the cap, below)**; 1.57 desync; 5.70 resumed |
| 6 b4 03:53:54 | 1, 4,008 | 4,137 | 5.95 | 3,236 / 0 | **6.2** (225.4) | 0.35 hold; 1.11 handover (855); 6.33 resumed |
| 6 b5 03:55:54 | 1, 4,008 | 4,107 | 6.17 | 3,239 / 1 | **5.7** (225.5) | 0.35 hold; 1.24 handover (989); 5.98 resumed |
| 7 b1 04:02:35 | 0 | 4,167 | 2.07 | 3,326 / 0 | 0.0 (0.0) | 2.48 desync; 6.09 encoder restart; 7.11 resumed |
| 7 b2 04:04:35 | 0 | 4,161 | 2.08 | 3,224 / 1 | 0.0 | 2.20 desync; 7.30 resumed |
| 7 b3 04:06:35 | 0 | 4,130 | 2.15 | 11 / 0 | 0.0 | 2.45 desync; 5.83 encoder restart; 7.02 resumed |
| 7 b4 04:08:35 | 0 | 4,170 | 2.16 | 3,198 / 0 | 0.0 | 2.56 desync; 6.54 encoder restart; 7.70 resumed (then `recovery_escalation` 7000→5000 at 04:08:47) |
| 7 b5 04:10:35 | 0 | 4,247 | 3.07 | 2,395 / 3 | 0.0 | 2.21 desync; 7.33 resumed |

**Per blackout, the core running without the player:**
- **cell 5: 85.0** (72.7-96.4);
- **cell 6: 22.6**, which is 5.6-7.0 in the four held blackouts and 88.7 in the one the cap skipped;
- **cell 7: 0.0**.

The raw counts are 234.5 / 228.3 / 0. The frozen picture keeps streaming while the core is paused (B2 §2).

**Read plainly:**
- **The bench blackout is the death's shape and harsher.**
  - The uplink was dark the full 4.0 s, not 2.65 s of 4.
  - The client's output gap was ~4.1-4.6 s, not 410 ms; ~3,300 packets were lost after FEC, not 61.
  - The heartbeat went ~6 s without arriving.
- **The core-running count matches the death (85 against 84) for a bench reason, disclosed: B1 lets the client's
  desync POST through.**
  - B1 §1: "Other uplink requests (start, stop, ready, desync) pass."
  - So v2's `client_output_silence` pause landed 1.4-1.7 s into each `@both` blackout, while the link was still
    dark.
  - On a real bidirectional drop that request cannot arrive until the link returns. The bench's ~234 raw frames per
    blackout (B2 expected ~225) is the upper bound of what a real 4-s drop costs without the hold.
- **v2 keeps the core paused 2-4 s past the link's return** in cells 5-7: `resumed` came 5.7-8.0 s after a 4-s
  blackout began.
- **Cell 7, the downlink only:**
  - The controller stream never stopped, so there are 0 unattended frames by definition.
  - The game ran on with input present but **no picture for ~2.2-2.6 s**, until v2's `client_output_silence` paused
    it. The player was pressing at a frozen screen.
  - 3 of 5 recoveries restarted the encoder, and after the fourth the ladder took 7000→5000 (`recovery_escalation`).
  - b3's 11 lost after FEC is as read. Not explained.

## 4. The hold (cells 6, 8)

**Cell 6 (blackouts + `PRIVYHUB_INPUT_HOLD=250`):**
- 21 `desync_pause input_hold`, 16 `resumed input_release` (held median 459 ms, total 7.2 s), 4 `input_hold_handover`
  → `client_output_silence`, 1 `input_hold_cap`.
- The hold fired in every blackout it was allowed in, at age 250.7-253.8 ms. The pause row landed 0.34-0.35 s in.
- **Then v2 took the pause over every time,** 1.11-1.57 s in. The client's desync passed the gate, as in cell 5.
  v2's exit resumed 5.98-6.33 s in, so **no blackout ended in an `input_release`.**
- **The cap skipped b3.** Six holds in 03:51:11-03:51:16Z on the room's own flapping uplink (each a pause / resume
  pair, held 349-573 ms) were followed by `input_hold_cap` at 03:51:17. The blackout at 03:51:54 fell inside
  that 60-s window, ran unheld, and cost 88.7 frames.
- **17 of the 21 holds were outside the blackouts:**
  - the room's own gaps (held 278-610 ms);
  - one at the session's teardown (03:57:49), which was not released.

**Cell 8 (`none` + the hold; the false-trigger check):**
- **18 holds and 18 releases in 11.5 min: 15.6 per 10 min.**
  - Held median 312 ms, range 256-1,335, total 7.9 s.
  - One `input_hold_skipped_paused`, at the teardown.
- **What the idle onn sends when nobody touches the pad:**
  - its whole controller state ~430 times a second, unconditionally (B2 §0, from `NativeControllerSender.sendLoop`);
  - the host saw 18 silences of ≥ 250 ms in it, the longest 1,335 ms (04:24:12Z);
  - the shim dropped nothing, so these are the room's LAN / the onn, not the bench.
- Each fired the hold: a ~0.3-s freeze of an idle game, 18 times.
- Unattended frames (core running) were still 64.5: the 250 ms before each hold lands.

## 5. The loss rule (cells 2-4), every row, against LAN-R1 §3

The times are seconds after the client session started (`session_started`). In brackets: minutes after the
driver's cell start, LAN-R1's own table clock (see §6).

| cell | `lan_loss_rule` rows (s in: windows → the ladder's answer) | steps |
| --- | --- | --- |
| 2 `loss-1` | 49 [4,4] guard; **90 [8,5] transition**; 116 [5,10] hold_down; 182 [5,4] hold_down; **283 [4,5] transition**; **492 [6,4] transition** | 7000→6000 **1.49 min** (3.9); →5500 4.71; →5000 **8.19 min** (10.6) |
| 3 `loss-5` | 15 / 35 guard [57-66]; **55 transition**; 81-162 hold_down ×5 [36-59]; **182 transition**; 208-289 hold_down ×5; **309 transition** | →6000 **0.92 min** (3.3); →5500 3.03; →5000 **5.15 min** (7.5) |
| 4 `burst-50x20` | 14 / 34 guard [25,12 / 9,21]; **54 transition** [4,19]; 80-165 hold_down ×5; **185 transition**; 213-295 hold_down ×5; **316 transition** | →6000 **0.90 min** (3.3); →5500 3.08; →5000 **5.26 min** |

- **The rule asks as soon as its windows fill.** Its first asks come 14-49 s into the session and are refused by the
  60-s session-age guard. It acts at the first ask after the guard, then once per hold-down, about every 2.1 min in
  cells 3-4 and 3.2-3.5 min in cell 2.
- The time to 5000 is the hold-down's cadence, not the loss level. 5 % reached 5000 sooner than 1 % only because
  its asks never missed.
- **Cell 4 against G8-S1 cell 07** (the same profile, the flag absent):
  - G8-S1's `capacity_mild` came 3 min 07 s after PLAYING; LAN-R1's replay put the rule 2 s before that.
  - Here the rule stepped **54 s** after the session started, about 2 min 13 s earlier.
  - With the rule on, no `capacity_mild` came, so there is no same-run pair.
  - A 50-packet burst every 20 s puts ≥ 4 unrecoverable groups in every 10-s-report window, so the rule fires at the
    guard's first chance.
- **Cell 1 (the rule off):** 7000 throughout, no transition, as G8-S1 cell 03.

## 6. The pre-registered expectations and the reading, applied as hashed

| # | written beforehand | result |
| --- | --- | --- |
| 1 | cell 1 at 7000 throughout, as G8-S1 cell 03 | **MET** (with the 27.7-s recovery, §2) |
| 2 | cells 2-3: first `lan_loss` step 3-4 min **into the stream**, 5000 by ~8-11 min | **NOT MET.** First step 1.49 / 0.92 min. 5000 at 8.19 (in range) / 5.15 min (early). |
| 3 | cell 4: the step ~2 s before `capacity_mild` (G8-S1 cell 07's step) | **NOT MET.** 54 s into the session, ~2 min 13 s before G8-S1's point. |
| 4 | cell 5 reproduces the death's shape per blackout: uplink gaps ≥ 250 ms, output gaps ≥ 200 ms, a heartbeat hold, FEC-unrecoverable loss | **MET**, 5 / 5 blackouts (harsher, §3) |
| 5 | cell 6 cuts unattended frames (core running) per blackout by ≥ 90 % against cell 5, with exactly one hold and one release per blackout | **NOT MET.** −73.4 % (22.6 against 85.0). Holds per blackout 2 / 1 / 0 / 1 / 1, releases 1 / 0 / 0 / 0 / 0 (4 handovers to v2, 1 capped). In the four held blackouts −92.8 %. |
| 6 | cell 7: unattended frames ~0; whether the game runs on, stated | **MET** (0.0). The game ran on, without a picture, ~2.2-2.6 s per blackout until v2 paused it. |
| 7 | cell 8 shows 0 holds per 10 min | **NOT MET:** 18 holds (15.6 / 10 min) |

**The reading, as hashed:**
- *"If 6 cuts unattended frames by ≥ 90 % with 0 false holds in 8"*: neither.
- *"If 8 shows holds on a clean link: the hold is not a candidate until its trigger is fixed"*: **this applies.**
  **The hold is not a candidate.** No adoption question arises for it.
- *"If 2-4 do not match LAN-R1's prediction: the thresholds were in-sample and the rule goes back to B"*: **this
  applies. The rule goes back to B.** No adoption question arises for it.

**Disclosed, against the hashed wording; the result stands:**
- **The clock in expectation 2.** The pre-registration says "into the stream". That is session A's paraphrase of LAN-R1
  §3's "3-4 min in".
- LAN-R1's own table measures "after the cell's start", the driver's cell start, which includes the suite's 120-s
  idle gap and the launch.
- On that clock, cell 2 steps at 3.9 min and reaches 5000 at 10.6 min, inside the prediction. Cell 3 steps at 3.3 min
  and reaches 5000 at 7.5 min, just under it.
- The hashed wording is the one applied. The user may weigh the other clock. Cell 4's miss holds on either clock
  (3.3 against 5.5 min after the cell's start).
- **B1's desync gate.** Expectation 5's comparison runs against a cell 5 whose core was already paused by v2 ~1.5 s
  into each blackout, because the desync POST passes the bench's uplink gate. Against the raw ~234 frames a real
  4-s drop would run unheld, the four held blackouts' ~6 frames would be −97 %.
  - The hashed bar (core running, against cell 5) is the one applied.

**For B, what the hold's trigger needs (from §4; the user's call what B takes):**
- **The false holds:** a 250-ms silence happens 15-16 times per 10 min on this idle LAN (cells 6, 8). That is what
  the user's room does, and the reading names it the hold's fault.
- **The cap:** six such holds in a flapping minute disarm the hold for the next blackout.
- **The release:** v2's `client_output_silence` takes every real-blackout hold over ~1 s in, and holds the core
  ~2 s past the link's return.

**For B, the LAN rule:**
- it fires at the session-age guard's first chance on 1 % random loss (the cost LAN-R1 named);
- its replay timing did not transfer.

**For B1 (the bench):** gate the client's desync request on `@both` too, so the bench's blackout is the real one.

## 7. Files

- **`bench_r1_2026-10-22/`:**
  - the driver's (launch record §6) and `cells.jsonl`, `bench_r1_state.json`, `runs/` (8 cells);
  - **`logs_bench/`** (the five logs over the run, `copied_at.txt`);
  - **`record/`:** `bench_r1_record_read.py`, `unattended_frames_at_b909735.py`, `record_read.json`,
    `record_read_console.txt`, `unattended_<cell>.json` ×8, `manifest.sha256`;
  - each cell's client report, added under `runs/<cell>/logs_run1/decoder_sessions/`;
  - `redact_check_record.txt`.
- **Elsewhere:**
  - `docs/KNOWN_ISSUES.md` (the top item), `docs/ROADMAP.md` (§G8, one line), `docs/memory/CURRENT.md` (Next Action);
  - `logs/bench_r1_git_status.txt`.
- **At the end:** `tools/e3_state.py --check` ok on the eight lines, no `e3_flag.conf` (`record/check_at_record.json`).
- No sudo, no nft, the Opal untouched, adb only read (`--check`), nothing fetched, deleted, adopted or committed.
