# SESSION B — done, 2026-11-11 AJ (QUEUE_2026-11-11AJ: B96 "decided" by held-out states and families, B97 hints from the cheat list and a level that need not empty; run 16:41-19:35Z)

- **Baseline:** `2e30c1cf` (H7-P1 committed in `132e6f2f`). **Checked first:** only the companion and `privyhub-diag`
  active; `git status --short` empty (the prompt files tracked and unchanged).
- **Not done:** nothing committed or adopted; the companion unchanged (tools and tests only); no companion or keeper
  restart, no stream, no adb, no sudo, no nft, the Opal not touched; `privyhub-diag` and `~/privyhub_diag/` untouched;
  nothing fetched; nothing written to the drive; nothing deleted but B's own scratch (test temp folders, mutation work
  copies, a diff-check copy and the stopped first B97 batch's work copy, all under `~/.cache/b_q21aj_tmp/`); nothing of A's touched (A's kept temp folder under `~/.cache` not opened); **the user's save
  states and A's copies not read, loaded or deleted; no real title started.**
- **RetroArch was run by B, headless, on synthetic fixtures only** (B61's form: B94's PS-X EXE and SNES ROM, no game;
  temp folders under `~/.cache`; the companion's display; no stream, no pad). **Counted by process after every set:
  0** (19:09Z, after both batches). Two intermediate counts read 2: one session of the other item's mutation runner,
  which ran at the same time from its own work copy (B97's 3 runs beside B96's mutations; noted in the files).
- **Found at the close:** B97's cheat-name check (every real description in the hub's lists, never printed) flagged five
  of the fixtures' made-up descriptions — generic phrases that also occur as real cheat names; reworded, the diff
  regenerated (0 FAILS), B97's 3 runs repeated on the new text (3 × 37 / 37, RetroArch 0 after); the mutations not repeated (no mutated code
  touched).
- **The hub's cached cheat lists were read in place for counts only** (B97's settle; no name, title, address or path
  written anywhere).
