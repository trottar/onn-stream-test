# SESSION B — done, 2026-11-20 BF (QUEUE_2026-11-20BF: B175 every save read by a spec learnt without it; B176 a save in the wrong role, the same match saved twice; B177 the fixed task; run ~01:45Z-03:49Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (user units; none system-wide); `git status
--short` empty (queue BE committed in `dbbc316b`).

**No title started** (this queue has no exception): every proof is on made-up titles.

**Rules kept:**
- No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive.
- Read only: the users' setups, slots and in-game saves, the kept H7 folders, the rules folder and `runtime/` pictures.
- No change in the board's repo; no Godot run.
- **No bar in `BARS` lowered or changed** (a cell added, with the replay's own bar); the learner (`h7_endscreen.py`) not
  changed, called as it is.
- No title, id, path or picture in any record (the three checks).

The /tmp work copy (companion/, tools/, tests/, PrivyHub/'s tracked sources) and my scratch on the main disk are off the
repo; no picture kept. Nothing adopted; nothing committed in either repo.

## B175 — BUILT (`evidence/B175_ADD_GAME_LEFT_OUT_2026-11-20.md`, `b175_2026-11-20/`, `patches/B175_…`)

- **The cell:** for every ending's every save (same-picture saves together, as one match), learn learns again without it
  and replays it. It must end as its own ending within 2.0 s (the replay's bar today) and never as another: one cell
  `left out: <role>` per save.
- **Unchanged:** the spec written is the one from every save. The line for one more save follows the cell, the cap as
  today.
- **rehearse carries it; bench is unchanged** (it learns nothing).

**The made-up titles with the new cell, one line each:**
- **one save per ending, other characters in each (settle's weak pass):** today's cells all met; left out 0 of 2
  (its ending's only match) → **FAIL**, asks `end_P1_2`.
- **two per ending, other characters in every match:** left out 0 of 4 (end_P2 read as end_P1) → asks `end_P1_3`,
  `end_P2_3`, `end_P2_4` → **PASS**.
- **near-alike, two per ending, P2's first match with P1's characters:** asks `end_P1_3`, `end_P2_3`, `end_P2_4` →
  **the cap** (end_P2: with P1's characters, never read as P2).
- **near-alike, three per ending, other characters:** left out 6 of 6 → **PASS**.
- **far apart, two per ending:** left out 4 of 4 → **PASS**.
- **two per ending, the same characters within an ending (cursor moved):** "end_P1 and end_P1_2 look like the same
  match saved twice" → **FAIL**.
- **two per ending, end_P2_2 holding a P1 win:** asks three saves, then "A save may be in the wrong role: end_P2_2
  reads as end_P1" → **FAIL**, nothing more asked.
- **three per ending, a large mark only the begin shows:** `margin_needed` alone not met → **FAIL**.

**The least saves per ending:** a near-alike title needs **three**, each from a different match; a far-apart one needs
**two**. Three is the least, not a promise: the near-alike title whose first P2 match had P1's characters reached the
cap at four.

**What it costs:** one learn per match left out. At 1280 × 960: two players 3.5 / 6.7 / 11.0 s with 2 / 3 / 4 saves an
ending; four players 10.9 / 22.8 / 38.3 s.

**Mutations, each caught by B175's own suite:** 6 of 6: the cell always met; the left-out save still among the sources; **the margin cell alone always met** (now caught: the made-up title whose margin alone fails); the same-picture measure off; the wrong-role rule without the relabel check; the wrong-role line still asking a save.

## B176 — BUILT (in B175's record and diff; `patches/B176_…`)

- **The same match saved twice:** two saves of one ending whose screens that stay are under 1.0 grey apart (64 × 48;
  H7-V1's kept number for one state run twice) are named, and count as one.
- **A save in the wrong role:** named only where the evidence tells it from a thin ending. The queue's wording, and my
  hashed design, would have accused a right save on the made-up title; the addendum explains the change. The rule as
  built: a save left out is not read as its own, the spec from every save fails, its ending kept two other matches, and
  relabelling that one save mends the spec. Nothing more is asked until it is cleared.
- **One line, in this order:** wrong role, the same match, one more save, the cap.

## B177 — DONE (`handoffs/ADD_GAME_TASK.md`; the template unchanged, sha256 `4ba6a99a…` before = after)

- **The lines, word for word:** the three lines the session passes on, plus the cap's.
- **§4:** the user's part with the least and the most saves.

## What I would change (not done — the queue is the task)

1. **Register's minimum: three saves per ending, not two**, for any title that is not plainly far apart. Two is enough
   only for a far-apart title. Today a near-alike title costs the user a learn and a "one more save" round per ending to
   learn that.
2. **The cell is strict on few matches.** A title whose players reuse the same characters for both winners can reach
   the cap even when its end screen does show who won. A count on the screen that never changes between matches is
   what learn needs. "Another mode or another screen" is the honest way out today; a learner that weighs the outcome
   mark by its own consistency across matches would be a learner change (not done).
3. **A title whose end screen is identical from match to match** would have every second save named "the same match"
   and could not be added. The same-picture check could skip an ending whose saves were made after matches with other
   characters, if the user says so — your call.
4. **bench only replays saves the spec learnt from.** With B175 the cross-match proof is in learn; bench could replay
   one left-out save through the hub's real path as well.

## Files

- **This repo:** `tools/party_add_game.py`.
- **Tests:** `tests/b175_left_out/` (new); `tests/b171_more_saves/near_capture.py`, `test_b171.py`,
  `tests/b157_add_game/fake_capture.py`, `tests/b163_rehearse/test_b163.py` (updated, disclosed).
- **Handoffs:** `handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt` (one line), and this file.
- **The record:** `evidence/B175_ADD_GAME_LEFT_OUT_2026-11-20.md` + `b175_2026-11-20/` (the design and its addendum,
  each hashed; `table.txt`; `cost.txt`; tests; mutations; checks; `b175_b176.diff`, which applies on `dbbc316b`;
  `manifest.sha256`).
- **Patches:** `patches/B175_ADD_GAME_LEFT_OUT.md`, `patches/B176_ADD_GAME_TWO_HINTS.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph).
- **Logs:** `logs/b175_git_status.txt`, `logs/b176_git_status.txt` (`logs/` is git-ignored).
- **The board's repo:** nothing.

