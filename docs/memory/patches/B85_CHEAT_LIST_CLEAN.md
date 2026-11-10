---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: c514c543
---

# B85 — every system's cheat list cleaned on the hub (NOT adopted; default on, `PRIVYHUB_CHEAT_CLEAN=0` = today's raw list and launch)

**Result:** `evidence/B85_CHEAT_LIST_CLEAN_2026-11-10.md`.

- **Apply:** `git apply evidence/b85_2026-11-10/b85.diff`, after `b84.diff`.
- **Live:** at the companion's next restart (the `cheat-catalog` reply and the launch's expansion; heading rows read).
  Every client sees the cleaned list, today's dialog too.
- **Off:** `PRIVYHUB_CHEAT_CLEAN=0` in the companion's environment; per request `raw=1` (list) / `cheat_raw=1` (launch).
- **Writes outside the code:** none.
- **Rollback:** `git apply -R` in order (86, 85, 84).
