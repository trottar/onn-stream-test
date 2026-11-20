# B171 + B172 — several saves per ending; learn says which save to add; the solo mark ends at close (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-20BE.md` §B171, §B172. Baseline `6d4a6c44`. **The tool only** (`tools/party_add_game.py`);
the learner (`tools/h7_endscreen.py`) not changed; no bar in `BARS` changed; no companion change.

## Settled first (B171's first bullet)

**What a source is to the learner.** `h7_endscreen.learn` takes one or several (runs folder, labels) pairs; a pair is a
"source". Amendment 3: two classes make the outcome mask only where both have frames **in one source**. The tool gives
one pair: its pictures folder, every kept save one run in it, each run's frames labelled with the save's class. So the
outcome mask is: per pixel, the largest difference between two classes' mean ranks, kept only where that difference is
over 0.25 **and over 3 x the widest within-class spread** (10th-90th percentile over every frame of a class). The
held-out split halves every labelled range (learn on the first half, score on the second): both halves of one save.

**Why one save per ending fails on T88 (and must).** With one still save per ending, the within-class spread is only
the save's noise, so every pixel where the saves differ for any reason — the characters picked, the cursor, the
begin's empty select screen against the endings' filled one — is "outcome". The endings share most of those pixels;
the win tally is a few of them; the distance between end_P1's and end_P2's references over that mask is small: not
separable, margin 0.0164, unknown 0.6552 (run 6). T88's real spec's outcome mask is **104 px, the tallies alone**,
learnt from three sittings.

**Shown with the learner itself on made-up near-alike screens** (scratch, off the repo, before this design: a still
select screen, two portraits per match, a two-digit tally of 2-px segments; one picture every other 0.5-s tick, as on
the hub):

| saves | margin_needed | separable | held-out unknown | outcome mask |
| --- | --- | --- | --- | --- |
| one per ending, the same characters in both matches | 0.0032 | end_P1, end_P2 no | 0.667 | 3,710 px |
| the same, a picture every tick (twice the pictures) | 0.0032 | end_P1, end_P2 no | 0.667 | 3,709 px |
| two per ending, the second of each **the same look** | 0.0032 | no | 0.80 | 3,710 px |
| two per ending, the second of each **other characters** | **0.159** | yes | 0 | **64 px (the tallies)** |
| three per ending, other characters | 0.158 | yes | 0 | 64 px |
| far-apart endings (a large side banner), one or two per ending | 0.119 / 0.196 | yes | 0 | 5,620 / 2,002 px |
| one per ending, **different** characters in each match | 0.167 — **passes** | yes | 0 | 5,888 px |

So: **the learner separates two near-alike end screens when every ending is seen in at least two matches whose
incidental look differs** (other characters, another stage, the cursor elsewhere) — then the pixels that change with
the match have a within-class spread and drop out, and only what tells the outcome stays. **More pictures of the same
save do not help** (the same picture with its noise; twice the ticks changed nothing), nor does a second save of the
same match. The last row is the danger the other way: one save per ending from matches with different characters
passes learn on the characters — a weak spec the bars cannot see. **Two saves per ending, each from a different match,
are therefore the minimum** for a `winner` title; a third or fourth when learn still asks.

**T88's kept `end_p1_b` / `end_p2_b`:** mid-fight saves (H7-P3: "player 1 ahead" / "player 2 ahead", nobody knocked
out) of plain play. From them the fight runs on with nobody playing; the round's time-out comes at 27 s / 35 s, then a
winner's pose and "round 2" — never the select screen with a tally, and not within the capture's 20 s; the real rules
read them `other` on every frame (run 6: `[null, null]`). The capture loads no setup's cheats, and a setup does not
change a mid-fight save into an end screen. **They are not end screens; they cannot serve as second sources.** They
stay read, not a role.

## B171 — the design

1. **Roles.** An ending may have up to `SAVES_PER_ENDING_MAX = 4` saves: `end_P<k>`, `end_P<k>_2`, `end_P<k>_3`,
   `end_P<k>_4`; for places `end_r<row>`, `end_r<row>_2` … `_4`. `ROLE` takes the suffixes `_2`..`_4`. The cap is a
   constant beside `BARS`, not a bar (no bar changed): the most saves the tool asks for, from T88's three sittings plus
   one. Each save is one run in the learner's one labelled folder; its class is the role without the suffix
   (`_role_class`). The learner unchanged.
2. **register asks for two per ending from the start** (`winner`): the roles needed are `begin`, `other`, and for each
   player `end_P<k>`, `end_P<k>_2`. Its "missing" names them. A third / fourth save of an ending is accepted (up to
   the cap); an ending of a player the title has not is still "another kind". **`places`:** unchanged minimum (the
   rows covering every place in every column — each row a different match by necessity); a further save of a row
   `end_r<row>_<n>` accepted.
