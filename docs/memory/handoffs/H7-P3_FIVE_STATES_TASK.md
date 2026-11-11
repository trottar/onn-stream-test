---
memory_schema: 1
as_of: 2026-11-11
status: TASK HANDOFF — H7-P3, the search on five states and the proof (session A, **unattended: no TV, no onn, no stream, nothing asked of the user**; RetroArch headless on the hub's display, on copies only). The user adds two saves made **in the middle of a fight** — slot 2 with player 1 clearly ahead on health, slot 1 with player 2 clearly ahead, nobody knocked out — because a PrivyParty fight will be stopped by a clock, and the rule that matters is "who is ahead when time is up". With the three kept copies that is two "end" states per winner. Accepted answer → the proof on all five → the copies kept, T88's slots 1-3 erased. Nothing adopted; nothing committed
---

# H7-P3 — five states: is the cheat list's pair really "who is ahead"?

Read first: `H7_P2_2026-11-11.md` and `h7p2_2026-11-11/run/search_rows.md` (the hinted pair and its values; the kept folder; the pre-registered acceptance rule), `SESSION_B_DONE_2026-11-11AJ.md` §"A — H7-P2" (**the run's commands, the rows and the record's shape — used exactly, with this task's inputs**), `B96_…` / `B97_…` (folds, evidence levels, hints, template h, (b2)'s cap), `H7-P2_SEARCH_WITH_HINTS_TASK.md` (the additions that still hold: the acceptance rule, no cheat text anywhere, B's tools not edited), `docs/ROADMAP.md` §H7, `docs/memory/CURRENT.md`.

**What H7-P2 left** (the record): the game's cheat list points at one per-player level pair; in the three saves it reads 0 / 0 before the fight, 140 / 70 in the save player 1 won, 133 / 140 in the save player 2 won — the right way round each time, **but the loser is not at 0**, so it is not yet shown to be health. Evidence "weak" (each winner seen once). The three saves are held as checked copies in the kept folder.

**The inputs — five states:**

| state | from | label | the fact |
| --- | --- | --- | --- |
| `begin.state` | the kept folder (slot 3, unchanged) | "begin" | "I saved begin in slot 3" |
| `end_p1.state` | the kept folder | "end", P1 | "Player 1 and [the player-1 character] wins! (I saved begin in slot 3 and end in slot 2)" |
| `end_p2.state` | the kept folder | "end", P2 | "I saved player 2 winning under slot 1" |
| `end_p1_b.state` | **slot 2 as it is now** | "end", P1 | the user's words after the read line: **"slot 2: player 1 ahead"** — mid-fight, player 1 clearly ahead on health, nobody knocked out |
| `end_p2_b.state` | **slot 1 as it is now** | "end", P2 | the user's words after the read line: **"slot 1: player 2 ahead"** — mid-fight, player 2 clearly ahead |

**The two new facts are taken only from the user's own words in the message after the read line** ("ahead" or "won" — recorded as said, verbatim). A slot named in the words must be **newer than H7-P2's close (20:15Z, 2026-11-11)** and differ by hash from its kept copy; named but not newer → stop: "YOU, now: slot N still holds the old save — save the new one over it, then send the read line again"; a slot newer but not named → stop, the line recorded. Slot 3 must still equal `begin.state` by hash. With only one new slot named, the run goes on with four states and says what is still missing. With none named → stop: "YOU, now:" and the hand step below.

## Preconditions

HEAD named with H7-P2 committed and the tree clean (else "YOU, now: commit first, then send the read line again"); nothing under `companion/` changed since queue AJ (no restart); only the companion and `privyhub-diag`; **no game running on the hub** (else "YOU, now: a game is running on the hub; end it and send the read line again"); `/tmp` ≥ 1 GB; outside 04:30-05:30Z (inside it: "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that"); eighteen `PRIVYHUB_` lines, `--check` ok; the kept folder's three copies read back OK against its `SHA256SUMS`.

## The run (pre-registered and hashed before the search)

- **Pre-registered:** the five inputs and facts; the slot checks; **"decided" = the tool's "strong" AND the acceptance rule** — the answer's template is **a** or **b**, or its family is **hinted**, or it is a hinted set (template **h**); a non-hinted (b2) or a (c) answer is recorded and treated as "weak"; **the proof met** = `--as-is --runs 3` per state: `begin` → "no winner yet" 3 of 3, **each of the four "end" states → its player 3 of 3**; the erase rule below. Stated beforehand: the two mid-fight states will rightly fail any rule that only changes when a fight ends (a round tally, a level that empties) — that is the point of them.
- The two new slot files copied into the kept folder (`end_p1_b.state`, `end_p2_b.state`), read back by hash, `SHA256SUMS` extended; the hub's slots untouched.
- The hint counts; B's search command with `--hints` and `--time` on the five (or four) states; B's rows, as H7-P2's `search_rows.md`: per template the count, families, passing, evidence, folds run / skipped; `hinted_sets`; **every hinted set with its values in all five states and where it fails**; the top five passing families per template with their values; `evidence`, `decided`, `template`.
- **In plain words, the question this run answers:** does the cheat list's pair read "player 1 higher" in the save where player 1 was ahead mid-fight and "player 2 higher" where player 2 was ahead? Yes → it is who-is-ahead (health or its like). No → it is not, said plainly, with what else passed.
- Accepted → the rule written to the kept folder (`rule.json`); the five `--as-is --runs 3` lines; the verdict.
- RetroArch processes counted after every set (0; any other count explained).

## The erase (only when the answer is accepted and the proof is met)

Every kept copy's hash checked just before; then **T88's slots 1, 2 and 3 erased** (the user's request at HOME-12V: "Can you erase these saves when you don't need them?"; the user was told that running this prompt is their word for it and that checked copies of all five saves are kept) — the hub's own slot delete if it has one, else each slot's state file and its picture removed; read back: those three slots empty in the hub's listing; T88's slot 9 and Continue copy and every other game's saves before = after (by count and hash). Not accepted, not met, or a hash differing → **nothing erased**, said plainly.

## The close and the record

- Nothing running; eighteen lines; `--check` ok; the companion and the keeper not restarted; the drive before = after; the hub's saves before = after, or T88's three slots erased and everything else the same.
- **The record** `evidence/H7_P3_<the UTC date>.md` + dir (H7-P2's shape: `pre/`, `run/`, `close/`, the pre-registration and its hash; the inputs with the user's lines verbatim; the slot and copy checks; the hints by counts; the search rows; the plain-words answer; the evidence level and whether the answer was accepted; the proof lines; the erase read-back or "nothing erased"; T-labels; no title, character name, cheat name, serial, game id or path; `title_check`, `redact_check`, `cheat_name_check`); `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 lines (the first real rule: decided or not; **what it does not yet show — the same read on a fight played on the stream, the independent check**; B's note on (b2) and hint pairs; the 4-player title; the candidate list's file `runtime/h7_minigame_candidates.md`, named only); `logs/h7p3_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after).
- **The reply begins "YOU, now: commit"**, then in plain words: whether the cheat list's pair is who-is-ahead; how sure the hub is; the five reads if the proof ran; whether the three slots were erased or kept, and why; what comes next (the same read on a live fight).

## The hand step, if no new slot is named (the user's terms)

"YOU, at the TV when you like (no Code needed): start [T88], LOAD slot 3 (the 'begin' save). Fight until player 1's health bar is clearly fuller than player 2's — nobody knocked out — then Home → SAVE into slot 2. LOAD slot 3 again, fight until player 2 is clearly ahead, SAVE into slot 1. (Both old saves in those slots are held as checked copies.) Then send the read line with: slot 2: player 1 ahead, slot 1: player 2 ahead."

No sudo, no nft, the Opal read-only, no adb, no stream; no network addresses, titles, serials, game ids, character names, cheat names or paths to the drive anywhere in git; nothing written to the drive; nothing fetched; B's tools not edited; nothing deleted but T88's three proof slots under the erase rule; no `e3_flag.conf`; nothing adopted; nothing committed.
