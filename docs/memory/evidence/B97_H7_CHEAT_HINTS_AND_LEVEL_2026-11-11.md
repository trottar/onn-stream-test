---
memory_schema: 1
as_of: 2026-11-11
status: BUILT (session B, queue AJ) — tools/h7_cheat_hints.py: from a cheat list in the hub's stored form, the RAM addresses its per-player codes write ({player, address, bytes, value, kind}; the description used at run time only, never output); tools/h7_rule_search.py --hints FILE: a family covering a hinted address for the right player is ranked first, every per-player set of hints is tested directly as a rule (template h); template (b2) — a per-player level whose loser need not be 0. Settled from the hub's cached lists, counts only. Synthetic fixtures and made-up cheat lists only; the user's states not touched; no real title started. Nothing committed. No title, serial, code name, character name, cheat name or path in this record
---

# B97 — hints from the game's own cheat list, and a level that need not empty (2026-11-11)

**Why:** a real game's memory fits thousands of candidates (H7-P1); the game's own cheat list is an independent source —
its per-player codes write the very addresses a rule needs. And a fight stopped by the clock leaves the loser's level
above 0, which B94's (b) cannot see. **Baseline:** HEAD `2e30c1cf` + `b96.diff`. **Design** hashed before code at
16:54:31Z (`b97_2026-11-11/design.sha256`); **addendum 1** ((b2)'s speed) hashed at 17:07:22Z — disclosed there: drafted
in a temp copy right after the measurement, before it entered the tree; **addendum 2** ((b2)'s cap) hashed at 17:34:57Z
before its code (the first B97 batch was stopped for it, nothing recorded from it).

## Settled — the hub's cached lists, read in place, counts only (`settle/`; no name, title, address or path printed)

| | PS1 (116 lists, 2,482 codes) | SNES (13 lists, 605 codes) |
| --- | --- | --- |
| written forms | 2,245 "8 hex + 4 hex", '+'-joined; 101 "'$' + 12 hex"; 73 "4-hex chunks, three per line"; 46 "8 hex ':' 4 hex"; 17 other | 529 Game Genie (ROM); **241 RAM writes, bank 7E / 7F** (`aaaaaavv`, `aaaaaa:vv`, `aaaaaa=vv` — all apply on the hub, B92); 53 other banks; 41 other |
| **constant RAM writes** | **type 80 → 2 bytes** (2,611 lines), **type 30 → 1 byte** (390); the address the 6 hex digits after the type, **all 2,909 below 2 MiB** (a RAM offset as the search reads); D0 (a condition) 789; 84 / 74 / 50 / 70 / 04 … not constant writes; the '$' form carries 87 / 85 / 77 / 37 … — another device's set, not read; 273 lines with a value to choose (`?`) | 1 byte per write |
| codes whose description names a player | **460 in 32 of 116 lists**: "P1"-style 433 codes / 31 lists; "Player 1" 23 / 3; "player one" 4 / 1; "1P" 0; "1st player" 0; of the 460, 335 are constant writes only | **0** |
| what `h7_cheat_hints.py` reads from them | **23 lists give hints** (hint lines: other 390, level 79, tally 19); **18 lists hold a P1 / P2 pair of one kind and width, all 18 with matching code names**; codes skipped: no player 2,022, no constant write 23, a form not read 8; unreadable 0 | no hints (no code names a player) |

## Built

- **`tools/h7_cheat_hints.py`** — `read_hints(path, system)`: RetroArch's `.cht` (`cheatN_desc`, `cheatN_code`). PS1:
  the three readable forms; `TTAAAAAA VVVV`, type 80 → 2 bytes, type 30 → 1 byte, address & 0x1FFFFF; other types and
  the '$' form skipped. SNES: bank 7E / 7F (and 00-3F / 80-BF below 0x2000, the low work RAM), 1 byte; Game Genie and
  ROM skipped. A `?` value → `null`. **The player** from the description ("P1", "P 1", "1P", "Player 1", "player one",
  "1st player"; two different players → skipped; none → skipped). **The kind**, whole words, level first: level
  {health, energy, life, lives, hp, power, vitality, stamina}; tally {round(s), win(s), victory/victories, score,
  points, ko(s)}; else other. **Output:** `{player, address, bytes, value, kind, code, line, pair_group}` — never the
  text (`pair_group`: codes whose descriptions match once the player tag is removed). Unreadable / empty / not a list →
  no hints and the reason, never an error. `--counts`: by player and kind only, no address.
- **`tools/h7_rule_search.py --hints FILE`** (a cheat list or the hints JSON): a family one of whose member reads covers
  a hinted byte **for the right player** is `hinted` (with `hinted_by`: kinds and code indexes) and ranked first;
  **every per-player set of hints (one kind, one width, one stride; 2 players: every P1 / P2 pair) is tested directly**
  — template **h**, at most 200 sets — with its values in every state, `holds`, `failing_states`, `found_by`
  (`hinted_sets` in the output); sets that hold are h's families, with B96's folds and evidence. **A hint is evidence,
  not a verdict**: three states with hints stay "weak".
- **Template (b2)**, kept apart: equal and ≥ 8 at every "begin", none above it at "end", the winner's strictly the
  largest — **a loser may be above 0**. Every (b) candidate also fits (b2). Addendum 1: a loser's level strictly below
  its begin (implied) and P1 / P2 paired by equal "begin" values — the same candidates as the stride loop (tested),
  133 s → 19.7 s on the random 2 MiB × 5 states. Addendum 2: **above 200,000 candidates (b2) stops and is reported
  not testable** ("too many (b2) candidates to rank") — a guard for A's unattended run on the hub (on random 2 MiB × 3
  states it had ~420,000). **The answer's template order: a hinted top family first, then a, b,
  c, b2, h.**

## Fixtures and tests

Made-up `.cht` lists (`fixtures.cht`, no real name): PS1 in each readable form ('+', ':', 4-hex chunks) — the planted
level and rounds per player ("P1", "Player 2", "2P"), the score pair, a per-player pair at B94's two-state decoy, two
codes naming no player, a code for a third thing (kind other, type 30), a code naming both players, a value to choose,
a condition before a write, the '$' form; SNES — PAR `aaaaaavv`, `aaaaaa:vv`, `aaaaaa=vv`, a bank-00 low-RAM write, a
Game Genie code.

| test | result |
| --- | --- |
| hints extracted | PS1 and SNES: players, addresses, widths, kinds, values as planted; skipped: no player 2, several players 1, a form not read 1 (SNES: no constant write 1, the Game Genie code); the two rounds codes (one worded P1-style, one 2P-style) one pair group |
| **no description in the output** | every description and every word of 4+ letters from them (but "player") absent from the tool's output and from `--counts`; `--counts` has no address — asserted, both systems |
| the hinted planted family ranked first with three states | PS1 and SNES fixtures, and made-up memories: without hints the smaller-stride decoy first; with hints the planted pair first (`hinted_by` its codes); still "weak", not decided |
| the decoy hint | the pair at B94's two-state decoy: `holds` false, failing P2's state; in no template's passing list |
| a hinted pair no template found | the score pair: tested directly, holds in every state, `found_by` []; h "strong" at five states; the answer stays template a (planted) |
| (b2), the loser above 0 | five states (P2b's loser at 25): the planted level passes (b2), absent from (b); b2 strong, the answer a; three states: the level in (b) and (b2); a hinted (b2) family is the answer when a and b have none |
| (b2) pairs = the stride loop | random memory, 2 and 4 players: the same candidates |
| (b2) over its cap | not testable with the reason, evidence "none", its folds skipped; a, b, c byte-equal to the uncapped search; the answer still a |
| an unreadable or empty cheat file | empty, binary, not a list, missing: no hints, the reason; the search's output byte-equal to the search without hints |
| the CLI | `--hints` with the made-up list: 11 hints read, strong, the planted rule, hinted; no description text in stdout |

**3 runs, 37 / 37 each, and again 3 × 37 / 37 after the rewording below, alone, RetroArch 0 after** (`tests_x3.txt`; 399 s each — run while B96's mutations ran beside them; the pure search with folds on random 2 MiB × 5 states 20.0 s; PS1 2 MiB, 5 states × 3 loads read 73.6 s, the search 0.94 s); `tests/h7_minigame_proof` 13 / 13; mutations **11 / 11 caught** (`tests_mutations.txt`: hinted not marked, hinted not first, the description written out, a two-player code taken, type 30 as 2 bytes, an unreadable list an error, a failing hinted set kept, (b2) loser at 0, (b2) pairs cut short, the loosest templates first, the cap ignored).

## Disclosed

- **(b2) is loose:** on the random 2 MiB × 5 states it leaves ~58,000 families passing every fold (under the cap) — "strong" by the
  stated rule. The template order keeps it behind a, b and c; on its own it answers as the queue states (hinted or
  held-out passing). See the DONE file's "what I would change".
- The kind is not required to match the template for a family to be hinted (a tally hint can rank a level family) —
  shown in `hinted_by`.
- Hinted sets: at most 200 (the count found is in `hinted_sets.found`).
- **Found by the cheat-name check at the close:** five of the fixtures' made-up descriptions were generic phrases that
  also occur as real cheat names in the hub's lists (in `b97.diff` through the fixture code). They were reworded to
  invented wording (codes, players, kinds and pair groups unchanged), `b97.diff` regenerated (the check then 0 FAILS)
  and **the 3 runs repeated** on the reworded text (`tests_x3.txt`, second block); the mutations were not repeated
  (they ran on the earlier wording; the rewording touches none of the mutated code).
- A timing check run without `-B` left one compiled file of `h7_rule_search` in `tools/__pycache__/` (git-ignored; left).
- The settle ran at the session's start (16:41-16:45Z, read-only, before B96's code); `settle_types_per_form.py` was
  first run inline and is kept and re-run as a script.
- RetroArch headless on synthetic fixtures only (B61's form); counted: **0 after both items' batches** (`ps`, 19:09Z). Two intermediate counts read 2 — one RetroArch session (an AppImage's two processes) of the other item's mutation runner, which ran at the same time from its own work copy; noted in `b96_2026-11-11/tests_mutations.txt` and `b97_2026-11-11/tests_x3.txt`.

## Files

`b97_2026-11-11/`: start files, the design + addendum 1 + hashes, `settle/` (four scripts and their counts),
`b97.diff` (applies after `b96.diff`), `diffs_apply_in_order.txt`, `tests_x3.txt`, `tests_mutations.txt`, `scripts/`,
redact / title checks, `manifest.sha256`. Patch note: `patches/B97_H7_CHEAT_HINTS_AND_LEVEL.md`.
