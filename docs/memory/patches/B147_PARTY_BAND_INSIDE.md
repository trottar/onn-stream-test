---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 1052fe82 (this repo)
---

# B147 — the practice band inside the frame's inner 90 % (PRIVYHUB_PARTY=1)

**Result:** `evidence/B147_PARTY_BAND_INSIDE_2026-11-18.md`.

- **Files:** companion/native_stream.py (PARTY_BANNER_FILTER), tests/b147_party_band_inside/ (new), tests/b144_party_practice_banner/test_b144.py (the band's rows); `evidence/b147_2026-11-18/b147.diff`.
- **Switch:** behind `PRIVYHUB_PARTY=1`; absent = today (the users' own sessions byte for byte with the flag set).
- **Rollback:** `git apply -R evidence/b147_2026-11-18/b147.diff` (later items' diffs first).
