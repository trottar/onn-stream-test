---
memory_schema: 1
as_of: 2026-10-23
status: TASK HANDOFF — CL-B10 PART 2 (session A, attended: the user at the TV with the phone; three stages, one paste each). Part 1 is done: `PRIVYHUB_LINK_REPORT=1` is the ninth adopted line (G-A3, VALID), `da09e154…` is installed and paired, cells 2 and 3 ran detached and closed "playing valid" at 19:11Z (`cl_b10_2026-10-23/cl_b10_state.json`), the properties `restart_guard` / `stall_signal` / `link_notice` / `link_report` are still 1. This part: cell 1 (5 GHz, the user presses Home ~4 min in), cell 4 (the user switches the onn to 2.4 GHz by hand for the notice, and back while the stream runs), then the properties cleared, `--check` on nine, the CONFIRMED rule for `da09e154…`, and the record for all four cells. Measurement only; nothing adopted; nothing committed
---

# CL-B10 PART 2 — the restart guard and the notice, attended

Read first: `handoffs/G-A3_AND_CL-B10_TASK.md` PART 2 (the cells as written there — this file only adds the staging), `CL_B10_LAUNCH_2026-10-23.md` (§1 how the driver is read; §4 the driver and the properties; the stale `privyhub_bench_r3` STOP string — fix it in this part's driver), `cl_b10_2026-10-23/cells.jsonl` and `runs/` (cells 2 and 3, to be read in stage 3), `SESSION_B_DONE_2026-10-23E.md` items 6-9 and `B11_…` / `B14_…` (the exact rows: `restart_cause.away_ms`, `session_ended` before the new start, `link_notice_shown` reason 1, `link_notice_cleared`, the notice strings), `CL_B7_…` §6 (the CONFIRMED rule), `LINK_N1_LAUNCH_2026-10-23.md` (no companion restart 04:30-05:30Z; no cell starting after 04:15Z).

**The stage is the user's message.** The read line alone = stage 1. "Stage 2 …" / "Stage 3 …" = those stages; the user's words in that message are evidence and go into the record verbatim.

## Stage 1 — cell 1, the restart guard (5 GHz)

- Precondition: nine lines, `--check` ok except the APK reading `MISMATCH` by the pin rule (expected; `da09e154…` on the onn, paired), no `e3_flag.conf`, no game, no `privyhub-*` unit but the companion and `privyhub-link-n1` (`privyhub-cl-b10` closed — confirm from `cl_b10_state.json` `closed_by`), the properties read back still 1 (if any reads empty: the onn rebooted — set the three again and `link_report 1`, disclose), **the band read: 5 GHz** (else stop and tell the user), HEAD named (G-A3 and the Part 1 files committed by the user — if the tree holds them uncommitted, stop and say so), the clock outside 04:15-05:30Z.
- **Pre-registration for Part 2** hashed before the launch: cell 1's and cell 4's rows as PART 2 states them, the validity rule, the CONFIRMED rule, the cap (launch + 40 min per cell).
- **The driver:** `cl_b10_2026-10-23/cl_b10_p2_driver.py` from `cl_b10_driver.py`, one cell per launch (`--cell 1` / `--cell 4`), unit `privyhub-cl-b10-p2`, status `~/privyhub_cl_b10/status.txt`, STOP `~/privyhub_cl_b10/STOP` (**the status text and the log tag corrected to this path**), the properties read back before and after each cell and **not cleared** (stage 3 clears them), each cell's drop-in removed at its teardown, `flags_absent` after, nine lines. It reads the band from the onn every 10 s through the cell into the cell's dir (frequency / band / RSSI / tx / rx only, the endpoint never printed).
- **Cell 1:** E1-SNES-STREAM (snes9x), `--e2 --window 600`, drop-in `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1` only (the nine lines plus one). Launch, confirm the preflight and PLAYING, then **print for the user, in the reply: the PLAYING time in UTC and in US Eastern, and the minute (Eastern) at which to press Home = PLAYING + 4 min.** The user plays from PLAYING; at that minute they press Home, wait ~5 s, return to the game, keep playing to the end (~PLAYING + 10 min). Exit. The reply must contain: the band, the properties, the unit name, the PLAYING time, the Home minute.

## Stage 2 — cell 4, the notice (2.4 GHz)

The user's message says the onn is on 2.4 GHz now (their hand, after cell 1's window ended).

