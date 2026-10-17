---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d
durable_memory_updated: true
---

# G4-P2: the remote row records gate 3

## Purpose

G4-S1's gate 3 (RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2 / min) was not
evaluable: the remote row recorded neither the FPS counter nor the encoder's
progress. Record: `evidence/G4_P2_REMOTE_ROW_GATE3_2026-10-17.md`.

## Change

- **`tools/e1_remote.py`** (predecessor and after sha256:
  `g4_p2_2026-10-17/predecessor_sha256.txt`, `after_sha256.txt`):
  - **The counter override:** the home row's per-run RetroArch counter override
    (`E.TEKKEN["override"]`, `E.COUNTER` + `E1_COUNTER_EXTRA`).
    - It is written after the preflight and before the sampler starts.
    - It is refused if a file is already there.
    - It is removed at teardown, **only if this run wrote it**. The home row's
      `finally` would also unlink a file it refused to overwrite.
    - One added log line at the wait says the override is per game. The
      existing wait line is unchanged.
  - **The sampler** is started with `--e2`, so `encoder.jsonl` is written in the
    run directory and kept.
  - **The summary:** `key["retroarch"]` (the home row's key) and `key["gate3"]`:
    `retroarch_fps`, `capture_fps`, `dupdrop_per_min`. The last two come from
    `segcap` (E4-S5's, re-implemented; a test asserts it equals E4-S5D's).
  - Nothing else changes: the endpoint class / hash, `path.jsonl`, the wait, the
    teardown's other steps, the refusals.
- **`tools/test_e1_remote.py`:**
  - the fake suite gains the override constants at a temp path;
  - 7 new tests;
  - 20 in all.
- `tools/e1_suite.py` and `tools/e1_sampler.py`: not edited.
- **Docs:** ROADMAP §G4, the G4-P2 line.

## Validation

- `(cd tools && python3 -m unittest test_e1_remote -v)` → 20 OK.
- The home row: `home_row_masked_hash.py`. The file sha256 and every named
  function's masked AST hash are identical to HEAD (`main` with its `--remote`
  branch masked).
- G4-S1's files read with the fixed code: `None` ×3. Gate 3 stays NOT
  EVALUABLE.

## Result

BUILT; NOT RUN off-site (G4-S2 is the first run with it); NOT ADOPTED; nothing
committed. `PATCH_INDEX.md` was not updated (not session B's file).