3. **learn says which save to add.** When any of these cells is not met — `every class separable`, `margin_needed`,
   `held-out frames read unknown (share)`, or a replay cell (`<role>: ended as itself`, `ended within`, `never
   ended`, `recognised within`) — learn's page ends with **one plain line** and its verdict records it
   (`recorded: {"one more save": <role>}`), and it is printed:
   - **which ending:** the endings the not-met cells name — the separable cell's end classes; a replay cell's ending;
     the endings whose held-out frames read unknown; none named (margin alone, or only the start) → every ending —
     the one with the fewest saves, then the lowest name; its next free role (`end_P1_3` …). Two players from
     register's minimum: `end_P1_3`, then `end_P2_3`, then `end_P1_4`, `end_P2_4`.
   - **the line, word for word** (winner): "One more save: <role> — the screen after a match player <k> won, from a
     match not saved yet (other characters or another stage than its saves kept); save it to a free slot, then
     register <code> … --collect <role>=<slot> and learn <code> again."
     (places): "One more save: a results screen from a match not saved yet; collect it as end_r<its row>, or
     end_r<its row>_<n> when that row is kept already, then learn <code> again."
   - **the cap:** when every ending named already has 4 saves (places: 4 x players results saves in all), no role is
     named; the line instead: "The end screens cannot be told apart this way: <endings> have 4 saves each from
     different matches and learn still does not meet its bars. Instead: another mode whose end screen shows who won
     by player, or save each ending on another screen that shows it, and start the title's saves again."
     (`recorded: {"cannot be told apart": [...]}`.)
   - Not for other failures (pictures made, a rules file of another title): no line. A PASS: no line.
   - After `register … --collect <that role>=<slot>`, learn runs again with **the same bars every time**.
4. **Pictures reused.** learn's pictures were made again for every change of the kept states; now each save's run is
   kept while its state's sha256 is the same, and only a new or changed save is captured (one capture per added
   save, not all of them).
5. **rehearse uses every usable kept ending.** Each kept extra ending (`end_p<k>_<x>`) is captured and read with the
   real rules **before** learn: one the real rules end on as its own ending becomes a learning role (`end_P<k>_<n>`,
   the next free, up to the cap); one they do not stays "read, not a role" (its reason in the note: "not an end
   screen to the real rules"). A learning role's ending is compared by its class (`end_P1_2` reads as `end_P1`).
   `rehearse --collect` takes the suffixed roles (`end_P1_2=<slot>` …). **A save rehearse collects is kept** in the
   title's own add_game folder (`~/privyhub_h7/add_game/<code>/kept/`, the tool's, off the repo; the kept H7 folder
   is never written), so the user may save over the slot and a later rehearse takes it from there (`--collect` again
   replaces it). Under a setup only slots 2 and 3 are free — T88 needs `other` and two more saves at least.
   rehearse's page carries learn's line ("--collect <role>=<slot>" in place of register) and lists the endings
   **below two saves** (a new title's minimum), apart from what is missing for learn to run at all.
6. **What rehearse T88 will show** (predicted, run after the tests): the kept end_p1 / end_p2 the only usable endings;
   end_p1_b / end_p2_b not end screens; learn FAIL in the scratch as run 6; the line naming `end_P1_2`; below two
   saves: `end_P1_2`, `end_P2_2`; the real rules folder before = after.

## B172 — the solo mark ends at close

`close` (after its cells are read) ends the title's solo mark and the files' and in-game saves' befores (the tool's own
files `solo_mark.json`, `files_before.json`, `saves_before.json` in the title's add_game folder), so the next solo
writes its own mark and before and reads only its own rows. **register** (the first stage of every use) also ends a
mark an earlier use left unclosed — T88's add_game folder holds the first use's mark from 11-19.

## Tests (`tests/b171_more_saves/`, made-up near-alike and far-apart screens; temp dirs removed)

1. register: one save per ending → FAIL, missing `end_P1_2`, `end_P2_2`.
2. near-alike, two per ending of the same look → learn FAIL, the line names `end_P1_3`; collected (other characters)
   → FAIL naming `end_P2_3`; collected → **PASS**, no line; the bars untouched.
3. far-apart screens: two per ending → PASS at once.
4. the cap: two endings that look the same → asked up to `_4` each → the cap's line, no role, FAIL.
5. rehearse of a made-up title already added, one save per ending (T88's shape) → FAIL naming `end_P1_2`; `--collect
   end_P1_2=2` → FAIL naming `end_P2_2`; `--collect end_P2_2=3` (slot 2 saved over since: the kept copy used) → PASS.
6. rehearse: a kept extra the real rules end on → a role; one they do not (mid-fight) → read, not a role.
7. pictures reused: an added save captures only itself.
8. no title, id or path in anything written or printed; run twice → the same bytes.
9. B172: solo → close → solo: the second mark is new, the first's rows not read; register ends a left mark.
**Mutations:** the ask cells ignored (margin always met → a weak spec passes); no line written; the suffix kept as a
class; the cap off; register back to one per ending; every extra promoted; the ask naming a kept role; close keeping
the mark. B157's, B162's, B163's, B167's, B169's suites green (B157's and B163's made-up titles updated for two saves
per ending / the promoted extra — disclosed).
