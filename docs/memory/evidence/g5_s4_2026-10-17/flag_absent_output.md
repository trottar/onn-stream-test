# G5-S4 — flag absent, byte for byte (re-runs with the cap code present), 2026-10-17T00:41:31Z

`PRIVYHUB_REMOTE_RUNG_CAP` and `PRIVYHUB_REMOTE_LADDER` absent in the process unless a harness sets G5-S3's globals.

1. **G5-S3's `flag_absent_proof.py`, re-run** (`g5_s3_proof_rerun/`): the actuator HEAD vs edited
   identical: **200** of 200; the games plugin's stream start 3 / 3
   identical; G5-S2's replay re-run: recorded decisions exact and HEAD's vs the edited `LiveController`
   (now carrying the cap's hooks too) identical; its WAN tables equal G5-S2's.
   -> -> flag absent: **PASS**
2. **G5-S3's `replay.py`, re-run with the cap absent and G5-S3's flag on** (`g5_s3_replay_rerun/`):
   `replay_tables.json` equal to G5-S3's recorded one (20 run x path x rules entries): **yes**;
   `replay_output.md` byte-identical: **yes**.
