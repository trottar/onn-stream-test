---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G8-S1 stop (session A): end the detached driver `privyhub-g8-s1` cleanly through its STOP file, confirm the adopted state, write G8-S1's record as PARTIAL from the cells the driver completed, and leave the remaining cells resumable. Measurement only; nothing adopted; nothing committed; the driver is not relaunched
---

# G8-S1 — stop, and the partial record

Context: `evidence/G8_S1_LAUNCH_2026-10-16.md` (the driver, its files, the pre-registration `g8_s1_2026-10-16/g8_s1_preregistration.txt` with hash `b2e02fa0…dcf73` — unchanged, the record is written against it), `g8_s1_2026-10-16/cells.jsonl` (one row per completed cell), `runs/<cell>/` (each cell's suite output, `wan_poll_run<n>.jsonl`, `impairment_run<n>.jsonl`). The user is on a phone and cannot reach the PC's shell: this session is the hand.

## 1. Stop (through the driver's own mechanism only)

1. `touch ~/privyhub_g8_s1/STOP`. Then poll `~/privyhub_g8_s1/status.txt` every 30 s until its `doing:` field reads
   `EXITED (the stop file)` — the cell in flight finishes first, so allow up to 16 min. **No kill, no
   `systemctl --user stop`, no companion restart** beyond what the driver's own teardown does: killed mid-run it
   could leave the drop-in and the stream up.
2. If `EXITED` has not appeared after 20 min: copy what `status.txt` says into the record's §1, say so, and stop
   (no record §3; tell the user).
3. `systemctl --user status privyhub-g8-s1` → inactive (the transient unit is collected; "could not be found" is
   that). Copy `~/privyhub_g8_s1/status.txt`, `history.csv` and `driver.log` into `g8_s1_2026-10-16/` as
   `final_status.txt`, `history.csv`, `driver.log`. The STOP file stays (the driver never removes it); note that a
   resume must remove it first.

## 2. The state

`tools/e3_state.py --check` ok: the seven adopted lines, no `e3_flag.conf`, no `e4_constraint`, no stream, no
RetroArch or encoder process, one device paired; the last `cells.jsonl` row's `flags_absent_after` and
`final_flags_absent` true. Any miss is written and the session stops.

## 3. The record — `evidence/G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-16.md`

**Classification: PARTIAL — n of 22 cells, stopped by the user's STOP file at <UTC>.** Written from the driver's
files, against the pre-registration as hashed (nothing in §1 of the pre-registration is reinterpreted).

- **Per cell, a table** of the pre-registered reported fields: validity (and any `profile-not-applied` repeat),
  PLAYING attempt and s_to_playing, host gates (RetroArch, capture, dup+drop — met or not, each), host CPU,
  the companion's cost, the shim's cost, pre-/post-FEC loss per min, FEC recovered / unrecoverable groups (from
  the run's telemetry; say the field), rendered fps, stale/min, spikes/min, resyncs, client pauses, the rung path
  (min–max and the polls), `rules_suggestions` (decisions with `source: wan_rules`, by rule id), the `wan` class
  and window counts, the shim's counters (in / dropped by kind / delayed / reordered / queue max).
- **`resyncs`:** cell 1's `cells.jsonl` row says 0 while its teardown report says `video.sequence_resyncs` 1. Say
  which source the driver's field reads, report both columns for every cell, and name the discrepancy; do not
  pick one silently.
- **The pre-registered comparisons, as far as the completed cells allow:** (i) `none` (off and on) vs CL-B3's R1
  and W — the shim's cost on the stream, host and link side, numbers side by side; (ii) per completed profile,
  off vs on: what the rules suggested and whether rendered / stale / loss moved — **stated, not judged**; (iii) the
  classifier check: class assigned vs the profile's intent, a table for the profiles done.
- **Reported:** the link's own loss tonight (the `none` cells), any session loss or recovery event (`recovery.jsonl`,
  `gaps.jsonl`), the ladder under any cap cell that completed.
- **Not run:** the remaining cells listed by number, profile and arm, "not run — resume".
- **Resume:** read `g8_s1_driver.py`: does a relaunch with `g8_s1_state.json` present skip the cells in `done`?
  State the answer from the code, and what a resume needs (remove STOP; a new cap — the cap is a constant in the
  driver; the same unit name). Do not relaunch.
- `manifest.sha256` over `g8_s1_2026-10-16/` (now complete), `validity.json`, the redactor over the whole directory
  including `runs/` (the benign rule as the launch record used it), `redact_check.txt` replaced.

## 4. The rest

- `docs/ROADMAP.md` §G8 status line: "envelope: n/22 cells measured (partial, <date>); resume pending".
- `logs/g8_s1_stop_git_status.txt`.
- `CURRENT.md`: the state line (seven lines, nothing running), Next Action: the user's commit (the launch, the
  shim's `none` profile, this record); the G8-S1 resume as a later task; **the off-site test (G4-S1) is no longer
  blocked by the driver**. Nothing adopted; nothing committed. Exit.
