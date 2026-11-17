# B126 — design amendment 1 (written and hashed before the runs it adds; after the first runs, disclosed)

**What the runs showed:** (a) the fold learnt from V1 + C2 without LIVE does not separate the start (gap -0.009, the
start's worst own 0.2103) and its screen threshold widens to 0.1547 (worst own 0.1336): all 73 live start pictures
`unknown` and **one live fight read as the screen** (class `unknown`, never an end); (b) C2's start pictures 4-7 read
`unknown` / `other` under every spec — RetroArch's notices (the cheat applied, the pads configured) still cover the
screen there; Cowork's labels mark only pictures 1-3 `ignore`.

**Added (diagnostics only; Cowork's labels file unchanged on disk; the tool unchanged):**

- **A1.1** the same folds and the three-source learn with **C2's pictures 4-7 set to `ignore` in memory** (the labels'
  first `start` range starting at 7.02 s instead of 3.02 s): V1 + C2' → LIVE; LIVE + C2' → V1; V1 + LIVE + C2' → each
  source; the tone grid on held-out C2' (V1 + LIVE + C2' first halves → C2' second halves). Reported beside the runs on
  Cowork's labels as they stand — the numbers of record stay the as-labelled ones.
- **A1.2** the screen distances of C2's start pictures 4-7 under V1 + C2 (which picture widens the threshold).
