---
memory_schema: 1
as_of: 2026-11-24
baseline_commit: ef8a0ce5 (this repo)
---

# B208-B210 — survey, plan, train; the hub keeps what it read (queue BP)

**Result:** `evidence/B208_SURVEY_PLAN_TRAIN_2026-11-24.md`.

- **Files:**
  - `tools/party_steps.py` (new): `survey`, `label` on the regions, `plan`, `train`, `rigidity`, the once rule.
  - `tools/party_add_game.py`: the stages `survey`, `plan`, `train`; `label` of a surveyed binding handed to
    `party_steps`; `bench` needs `train`'s PASS for a surveyed binding; `learn` refused for one; `BARS["rigid_min"]`
    0.0995 (B211).
  - `tools/h7_endscreen.py`: `learn_letters(..., regions=None)` / `_letters_places(..., regions=None)` — given, the
    letters looked for only inside the surveyed regions, the places the regions; absent → today.
  - `companion/h7_minigame.py`: with `PRIVYHUB_PARTY=1` and a version-4 / 5 spec, the watch holds the last K end /
    unread pictures; `end_pictures()`.
  - `companion/party_minigame.py`: `_keep_result` (PRIVYHUB_PARTY=1): score / letters results kept under the title's
    code, newest 200 (`PLAYED_KEEP`).
  - Tests: `tests/b208_survey/`, `tests/b210_keep_result/` (new); `tests/b114_party_minigame_hang/b114_scenario.py`
    (the `b210` mode, two lines); B212's per-picture noise in `tests/b178_score_kind/` (`score_capture.py`,
    `test_b178.py`), `tests/b181_every_digit/` (`line_capture.py`, `test_b181.py`), `tests/b185_overtime/test_b185.py`,
    `tests/b198_max_score/low_capture.py`, `tests/b200_drawn_places/pad_capture.py`.
  - The diff: `evidence/b208_2026-11-24/b208.diff`.
- **Switch:** the new path is entered only by `survey`; a binding without a survey runs today's code. The hub's keep
  only with `PRIVYHUB_PARTY=1` (both flags for a mini game at all). The running companion takes the change after its
  next start (not restarted here).
- **Rollback:** `git apply -R evidence/b208_2026-11-24/b208.diff`.
