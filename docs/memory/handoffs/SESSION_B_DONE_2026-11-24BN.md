# SESSION B — done, 2026-11-24 BN (QUEUE_2026-11-24BN: B204 every number on T92's screen; B205 synthetic training; B206 T92; B207 how long a queue takes; read line 00:39:51Z, limit 02:09:51Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BM committed (`2b4afeab`).

**Rules kept:**
- No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive.
- Nothing deleted by hand: scratch copies of mine stay off the repo. One scratch `rm` was refused by the safety check;
  I used fresh folders instead.
- **The picture source never ran** (T92's pictures reused). `status` and `native-stream-status` were checked first:
  nothing running, no client.
- Read only: your setups, slots and saves, the kept H7 folders, the runtime pictures, and the rules folder (sha256 the
  same).
- No bar lowered; T88-T91's rules unchanged; the proof still on real pictures. The template is unchanged.
- No title, id, team name or path in any record (four checks).
- Nothing adopted; nothing committed.

## B204 — BUILT

- **The cells and the stats table are the score's font.**
  - Scaled to the finals' height, one digit across the sizes is at most **0.652** apart. Two different digits are at
    least **0.830** apart. One size alone stays within 0.49.
  - The learner's own measure over every picture: 0.6745 against 0.8296.
  - The cells and the stats table are one small font: one digit 0.04-0.50 apart.
- **The label stage reads every number:** the finals, the period cells, and the stats rows after `:`.
  - Only the final is the result, and only the period cells add up to it.
  - Each stats row is guarded by the two readings, the read-back and the last look.
- **Another size counts as its digit only when the title's own numbers say so** (T92: yes). A small font of another
  face teaches nothing.
- **Disclosed:** B200's `Drawn` and `Counted` asserted "a small size teaches nothing". Both now assert B204's "counted
  when one font".

## B205 — NOT BUILT (the limit)

It trains only, so it would not have changed B206: the every-digit cell counts real glyphs.

## B206 — T92

| stage | verdict |
| --- | --- |
| register `--max-score 5`, no `--collect` | **PASS** (9) |
| label, every number as drawn, the last look `all` | **PASS** (19) |
| learn | **FAIL** (24) |

Now covered:
- 0 and 2 in several saves;
- **3** in two saves (end_P2, and the "13" in end_P1's stats);
- **1** learnt from end_P1 alone (SHOOT 13, CK 01);
- **4** learnt from end_P1_2 alone (final and cell).

**Only 5 is short.** end_P1_2 shows it twice, P1's final 05 and P1's 1ST cell 05. That pair is the farthest
cross-size pair (0.652), and neither reads the other back. No other save shows a 5 anywhere: no final, no cell, no
stats row.

Also not met:
- **left out: end_P2:** read 03 right, but only after 14 s (bar 2 s). A small 3 reads the big 3 slowly.

## B207 — where queue BM's five hours went (18:20Z-23:27Z)

| what | about |
| --- | --- |
| reading the queue, the code, settling T92's screen | 30 min |
| building B200 / B201 / B202, trial label + learn on copies (1.5-4 min each) | 40 min |
| B200's tests, each run ~8 min, five rules tried for the same-shape place | 35 min |
| T92's real runs (register, label twice, look, learn) and the fix in between | 15 min |
| **three full serial suite runs (~1 h 20 to 1 h 30 each; two set aside after fixes)** | **~3 h 45** |
| mutations (5, ~1.5 min each, twice), T90 / T91 re-runs (~8 min, three times) | 35 min, mostly overlapped |
| record, diff, checks | 15 min |

**Almost four of the five hours were the earlier suites run one after another, three times,** most of it waiting.

**This queue:**
- every suite at once, 12 at a time: ~15 min wall (the slowest, B171, 15 min);
- the new tests are fast unit tests (0.2 s);
- three mutations in seconds;
- no second full run, only the one suite whose assertions changed.

**Worth running every time** (the score kind's own path: label, learn, the reader, the place finder):
- B204, B200, B198, B181, B185, B178;
- B175 and B171 (learn's left-out and more saves);
- B157 (the tool's core).

**Only when their own code changes:**
- B191 (letters), B195 / B162 / B169 (solo and close), B163 (rehearse), B158 (winner);
- B167 (the picture source), B102 / B122 (the version 2-3 readers), B103 (the hub's watch), B124 (four seats);
- B201 (`--find`).

## What I would change (not done)

1. **Count a 5 from any number on the screen, not only from scores.** "5 shots" or "5 corners" in the stats table
   counts as much as a final of 5. The one match the user still owes T92 is easy that way.
2. **Build B205** for the score kind next, B192's way. It would not add a digit, but it would make cross-size samples
   read faster: the 14 s on end_P2 would come down.
3. **Weigh a cross-size sample apart in B186's one-save rule:** a 5 seen at both sizes in one save could count when
   each reads the other within the cross-size spread measured (0.652) rather than within one size's.

## Files

- **Code:** `tools/h7_endscreen.py`, `tools/party_add_game.py`.
- **Tests:**
  - `tests/b204_every_number/` (new);
  - `tests/b200_drawn_places/test_b200.py` (two assertions).
- **Handoffs:** `ADD_GAME_TASK.md` (§2), `SESSION_B_STATUS.txt`, this file.
- **Record:** `evidence/B204_EVERY_NUMBER_2026-11-24.md` + `b204_2026-11-24/`, and T92's verdicts
  (`add_game/T92/label.*`, `learn.*`).
- **Patch:** `patches/B204_EVERY_NUMBER.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line).
- **Logs:** `logs/b204_git_status.txt`.

## T92 now

T92 is at learn; every digit 0-4 is covered. **It needs one more match where a 5 shows anywhere on the final screen:**
- a side scoring 5;
- or 5 in either side's stats (5 shots, 5 corners, 5 fouls…).

Any teams, saved on the screen after the match to slot 2 or 3. Session A then runs register, label (reading every
number) and learn. Then bench, and solo with you.

**The one line you type in session A:**

```
Read docs/memory/handoffs/ADD_GAME_TASK.md and continue T92 (score, two players, --max-score 5) from learn's line: ask me for one more match with a 5 anywhere on its final screen (a score of 5, or 5 in either side's stats), saved after the match to slot 2 or 3 — then register, label with every number on the screen, and learn.
```
