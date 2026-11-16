---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: d61f9b56
---

# B105 — H7's watcher: replace, recognised, stop, keep (behind `PRIVYHUB_H7=1`; absent / 0 = today)

**Result:** `evidence/B105_H7_WATCHER_GAPS_2026-11-16.md`.

- **Files:** `companion/h7_minigame.py`, `companion/plugins/games.py` (the `keep` word passed to `h7-start`; the new
  `h7-stop` route, inside B103's flag), `tests/b105_h7_watcher/test_b105.py` (new), `tests/b103_h7_minigame/test_b103.py`
  (five places, where B105 changes B103's behaviour); `evidence/b105_2026-11-16/b105.diff` (applies on `d61f9b56` +
  `b104.diff`; it needs B104's tool for `thresholds()` and the old-measure line).
- **Switch:** `PRIVYHUB_H7=1` → a start over a running watch replaces it (row `replaced`); `h7-result` carries
  `recognised` (true / false / null; 8 s after a start with the load) and `last` with thresholds and the spec's
  version; `POST /plugins/games/h7-stop`; `h7-start?keep=1` → `runtime/h7_frames/<game id>_<UTC stamp>/` (JPEG +
  `index.csv`; git-ignored). Absent / `0` = today — proved byte for byte through the real HTTP route against
  `d61f9b56`'s companion (`h7-stop` answers "Unknown Games plugin POST action: h7-stop" as today).
- **Live:** not adopted. A sitting sets B99's bench drop-in for its length only, as before.
- **Cost of keep=1:** ~5.3 ms and ~5 ms CPU a picture (1920 × 1080, ~210 KB); a 60-fps fixture's frames over 60 s
  unchanged (3,600 / 3,600).
- **Rollback:** `git apply -R b105.diff`; the kept pictures are under the git-ignored `runtime/`.
