---
memory_schema: 1
as_of: 2026-11-11
status: TASK HANDOFF — H7-P1, the real win-rule search and proof on T88's three save states (session A, **unattended: no TV, no onn, no stream, nothing asked of the user**; RetroArch headless on the hub's display in temp folders, on copies of the states; the hub's saves untouched until the erase step). Pre-registered: the proof is met when, read as they stand, the "begin" state names no winner, the "end" state won by player 1 names P1 and the "end" state won by player 2 names P2, 3 of 3 loads each. **Only if met:** the three states kept as copies off the user's slots, then T88's slots 1, 2 and 3 erased (the user's request). Nothing adopted; nothing committed
---

# H7-P1 — where the game keeps who won: the search and the proof on the real states

Read first: `SESSION_B_DONE_2026-11-11AI.md` §"A — H7-P1" (**the preconditions, the run's commands, the rows and the record's shape are B's — use them exactly**, with the additions below), `B94_H7_RULE_SEARCH_2026-11-11.md` (the three templates; "decided" only when a template leaves exactly one; "Disclosed": chance fits from memory that changes with time; what is not found), `B95_H7_STATE_AS_IS_2026-11-11.md` (`--as-is --runs 3`; "no winner yet"; the load check), `HOME_12V_PARITY_2026-11-11.md` §"The optional H7 step" and `home12v_2026-11-11/h7/H7.md` (T88; the states' slots; the user's lines), `docs/ROADMAP.md` §H7 (the proof's statement as B95 rewrote it), `docs/memory/CURRENT.md`.

