---
memory_schema: 1
as_of: 2026-11-20
status: BUILT (B171 several saves per ending, learn's line for one more save; B172 the solo mark ends at close) — the tool only; no bar changed; the learner not changed; nothing adopted
---

# B171 — several saves per ending; learn says which save to add (and B172, the solo mark ends at close)

Queue: `handoffs/QUEUE_2026-11-20BE.md` §B171, §B172. The directory is `b171_2026-11-20/`: the design + `.sha256`
(hashed 2026-11-20T00:37:30Z, before any code), its addendum after the code (hashed), `settle.txt` and its script, the
real run (`runs.md`), the tests ×3, the mutations, the checks, `manifest.sha256`, `b171_b172.diff` (applies on
`6d4a6c44`). Patches: `patches/B171_ADD_GAME_MORE_SAVES.md`, `patches/B172_SOLO_MARK_ENDS.md`.

## Settled first — what the learner needs to tell two near-alike end screens apart

**Each ending seen in at least two matches whose incidental look differs** (other characters, another stage, the cursor
elsewhere). The learner's outcome mask keeps only pixels that differ between classes by more than three times their
widest spread within a class. With one still save per ending, that spread is the save's noise alone, so everything that
changed between the saved matches counts as outcome. T88's endings share most of that, and the tally is a few pixels of
it. With two saves per ending from different matches, what changes with the match has a spread and drops out, and the
tally stays. The real spec's mask is 104 px, the tallies alone, learnt from three sittings.

Shown with the learner itself on made-up near-alike screens (`settle.txt`; the same screens as the tests). All of it
learnt on the same bars:

| saves | margin_needed (bar 0.0796) | not separable | held-out unknown (bar 0.105) | outcome mask |
| --- | --- | --- | --- | --- |
| one per ending, the same characters | 0.0032 | end_P1, end_P2 | 0.667 | 3,710 px |
| the same, **twice the pictures** | 0.0032 | end_P1, end_P2 | 0.667 | 3,709 px |
| two per ending, **the same look** | 0.0032 | end_P1, end_P2 | 0.80 | 3,710 px |
| **two per ending, the second other characters** | **0.159** | none | 0 | **64 px (the tallies)** |
| three per ending, other characters | 0.158 | none | 0 | 64 px |
| far apart (a side banner), one / two per ending | 0.119 / 0.196 | none | 0 | 5,620 / 2,002 px |
| one per ending, different characters in each | 0.167, **a weak pass** | none | 0 | 5,888 px (the characters) |

- **More pictures of one save do not help**, and nor does a second save of the same match. Twice the ticks changed
  nothing, so the capture's half-filled ticks (BD item 2) are not what stops T88.
- **One save per ending can also pass weakly.** When the two matches had different characters, the spec learns the
  characters, not the tally, and the bars cannot see it. So two saves per ending is the minimum.
- **T88's kept `end_p1_b` / `end_p2_b`** are mid-fight saves of plain play ("player 1 / 2 ahead", H7-P3). Nobody
  plays, the round times out at 27 / 35 s, then come a winner's pose and "round 2". There is never a select screen
  with a tally, and none within the capture's 20 s. The real rules read neither as ended (run 6, and again here). A
  setup does not make a mid-fight save an end screen. **They cannot serve as second sources.**

## B171 — built

- **Roles:** an ending has up to `SAVES_PER_ENDING_MAX = 4` saves: `end_P<k>`, `_2`, `_3`, `_4`. Places rows work the
  same way (`end_r<row>_2` …). Each save is one more run for the learner, its class the role without the suffix. The
  cap is a constant beside `BARS`, not in it.
- **register asks for two per ending from the start** (`winner`): `begin`, `other`, `end_P<k>`, `end_P<k>_2`. A third
  or fourth save is accepted; a fifth is refused (`ROLE`). `places` keeps its minimum: the covering rows are different
  matches by necessity.
- **learn's line.** When `every class separable`, `margin_needed`, `held-out frames read unknown`, or a replay cell is
  not met, learn's page ends with one plain line, which is also printed and recorded (`recorded: {"one more save":
  role}`):
  - The line, word for word: "One more save: end_P1_3 — the screen after a match player 1 won, from a match not saved
    yet (other characters or another stage than its saves kept); save it to a free slot, then register <code> …
    --collect end_P1_3=<slot> and learn <code> again."
  - **Which ending:** those the failing cells name (the separable cell's endings, a replay's ending, the endings with
    unknown held-out frames); every ending when only the margin fails; the one with the fewest saves first, then the
    lowest name. For a two-player title the order is `end_P1_3`, `end_P2_3`, `end_P1_4`, `end_P2_4`.
  - **At the cap** the line says instead: "The end screens cannot be told apart this way: end_P1, end_P2 have 4 saves
    each from different matches and learn still does not meet its bars. Instead: another mode whose end screen shows
    who won by player, or save each ending on another screen that shows it, and start the title's saves again."
  - There is no line for other failures (pictures not made), and none on a PASS. The bars are the same every time.
- **Pictures:** each save's run is kept while its state is the same; an added save is the only one captured.
- **rehearse:**
  - It captures each kept extra ending first and reads it with the real rules. One they end on as its own ending
    becomes one more source; one they do not is listed as "not an end screen to the real rules".
  - `--collect` takes the suffixed roles, and **every save it collects is kept** in the title's own add_game folder
    (`kept/`, off the repo; the kept H7 folder is never written). The user may then save over the slot: under a setup
    only slots 2 and 3 are free, and T88 needs `other` plus two more saves.
  - Its page carries learn's line ("… then rehearse <code> --collect <role>=<slot>.") and the endings **below two
    saves per ending**.
- **bench** (added after the hash, `design_addendum_after_code.md`): every save of an ending is benched as that ending.

## rehearse T88, as I ran it — FAIL (one run, `runs.md`)

`rehearse T88 --collect other=2`, run once at 00:54-00:57Z, after `status` and `native-stream-status` showed nothing
running and no client:
- **What was not met:** learn's separable [end_P1, end_P2], margin_needed 0.0165 (bar 0.0796), held-out unknown
  0.6552 (bar 0.105), and the endings' replays.
- **The usable kept endings are end_p1 and end_p2 only.** end_p1_b / end_p2_b were captured and read first: "not an
  end screen to the real rules".
- **The page's line:** "One more save: end_P1_2 — … then rehearse T88 --collect end_P1_2=<slot>." Below two saves per
  ending: `end_P1_2`, `end_P2_2`.
- **Nothing changed that must not:** the real rules folder 15 files, 0 changed; the kept folder and rules folder
  before = after (my own check); the scratch removed.
- **The user's slot 2 was only read.** Its copy is kept by the tool, so `other` no longer needs a slot.

**What T88's rehearsal needs from the user:**
- **At least two saves:** `end_P1_2`, a match P1 wins, and `end_P2_2`, a match P2 wins. Each must be played with other
  characters (or another stage) than the kept end_p1 / end_p2 matches, under its setup, and saved on the select screen
  that shows the tally. They go to slots 2 and 3: `rehearse T88 --collect end_P1_2=2`, then `--collect end_P2_2=3`.
- **Then as learn's line asks:** up to `end_P1_4` / `end_P2_4`.

On the made-up title of T88's shape, the two saves were enough: the asks were `end_P1_2`, then `end_P2_2`, then PASS.
**T88's own rules stand untouched either way:** rehearse never writes the rules folder.

## B172 — built

`close` ends the title's solo mark and the files' and in-game saves' befores. These are the tool's own
`solo_mark.json`, `files_before.json` and `saves_before.json` in its add_game folder. The next solo writes its own mark
from the logs as they are then, and reads only its own rows. **register**, the first stage of a use, also ends a mark
an earlier use left unclosed: T88's add_game folder holds the first use's mark from 11-19, which the next `register
T88` ends.

## Tests (`tests/b171_more_saves/`, 10; made-up screens, a made-up hub on loopback; temp dirs removed)

**B171 (8):**
- One save per ending: register FAIL, missing `end_P1_2`, `end_P2_2`, and learn refused.
- `end_P1_5` is refused; `end_P3_2` is "another kind".
- **Near-alike, two per ending of one look:** learn FAIL with the line naming `end_P1_3`. The test collects each named
  save from another look; learn named `end_P2_3` next, then **PASS** with no line. The bars were checked unchanged after
  every test. Only the added save was captured each time; nothing was named in what was written or printed. learn
  twice gives the same bytes.
- **Far-apart: PASS on two per ending.**
- **The cap:** endings whose screens are the same → asked `end_P1_3`, `end_P2_3`, `end_P1_4`, `end_P2_4`, then the
  cap's line; no role named, FAIL, nothing written to the rules.
- No line when the pictures fail.
- **rehearse, T88's shape:** FAIL naming `end_P1_2`; the mid-fight extra is "not an end screen"; below two saves
  `end_P1_2`, `end_P2_2`. With slot 2 saved over between runs (the tool's copy of `other` used), it named `end_P2_2`,
  then PASS. The real rules and the kept folder stayed the same.
- A kept extra that is an end screen becomes a source.

**B172 (2):**
- solo → read → close ends all three files. The next solo's mark is new, and its read counts 0 switches with no new
  rows (the first solo's 4 are not read again).
- register ends a mark left unclosed.

**Runs:** 10 OK ×3 (`tests_x3.txt`). B163's 7 and B169's 5 ×2 (updated); B157's 17, B162's 17 and B167's 9 ×1.
**Mutations (`tests_mutations.txt`, then `tests_mutations_2.txt`): 11, each caught by some suite.**
- **Weak spec passes:** learn's three bars off (separable, margin, unknown always met) is caught by the near-alike
  test.
- **The margin cell alone always met is not caught by B171's own suite.** The one-save near-alike case also fails
  separability and unknown, so the margin never decides it alone there. The mutation was rerun against B163, whose
  test_3 (its own bar raised past the made-up spec) catches it.
- **Names no role:** no line written; the ask naming a kept role. Both caught.
- **The rest, caught:** the suffix kept as a class, the cap off, register back to one per ending, every extra promoted,
  all pictures made again, rehearse reading by role not class (B171's and B163's suites), and close keeping the mark
  (B172).

**Earlier suites updated, disclosed (no bar, no cell changed):**
- B157: its made-up T90 / T91 collect their second saves, and its missing-state test reads the three missing roles.
- B163: its kept extra `end_p1_b` (end_P1's screen) is now a source.
- B162 / B169: the close-twice tests take a new before between the closes.

## What it does not prove

- **That T88 passes:** that needs the user's two saves (above).
- **That every new title passes on two:** a spec learnt from three made-up looks per ending read looks 2-6 but **not
  look 7**. Learn's held-out split halves each save, so its bars never test a match the spec did not learn from (the
  addendum). Not changed: the queue changes no bar and not the learner's rule.
- **That two matches the user calls "different" are:** the tool cannot tell matches apart from the states. The task's
  line asks for other characters or another stage.
- Four players / places beyond the made-up row case; N64 / SNES on the real capture.
