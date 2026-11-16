---
memory_schema: 1
as_of: 2026-11-16
status: NOTE FOR THE PC SIDE — from PP-H1 (the board game's first run on the hub, 2026-11-16): 24 of the 25 scripted checks pass on the hub; step 19 fails one of its 125 assertions, the same on three runs. The text below the line is for the user to paste to the PC side. Nothing on the hub was edited
---

# For the PC side: step 19 fails one assertion on the hub

Record: `evidence/PP_H1_2026-11-16.md`, `pph1_2026-11-16/checks/`. The hub ran the board game's repo at the commit the user pushed (`21e7e44f`), Godot `4.7.2.stable.official.ed1daf0bf` (the standard Linux build, checksum equal to the published one), headless, with **the import step run fresh on the hub** (there was no `.godot/` cache before).

---

PrivyParty ran on the hub for the first time (Linux, Godot 4.7.2.stable.official.ed1daf0bf, headless, a fresh `--import` with no `.godot/` folder beforehand). 24 of the 25 checks pass. `checks/step19_round_bodies.gd` fails one of 125 assertions, identically on three runs:

    FAIL: the picture wraps round a part's front; its back carries the edges on: Hips has a front, sides and a back
    STEP 19 CHECK: FAIL (1 of 125 assertions)

That is `_wrapped_round` for the Hips piece: it needs more than four corners facing each of front, sides and back, and on the hub one of the three counts is four or fewer. Everything else in step 19 passes, and the game itself runs on the hub under all three renderers at a steady 60 frames a second.

Please: (1) on the PC, in a fresh clone of the repo with no `.godot/` folder, run `--import` and then step 19, to see whether it fails there too — the PC's passing run may rest on an older import cache; (2) print the three counts for Hips (and the other pieces, for comparison) on that fresh clone; (3) decide whether the check sits at its limit or the imported body really differs after a fresh import, fix whichever it is, run all 25, and push to the `hub` remote. The hub side will run the 25 again after the push. Nothing was edited on the hub.
