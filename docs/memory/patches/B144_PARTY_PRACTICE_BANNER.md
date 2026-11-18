---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 246c67da (this repo) + B143's diff
---

# B144 — a practice banner on the onn's picture only (PRIVYHUB_PARTY=1)

**Result:** `evidence/B144_PARTY_PRACTICE_BANNER_2026-11-18.md`.

- **Files:** `companion/native_stream.py` (`PARTY_BANNER_TEXT`, `PARTY_BANNER_FILTER`; `party_banner_next(pid)`,
  `_take_party_banner`; `_party_banner_on` taken once per Linux start; the band inserted before `,hwupload` only while
  it is on), `companion/party_minigame.py` (`_switch_stream(…, banner=False)`, `_arm_banner`; a practice's go passes
  `banner=True`), `tests/b144_party_practice_banner/` (new); `evidence/b144_2026-11-18/b144.diff` (applies after
  b143.diff).
- **Switch:** only a practice's planned switch arms it; every other start's encoder command is byte for byte today's.
- **Rollback:** `git apply -R evidence/b144_2026-11-18/b144.diff` (after B145's).
