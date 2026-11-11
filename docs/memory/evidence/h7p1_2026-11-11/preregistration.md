# H7-P1 — pre-registration (written and hashed before the search and before anything is erased)

Sources: the task `handoffs/H7-P1_REAL_SEARCH_AND_PROOF_TASK.md`; B's rows `handoffs/SESSION_B_DONE_2026-11-11AI.md`
§"A — H7-P1" (used as written); `evidence/B94_H7_RULE_SEARCH_2026-11-11.md` (the templates, "decided");
`evidence/B95_H7_STATE_AS_IS_2026-11-11.md` (`--as-is --runs 3`). Unattended: no TV, no onn, no stream, no adb.

## The inputs — T88 (a PS1 title; HOME-12V's 2-player test), three states, each with the user's fact

| slot | label | the fact (the user's words, verbatim; a title or character replaced by its label) |
| --- | --- | --- |
| 3 | `begin`, winner null | "I saved begin in slot 3" (HOME-12V) |
| 2 | `end`, **P1** | "Player 1 and [the player-1 character] wins! (I saved begin in slot 3 and end in slot 2)" (HOME-12V) |
| 1 | `end`, **P2** | "I saved player 2 winning under slot 1" (to Cowork, after HOME-12V) |

The user's request (HOME-12V): "Can you erase these saves when you don't need them?" — running this task is the user's
word for the erase step below, under its conditions only.

## The slot checks (done before this file; `pre/slot_checks.txt`)

Slot 3 2026-11-11T08:03:38Z 1,678,205 bytes; slot 2 08:08:47Z 2,184,533 bytes (HOME-12V's); slot 1 08:24:09Z, newer
than HOME-12V's close (08:09Z). All as expected.

## "Decided" (B94's)

A template leaves exactly one candidate. The rule is the first decided in **a, b** order ((a) a per-player counter,
(b) a per-player level that empties). **A decided (c) (a single winner field) alone is not taken as the rule** (B's note:
(c) also fits memory that merely changes with time).

## The proof (met / not met)

With the decided rule, `tools/h7_minigame_proof.py --system ps1 --state <copy> --as-is --runs 3 --rule rule.json` per
state:
- `begin` → `"winner": null` ("no winner yet") **3 of 3**;
- the P1 end → **P1 3 of 3**;
- the P2 end → **P2 3 of 3**.
All three → **met**. Anything else → **not met** (the lines recorded). No rule decided → **not decided**.

## The headless load check (before the search; not a verdict)

One `--as-is` load of the `begin` copy with a throwaway rule: RetroArch's `Loading state … N bytes` with N > 0, no
failure line, the core's own lines showing the content started. A missing BIOS in the tool's temp system folder → the
tool's own system-folder option if it has one (it has none: `--help`), else symbolic links to the hub's BIOS files in
the temp system folder by the smallest change to how A calls the tool (B's tools not edited; the hub's folder only
read); neither works → stop, the exact line recorded for B. The core options' counts (the hub's PS1 games vs the
headless session) noted.

## The erase rule

Only if **decided and met**: the three copies moved to a kept folder off the repo and off the user's slots, on the
hub's own disk (`begin.state`, `end_p1.state`, `end_p2.state`, `rule.json`, `SHA256SUMS`), each copy's sha256 equal to
its slot's file before any erase; then T88's slots 1, 2 and 3 erased (the hub's own slot delete if it has one, else the
slot's state file and its picture removed) and read back: the hub's listing for T88 shows the three slots empty; T88's
other slots and every other game's saves before = after (count and hash); the game's Continue copy not touched (it
holds the last save made). Any copy's hash different, or not met, or not decided → **nothing is erased**.
