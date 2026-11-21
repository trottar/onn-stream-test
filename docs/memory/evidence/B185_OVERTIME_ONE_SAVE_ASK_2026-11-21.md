---
memory_schema: 1
as_of: 2026-11-21
status: BUILT (B185 a column only one save fills learnt from it and "shown only here" when left out — never a misread, never read again, never asked of the user; B186 a digit one save shows at least twice learnt from it, each glyph read back by that save's other glyphs, the title's across-save spread within its within-save spread + 0.05 — T90 0.401 against 0.418; B187 the user asked only after two readings differ twice or a sum fails twice, by the match, for the cells in doubt in the line score's form, with that one picture in the git-ignored logs/add_game_ask/; B188 the task's words) — T90 from its seven kept saves, in a scratch: register PASS, label PASS (23 cells), learn PASS (27 cells); no bar lowered; nothing adopted; nothing committed
---

# B185-B188 — overtime counts, one save can teach a digit, the ask is rare and plain

Queue: `handoffs/QUEUE_2026-11-21BI.md`. The directory is `b185_2026-11-21/`:
- the design + `.sha256` (hashed 2026-11-21T00:41:58Z, before any code); the addendum after code + `.sha256`;
- `t90_spread.txt` (B186's settle) and `scripts/t90_spread.py`; `t90/` (register, label, learn pages; the tool's
  lines); `check_ignore.txt`; `template_sha256_before.txt` / `_after.txt`; `task_sha256.txt`;
- the tests, the mutations, the checks, `scripts/`;
- `b185.diff` (applies on `45e8ec97`); `manifest.sha256`.

