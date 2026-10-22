---
memory_schema: 1
as_of: 2026-10-22
status: TASK HANDOFF — BENCH-R1 (session A, hardware, unattended: the TV and the onn on and idle, nobody plays; after session B's QUEUE_2026-10-22B has landed and the user has committed it): the death reproduced on the bench and the two fixes measured against it. One detached driver: the LAN loss rule on the shim's loss cells (LAN-R1's out-of-sample test), then the blackout cells with the input hold off and on. Measurement only; nothing adopted; nothing committed
---

# BENCH-R1 — the bench run: loss cells, blackout cells, the hold

Read first: `SESSION_B_DONE_2026-10-22.md` and the three B records (`B1_SHIM_BLACKOUT_BOTH_…`, `B2_INPUT_HOLD_…`, `B3_CLIENT_LINK_REPORT_…`) **for the exact flag names and profile strings — use theirs, not this file's spelling if they differ**; `LAN_R1_LOSS_STEPDOWN_2026-10-21.md` §3 (the prediction: loss-1 and loss-5 step down 3-4 min in and reach 5000 by ~8-11 min; burst-50x20 ~2 s before `capacity_mild`; flag absent as G8-S1), `UX_R3_…` (the hitch definition, §1; the death's numbers), `G8_S5_…` / `g8_s5_driver.py` (the scaffolding, the encoder read-back, the frame-log copy), `G8_S1_…` §2c (loss-1 / loss-5 / burst-50x20 at 7000 with the flag absent — the comparison rows).

**If B2 stopped at "the client sends only on change":** the blackout cells still run (hold absent only), and §1's hold arms are recorded "not built"; the record says so.

## 1. Pre-registration (hashed before the first cell)

**Cells**, each E1-PS1-STREAM `--e2 --window 600`, the suite launching the title, a 120-s gap, a 7000 start (no `START_RUNG`), `e3_flag.conf` per cell read back under load and removed at teardown with `flags_absent` true:

| # | shim profile (`PRIVYHUB_IMPAIRMENT=…@post-fec,seed=1`) | other flags | question |
| --- | --- | --- | --- |
| 1 | `loss-1` | — | LAN-R1's control (G8-S1's row again on today's HEAD) |
| 2 | `loss-1` | `PRIVYHUB_LAN_LOSS_RULE=1` | the rule out of sample: first step at 3-4 min, 5000 by 8-11? |
| 3 | `loss-5` | `PRIVYHUB_LAN_LOSS_RULE=1` | the same under 5 % |
| 4 | `burst-50x20` | `PRIVYHUB_LAN_LOSS_RULE=1` | steps ~2 s before `capacity_mild`? |
| 5 | `blackout-4s@both,every=120s` | — | **the death reproduced**: per blackout, the uplink gaps, the output gaps, the heartbeat hold, the loss — against UX-R3's numbers; **unattended frames** per blackout (B2's reader) |
| 6 | `blackout-4s@both,every=120s` | `PRIVYHUB_INPUT_HOLD=250` | the hold: `input_hold` / `input_release` rows per blackout; unattended frames per blackout (expected ≈ 15 against ~240); the time held; recovery v2's rows (none expected beyond the hold's own); the core resumes on release (frames flow within one report) |
| 7 | `blackout-4s@down,every=120s` | — | the downlink only: does the game run on with input present (unattended frames ≈ 0 by definition) — the control for "it is the missing input that kills" |
| 8 | `none` | `PRIVYHUB_INPUT_HOLD=250` | **the hold's false-trigger check on a clean link**: holds per 10 min must be 0 (the suite's own input is none, so a continuous controller stream from the idle onn is what is tested — state what the onn sends when nobody touches the pad; if the hold fires here, the hold is wrong, not the link) |

- **Validity:** as G8-S1 / G8-S5 (the shim's profile applied by its counters, `uplink_dropped` on the `@both` cells; `flags_absent` after). A `no_play` cell is an outcome.
- **Gates (host):** the four as always.
- **Reported per cell:** the rung path and every decision with its reason (the `lan_loss_rule` rows in 2-4); **hitch seconds per 10 min and the longest run** (UX-R3's definition, the same script); **unattended frames** per blackout and per 10 min (B2's reader); the hold rows and the time held (6, 8); the per-blackout table in 5-7 (uplink gaps, output gaps, heartbeat hold, loss, the recovery log); post-FEC loss, rendered, resyncs, max output gap; host CPU and the encoder's.
- **Written beforehand (met / not met, not gated):** cells 2-4 as LAN-R1 §3 predicts; cell 1 at 7000 throughout as G8-S1; cell 5 reproduces the death's shape (uplink gaps ≥ 250 ms inside each blackout, output gaps ≥ 200 ms, a heartbeat hold, FEC-unrecoverable loss); cell 6 cuts unattended frames per blackout by ≥ 90 % against cell 5 with exactly one hold and one release per blackout; cell 8 shows 0 holds.
- **The reading, written beforehand:** if 6 cuts unattended frames by ≥ 90 % with 0 false holds in 8, the hold is a candidate — the user's call to adopt, with its cost (up to 250 ms of unattended game per event; the picture frozen while held) stated; if 8 shows holds on a clean link, the hold is not a candidate until its trigger is fixed; if 2-4 match LAN-R1's prediction, the rule is a candidate for the sustained-loss case, with LAN-R1's random-loss cost stated; if they do not, the thresholds were in-sample and the rule goes back to B.

## 2. The driver and Code's steps

- Precondition: the eight lines, `--check` ok (adb reconnected by hand if needed, the endpoint never printed), no `e3_flag.conf`, no game, one device paired, no `privyhub-*` unit but the companion, HEAD named (B's queue committed by the user), the tree clean but the prompt and this file.
- `bench_r1_2026-10-22/bench_r1_driver.py` from `g8_s5_driver.py`'s scaffolding (eight cells; the status file `~/privyhub_bench_r1/status.txt`, `STOP`, the busy skip, **cap = launch + 3 h, written in the pre-registration**); a 2-min `--dry` on cell 6's flags; the pre-registration hashed; the tool hashes (`impairment.py`, `lan_loss_rule.py`, the input-hold module, `adaptive_bitrate_live.py`, the recovery module, `native_session_io.py`, `native_stream.py`, the suite, the driver); launch under `systemd-run --user --unit=privyhub-bench-r1 --collect`; confirm cell 1's preflight passed; **exit** — the record is a later one-line task (eight cells ≈ 1 h 50 min). `evidence/BENCH_R1_LAUNCH_2026-10-22.md`, `logs/bench_r1_launch_git_status.txt`, the redactor.
- The record (later): `evidence/BENCH_R1_BLACKOUT_AND_LOSS_CELLS_2026-10-22.md` + the directory (the heartbeat and control-gap logs copied in — they rotate), the per-cell tables, the reading applied, `KNOWN_ISSUES.md`, ROADMAP lines, `CURRENT.md` Next Action (the user's commit; the adoption questions as the reading gives them; then the user plays, wherever they like).

No sudo (systemd --user is not sudo), no nft, the Opal read-only, adb only for state reads, no addresses or identifiers; nothing fetched, nothing deleted; nothing adopted; nothing committed; the eight lines only and no `e3_flag.conf` when the driver closes.
