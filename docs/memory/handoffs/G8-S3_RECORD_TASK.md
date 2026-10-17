---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G8-S3 record (session A): the record of the three cap cells with the start rung, from the driver's files (`g8_s3_2026-10-17/`, closed "all 3 cells done" 18:21:36Z). Measurement only; nothing adopted; nothing committed; the driver is not relaunched
---

# G8-S3 — the record

Read first: `G8-S3_CAP_CELLS_START_RUNG_TASK.md` §1 (the pre-registration, hashed `e3f0675a…`: the predictions, the reported set, the comparisons), `G8_S3_LAUNCH_2026-10-17.md`, `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §5 (the no_play reading; cells 17–19 as the counterparts), `G8_S2_START_RUNG_2026-10-17.md` (the bench: 5000 enters at ~6.1 Mbit/s, ~2 % drop under cap-6000; the 8.25 / 7.0 ratio).

## 1. Precondition

The unit `privyhub-g8-s3` collected; `~/privyhub_g8_s3/status.txt` reads EXITED (all 3 cells done) — copy it, `history.csv` and `driver.log` into the directory; `--check` ok on the seven lines, no `e3_flag.conf`, no game, one device paired. The tree is committed through G8-S2 plus the launch's uncommitted files (HEAD named; touch nothing).

## 2. The record — `evidence/G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md`

**Classification: MEASURED — cells 1 and 2 reached PLAYING at the 5000 start (9.1 s, 7.1 s, first attempt; valid); cell 3 `no_play` as predicted.** Then, reported, not judged:

- **Per cell, the pre-registered set** (a table): the start rung and its source from the first decisions row; PLAYING (attempt, s); the rung path and every acted transition with its reason (none expected — say why from the code: 5000 is the LAN list's floor, nothing below it to step to); the rules' suggestions by rule id (cell 2); post-FEC loss/min, FEC recovered / unrecoverable, rendered, stale, resyncs, pauses; the `wan` class and windows; the shim's counters (in / out / dropped_queue / queue_max); host gates (met or not); `flags_absent_after`.
- **The comparison with G8-S1's cells 17, 18, 19** (the same profiles at a 7000 start): PLAYING vs none; drop fraction 6.5 % / 8.6 % / 27.8 % here vs 27–30 % / 45–48 % there; rendered 53.1 / 36.6 / — ; one table.
- **The live wire rate at the 5000 rung, from the files, vs the bench:** the shim's per-second bytes in (`impairment_run1.jsonl`) give the input rate over the window — compute it and the drop fraction per second; the bench said ~6.1 Mbit/s and ~2 %, the live cells show 6.5 % / 8.6 % dropped, so the live input exceeds the bench. From `encoder.jsonl` (the encoder's actual output bitrate at the 5000 target over the window), the FEC sender's overhead (8+1 → ×1.125) and the audio stream's rate, account for the wire rate term by term as far as the files allow — a table of measured terms, with any residual named as unexplained. State which term differs from the bench's synthetic source (the bench fed 5000 kbit/s exactly; an encoder at a 5000 target may run above it — read `encoder.jsonl`'s bitrate distribution: mean, p95, the share of seconds over 5000).
- **Cell 1 vs cell 2 (rules off vs on):** cell 2 was worse (loss 3,245 vs 2,379/min, rendered 36.6 vs 53.1, class latency-limited vs capacity-limited); the rules' rows (what they suggested, what the ladder did — at the floor it can only hold); the shim dropped more in cell 2 (8.6 % vs 6.5 %), so the input was higher — read whether the encoder's output differed between the two cells before attributing anything to the rules. Stated side by side; no cause chosen.
- **Cell 3 (`cap-4500` at 5000):** the G8-S1 §5 reading (attempts, the client's last state, the shim's counters: 64,745 of 233,226 dropped = 27.8 %, the bench said ~29 %); the prediction held.
- **What the files say about "settling under a cap":** at the LAN floor the ladder has nowhere to go; the stream stayed up for the whole window at 2,400 loss/min and 53 fps. Whether that is playable is the user's judgement, not the record's.

## 3. The rest

- `manifest.sha256`, `validity.json`, the redactor over the whole directory (`.pyc` excluded), `redact_check.txt` replaced; `logs/g8_s3_record_git_status.txt`.
- ROADMAP §G8: "start rung: PLAYING reached under cap-6000 at the 5000 start (G8-S3); the 5000 rung's live wire rate exceeds 6 Mbit/s; cap-4500 needs a rung below 5000, remote-only today".
- `CURRENT.md`: the state line; Next Action: the user's commit; **options, not decided here:** (a) G4-S2 off-site with G5-S3 + G8-S2 (`START_RUNG=floor` → 4000 on the remote path) — the first real test of a 4000 start; (b) a wire-overhead measurement task (session B): the per-rung wire rate measured, not the 1.18 ratio, so the floor / cap arithmetic uses real numbers; (c) whether a LAN rung below 5000 should exist (C5-M3 screened 720p/4000 as passing transport; the LAN list stops at 5000 by C3-L4's validation) — the user's call. Nothing adopted; nothing committed. Exit.
