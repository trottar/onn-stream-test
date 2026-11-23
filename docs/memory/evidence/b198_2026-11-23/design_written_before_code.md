# B198 / B199 — design, written before any code (queue BL)

## B198 — `register --max-score N` (score kind only)

**register**
- `--max-score N`: a whole number 1-9999, only with `--result score` (else usage). Kept in the binding as `max_score`.
- One more register cell when given: "the highest score one side reaches (--max-score)", read N, bar "a whole number
  1-9999".
- `register_inputs` gains `max_score` only when it is given: without it the digest is today's, so every kept verdict
  of today's titles (T90) stays as it is. A changed N changes the digest, so label / learn / bench run again.
- A register run without the flag drops it from the binding (the binding is built afresh each run): today.

**learn (the every-digit cell)**
- The expected digits: every digit of every number 0..N (`{c for k in 0..N for c in str(k)}`): N = 1-8 gives 0..N;
  N >= 9 gives 0-9 (no change but the cell's name). Line-score cells are never above their final (they add up to it),
  so the same set serves the cells and the finals.
- The cell, with N: "every digit that can occur up to N (<digits>) read by a reader learnt without each save that
  shows it" — each expected digit shown by two saves or more, or learnt from one save by B186's rule, as today. Its
  read adds "not expected (above N)": the other digits — recorded, never a cell.
- `recorded["digits"]` adds "expected" and "not expected"; and "above the highest score": the end saves with a number
  above N (recorded only — not a cell: the queue asks none; named in my reply).
- Without `--max-score`: the cell, its name and its read are today's, byte for byte.

**the line for one more save**
- `_score_line` names only expected digits: the digits fewer than two saves show, and the digits a left-out save was
  not read for, each kept only when expected. With none left after that, B171's line as today.

**the spec / the hub**
- With N, learn writes `score.max_score = N` into the version-4 spec before it scores or saves it; the spec's reuse key
  gains N (only when given), so a changed N re-learns.
- `check_spec`: a version-4 spec's `max_score`, when present, a whole number >= 0, else not read.
- `ReaderScore.read`: on the final screen, every number read and any final above `max_score` -> `unknown` with
  `end_unread` (B182) and `above_max` — never a result. A digit never learnt has no template: B178's rule already gives
  "?" -> `unknown`, `end_unread`. Then B182's watch gives up after K such reads in a row: `final_unreadable`, no
  scores, no winner. No change in `companion/` (the watch reads `end_unread` as it is).
- Spec without `max_score` (every spec today): today.

**how often, in plain words (from N):** after learn passes, every digit 0..N is learnt, so the hub gives up only on a
match where a side ends above N: as often as your matches end above N. A match given up shows no result on the board,
never a wrong one.

**tests (`tests/b198_max_score/`, made-up line-score pictures, B181's `line_capture`)**
- `Low`: four end saves, finals 0-4, line cells 0-4, each of 0-4 in two saves, no 5-9:
  - `--max-score 4` -> label and learn PASS; the cell names 0-4; 5-9 recorded not expected;
  - `--max-score 5` -> learn FAIL on the every-digit cell alone, its line naming only 5 (never 6-9); two more saves
    showing a 5 -> PASS without 6-9;
  - no flag -> today: FAIL naming 5-9 (the cell's old name).
- `Hub`: the spec learnt with N = 4: a final of 7 -> `unknown` + `end_unread`, never `end`; a final of 10 (both its
  digits learnt) -> the same (above N); 4-1 -> `end` [4, 1]. Through B182's watch (`companion/h7_minigame.py`'s
  `_run`, its picture and its game stubbed): the final of 7 -> state `unreadable`, one `final_unreadable` row, no
  scores.
- `Register`: `--max-score` with `--result winner` refused (usage); its cell; the binding; the inputs digest unchanged
  without it.
- Mutations: (1) the expected set always 0-9 -> `Low` caught; (2) the reader's threshold skipped, a glyph read as the
  nearest template -> `Hub` caught; (3) the above-N check removed -> `Hub` caught.
- B178-B195's suites green.

**Disclosed now:** the queue's test "finals 0-4, `--max-score 5`, passes without 6-9" cannot pass under the queue's own
rule (5 can occur from 0 to 5, and no save shows it). The rule is kept; the tests above show N = 4 passing on those
saves, and N = 5 asking only for a 5 then passing.

## B199 — the task's question

`ADD_GAME_TASK.md` §1, the score bullet: one more question, once, after "who wins is shown how" answers score —
"YOU, now: what's the highest score one side will reach in a match at the settings you play (for example 5)? I only
need the digits up to that." -> `register … --result score --max-score <N>`; and "can a match end level, or does it
go to extra time / penalties until someone wins?" — the answer recorded in the session's page in the user's words;
when it can end level, the session tells the user in its line what the board does with a draw (the hub's winner none
on a tie; the board's own rule for it, the PC side's note). The template unchanged (sha256 before = after).
