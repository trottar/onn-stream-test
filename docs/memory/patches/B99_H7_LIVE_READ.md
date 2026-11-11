---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: 6cb4663b
---

# B99 — H7's live read, behind `PRIVYHUB_H7=1` (the companion; absent / 0 = today)

**Result:** `evidence/B99_H7_LIVE_READ_2026-11-11.md`.

- **Files:** `companion/h7_live_read.py` (new), `companion/plugins/games.py` (the flagged import and route),
  `tests/b99_h7_live_read/test_b99.py` (new); `evidence/b99_2026-11-11/b99.diff` (applies on `6cb4663b`).
- **Switch:** `PRIVYHUB_H7=1` → `GET /plugins/games/h7-read`; absent / `0` = today (the module not imported, the action
  unknown, no rules folder read, no row) — proved byte for byte through the real HTTP route.
- **Live:** not adopted. A companion restart is needed for it to exist at all; H7-L1 sets the flag as a bench drop-in
  (`b99-h7-live-read.conf`) for its sitting only and removes it at the close.
- **Rollback:** `git apply -R b99.diff`; no data to migrate (`logs/games/h7_reads.jsonl` and `~/privyhub_h7/` are
  outside git).
