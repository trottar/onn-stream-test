---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: cb16e0c8
---

# B123 — h7-start's load for N64 titles, the watch on a row of places, the four-player sidecar (PRIVYHUB_H7=1)

**Result:** `evidence/B123_H7_N64_START_2026-11-17.md`.

- **Files:** `companion/h7_minigame.py` (N64 in the load: the session's own core's folder `Mupen64Plus-Next`, the load
  sent only into a core answering `PAUSED`, else a plain refusal with nothing sent; the watch ends on the whole row and
  carries `places`), `companion/h7_contest.py` (one `CORE_FOLDERS` entry; the contest's own list unchanged),
  `companion/party_minigame.py` (the sidecar's places form `{"players": n, "places_to_scores": [...]}`, default n..1;
  the scores in the seats' order), `tests/b123_h7_n64_start/test_b123.py` (new), `tests/b103_h7_minigame/test_b103.py`
  (one expectation); `evidence/b123_2026-11-17/b123.diff` (applies after `b122.diff`).
- **Switch:** `PRIVYHUB_H7=1` (the load, the watch); with `PRIVYHUB_PARTY=1` too (the sidecar); either absent → today.
- **Live:** not adopted; A's H7-V5 sets the flags for its task only.
- **Rollback:** `git apply -R` B124's, then this diff.
