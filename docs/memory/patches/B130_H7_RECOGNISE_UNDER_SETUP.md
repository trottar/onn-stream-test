---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: 1fc0ced0 (this repo)
---

# B130 — the recognition window under a cheat setup (PRIVYHUB_H7=1)

**Result:** `evidence/B130_H7_RECOGNISE_UNDER_SETUP_2026-11-17.md`.

- **Files:** `companion/h7_minigame.py` (`RECOGNISE_SETUP_S` = 15.0: a watch begun with the load under a cheat setup
  settles `recognised` false after 15 s; every other watch 8 s as today; the watch keeps its own window and its
  `watching` row says it) — in `evidence/b129_2026-11-17/b129.diff` (the same file); `tests/b130_h7_recognise_setup/`
  (new) — `evidence/b130_2026-11-17/b130.diff`.
- **Switch:** `PRIVYHUB_H7=1`; absent → today. Without a cheat setup → 8.0 s as today.
- **Rollback:** `git apply -R` (with B129's diff, the same file).
