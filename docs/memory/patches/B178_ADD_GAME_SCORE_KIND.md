---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: b243dd63 (this repo)
---

# B178 — the `score` result kind (each side's number read on the final screen; the labels read by the session)

**Result:** `evidence/B178_ADD_GAME_SCORE_KIND_2026-11-20.md`.

- **Files:**
  - `tools/h7_endscreen.py`: spec version 4, a new path — `score_sides`, `score_picture`, `score_strings`, the place
    search, `place_glyphs`, `glyph_cell`, `cell_dists`, `read_scores`, `learn_scores`, `_learn_v4`, `ReaderScore`,
    `EndedScore`, `score_scores`; `learn` / `check_spec` / `load_spec` / `Reader` / `Ended` / `thresholds` route
    version 4. Versions 2 / 3 unchanged.
  - `tools/party_add_game.py`: `--result score`; the `label` stage (`cmd_label`, `parse_readings`, `_two_pictures`,
    `_crops`, `label_inputs`); `_learn_score`, `_score_spec_cells`, `_score_line`, `_replay_scores`, `_learn_without`;
    the sidecar `"result": "score"`; learn's inputs carry the readings; rehearse carries the label record; bench's
    expected numbers and winner; `solo --read --winner draw`.
  - `companion/h7_minigame.py`: `Ended` fed a read's `scores` when it has them; `scores` kept in the watch and its
    `ended` row.
  - `companion/party_minigame.py`: `_score_entry`; at `ended` the real numbers and the winner seat, null on a tie.
  - Tests: `tests/b178_score_kind/` (new); `tests/b114_party_minigame_hang/b114_scenario.py` (a `b178` mode, one
    line pair, disclosed).
  - The diff: `evidence/b178_2026-11-20/b178.diff`.
- **Switch:** `PRIVYHUB_H7=1` and `PRIVYHUB_PARTY=1` (the companion modules that read a version-4 spec are imported
  only with them). Either absent → today, byte for byte (`TodayUnchanged`). A sidecar without `"result": "score"` →
  today. No bar in `BARS` lowered or changed; `winner` / `places` unchanged.
- **Rollback:** `git apply -R evidence/b178_2026-11-20/b178.diff`.