- **The user's correction to the queue's text** (the onn offers save slots 1 to 3 only; slot 9 is the hub's own) is
  applied below: further "end" states are saves **over slots 2 and 1** once A holds copies of the current ones.

## What was found and built

| Item | Found | Built | Tests | Mutations |
| --- | --- | --- | --- | --- |
| **B96** | "exactly one candidate" cannot be met on a real game; with one winner only, a "P1 is always larger" field would pass every fold (addendum 1) | `tools/h7_rule_search.py`: **families** (an overlapping read; a copy with identical values within 0x100 bytes — one family, its lowest aligned member the rule); **held-out folds** (each "end" held out; a fold with no other example of its winner skipped and counted); **evidence per template** in words and as data — **"decided" = "strong" only** (two ends per winner, two winners, a family passing every fold; the top one the answer); "weak" names the states that would make it strong; template (c) tightened (player number or flag) | 22 (×3 green; PS1 5 states × 3 loads read 73.7 s, the search 0.72 s; folds on a random 2 MiB × 5 states 0.74 s) | 9 / 9 |
| **B97** | PS1 lists: constant RAM writes are types 80 (2 bytes) and 30 (1 byte), the address the 6 digits after the type (all below 2 MiB); 460 codes in 32 of 116 lists name a player; **23 lists give hints, 18 with a matching P1 / P2 pair**; SNES lists name no player | `tools/h7_cheat_hints.py` (the hints, never the text); `--hints FILE` on the search (hinted families first; every per-player hint set tested directly as template h, with its values in every state); **template (b2)**, a level whose loser need not be 0 (paired by equal "begin" values: 133 s → 20 s; **above 200,000 candidates not testable** — a guard for the hub's memory in A's run) | 37 with B96's (×3 green) | 11 / 11 |

**What the fixture answers with three states against five:** begin + one end per winner → **"weak"**: the planted
family passes, every fold is skipped, the tool asks for "one more 'end' won by P1 and one more 'end' won by P2" (and by
the order alone a decoy fitting those three states ranks first — with the cheat list's hints the planted family is
first); **five states → "strong", the planted pair the answer**, its mirror in the same family, the decoys failing the
fold that holds out the state they don't fit.

**One line for the user:** the hub can now tell how sure it is about where a game keeps "who won" — with your three
saves it can only say "probably here" (it also uses the game's own cheat list to point at the right place); one more
save where player 1 wins and one more where player 2 wins would let it say "sure".

**What I would change (the queue's items were done as written):** (1) **(b2) and the directly tested hint pairs should
answer only when hinted** — (b2) is so loose that on random memory with five states ~58,000 families pass every fold;
as built (the queue's words: "hinted or held-out-passing") a non-hinted (b2) family becomes the answer whenever a, b and
c are not strong, and the proof on the same states would then pass trivially. (2) **"Strong" with many passing families
is a ranking pick**, not a unique fit; the proof re-reads the same states, so a fight played later on the stream (H7's
next step) is the real independent check before anything is erased — I would make the erase wait for it, or at least
for a held-out state the search never saw.

## A — H7-P2, the search with folds and hints on T88's states (unattended: no TV, no stream, nothing asked of the user)

**Inputs — T88's states by slot, with the user's facts** (taken only from the user's words in A's prompt):

| slot | label | the fact |
| --- | --- | --- |
| 3 | `begin` | "I saved begin in slot 3" (HOME-12V) |
| 2 | `end`, P1 | HOME-12V: "Player 1 … wins!"; **A's kept copy reused by hash** (H7-P1 `run/copies.txt`: slot-2 copy `a0efb49b9101…`) |
| 1 | `end`, P2 | "I saved player 2 winning under slot 1"; **A's kept copy reused by hash** (`ef011ec5277b…`) |
| 2 or 1, later | a further `end` | **only if the user's words in A's prompt say they saved over slot 2 (player 1 won) or slot 1 (player 2 won)** after A holds the copies above |

**The slots checked by time before copying** (the hub's slot listing; H7-P1's times: slot 3 08:03:38Z 1,678,205 B, slot 2
08:08:47Z 2,184,533 B, slot 1 08:24:09Z 1,939,333 B): a slot with H7-P1's time and size → its file's sha256 must equal A's
kept copy → the kept copy is used (no new copy, not counted twice); slot 2 or 1 newer **and** named in the user's words →
copied as a further `end` with that winner (the kept copy stays the earlier `end`); newer but not named, or a hash that
differs at H7-P1's time → stop, the line recorded, nothing searched. **The hub's saves are never changed until the erase
step.** RetroArch headless loads only copies.

### Preconditions

HEAD with queue AJ committed and the tree clean (else "YOU, now: commit queue AJ first, then send the read line again");
only the companion and `privyhub-diag`; **no game running on the hub** (`curl -s http://127.0.0.1:8765/plugins/games/status`
→ `"active": false`); `/tmp` ≥ 1 GB; outside 04:30-05:30Z.

### The run

```
pid=$(systemctl --user show -p MainPID --value privyhub-companion)
export $(tr '\0' '\n' < /proc/$pid/environ | grep '^DISPLAY=\|^XAUTHORITY=' | xargs)
W=<A's kept H7-P1 temp folder under ~/.cache>            # the three copies; new copies (if any) beside them
python3 tools/h7_cheat_hints.py --system ps1 --cheats <T88's cached list, from data/games/cheats.json> --counts > $W/hints_counts.json
cat > $W/states.json <<EOF
[{"state": "$W/<slot-3 copy>", "label": "begin", "winner": null},
 {"state": "$W/<slot-2 copy>", "label": "end", "winner": "P1"},
 {"state": "$W/<slot-1 copy>", "label": "end", "winner": "P2"}]          # + {"state": …, "label": "end", "winner": "P1"|"P2"} per further end
EOF
python3 tools/h7_rule_search.py --content <T88's game file> --system ps1 --states $W/states.json \
        --hints <T88's cached list> --time > $W/search.json
```

**Rows to record** (memory addresses may be recorded — they are the game's RAM offsets, not an identifier; **the hints
by counts only**: `hints_counts.json`'s by player and kind, codes read, skipped — never a description or a code index's
text): read / search seconds; `unstable_bytes`; per template **a, b, c, b2, h**: `count`, `families_found`,
`passing_count`, `evidence.level`, `folds_run` / `folds_skipped`; `hinted_sets`: found / tested / hold; the top five
passing families per template (addresses, width, members, `hinted`, values in every state); every hinted set that holds
(addresses, kind, values in every state, `found_by`) and the count that fail; `evidence`, `decided`, `template`,
`would_make_strong`.

**Pre-registration** (written and hashed before the search, as H7-P1's): the inputs above; "decided" = the tool's
`"strong"` (B96 / B97); the proof and the erase rule below.

### If "decided" (strong) — the proof, then the erase on the user's word

`python3 -c 'import json;d=json.load(open("'$W'/search.json"));json.dump(d["rule"],open("'$W'/rule.json","w"))'`; per
state: `python3 tools/h7_minigame_proof.py --content <T88's game file> --system ps1 --state $W/<copy> --as-is --runs 3
--rule $W/rule.json`. **Met** when `begin` → `"winner": null` ("no winner yet") **3 of 3** and **every** `end` → its
winner **3 of 3**. Met → **every copy kept off the user's slots** (A's kept folder on the hub's disk: the copies,
`rule.json`, `SHA256SUMS`, each copy's sha256 equal to its slot's file just before), then **the proof slots erased only on
the user's word in A's prompt naming the slots** (the hub's own slot delete; read back: the slots empty; T88's other slots
— slot 9, the Continue copy — and every other game's saves before = after). Not met → nothing erased, the lines recorded.

### If "weak" (expected with today's three states) or "none" — nothing erased

Record the rows above, the top families with their values and the hinted sets' values, and the states that would make it
strong **in the user's terms** (check first how many presses the SAVE confirm is in the onn's list):
**"YOU, at the TV when you like: start [T88] → Continue → LOAD slot 3 (the 'begin' save), play the fight and let player 1
win, then Home → SAVE into slot 2 (it replaces your first 'player 1 won' save — I already hold a copy). Then the same
again with player 2 winning, SAVE into slot 1. Tell me 'slot 2: player 1 won, slot 1: player 2 won'."** — then H7-P2
again with five states.

### The record

`evidence/H7_P2_<date>.md` + `h7p2_<date>/` (`pre/`: slot checks, units, HEAD, the kept copies' hashes; `run/`:
`hints_counts.json`, `search.json`, `search_rows.md`, the proof lines if any; `close/`: processes 0, saves before / after,
drive before = after; `preregistration.md` + `.sha256`; `title_check.*`, `redact_check.txt`, **B97's
`cheat_name_check.py`** over the record; `manifest.sha256`); `logs/h7p2_git_status.txt`. No title, character name, cheat
name, serial or path; nothing committed.

## Files

`evidence/B96_H7_HELD_OUT_AND_FAMILIES_2026-11-11.md` + `b96_2026-11-11/`; `evidence/B97_H7_CHEAT_HINTS_AND_LEVEL_2026-11-11.md`
+ `b97_2026-11-11/` (each: the design + addendum + hashes, the diff, `diffs_apply_in_order.txt`, tests ×3, mutations,
scripts, `sha256_before_after.txt`, redact / title / cheat-name checks (0 FAILS each), manifest; B97 also `settle/` and
`cheat_name_check.py`); patch notes `patches/B96_H7_HELD_OUT_AND_FAMILIES.md`,
`B97_H7_CHEAT_HINTS_AND_LEVEL.md`; code `tools/h7_rule_search.py`, `tools/h7_cheat_hints.py` (new),
`tests/h7_rule_search/` (`fixtures.py`, `test_h7_rule_search.py`, `test_h7_cheat_hints.py` new); `docs/ROADMAP.md` §H7
and `docs/KNOWN_ISSUES.md` (insertions); `logs/b96_git_status.txt`, `logs/b97_git_status.txt`;
`handoffs/SESSION_B_STATUS.txt`. Left (not deleted): `~/.cache/b_q21aj_tmp/`, `/tmp/b_q22aj_b96/`, `/tmp/b_q22aj_b97/`
(snapshots: `companion/`, `tools/`, `tests/`, `PrivyHub/` only).

Written last, 2026-11-11T19:32:10Z, after the status line, the logs and both manifests.
