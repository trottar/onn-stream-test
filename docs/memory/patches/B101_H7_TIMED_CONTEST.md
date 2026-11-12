---
memory_schema: 1
as_of: 2026-11-12
baseline_commit: 33d8d2cf
---

# B101 — H7's timed contest, behind `PRIVYHUB_H7=1` (the companion; absent / 0 = today)

**Result:** `evidence/B101_H7_TIMED_CONTEST_2026-11-12.md`.

- **Files:** `companion/h7_contest.py` (new), `companion/plugins/games.py` (the flagged routes; B99's reader shared),
  `tests/b101_h7_contest/test_b101.py` (new); `evidence/b101_2026-11-12/b101.diff` (applies on `33d8d2cf`).
- **Switch:** `PRIVYHUB_H7=1` → `POST` / `GET /plugins/games/h7-contest`; absent / `0` = today — proved byte for byte
  through the real HTTP route.
- **Live:** not adopted; H7-L2 sets B99's bench drop-in (`evidence/b99_2026-11-11/b99-h7-live-read.conf`) for its sitting
  only. The mini game's files (`<game id>.json`, `<game id>.state`) live in the rules folder, off the repo.
- **Rollback:** `git apply -R b101.diff`; `logs/games/h7_contests.jsonl` is git-ignored.
