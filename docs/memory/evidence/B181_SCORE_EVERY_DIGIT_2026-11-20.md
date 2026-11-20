---
memory_schema: 1
as_of: 2026-11-20
status: BUILT (B181 every digit learnt from the whole line score, learn passing only with every digit 0-9 shown by two saves; B182 an unreadable final screen given up at once; B183 the last look at every glyph by the digit it was read as; B184 the template's one exception and the held anchor) — T90 labelled by me with every line-score number through the label stage: label PASS, learn FAIL (1, 3, 7, 8 shown by one save each, 4 and 6 never), its line asks one more match showing any of them; no bar lowered; nothing adopted; nothing committed
---

# B181-B184 — every digit, nothing hangs, one last look

Queue: `handoffs/QUEUE_2026-11-20BH.md`. The directory is `b181_2026-11-20/`:
- the design + `.sha256` (hashed 2026-11-20T21:16:05Z, before any code);
- `t90/` (label and learn pages, `settle.txt`); `b184_template_sha256.txt`;
- the tests, the mutations, the checks, `scripts/`;
- `b181.diff` (applies on `8f1e99ed`); `manifest.sha256`.

Patch: `patches/B181_SCORE_EVERY_DIGIT.md` (B181-B184).

**BG's exception was not used:** the picture source never ran and no title was started. T90's pictures (session A's)
were copied, read only, to a scratch off the repo and removed after the record.

## Settled (`t90/settle.txt`)

- **The line score is the FINAL column's font at its size:**
  - every quarter / overtime cell and every final is 16 px tall at 640 × 480, 8-9 px wide, on that side's row;
  - the same digit, a quarter against the FINAL, at most 0.418 apart (B178's local measure); two different digits at
    least 0.685 apart over every labelled glyph.
- **The columns:** Q1-Q4 at the same x in every save; OT1 only in the overtime save; OT2 blank in all four. Column
  separators sit between them, of the digits' height.
- **Digits across T90's whole line score** (glyphs; saves showing them):
  - 0 (14; 4), 2 (12; 4), 9 (7; 3), 5 (2; 2);
  - 7 (9; but 1 save), 1 (1; 1), 3 (1; 1), 8 (1; 1);
  - **4 and 6 never.**

## B181 — every digit from the line score (`score` kind)

- **The readings:** a side is its final (`15`, as B178) or its line score, `9+2+2+2+_+_=15` (cells left to right, `_`
  a blank, `=` the final). The final stays the result: the role, the sidecar, the hub.
- **The checks:** B178's, over every number, plus **the sum** — each side's cells add up to its final, else that save
  is named ("P1's cells add up to 15, not its final 10").
- **The learner** (spec version 4, `score.columns`):
  - **each column's place on its final's line:** clusters of strings left of the final; valid only where every save
    has a string of the labelled length where the cell is labelled and none where it is blank;
  - **a column whose glyphs labelled with different digits are nearer than the finals' digit margin is refused** —
    a separator, the same glyph whatever the score;
  - then the most glyphs the finals' own reader reads as labelled; then the spacing; then the leftmost;
  - **templates from every glyph of every labelled number;**
  - **the hub still reads the finals only.**
- **learn:**
  - B178's cells; **left out: <role> now over every number** of the save;
  - a new cell, **"every digit 0-9 read by a reader learnt without each save that shows it"** — every digit shown by
    two saves or more, so the left-out cells read it;
  - its line names the missing digits: "One more save: a match either player won whose line score shows 1, 3, 4, 6, 7
    or 8 (in any quarter, overtime or final, either side) …";
  - the cap as today.
- **A title whose screen shows only the final:** the same rule over its finals.
  - Each save shows 2-4 digits, and twenty sightings are needed: **5 end saves at the very best** (7 saves with the
    begin and the mid-match).
  - Rarely-reached digits push it to the cap: 4 saves a player, 8 end saves. **The cap's line then says it cannot be
    added this way.**
  - A game whose scores never reach some digit can never pass.
  - The made-up finals-only title (21-14, 42-12, 14-24, 12-41): every save read back, learn FAIL on the every-digit
    cell alone, the line naming 0, 3, 5, 6, 7, 8, 9.

## B182 — an unreadable final screen given up at once

- **The reader:** a version-4 read on the final screen with a number not read gives `unknown` with `end_unread`.
- **The watch:** K such reads in a row → state `unreadable`, one `final_unreadable` row, the watch stops.
- **The party layer:** `given_up`, why "the final screen was seen and a number on it was not read" — no scores, no
  winner, the board's own given-up path. The party row carries that why only.
- **In B114's harness:** held, given up in under 30 s; moving on after 4 unread pictures, given up the same way, never
  the 900-s wait.
- Versions 2 / 3 never read so: today. The flags absent: today (`TodayUnchanged`, HEAD's bytes).

## B183 — the last look

- **The sheet:** before label's PASS, `label/digits.png` — a row per digit, every glyph of every labelled number (one
  picture of each save) read as it, numbered.
- **The session answers** `look=all` or `look=<d>:<tiles>`.
- **One cell, "the last look: every glyph is the digit it was read as"**, met only by `look=all` for these exact
  readings. Named tiles name their saves to read again.
- **BG's residual — every 4 read as 9 — is now caught:** the 9 row holds only 4-shapes. The session names its tiles,
  and every save showing one is named.

## B184 — the template and the anchor

- **`ADD_GAME_PROMPT_TEMPLATE.txt`:** "You never judge a picture (but for the label stage of a score title: its
  readings and its last look, each checked by the tool), …". sha256 `4ba6a99a…` before, `aadccb04…` after
  (`b184_template_sha256.txt`).
- **The anchor:** a final screen's anchor is now **the first picture held still 3 s** after the load (else B167's).
  The same anchor is used in B176's same-picture check and the label stage's two pictures. On a made-up final screen
  held 4 s inside a longer later screen, the labelled range is the final screen's; B167's anchor took the later one.
- **T88's and T89's numbers unchanged:** their kept specs are never learnt here; `learn --check` reads them as before
  (B157's `Described`, green).

## T90 with the line score (labelled by me through the label stage, as the session will)

**My readings**, the same from both pictures each:
- end_P1: `9+2+2+2+_+_=15-0+0+2+0+_+_=2`;
- end_P1_2: `7+7+7+7+7+_=35-7+7+7+7+0+_=28`;
- end_P2: `0+0+0+0+_+_=0-2+9+2+9+_+_=22`;
- end_P2_2: `0+0+0+0+_+_=0-9+9+2+9+_+_=29`.

**The last look:** fourteen 0s, one 1, twelve 2s, one 3, two 5s, nine 7s, one 8, seven 9s — every tile its row's
digit; `look=all`.

**label: PASS (19 cells).**
- every sum met;
- the places found, the columns Q1-Q4 and OT1 (OT2 blank everywhere);
- read back without itself: end_P2 and end_P2_2 exactly, every number;
- end_P1 not read for 1, end_P1_2 for 3, 7, 8 — each shown only there.

**learn: FAIL (21 of 24 cells met)** — `t90/learn.md`:
- **met:** spec usable; the places found; every digit separable; digit margin_needed 0.2085 ≥ 0.0796; held-out 0
  wrong, 0.0 unknown; begin and other as before; every end save ended with its finals within 2.0 s; **left out:
  end_P2 and end_P2_2, every number.** end_P2_2 failed in BG; its 9 is now shown by three saves.
- **not met:**
  - left out: end_P1 (1 only there);
  - left out: end_P1_2 (3, 7, 8 only there);
  - **every digit 0-9: 1, 3, 4, 6, 7, 8 shown by fewer than two saves.**
- **Its line:** "One more save: a match either player won whose line score shows 1, 3, 4, 6, 7 or 8 (in any quarter,
  overtime or final, either side); the more of them the better — … (end_P1_3 if P1 won, end_P2_3 if P2 won), label
  T90 and learn T90 again."
- **Digits still missing:** 4 and 6 never; 1, 3, 7, 8 once. A football quarter of 3, 6, 7 or 14 and a final like 31
  or 48 carry several at once.

**Disclosed:** register's PASS for `--result score` was written in the scratch as rehearse's scratch writes it (as in
BG). The real rules folder, the tool's T90 folder and the users' slots only read; the scratch's rules folder stayed
empty.

## Tests, mutations

**B181's suite, 7 tests** (`tests/b181_every_digit/`, made-up line-score screens with a separator of the digits'
height between columns):
- **`LineScore`:**
  - every digit in two saves → label (the last look `look=all`) and learn PASS;
  - the columns found where they are drawn, the separators refused, the blank OT columns without a place;
  - a misread breaking a sum named ("P1's cells add up to 15, not its final 10");
  - a 6 shown by one save → learn FAIL on the every-digit cell, its line "whose line score shows 6"; one more save → PASS.
