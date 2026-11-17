# Steps 3-4 against `b126_2026-11-17/h7v5_expected/` (number for number)

- **T88's spec learnt** (three pairs: H7-V1's frames, H7-V2's live run, H7-C2's T88 run): the learn report equals B's in **every key but `learn_s`** (the seconds the learn took: 12.92 vs 12.93) — 55 keys.
- **T89's spec learnt** (H7-C1's and H7-C2's T89 runs): equal in **every key but `learn_s`** (7.36 vs 7.37) — 71 keys.
- **T88's score:** equal in every key but `read_ms` (median 1.73 vs 1.71, worst 200.62 vs 205.95 ms — the reading speed); `other_read_as_screen` 0.
- **T89's score:** equal in every key but `read_ms` (median 2.89 vs 2.95, worst 186.55 vs 187.67 ms); `places_wrong` 0, `other_read_as_screen` 0.
- **The replays:** every `ended` and summary line **identical byte for byte** — T88: one end_P1 at 46.02 s on H7-C2's run; end_P1 153.03 s and end_P2 419.02 s on H7-V2's; T89: one `end` places [1, 2, 3, 4] at 43.02 s on H7-C2's run; five on H7-C1's, places [1, 2, 3, 4], [4, 1, 2, 3], [3, 4, 1, 2], [3, 4, 2, 1], [1, 3, 2, 4].
- The `.npz` arrays not compared by hash (B: not byte-reproducible). The reports, scores and the replays' end lines in `learn_score/`.

**Steps 3-4 met.**