## The user's part for a new two-player title (as the task now has it)

**Saves:**
- **6 at the least:** the begin, a mid-match save, two wins for each player. Enough only when the two players' end
  screens look clearly different.
- **8 for a game whose end screens look nearly alike:** three wins for each player.
- **10 at the most:** four wins for each player.
- A save the session names as the wrong player's or the same match is saved again, not added.

1. Tell the session which game the code is (chat only; never written down).
2. Answer: two players; who won is shown by player after a match; anything to unlock (its setup made in Extras →
   Cheats first); the words to find it in Games.
3. Set the shortest match (one round, items off), the same for every save.
4. Round 1:
   - **No setup:** slot 1 on the select screen before anyone picks, slot 2 in the middle of a match, slot 3 after a match
     P1 won.
   - **Under a setup:** never slot 1; slot 2 in the middle of a match, slot 3 after a P1 win.
5. Round 2, each match with other characters (or another stage) than any saved so far:
   - **No setup:** P2 wins → slot 1, P1 wins → slot 2, P2 wins → slot 3.
   - **Under a setup:** P2 wins → slot 2, P1 wins → slot 3; then one more P2 win → slot 2.
6. Then as the session asks, one at a time, each to slot 2 or 3:
   - one more win for the player it names, with other characters again (up to four wins each);
   - a win saved again as the right player's, when it says a save looks like the other player's;
   - a win saved again from another match, when it says two saves look like the same match.
7. Nothing during bench.
8. Solo: the pads on the onn; follow the lines; say who won and whether the board showed one card.
9. If the session says the game can't be added this way, choose another mode or another screen that shows who won by
   player, or the game stays off the board.
10. Commit.

**The user, now:** this repo — commit the tree (queue BF). The board's repo — nothing to commit.
