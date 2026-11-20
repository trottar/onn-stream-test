---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: 8f1e99ed (this repo)
---

# B181-B184 — every digit from the line score; an unreadable final screen given up; the last look; the anchor

**Result:** `evidence/B181_SCORE_EVERY_DIGIT_2026-11-20.md`.

- **Files:**
  - `tools/h7_endscreen.py`: the score label with line-score cells (`SCORE_SIDE`, `score_cells`); `_find_columns`,
    `read_columns`, `_digit_stats`, `_read_digits`; `learn_scores` learns the columns; `end_unread` on an unread final
    screen.
  - `tools/party_add_game.py`: readings with cells; the sum check; every number read back; the culprit and the last
    look (`_sheet`, `look=`); learn's every-digit cell and line; the held anchor (`_anchor_held`).
  - `companion/h7_minigame.py`: the watch `unreadable` after K unread final-screen reads (B182).
  - `companion/party_minigame.py`: `unreadable` → given up at once.
  - `docs/memory/handoffs/ADD_GAME_PROMPT_TEMPLATE.txt`: the one exception (B184).
  - Tests: `tests/b181_every_digit/` (new). `tests/b178_score_kind/` (its tests follow B181-B183: the last look's
    `look=all`, learn's every-digit cell, the harness on a line-score title, B182's two cases; disclosed).
  - The diff: `evidence/b181_2026-11-20/b181.diff`.
- **Switch:** the `score` kind and the label stage only. B182 in `h7_minigame` / `party_minigame` is imported only with
  `PRIVYHUB_H7=1` (and the party layer with `PRIVYHUB_PARTY=1`). Versions 2 / 3 never read `end_unread`. Either flag
  absent → today (`TodayUnchanged`). No bar in `BARS` lowered; `winner` / `places`, T88's / T89's rules unchanged.
- **Rollback:** `git apply -R evidence/b181_2026-11-20/b181.diff` (and the template line).