- **`FinalsOnly`:** B178's title → every save read back; learn FAIL on the every-digit cell alone; the line names 0, 3,
  5, 6, 7, 8, 9.
- **`LastLook`:** every 4 read as 9 → only the look not met; the 9 row holds 4s; the session's `look=9:…` names every
  save showing one. `look=all` → PASS.
- **`Anchor`:** a final screen held 4 s then a longer still screen → the labelled range 0-3 s (B167's anchor: the later
  screen).

**Three runs, 7 OK each.**

**B178's suite, 23 tests, two runs OK.** Its tests changed for B181-B183, disclosed:
- the last look's `look=all` after the readings;
- learn's every-digit cell, a finals-only title now failing on it alone;
- the reads taken from the learner's own call;
- the harness's tool path on a made-up line-score title showing every digit twice (register → label → learn →
  bench PASS);
- **B182's two cases:** held, and moving on after it. Each `given_up` in under 30 s, why "the final screen was seen
  and a number on it was not read", no scores, no winner, the party row that why alone, the watch's
  `final_unreadable` row.
- `TodayUnchanged` (the flags absent, HEAD's bytes) still green.

**Mutations, 4 of 4 caught** (`tests_mutations.txt`; temp dirs left 0):
- the sum check skipped → `LineScore`;
- a pass with a digit unlearnt → `FinalsOnly`;
- the give-up waiting → B178's `Hub`;
- the look skipped → `LastLook`.

**The earlier suites, green:** B175 9, B171 10, B163 7, B157 17 (T88 / T89 `--check`, read only), B162 17, B167 9,
B169 5, B158 6, B102 16, B122 12, B103 13, B124 6. Temp dirs left 0.

## Checks

- **The diff:** `b181.diff` applies on a clean export of `8f1e99ed`, every file byte for byte the tree (9 of 9);
  `git diff --check` clean (`apply_check.txt`). The tests ran on a work copy whose code is byte for byte the tree.
- **No title, game id, setup id, serial, path or address** in any file this queue wrote. BF's three checks, reused
  unchanged: `redact_check.txt`, `id_check.txt`, `title_check.txt`. They ran after every file was written.
- **No picture in git:** the label pictures, the digit sheets and T90's picture copies stayed in the scratch, removed
  after the record with the work copies.
- **Read only:** the real rules folder, the tool's T90 folder, the users' slots, the kept H7 folders.
- **Nothing a hard rule forbids:** no stream, no restart, no flag set on the hub, no adb, nothing fetched or
  installed.
