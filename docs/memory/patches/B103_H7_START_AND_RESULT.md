---
memory_schema: 1
as_of: 2026-11-12
baseline_commit: 8b43a266
---

# B103 — H7's mini game: start and result, behind `PRIVYHUB_H7=1` (the companion; absent / 0 = today)

**Result:** `evidence/B103_H7_START_AND_RESULT_2026-11-12.md`.

- **Files:** `companion/h7_minigame.py` (new), `companion/plugins/games.py` (the flagged routes, inside B99 / B101's
  flag block), `tests/b103_h7_minigame/test_b103.py` (new); `evidence/b103_2026-11-12/b103.diff` (applies on
  `8b43a266` + `b102.diff`; it needs B102's `tools/h7_endscreen.py`).
- **Switch:** `PRIVYHUB_H7=1` → `POST /plugins/games/h7-start[?load=0]` and `GET /plugins/games/h7-result`; absent /
  `0` = today — proved byte for byte through the real HTTP route against `8b43a266`'s companion.
- **Live:** not adopted. A sitting sets B99's bench drop-in (`evidence/b99_2026-11-11/b99-h7-live-read.conf`) for its
  length only. The game's files live in the rules folder, off the repo: `<game id>.state` (B101's kept start) and
  `<game id>.endscreen.json` + `.npz` (B102's spec).
- **Needs:** the companion's display (`DISPLAY`, already in its unit) and `xdotool` (already required by the stream).
- **Rollback:** `git apply -R b103.diff`; `logs/games/h7_results.jsonl` is git-ignored.
