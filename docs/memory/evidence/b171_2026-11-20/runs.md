# B171 — the one run of `rehearse T88 --collect other=2` (the queue's exception; after `status` and
# `native-stream-status` showed nothing running and no client; headless, nothing streamed, no restart, no flag)

| run | the code | the tool's verdict | not met | what it showed |
| --- | --- | --- | --- | --- |
| 1 (00:54:19-00:56:46Z, 2 min 27 s) | B171 + B172 (this queue's diff) | **FAIL (20 cells)** | learn: separable [end_P1, end_P2], margin_needed 0.0165 (bar 0.0796), held-out unknown 0.6552 (bar 0.105), end_P1 / end_P2 replays not ended, learn's verdict; the four endings' scratch-vs-real cells (no scratch spec: learn failed) | **the usable kept endings are end_p1 and end_p2 only**: end_p1_b / end_p2_b captured first and read by the real rules — never ended on (`[null, null]`), "not an end screen to the real rules", kept read, not a role; **learn's line: "One more save: end_P1_2 — … then rehearse T88 --collect end_P1_2=<slot>."**; below two saves per ending: end_P1_2, end_P2_2 |

**The real rules folder 15 files, 0 changed** (the tool's cell, met); **the scratch removed** (met); my own check of the
kept folder and the rules folder together (22 files, sha256 of the sorted list) before = after. The user's slot 2 only
read — **its copy kept by the tool in the title's add_game folder** (`kept/other.state`, off the repo; B171), so a later
rehearse needs no slot for `other`. The tool's page in this repo (`add_game/T88/rehearse.*`) now holds this run's
verdict (run 6 of queue BD is in `6d4a6c44`). Nothing else started a title.
