---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: 73284310 (this repo)
---

# B134 — the listing's names, and practice from the load screen (PRIVYHUB_PARTY=1)

**Result:** `evidence/B134_PARTY_TITLES_AND_PRACTICE_2026-11-17.md`.

- **Files:** `companion/party_minigame.py` (the listing's `"title"`; `go(practice)`; the practice's way back; the
  Start hook) — in `b133.diff`; `companion/native_session_io.py` (`_party_buttons`: a report hook, `None` = today),
  `tests/b134_party_practice/` (new) — `evidence/b134_2026-11-17/b134.diff`.
- **Switch:** `PRIVYHUB_PARTY=1`; absent → today. The hook is set only while a practice plays.
- **Rollback:** `git apply -R` the diffs (b134, then b133).