- `privyhub-cl-b10-p2` closed, cell 1's dir complete; **the band read: 2.4 GHz** (else stop and tell the user the swap did not take). The properties still 1. The clock outside 04:15-05:30Z.
- **Cell 4:** the same driver `--cell 4`, `--window 780`, drop-in `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1`. Launch, confirm PLAYING, then **print for the user: the PLAYING time (UTC and Eastern) and the minute (Eastern) at which to switch the onn back to 5 GHz = PLAYING + 10 min, with the game still running.** The notice should be at bottom-left within the first seconds of PLAYING. Whatever the switch does to the stream (a drop, the client's self-restart under the guard, a new session) is recorded as it comes; `link_notice_cleared` is looked for in whichever session runs from ~30 s after the band reads 5 GHz to the window's end. Exit. The reply must contain: the band, the unit, the PLAYING time, the switch-back minute, and the sentence "look bottom-left now".

## Stage 3 — the close, the rule, the record

The user's message carries their word on the notice (seen or not, when, the words on screen, or that a photo exists) and their one line on the Home-and-back.

- `privyhub-cl-b10-p2` closed, cell 4's dir complete, the band read (5 GHz expected; stated as read).
- **The properties cleared** (`setprop` to empty for `restart_guard`, `stall_signal`, `link_notice`; **`link_report` cleared too** — absent = on with `da09e154…`) and read back empty; nine lines; no `e3_flag.conf`; `flags_absent`.
- **The CONFIRMED rule as CL-B7 §6 applies it** (the property-empty / flag-absent behaviours as today, with B13's one intended difference: the link keys present with `link_report` empty). All four cells valid and the behaviours as today → `da09e154…` CONFIRMED (the pin moved where §6 moved it, `--check` ok on nine with no MISMATCH). Else `bf5114a2…` reinstalled from `cl_b10_preserved/`, read back, paired, `--check` ok, and the user told which cell failed and why.
- **The record `evidence/CL_B10_RESTART_GUARD_STATE_STALL_NOTICE_2026-10-23.md` + `cl_b10_2026-10-23/`** (the dir grows; `manifest.sha256` over all of it):
  - **cell 2** (`@both`): per blackout `state_saved` kind silence ~0.40 s in, `input_release` method `state`, playing after, `--net` ≈ 24 (B's number; the table per blackout), the resume ≤ 1 heartbeat after the return, no second `desync_pause`, no `session_started`; met / not met per row;
  - **cell 3** (`@down`): `state_saved` kind stall, the pause 400-460 ms after the client's last frame, no `encoder_restart`, no `recovery_escalation`, one `resumed via client_ready_stall` / `stall_end` with the load, net ≈ 9-12, `stall_end_late`, no second pause; per blackout;
  - **cell 1:** the Home press found (the surface loss, the old report + `session_ended` before the new start, `restart_cause.away_ms`, the new session's underruns against the others' — not ~170 / s), `link_notice=0` throughout, silences ≥ 250 ms and hitch s / 10 min against LINK-R1 / G-A3 (0 / 0.9), the user's line;
  - **cell 4:** the band per 10 s, `link_notice_shown` reason 1 and its second, the user's word or photo (**the user's word is the gate on "shown" — the row alone is not**), 10 min of 2.4 GHz with silences and hitch s per 10 min **against cell 1's on 5 GHz in the same hour** (the A/B LINK-R1 could not make), the switch-back as it came, `link_notice_cleared` and its delay after the band read 5 GHz;
  - the reading applied (the hold / state / stall stack a candidate on SNES or back to B, with the costs; the guard; the notice), the CONFIRMED decision, the APK on the onn named.
  - `docs/KNOWN_ISSUES.md`, ROADMAP lines, `logs/cl_b10_git_status.txt`, `redact_check.txt`; `CURRENT.md` Next Action: the user's commit; the three adoption questions each with its cost (the stack on SNES; the loss guard `PRIVYHUB_LOSS_GUARD=1` + `loss_guard=1`; the notice as a client default); "read LINK-N1's nights" after a few nights; the user's own play on 5 GHz with everything in force.

No sudo, no nft, the Opal read-only (both band switches are the user's hand), adb for the `setprop`s named, the reinstall if the rule says so, and state reads only; no addresses or identifiers anywhere; nothing fetched, nothing deleted; nine lines and no `e3_flag.conf` at every teardown; nothing adopted; nothing committed.
