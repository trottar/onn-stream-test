---
memory_schema: 1
as_of: 2026-11-12
baseline_commit: 8b43a266
---

# B102 — H7's end-screen learner (a tool; no companion change)

**Result:** `evidence/B102_H7_END_SCREEN_LEARNER_2026-11-12.md`.

- **Files:** `tools/h7_endscreen.py` (new), `tests/b102_h7_endscreen/test_b102.py` (new);
  `evidence/b102_2026-11-12/b102.diff` (applies on `8b43a266`).
- **Switch:** none — a tool run by hand (`learn` / `score` / `read`); nothing imports it but B103's watcher, and that only
  with `PRIVYHUB_H7=1`.
- **Needs:** Python 3 with Pillow and numpy (both Debian packages already on the hub; nothing fetched).
- **Live:** not adopted. A game's spec (`<game id>.endscreen.json` + `<game id>.endscreen.npz`) is made with
  `h7_endscreen.py learn <runs> <labels> <rules folder>/<game id>.endscreen.json` and lives in the rules folder, off
  the repo; no picture is kept by the tool.
- **Rollback:** `git apply -R b102.diff`.