Patch: `patches/B185_OVERTIME_ONE_SAVE_ASK.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty; T90's second record
committed (`45e8ec97`).

**BG's exception: not used.** The picture source never ran: T90's pictures in the tool's folder were made from exactly
its seven kept states, so a scratch copy of that folder served label and learn. The real T90 folder, the rules folder,
the user's slots and the kept H7 folders only read. Register's library lookup asked the companion for the title's
entry (a read; the title from the binding copy in process, never on a command line or in an output).

**Another session worked in this tree at the same time** (the app's handheld sources, G6 tests and records,
`CURRENT.md`, `PATCH_INDEX.md`, a prompt file): not mine, not touched, not in this diff or the patch.

## Settled — B186's numbers (`t90_spread.txt`)

T90's five end saves, the label stage's first picture of each (the hub's capture, 640 × 480, glyphs 16 px), my readings,
B178's local measure:

| | within one save | across saves |
| --- | --- | --- |
| every digit two saves show, at most | **0.418** (48 pairs) | **0.401** (182 pairs) |
| the same, mean | 0.299 | 0.260 |
| 0 / 2 / 9, at most | 0.336 / 0.418 / 0.366 | 0.374 / 0.357 / 0.401 |

- Across is 0.017 below within at the most, 0.040 on the mean: one font, drawn the same in every match.
- Two pictures of one save: the same glyph exactly the same (0.000, 59 glyphs).
- Two different digits: at least 0.656 apart.
- The digits only one save shows: 7 (end_P1_2, 9 glyphs, within ≤ 0.343), 6 (end_P2_3, 3, ≤ 0.333), 4 (end_P2_3, 2,
  0.259). Each glyph to its save's other glyphs of that digit 0.228-0.327; to the nearest other digit 0.664-0.811.
- **The margin, from these numbers: 0.05.** T90 sits 0.067 inside it. 0.05 is under half T90's room between the same
  digit (≤ 0.418) and two digits (≥ 0.656), 0.119.

**The numbers support B186; it is built.**

## B185 — a column only one save fills (overtime)

- **The learner:** unchanged in rule. A column's place comes from every save filling it; one save is enough (its
  cell's string on the final's line); a column blank in every save has no place.
- **The left-out reading:** a column the reader learnt without the save has no place for reads `*`; a filled cell
  there is **"shown only here" (`P<k> column <c>`)**, as a digit only that save shows. Never a misread, never read
  again, never sent to the user. A blank cell there reads `_`.
- **Read in full:** when that reader cannot end (a final with a digit only this save shows), its numbers are read at
  their places on the save's first labelled picture, in label and in learn's left-out cell (addendum 1).
- **A save whose rows add up is never refused for which columns it fills.** The sum check, the two readings, the
  places and the last look are unchanged.
- **At the hub, an overtime match now:** the hub reads the finals only (B181), at the FINAL column's place, which an
  overtime screen shares. T90's overtime save through the spec learnt from all seven saves: **"end_P1_2: ended as
  itself [35, 28]" within 2.0 s** — read as any other match.

## B186 — a digit one save shows several times

- **Counted as learnt** when two saves show it (today), **or** one save shows it at least twice, every glyph read back
  as it by templates learnt from the other saves' glyphs and that save's own other glyphs of that digit (never the
  glyph under test, by its place, in any picture), by B178's own thresholds and margin, **and** the title's
  across-save spread ≤ its within-save spread + 0.05.
- **learn's left-out cell** reads a digit only the save shows with those templates; its time to end is then the full
  reader's own (`"1.5 (the full reader's)"`).
- **The every-digit cell** shows what one save taught and the spread.
- **What still gets through:**
  - a digit only one save shows, labelled as another digit only that save shows, in every glyph, with the sums still
    adding up — the last look is then the only guard;
  - a digit one save shows that the game draws differently in other matches (a colour, a highlight) — seen only
    through the spread of the title's other digits.

## B187 — the ask to the user

- **When:** only when a save's two readings differ twice, or its sum fails twice. A read-back contradiction named twice
  gives "Stop: <role> (…) after it was read again twice. Do not ask the user and do not ask for another match: take
  this line back to the chat (Cowork)." Never for a missing sample: those are never named.
- **What it says** (printed; the verdict's line has the final left out):
  "Ask the user about the match player 1 won 27-18 in overtime, kept at <the kept copy's time> (its slot not recorded): player 1's
  Q4, as its final stats screen shows them. YOU, now: ask Cowork to show you the picture of that match; then reply
  with its scores. Then label <code> end_P1_2=<P1 cells>=<P1>-<P2 cells>=<P2>,user — the whole line score, the
  user's numbers in those cells (the picture: logs/add_game_ask/<code>_end_P1_2.png, git-ignored)." (a made-up title)
  - register `--collect` now keeps each role's slot and the slot file's time in the binding: "saved at 6:31 pm to
    slot 2". T90's kept saves were collected before, so they read "kept at …".
  - The hub's clock, 12-hour.
- **The answer:** a `,user` answer on a line-score title must be the whole line score; a final alone is refused.
- **The picture:** the ask copies `label/<role>.1.png` to `logs/add_game_ask/<code>_<role>.png` — that one only.
  `git check-ignore -v` → `.gitignore:2:logs/` (`check_ignore.txt`). `close` removes `<code>_*.png` there.
- No ask ran on the hub in this queue; the folder in this repo was never made.

## B188 — the task's words

`handoffs/ADD_GAME_TASK.md`:
- **the overtime rule** in the label stage — never ask to replace a save whose rows add up;
- **the ask line** as B187, the user's words word for word, the picture through Cowork, never a final alone; the "Stop"
  line;
- **learn's every-digit words:** learnt by two saves or several glyphs of one; with its line, the session says how many
  digits are still short and that learn may ask once more — never that one match is enough;
- §4 the same.

The template unchanged: `aadccb04…` before and after.

## B189 — T90 from its seven kept saves (no new save), in a scratch

| stage | verdict | notes |
| --- | --- | --- |
| register (no `--collect`) | **PASS** (8 cells) | the seven kept saves |
| label, my five readings ×2 | FAIL "Look at label/digits.png …" (22 of 23) | every reading the same, the role's player ahead, every sum, the places found; end_P1, end_P2, end_P2_2 read back exactly; **end_P1_2 "?+?+?+?+*+_=35-?+?+?+?+*+_=28 (shown only here: 7; P1 column 5, P2 column 5)"** met; end_P2_3 "0+?+0+8+_+_=1?-9+3+?+?+_+_=2? (shown only here: 4, 6)" met |
| the last look | my answer `look=all` | sixteen 0s, two 1s, thirteen 2s, two 3s, two 4s, two 5s, three 6s, nine 7s, two 8s, eight 9s — every tile its row's digit |
| label `look=all` | **PASS** (23 cells) | |
| learn | **PASS** (27 cells) | margin 0.2047 ≥ 0.0796; 0 wrong, 0.0 unknown; every end save ended as its finals within ≤ 2.0 s (end_P1_2 [35, 28] in 2.0 s); **left out: all five met** (end_P1_2's OT cells shown only here, its 7s by its own; end_P2_3's 4s and 6s by its own, its end the full reader's 1.5 s); **every digit: none short** — 7 "9 glyphs in end_P1_2, 9 read back", 6 "3 glyphs in end_P2_3, 3 read back", 4 "2 glyphs in end_P2_3, 2 read back"; spread across 0.4009, within 0.4183 |

**My readings, checked against both pictures of each save** (P1 first, Q1-Q4, OT1, OT2, `=` the final) — the
record's, every cell: end_P1 `9+2+2+2+_+_=15-0+0+2+0+_+_=2`; end_P1_2 `7+7+7+7+7+_=35-7+7+7+7+0+_=28`; end_P2
`0+0+0+0+_+_=0-2+9+2+9+_+_=22`; end_P2_2 `0+0+0+0+_+_=0-9+9+2+9+_+_=29`; end_P2_3 `0+6+0+8+_+_=14-9+3+6+6+_+_=24`.

**learn passes — stopped there.** Bench and solo are session A's with the user. The pass is in the scratch: the real T90
folder still holds the second run's label record (end_P1_2 the user's `35-28`), so session A runs register, label (the
five readings), the look and learn for real; the rules folder is written then.

## Tests, mutations

**B185's suite, 9 tests** (`tests/b185_overtime/`, B181's made-up line-score screens):
- **`Overtime`:**
  - one save fills OT1 → label PASS, its OT cells "shown only here", never read again; learn PASS; the column learnt
    from that one save;
  - two overtime saves → the column read back in each left out;
  - a filled OT cell breaking the sum still named;
  - **T90's shape** (the overtime save the only one with a 7, nine of them) → label twice, never read again or asked;
    learn PASS, the 7 learnt from its own nine.
- **`OneSave`:** a digit one save shows three times → learnt, learn PASS, the spread within its bar; shown once → short,
  learn FAIL, its line "1 digit is still short (6); if one is still short after that match, learn asks for one more."
- **`Ask`:** two readings differing twice → the ask (who won, the final, "in overtime", when kept, "player 1's Q4"),
  the picture in the ask folder (only it), the final not in the verdict or its page; a final alone refused; the line
  score with the user's numbers → PASS; close removes the picture. A sum failing twice → that side's every cell. A
  read-back contradiction twice → the "Stop" line, never the user, no picture.

**Three runs of B185's suite, 9 OK each** (`tests_x3.txt`, temp dirs left 0). **B181's 7 and B178's 23, two runs OK
each.** B175 9, B171 10, B163 7, B157 17 (T88 / T89 `--check`, read only), B162 17, B167 9, B169 5, B158 6, B102 16,
B122 12, B103 13, B124 6 — green.

**Mutations, 5 of 5 caught** (`tests_mutations.txt`; temp dirs left 0):
- a one-save column refused (its `*` taken as a misread) → `Overtime.test_1`;
- a missing sample asked of the user (a digit only that save shows taken as not read, and a read-back reason asked) →
  `Overtime.test_4` (T90's shape) — two changes in one mutation, disclosed;
- the user asked for a read-back contradiction → `Ask.test_3`;
- a final alone taken on a line-score title → `Ask.test_1`;
- a digit seen once counted (the glyph under test in its own template, and one glyph enough) → `OneSave.test_2` — two
  changes: either alone is stopped by the other (one glyph leaves no template; a template holding the glyph still needs
  two), disclosed.
- Not mutated: the across-save bar (no made-up title draws one digit two ways).

**Disclosed:**
- **B178's tests changed:** the ask's words; the ask folder in the harness's temp dir; end_P1's read-back now
  `?5-2 (shown only here: 1)`; the 16-for-15 misread now named at the first label, read right → PASS.
- **B181's test:** its every-digit cell compared by its one key (the cell now also says what one save taught).
- **The made-up font's own thresholds are tight** (noise ±2): at some noise seeds a reader learnt without a save misses
  that save's 5s and 8s — HEAD's code too (N = 18, 24, 36 fail, 0 passes, on B181's own test_3 saves; margin needed
  0.006). B181's suite passes by its order. **B185's tests pin their seeds** (the state counter from 0 in each test).
  T90's real thresholds are not near this.
- A `pkill` of mine ended its own shell once; one temp dir of the killed run removed, the run made again.

## Checks

- **The diff:** `b185.diff` (my six files only) applies on a clean export of `45e8ec97`, every file byte for byte the
  tree (6 of 6); `git diff --check` clean (`apply_check.txt`). The tests ran on a work copy whose code is byte for
  byte the tree.
- **No title, game id, setup id, serial, team, path or address** in any file this queue wrote: BF's three checks,
  reused unchanged (`redact_check.txt`, `id_check.txt`, `title_check.txt`), run after every file was written.
- **No picture in git:** the label pictures, the digit sheet, my strips of the line scores and T90's copies stayed in
  the scratch off the repo, removed after the record with the work copies' outputs; `logs/add_game_ask/` never made
  here.
- **Read only:** the real T90 folder, the rules folder, the user's slots and in-game saves, the kept H7 folders.
- **Nothing a hard rule forbids:** no stream, no restart, no flag set, no adb, no sudo, no nft, nothing fetched or
  installed, nothing written to the drive; the app and the board's repo not touched.
