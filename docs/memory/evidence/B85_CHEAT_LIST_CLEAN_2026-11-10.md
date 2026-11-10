---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT ADOPTED (session B, queue AE) — every system's cheat list cleaned on the hub (cheat-catalog handler) and expanded back at the launch; heading rows no longer make the reader refuse a whole file. Default on; PRIVYHUB_CHEAT_CLEAN=0 = today's raw list and launch. The hub's real cheat files read for counts and shapes only. Nothing committed. No title, serial, code name, path or identifier in this record
---

# B85 — the cheat list cleaned, every system (2026-11-10)

**Why:** HOME-12's C46: "a lot of overlap and ones just called p1 or p2 what does that even mean". A's read of that
list: 677 entries, 290 repeats, 85 enabler / activator entries, 461 tagged P1-P4.

**Baseline:** HEAD `c514c543`. **Design** hashed before code at 21:17:00Z (`b85_2026-11-10/design.sha256`); **addendum
1** (heading rows) hashed before its fix at 21:21:13Z (`design_addendum_1.sha256`).

## Settled from the hub's own files (counts only — `settle_counts.txt`, `settle_shapes.txt`, `scripts/`)

| what | N64 (18 files, 7,562 entries) | PS1 (116 / 2,486) | SNES (13 / 610) | settled as |
| --- | --- | --- | --- | --- |
| repeats of an earlier name | 2,441 (identical code 9; same value, another address 1,472) | 28 | 83 | the same cheat for another target (player / slot / character) with its heading lost → **shown under the first as "variant n"**; identical code → folded |
| "enabler / activator" names | 903, of which **884 lone joypad conditionals** (every line `D0`-`D3`) | 16 | 6 | a lone conditional writes nothing on its own (a cheat cartridge's button trigger) → **hidden, never applied** (N64 / PS1, by the code type) |
| "must be on" names with real writes | 17 | 15 | 6 | what the list's authors say other codes need; no core documentation on the hub says otherwise → **applied with any pick from that file, not shown** |
| P1-P4 tags | 1,934 | 456 | 0 | player-specific cheats → "Player n", **a section per player** |
| bare "P1" / "P2" rows | 133 (all with codes; 7 runs after a named cheat) | 0 | 0 | cheats, not headers → **"<that cheat> — Player n"** |
| heading rows (a name, empty code) | 67 | 4 | 5 | hidden |
| split parts | 23 "Part n" (8 groups numbered 1..k) | 2 | 0 | folded into one entry that enables every part |

## What was built (`b85.diff`)

- **`companion/cheat_clean.py`** (new): `clean(catalog)` per source — RetroArch's lists (PS1 / SNES / N64): the codes
  read again from the cached file; heading rows, lone conditionals and "must be on" codes hidden (the last applied as
  `requires`); "Part n" groups folded (`parts`); bare player rows named from their cheat; labels tidied ("P1" →
  "Player 1", a trailing `(M)` / code / empty brackets removed); `group` = general / player1-4 / other; a repeated
  label's other codes shown right after it as "<label> — variant k" (`variant_of`), identical ones folded. **The
  user's own files** (B81's `.cht`, the PS2 `.pnach`): as they are, group `yours`. **GameCube** (Dolphin's names):
  tidied and grouped, nothing hidden. `expand()` turns the picks back into the file's real indexes.
- **`plugins/games.py`:** `cheat-catalog` returns the cleaned list (`raw=1` → today's); `launch` expands the sent
  indexes (`cheat_raw=1` → as sent). A saved profile's real indexes expand to themselves.
- **`games/emulator_manager.py`** (addendum 1): with the knob on, an entry with a name and an empty code is read as a
  heading instead of refusing the whole file.

## The hub's own lists, before → after (`hub_before_after.txt`, counts only)

| system | entries before → shown after | hidden: heading / trigger / "must be on" (applied) / duplicate | parts folded | shown as variants | biggest list |
| --- | --- | --- | --- | --- | --- |
| N64 | 7,562 → 6,561 | 67 / 886 / 17 / 19 | 12 | 2,407 | 2,092 → 2,072 |
| PS1 | 2,486 → 2,449 | 0 / 0 / 15 / 21 | 1 | 7 | 188 → 188 |
| SNES | 610 → 598 | 5 / 0 / 6 / 1 | 0 | 82 | 162 → 162 |

- **HOME-12's C46 list (677):** 588 shown — 306 names + 282 variants under them; 84 triggers, 1 "must be on"
  (applied), 4 duplicates hidden; sections General 135, Player 1 152, Player 2 131, Player 3 87, Player 4 83.
- **Lists that failed on the onn before B85** (a heading row made the reader refuse the file): **N64 8 of 18, SNES 1 of
  13** — listed with B85.
- **Read honestly:** the biggest N64 lists stay long (2,092 → 2,072): most of their repeats are real, distinct cheats
  for other targets whose names the source file lost; folding them would drop cheats. B84's sections (collapsed, with
  counts), its filter and its top-fixed Launch are what make those lists usable.

## Absent = today

`PRIVYHUB_CHEAT_CLEAN=0` and `raw=1` / `cheat_raw=1`, on the same fixture tree as HEAD's code
(`proof_absent_run.txt`): the `cheat-catalog` reply byte-equal (knob 0; raw=1), the launch's staged indexes equal
(knob 0; cheat_raw=1), and a file with a heading row refused exactly as HEAD refuses it (knob 0) — **5 / 5 SAME**, 0
network attempts.

## Tests (`tests/art_systems/test_b85.py`, 8, through the plugin as the companion builds it)

B83's harness; fixture `.cht` files with made-up names and codes in every shape above; the real
`handle_post_request("cheat-catalog")` and `handle_post("launch")` (RetroArch faked at its process and its network
command port): **the N64 list cleaned** (7 of 12 shown, the counts per kind, "Player 1", the bare row named, the
variant, the parts, `requires`); **raw=1 and the knob 0 = today's list byte for byte**; a heading row read with the
knob and refused without; GameCube tidied with nothing hidden; the user's file as it is under "yours"; **a cleaned
selection stages the real indexes** — N64 `5,0` → `0, 2, 5, 6` (both parts and the "must be on" code), PS1 `2` →
`0, 2`; the knob 0 and `cheat_raw=1` launch as sent; a saved profile's real indexes unchanged.

- 3 runs: 8 / 8, and `tests/art_systems` 120 / 120 each (`tests_x3.txt`). Mutations: **11 / 11 caught**
  (`tests_mutations.txt`). Host suites: see `b86_2026-11-10/tests_host_compare.txt`.

## Disclosed

- **"Must be on" codes are applied, not proven needed:** no core documentation on the hub settles whether
  Mupen64Plus-Next / Beetle PSX HW need them; B follows the list's instruction. If a file holds such codes for several
  game versions, all are applied (a risk the onn would show as a game misbehaving with cheats; none seen in counts).
- **The split-part rule changed from the hashed design** ("n of m" at the end of a name → "Part n" or "n of m"
  anywhere, groups numbered 1..k): the hub's lists have no "n of m" and 8 "Part n" groups (settled before the change).
- **Addendum 1** (heading rows) is a fix found by testing through the real handler; hashed before the fix.
- The bare-row label drops the player tag of the cheat it follows ("Infinite Health — Player 2", not "… Player 1 —
  Player 2"), a refinement made while writing the tests.
- Hidden entries are counted per source (`hidden`) in the reply; the onn does not show them.

## Files

`b85_2026-11-10/`: start files, the design + hash, addendum 1 + hash, `b85.diff`, the settle counts, the hub's before /
after counts, `proof_absent_run.txt`, `tests_x3.txt`, `tests_mutations.txt`, `scripts/` (`settle_counts.py`,
`settle_shapes.py`, `hub_before_after.py`, `proof_absent.py`, `mutate.py`, `mutations.json`), redact / title checks,
`manifest.sha256`. Patch note: `patches/B85_CHEAT_LIST_CLEAN.md`.