**The inputs — T88 (a PS1 title; HOME-12V's 2-player test), three states, each with the fact the user gave:**

| slot | label | the fact (the user's words) |
| --- | --- | --- |
| 3 | "begin" | HOME-12V: "I saved begin in slot 3" — just before the fight |
| 2 | "end", **P1** won | HOME-12V: "Player 1 and [the player-1 character] wins! (I saved begin in slot 3 and end in slot 2)" |
| 1 | "end", **P2** won | to Cowork, 2026-11-11, after HOME-12V: **"I saved player 2 winning under slot 1"** |

**A writes these lines verbatim into the record** (a title or character in a line replaced by its label, HOME-12R's rule). The user's request, HOME-12V: "Can you erase these saves when you don't need them?"

**Additions to B's sketch (Cowork's):**

1. **The slots are checked before anything is copied.** Each of T88's slot 1, 2, 3 state files: present; its time. Slot 3 and slot 2 must carry HOME-12V's times (08:03:38Z and 08:08:47Z, 2026-11-11) and sizes (1,678,205 and 2,184,533 bytes); **slot 1 must be newer than HOME-12V's close (08:09Z)** — the user's player-2 save. Anything else → stop: "YOU, now:" and say which slot is not what the task expects; nothing copied, nothing erased.
2. **The real title must load headless before the search is trusted.** B's PS1 fixture did not run its own code headless because the tool's temp system folder holds no BIOS. Before the search: one `--as-is` load of the "begin" copy with a throwaway rule — RetroArch's `Loading state … N bytes` line with N > 0 and no failure line, and the core's own lines show the content started. If it fails for a missing BIOS in the temp system folder: use the tool's own option for the system folder if it has one; otherwise place **symbolic links** to the hub's BIOS files in the temp system folder (read-only use; nothing copied, the hub's folder untouched) by the smallest change to how A calls the tool — **A does not edit B's tools**; if neither works, stop and record the exact line for B. The core options the hub's PS1 games run with are noted (counts only) beside the ones the headless session used; a state that loads with a warning is recorded.
3. **Three states from the start** — the `states.json` holds begin, the P1 end and the P2 end, so template (c) is testable. B's note stands: (c) as written also fits memory that merely changes with time and will not decide; a decided (a) or (b) is what the proof uses.
4. **If not decided:** the counts per template, the tool's `would_split`, and the top five candidates per template with their values in the three states (addresses are the game's, not an identifier — recorded). The reply names the one hand step that would split it in the user's terms, and says plainly that nothing was erased.
5. **If decided and the proof is met — keep copies, then erase the user's three slots** (the user's request; the user was told in Cowork's hand steps that running this prompt is their word for it):
   - the three copies moved to a kept folder **off the repo and off the user's save slots** (`~/privyhub_h7/t88/` on the hub's own disk: `begin.state`, `end_p1.state`, `end_p2.state`, the decided `rule.json`, and a `SHA256SUMS`) — the "begin" copy is the mini game's starting state for later; each copy's sha256 equal to its slot's file before any erase;
   - **then** T88's slots 1, 2 and 3 erased — through the hub's own delete for a slot if it has one, else the slot's state file and its picture removed — and read back: the hub's own listing for T88 shows those three slots empty; T88's other slots and every other game's saves before = after (a listing by count and hash); the game's "Continue" copy is **not** touched (it is how SAVE works; noted in the record that it holds the last save made);
   - if any copy's hash differs, or the proof is not met, or the search is not decided → **nothing is erased**.
6. **No companion restart** (queue AI is tools and tests only — confirm from `git show --stat` that its commit touches nothing under `companion/`; if it does, stop and say so). No adb, no onn.

## Preconditions (B's, exactly)

HEAD named with queue AI committed and the tree clean (else "YOU, now: commit queue AI first, then send the read line again"); only the companion and `privyhub-diag`; **no game running on the hub** (the status read `"active": false`; if a game is running, stop: "YOU, now: a game is running on the hub; end it and send the read line again") — RetroArch runs headless on the hub's display; `/tmp` ≥ 1 GB; outside 04:30-05:30Z (inside it: "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that"); eighteen `PRIVYHUB_` lines, `--check` ok.

## The run (B's commands; the pre-registration hashed before the search)

- **Pre-registered, hashed first:** the inputs and facts above; the slot checks; "decided" = B94's (a template leaves exactly one; the first decided in a, b order is the rule — a decided (c) alone is **not** taken as the rule, B's note); **the proof met** = `--as-is --runs 3` per state: begin → `"winner": null` ("no winner yet") 3 of 3; the P1 end → P1 3 of 3; the P2 end → P2 3 of 3; anything else not met; the erase rule (addition 5).
- The copies into a temp folder under `~/.cache`; the headless load check (addition 2); the search with `--time`; the rows: the read and search seconds, `unstable_bytes`, the count per template, `decided`, the rule and its template.
- Decided → the rule written out; the three `--as-is --runs 3` lines; the verdict.
- RetroArch processes counted after every set (0; a count that is not 0 explained).

## The close and the record

- Nothing running; eighteen lines; `--check` ok; the companion and the keeper not restarted; the drive before = after; the hub's saves: T88's three slots erased or untouched (as the rule says), everything else before = after.
- **The record** `evidence/H7_P1_<the UTC date>.md` + dir (the inputs by slot and fact, the user's lines verbatim; the slot checks; the headless load check and what it needed; the search's seconds and counts, decided or not, the rule; the as-is lines per state; the verdict — met / not met / not decided; the kept folder named by what it holds, no path; the erase read-back or "nothing erased"; T-labels; no title, character name, serial, game id or path; `redact_check`); `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §H7 lines (the first real proof: its verdict; what waits — the same read at the end of a fight played on the stream; the 4-player title; a stricter single-field template; N64's search; Godot's probe and the game repo, both a fetch on the user's word); `logs/h7p1_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after).
- **The reply begins "YOU, now: commit"**, then in plain words: whether the hub found where the game keeps who won; the three reads (no winner yet / player 1 / player 2) with their "3 of 3"; whether the three saves were erased or kept, and why; if not decided, the one step that would settle it.

No sudo, no nft, the Opal read-only, no adb, no stream; no addresses of the network, titles, serials, game ids, character names or paths anywhere in git; nothing written to the drive; nothing fetched; B's tools not edited; nothing deleted but T88's three proof slots under addition 5; no `e3_flag.conf`; nothing adopted; nothing committed.
