# B97 — hints from the game's own cheat list, and a level that need not empty (design, before code; queue AJ)

Builds on B96 (HEAD + `b96.diff`). New `tools/h7_cheat_hints.py`; `tools/h7_rule_search.py` gains `--hints FILE` and
template (b2); tests in `tests/h7_rule_search/`. The companion unchanged.

## Settled (the hub's cached lists, read in place, counts only — `settle/`; run at 16:41-16:45Z, before B96's code)

- **PS1: 116 cached lists, 2,482 codes.** Written forms: 2,245 "8 hex + 4 hex, lines joined by '+'"; 101 "'$' + 12
  hex"; 73 "4-hex chunks, three per line"; 46 "8 hex ':' 4 hex"; 17 other. Lines by type: **80** 2,611 (a 16-bit
  constant write — 2 bytes, the value 4 hex), **30** 390 (an 8-bit constant write — 1 byte, value `00vv`), D0 789 (a
  16-bit "equal" condition), then 84 / 74 / 50 / 70 / 04 … (other device types, increments, repeaters; not constant
  RAM writes for this tool). The address field is the 6 hex digits after the type; **all 2,909 type 80 / 30 addresses
  are below 2 MiB** (a RAM offset as the search reads it). The '$' form carries types 87 / 85 / 77 / 37 … — another
  device's set, **not read** as constant writes. 273 lines have a value to choose (`?`).
- **Player-naming descriptions (PS1): 460 codes in 32 of 116 lists**; per pattern: "P1"-style 433 codes / 31 lists,
  "Player 1" 23 / 3, "player one" 4 / 1, "1P" 0, "1st player" 0. Of the 460, 335 are constant writes only.
- **SNES (B92's bench + the 13 cached lists):** RAM-write forms `7E/7F aaaa vv` (Pro Action Replay `aaaaaavv`, raw
  `aaaaaa:vv` / `aaaaaa=vv`, 1 byte; all apply on the hub's snes9x, B92) — 241 such lines; 529 Game Genie lines (ROM);
  **0 codes name a player.**

## `tools/h7_cheat_hints.py`

`read_hints(path, system) -> {"hints": [...], "codes": n, "skipped": {reason: n}, "unreadable": None | why}` — never
raises on a bad file: unreadable / not a cheat list / empty → no hints and the reason.
- **Input:** a cheat file in the hub's stored form (RetroArch `.cht`: `cheatN_desc`, `cheatN_code`).
- **Code lines:** PS1 — the three readable forms above ('+'-joined 8+4, ':' 8+4, 4-hex chunks three per line); a
  line `TTAAAAAA VVVV`: type 80 → 2 bytes, value VVVV; type 30 → 1 byte, value VV; address AAAAAA & 0x1FFFFF; any
  other type is not a constant write (that line skipped, the code kept if it has a write); the '$' form → skipped
  ("another device's form"). SNES — `7E`/`7F` bank (`aaaaaavv`, `aaaaaa:vv`, `aaaaaa=vv`): 1 byte at
  `(bank - 0x7E) * 0x10000 + aaaa`; banks 00-3F / 80-BF with `aaaa < 0x2000` → the low work RAM (`aaaa`); anything
  else (Game Genie, ROM banks) skipped. A value with `?` → `value: null` (the address still a hint).
- **Player:** from the description, case-folded: `P1`, `P 1`, `1P`, `Player 1`, `player one`, `1st player` (B85's tag
  plus the word forms). A description naming two different players → skipped ("several players"); none → skipped
  ("no player").
- **Kind:** whole words, level-like checked first — **level** {health, energy, life, lives, hp, power, vitality,
  stamina}; **tally** {round, rounds, win, wins, victory, victories, score, points, ko, kos}; else **other**.
- **Output per hint:** `{player, address, bytes, value, kind, code, line, pair_group}` — `code` the list's index,
  `pair_group` a small number shared by codes whose descriptions are equal once the player tag is removed (computed
  at run time). **The description text is used at run time only and never written to the output or any record**
  (asserted by the tests: no word of 4+ letters from any description appears in the output).
- **CLI:** `--system ps1|snes --cheats FILE [--counts]`; `--counts` prints the counts by player and kind only (no
  address) — the form A's record uses.

## The search: `--hints FILE`

- FILE: a cheat list (read through `read_hints`) or the hints tool's JSON; unreadable / empty → no hints and the
  search exactly as without (the output says `"hints": {"read": 0, "why": …}`).
- **Hinted family:** a family one of whose member reads covers, for some player k, a byte of a hint for player k
  (the right player) → `hinted: true`, `hinted_by` (kinds and code indexes). B96's order already puts hinted first.
  The kind is not required to match the template (stated; shown).
- **Hinted sets tested directly (template `h`, "a hinted pair, tested directly"):** for each kind, every choice of one
  hint per player (all players of the search), the same width, a constant stride (2 players: every P1 / P2 pair of the
  kind), at most 200 sets (the count stated). Each set is a rule (`winner: max`, `none_when: equal`) read in every
  state: `holds` = all equal at every "begin" and the winner strictly the largest at every "end"; the values per state
  and the failing states are reported; `found_by` = the templates whose family contains it. Sets that hold are `h`'s
  families (hinted), with B96's folds (a fixed rule: a fold passes when it names the held-out winner) and evidence
  levels. Sets with matching `pair_group` rank first among `h`.
- **A hint is evidence, not a verdict:** a hinted family or set must still hold in every labelled state and pass the
  folds; the evidence rules are B96's.

## Template (b2) — a per-player level, the winner's the larger

Equal and ≥ 8 at every "begin"; at every "end" none above its "begin" value and the winner's strictly larger than
every loser's — **the loser need not be 0** (a contest stopped by the clock). Kept apart as `b2` (every (b) candidate
also fits it; its own count, families, folds, evidence). (c)'s exclusions unchanged (a and b only). **The answer's
template order: a hinted top family first, then a, b, c, b2, h** — b2 and h, the loosest, answer only when no other
template is strong, or when hinted.

## Fixtures and tests

Made-up `.cht` files (no real name): PS1 in each readable form — the planted rounds and level per player ('+', ':',
4-hex chunks; "P1" / "Player 2" / "2P" wordings), the score pair (tally; no template finds it), a per-player tally pair
at B94's two-state decoy (fails P2), codes naming no player, a per-player code for a third thing (kind other), a code
naming both players, a value to choose (`?`), the '$' form; SNES — the same plan as PAR `aaaaaavv`, `aaaaaa:vv` and
`aaaaaa=vv`, a Game Genie code. Tests: the hints extracted (players, addresses, widths, kinds; no description text in
the output — asserted); with three states the hinted planted family ranked first in (a) (without hints the
smaller-stride decoy is first) and in (b); the decoy hint pair fails P2's state and is reported failing, not chosen;
the score pair, which no template finds, tested directly and holding (strong at five states, not the answer: a is);
(b2) on five states finds the planted level where (b) does not (P2b's loser at 25); an unreadable and an empty cheat
file → no hints, the templates' output equal to the search without hints; the CLI with `--hints`.
