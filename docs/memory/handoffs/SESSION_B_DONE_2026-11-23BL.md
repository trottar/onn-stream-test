# SESSION B — done, 2026-11-23 BL (QUEUE_2026-11-23BL: B198 `register --max-score N`; B199 the task's question; run ~01:00Z-02:25Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BK (`58326923`) and T91's third record (`3da018eb`) committed.

**Rules kept:**
- No title started; no stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed;
  nothing written to the drive; nothing deleted by hand (two temp dirs from my first failing test run stay in my
  scratch, off the repo — the record says so).
- Read only: your cheat setups, their slots and in-game saves, the kept H7 folders, the rules folder, the runtime
  pictures.
- No bar in `BARS` lowered; T88-T91's rules unchanged; the sum check, the two readings, the last look and the left-out
  cells stay; the app, the companion and the board's repo not touched; the template unchanged (`aadccb04…`).
- No title, id, path or picture in any record (the three checks).

Mine: `tools/party_add_game.py`, `tools/h7_endscreen.py`, `tests/b198_max_score/`, `handoffs/ADD_GAME_TASK.md`,
`docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one line), `handoffs/SESSION_B_STATUS.txt` (one line),
this file, the B198 record + dir, the B198 patch, `logs/b198_git_status.txt`. Nothing adopted; nothing committed in
either repo.

## B198 — BUILT

- **register `--max-score N`** (score only; kept in the binding; in the inputs digest only when given, so T90's
  verdicts stay as they are).
- **learn** needs only **the digits a number 0..N can show** (N = 3: 0-3; N = 5: 0-5), the finals and the line-score
  cells, each learnt as today (two saves, or one save several times). The others are recorded "not expected", never
  a cell.
- **The line for one more save names only expected digits.**
- **At the hub:** a final above N, or with a digit never learnt, is unreadable and given up at once (B182): no result,
  never a guess.
- **How often to expect a give-up:** only on a match where a side ends above the number you name — as often as your
  matches go past it. A match given up shows no winner, and the board counts it as a draw.
- **Without the flag:** today.

**Tests:** B198's 11, three runs, OK. B178-B195's suites and the ones the code touches, once each, green, none
changed; temp dirs left 0. **Mutations 3 of 3 caught:** 0-9 required anyway; an unexpected digit read by nearness; a
final above N read.

**Disclosed:**
1. The queue's test "finals 0-4, `--max-score 5`, passes" cannot pass under its own rule, because 5 can occur and no
   save shows it. The tests show N = 4 passing on those saves, and N = 5 asking only for a 5, then passing.
2. **B178's place finder and single-digit finals.** When every final is one digit, the learner can take another fixed
   single shape (a panel under the number, a heading bar, a quarter column) for the score. Every reading fits it, and
   the tallest ranks first. It fails safe: label's "the numbers at one place in every save" cell, or the last look's
   sheet, shows it; never a wrong result. **T92 may stop there.** B198's tests use a made-up screen without such a
   shape.

## B199 — DONE

`ADD_GAME_TASK.md` §1, for `score`: right after "who wins is shown how", the session asks once:
- "YOU, now: what's the highest score one side will reach in a match at the settings you play (for example 5)? I only
  need the digits up to that." → `--max-score`;
- "Can a match end level, or does it go to extra time / penalties until someone wins?" — recorded in your words.
- When a match can end level, the session tells you what the board does: nobody wins, each player gets half of the
  winner's coins (5 by default), a duel's draw pays nothing (the PC side's note). With `--max-score` it also tells you
  when a match is given up.

## What I would change (not done — the queue is the task)

1. **The place finder for single-digit scores** (B178's `_choose_places`): never take a place whose glyphs are the same
   shape in saves labelled with different digits (a panel or a bar), as B181 already refuses such a column. That is
   the one thing likely to stop T92. If T92's label stage fails "the numbers at one place in every save", this is the
   fix.
2. **A save above N:** today it is only recorded ("above the highest score"); learn's replay of it then fails as
   unread. A plain line ("end_P1_2 shows 6, above the highest score you named: name a higher one, or save another
   match") would say why.
3. **Choosing N:** a lower N asks fewer digits but gives up more matches. The question could add "the highest your
   matches usually reach" — your call.

## Files

- **Code:** `tools/party_add_game.py`, `tools/h7_endscreen.py`.
- **Tests:** `tests/b198_max_score/` (new: `test_b198.py`, `low_capture.py`).
- **Handoffs:** `ADD_GAME_TASK.md`, `SESSION_B_STATUS.txt`, this file.
- **Record:** `evidence/B198_SCORE_MAX_2026-11-23.md` + `b198_2026-11-23/` (the design hashed 01:08:26Z, the tests,
  the mutations, the three checks, `scripts/`, `b198.diff`, `apply_check.txt`, the template's sha256,
  `manifest.sha256`).
- **Patch:** `patches/B198_SCORE_MAX.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line), `docs/ROADMAP.md` §PrivyParty (one line).
- **Logs:** `logs/b198_git_status.txt`.

## T92 now

**Your saves, in session A** (it asks each step; the game named in its replies only):
1. Answer its questions: which game T92 is; two players; who wins is shown by the scores; whether it has things to
   unlock; the words to find it.
2. **The highest score:** name the highest score one side really reaches in your short matches (if they end 2-1 or
   3-0, say 3). Every digit up to it has to show in two saved matches; a match that ends higher is given up (no winner,
   a draw on the board).
3. **Level:** say whether a match can end level or always goes on until someone wins.
4. **Round 1:** set the shortest match. Save to slot 1 on the screen before a match, nobody picked; slot 2 in the
   middle of a match; P1 wins → slot 3 on the screen after the match that shows the final score.
5. **Round 2:** three more matches, each with other teams than any saved: P2 wins → slot 1; P1 wins → slot 2; P2 wins
   → slot 3. Try to get every score from 0 up to your number into those finals, each in two matches.
6. **Then only what learn names:** one more match showing the digit it lists, saved where the session says.
7. **solo:** one match from the board, at the TV.

**The one line you type in session A:**

```
Read docs/memory/handoffs/ADD_GAME_TASK.md and add T92 (score, two players) from the start, as §1-2 say — ask me §1's questions first, the highest score and whether a match can end level among them.
```
