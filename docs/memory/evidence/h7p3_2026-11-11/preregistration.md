# H7-P3 — pre-registration (written and hashed before the search and before anything is erased)

Sources: the task `handoffs/H7-P3_FIVE_STATES_TASK.md`; B's rows `handoffs/SESSION_B_DONE_2026-11-11AJ.md` §"A — H7-P2"
(the run's commands, the rows and the record's shape — used exactly, with this task's inputs); H7-P2's record and its
`run/search_rows.md`; `evidence/B96_H7_HELD_OUT_AND_FAMILIES_2026-11-11.md`, `evidence/B97_H7_CHEAT_HINTS_AND_LEVEL_2026-11-11.md`.
Unattended: no TV, no onn, no stream, no adb of this run's own (the `--check` precondition reads the APK as every run
does); RetroArch headless on the hub's display, on copies only; B's tools not edited.

## The inputs — T88 (the PS1 title of HOME-12V's 2-player test), five states, with the user's facts (verbatim; a character replaced by its label)

| state | from | label | the user's words |
| --- | --- | --- | --- |
| `begin.state` | the kept folder (slot 3, unchanged) | `begin` | "I saved begin in slot 3" |
| `end_p1.state` | the kept folder (H7-P2) | `end`, P1 | "Player 1 and [the player-1 character] wins! (I saved begin in slot 3 and end in slot 2)" |
| `end_p2.state` | the kept folder (H7-P2) | `end`, P2 | "I saved player 2 winning under slot 1" |
| `end_p1_b.state` | slot 2 as it is now | `end`, P1 | **"slot 2: player 1 ahead"** — mid-fight, player 1 clearly ahead on health, nobody knocked out |
| `end_p2_b.state` | slot 1 as it is now | `end`, P2 | **"slot 1: player 2 ahead"** — mid-fight, player 2 clearly ahead |

The user's message after the read line, verbatim: "slot 2: player 1 ahead, slot 1: player 2 ahead" ("ahead", as said).

## The slot checks (done before this file; `pre/slot_checks.txt`, `pre/kept_folder.txt`)

A slot named in the user's words must be newer than H7-P2's close (2026-11-11T20:15Z) and differ by hash from its kept
copy (named but not newer → stop: "YOU, now: slot N still holds the old save — save the new one over it, then send the
read line again"); a user slot (1-3) newer but not named → stop, the line recorded; slot 3 must equal `begin.state` by
hash. Result: slot 3 = `begin.state`; slot 2 newer (20:24:28Z) and different, named; slot 1 newer (20:25:13Z) and
different, named → **five states**. (T88's slot 9 is the hub's scratch slot, not a user slot — newer, not an input,
not touched.) The two new slot files copied into the kept folder (`end_p1_b.state`, `end_p2_b.state`), read back by
hash, `SHA256SUMS` extended to five lines; the hub's slots untouched.

## "Decided" (B96 / B97's "strong" AND this acceptance rule)

The tool's evidence `"strong"` **and** its answer's template is **a** or **b**, or its family is **hinted**, or it is a
hinted set (template **h**). A non-hinted **(b2)** answer or a **(c)** answer is recorded and treated as **"weak"** — no
proof, no erase.

**Stated beforehand:** the two mid-fight states will rightly fail any rule that only changes when a fight ends (a round
tally, a level that empties, a winner flag set at the knock-out) — that is the point of them. A PrivyParty fight will be
stopped by a clock, and the rule that matters is "who is ahead when time is up".

## The plain-words question this run answers

Does the cheat list's per-player pair (H7-P2: 0 / 0 at begin, 140 / 70 where P1 won, 133 / 140 where P2 won) read
"player 1 higher" in the save where player 1 was ahead mid-fight and "player 2 higher" where player 2 was ahead?
Yes → it is who-is-ahead (health or its like). No → it is not, said plainly, with what else passed.

## The proof (only if decided)

`rule.json` (the search's `rule`) written to the kept folder; per state
`tools/h7_minigame_proof.py --content <T88's game file> --system ps1 --state <copy> --as-is --runs 3 --rule rule.json`:
`begin` → `"winner": null` ("no winner yet") **3 of 3**; **each of the four `end` states → its player 3 of 3** → **met**;
anything else → not met.

## The erase rule (only if decided and met)

Every kept copy's sha256 checked against `SHA256SUMS` just before; then T88's slots 1, 2 and 3 erased (the user's request
at HOME-12V, "Can you erase these saves when you don't need them?" — running this prompt is the user's word for it, with
checked copies of all five saves kept) through the hub's own slot delete if it has one, else each slot's state file and
its picture removed; read back: the three slots empty in the hub's listing; T88's slot 9, its Continue copy and every
other game's saves before = after (count and hash). Not decided, not met, or a kept copy's hash differing → **nothing
erased**.

## What is recorded either way

The hints by counts only (by player and kind); the search rows (per template a, b, c, b2, h: count, families_found,
passing_count, evidence level, folds run / skipped; hinted sets found / tested / hold; every hinted set with its values in
all five states and where it fails; the top five passing families per template with their values; evidence, decided,
template, would_make_strong); the plain-words answer; RetroArch processes after every set. **No cheat's description, name
or code text anywhere** (B97's `cheat_name_check.py` over the record).
