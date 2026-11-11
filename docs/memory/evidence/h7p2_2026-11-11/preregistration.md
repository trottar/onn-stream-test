# H7-P2 — pre-registration (written and hashed before the search and before anything is erased)

Sources: the task `handoffs/H7-P2_SEARCH_WITH_HINTS_TASK.md`; B's rows `handoffs/SESSION_B_DONE_2026-11-11AJ.md`
§"A — H7-P2" (used as written); `evidence/B96_H7_HELD_OUT_AND_FAMILIES_2026-11-11.md`,
`evidence/B97_H7_CHEAT_HINTS_AND_LEVEL_2026-11-11.md`; H7-P1's record. Unattended: no TV, no onn, no stream, no adb;
RetroArch headless on copies only; B's tools not edited.

## The inputs — T88 (the PS1 title of HOME-12V's 2-player test), with the user's facts (verbatim; a character replaced by its label)

| slot | label | the user's words |
| --- | --- | --- |
| 3 | `begin` | "I saved begin in slot 3" |
| 2 | `end`, P1 | "Player 1 and [the player-1 character] wins! (I saved begin in slot 3 and end in slot 2)" |
| 1 | `end`, P2 | "I saved player 2 winning under slot 1" |

The read line came alone — **no further "end" named → three states.** The onn offers save slots 1-3; slot 9 is the hub's.

## The copy checks (done before this file; `pre/copy_checks.txt`) and the kept folder

The three copies in A's kept H7-P1 folder equal H7-P1's recorded hashes and — every slot still at H7-P1's time and
size — their slot's file. They are copied next to a kept folder off the cache and off the user's slots, on the hub's
own disk (`begin.state`, `end_p1.state`, `end_p2.state`, `SHA256SUMS`; later a decided `rule.json`), each read back by
hash. A kept copy missing or different → stop, nothing searched or erased.

## "Decided" (B96 / B97's "strong" AND this acceptance rule)

The tool's evidence `"strong"` **and** its answer's template is **a** or **b**, or its family is **hinted**, or it is a
hinted set (template **h**). A non-hinted **(b2)** answer or a **(c)** answer is recorded and treated as **"weak"** — no
proof, no erase. **With three states the expected level is "weak"; that is not a failure of the run.**

## The proof (only if decided)

`tools/h7_minigame_proof.py --system ps1 --state <copy> --as-is --runs 3 --rule rule.json` per state: `begin` →
`"winner": null` ("no winner yet") **3 of 3**; every `end` → its winner **3 of 3** → **met**; anything else → not met.

## The erase rule (only if decided and met)

`rule.json` into the kept folder; each kept copy's sha256 checked again just before; then T88's slots 1, 2 and 3 erased
(the user's request at HOME-12V, "Can you erase these saves when you don't need them?" — running this prompt is the
user's word for it, checked copies kept) through the hub's own slot delete if it has one, else the slot's state file and
its picture removed; read back: the three slots empty in the hub's listing; T88's slot 9, its Continue copy and every
other game's saves before = after (count and hash). Not decided, not met, or a kept copy's hash differing → **nothing
erased**.

## What is recorded either way

The hints by counts only (by player and kind); the search rows (per template a, b, c, b2, h: count, families_found,
passing_count, evidence level, folds run / skipped; hinted sets found / tested / hold; the top five passing families;
every hinted set that holds with its values; evidence, decided, template, would_make_strong); what the cheat list points
at in plain words. **No cheat's description, name or code text anywhere** (B97's `cheat_name_check.py` over the record).
