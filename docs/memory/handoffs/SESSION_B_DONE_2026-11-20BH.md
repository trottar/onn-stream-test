# SESSION B — done, 2026-11-20 BH (QUEUE_2026-11-20BH: B181 every digit from the line score; B182 an unreadable final screen given up at once; B183 the last look; B184 the template and the anchor; run ~21:05Z-22:30Z)

**Checked first:**
- the first try stopped: queue BG was not committed. On the second, BG committed (`8f1e99ed`), `git status --short`
  empty;
- only `privyhub-companion` and `privyhub-diag` active.

**BG's exception: not used.** The picture source never ran and no title was started. T90's pictures (session A's)
were copied, read only, to a scratch off the repo and removed after the record.

**Rules kept:**
- No stream, no restart, no flag set on the hub, no adb, no sudo, no nft; nothing fetched or installed; nothing written
  to the drive.
- Read only: the setups, slots and saves, the kept H7 folders, the rules folder, the tool's T90 folder.
- No bar in `BARS` lowered; `winner` / `places` and T88's / T89's rules unchanged.
- The app and the board's repo not touched.
- No title, id, path or picture in any record (the three checks).

Nothing adopted; nothing committed in either repo.

## Whether the line score is the FINAL column's font — in one line

**Yes:** every quarter, overtime and final digit is 16 px tall, 8-9 px wide, on the same row. The same digit, a
quarter against the FINAL, is at most 0.418 apart; two digits at least 0.685.

## B181 — BUILT (`evidence/B181_SCORE_EVERY_DIGIT_2026-11-20.md`, `b181_2026-11-20/`, `patches/B181_…`)

- **The readings:** the session reads every line-score number (`9+2+2+2+_+_=15-0+0+2+0+_+_=2`); the final is still
  the result.
- **The checks:** B178's, plus **each side's cells add up to its final**, plus every number read back by a reader
  learnt without its save.
- **The columns:** each learnt on its final's line. A column separator is refused: its glyph is the same whatever the
  score.
- **The digits** are learnt from every number.
- **learn passes only when every digit 0-9 is shown by two saves** (so read by a reader learnt without each save that
  shows it). Its line names the missing digits and a match to show them.
- **A title with only the final:** 5 end saves at the very best (7 saves with the begin and the mid-match), often the
  cap. A game whose scores never reach some digit can never pass.

**T90 with the line score** (labelled by me through the label stage; my last look: every tile its digit):
- **label: PASS (19 cells).**
- **learn: FAIL (21 of 24).** Not met: left out end_P1 (its 1), end_P1_2 (its 3, 7, 8), and every digit 0-9.
- **Digits still missing: 4 and 6 never; 1, 3, 7, 8 shown by one save each.**
- end_P2_2, which failed in BG, now reads back: its 9 is shown by three saves.

## B182 — BUILT

A final screen read K times with a number on it not read is **given up then**, with why "the final screen was seen
and a number on it was not read". No scores, no winner: the board's own given-up path, never the 900-s wait.
- In B114's harness, held or moving on after it, it is given up in under 30 s.
- The party row carries that why alone.

## B183 — BUILT

Before label's PASS, `label/digits.png` puts every glyph of every labelled number side by side, by the digit it was
read as. The session answers `look=all` or names the tiles that are not that digit; their saves are named to read
again.
- One cell.
- **BG's every-4-read-as-9 is now caught.**

## B184 — DONE

- **The template:** "You never judge a picture (but for the label stage of a score title: its readings and its last
  look, each checked by the tool), …". sha256 `4ba6a99a…` → `aadccb04…`.
- **A final screen's anchor:** the first picture held still 3 s after the load.
- T88's and T89's numbers unchanged.

**Tests and checks:**
- B181 7 ×3; B178 23 ×2 (its tests follow B181-B183, disclosed); B157-B176 and the touched suites green;
- mutations 4 of 4 caught: the sum check skipped; a pass with a digit unlearnt; the give-up waiting; the look skipped.

**`ADD_GAME_TASK.md`:** the line score's readings, the sum's and the look's lines, learn's every-digit line, and the
user's part, word for word. A slip left by BG (the bench bullet run into the score line) fixed.

## What happens now at the TV when a final score has a digit never learnt

- A title can no longer be added with a digit unlearnt (B181), so this should not arise.
- If a final screen's number is still not read (another font, a picture the reader cannot read), the mini game is
  **given up about 3 s after the final screen shows** (B182). The board takes its given-up path — the board's draw
  for everyone, as the PC side pays a draw — with no guessed winner. It never waits 15 minutes.

## What I would change (not done — the queue is the task)

1. **A title whose finals cannot reach some digit can never pass**, and many mini games score only to 5 or 10. The
   user could name the highest score the game allows, and learn would ask only for the digits that can occur — your
   call.
2. **The hub reads only the finals.** It could also read the line score and give up (never guess) when the quarters
   do not add up to the final, as the label stage already checks. That is a second, independent check at the TV.
3. **The digit sheet holds one picture per save.** With many saves it grows long. Showing only the glyphs farthest from
   their row's mean (the likeliest misreads) first would keep the look short.

## Files

- **This repo:**
  - code: `tools/h7_endscreen.py`, `tools/party_add_game.py`, `companion/h7_minigame.py`,
    `companion/party_minigame.py`;
  - the template: `handoffs/ADD_GAME_PROMPT_TEMPLATE.txt` (one line);
  - tests: `tests/b181_every_digit/` (new); `tests/b178_score_kind/` (updated, disclosed).
- **Handoffs:** `handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.
- **The record:** `evidence/B181_SCORE_EVERY_DIGIT_2026-11-20.md` + `b181_2026-11-20/`:
  - the design, hashed; `t90/`; `b184_template_sha256.txt`;
  - tests, mutations, checks, `scripts/`;
  - `b181.diff`, `apply_check.txt`, `manifest.sha256`.
- **Patch:** `patches/B181_SCORE_EVERY_DIGIT.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph).
- **Logs:** `logs/b181_git_status.txt` (`logs/` is git-ignored).

## T90 now

**It does not pass on its six kept saves.** With every line-score number labelled, 4 and 6 have never been shown, and
1, 3, 7 and 8 only once.

**The match it asks for:** one more match, either player winning, with other teams than any saved so far, whose line
score shows as many of **1, 3, 4, 6, 7, 8** as it can, in any quarter, overtime or the final, either side. A quarter of
3, 6, 7 or 14 and a final like 31 or 48 carry several at once. Saved on the final stats screen to slot 2 or 3; say who
won. If a digit is still missing, learn asks for one more the same way (at most four wins per player).

**The one line the user types in session A:**

```
Read docs/memory/handoffs/ADD_GAME_PROMPT_TEMPLATE.txt, put T90 where it says ____, and follow it as my prompt.
```

At the questions, answer "who won is shown how" with: the scores of each side on the final stats screen, the winner
the side with more.
