---
memory_schema: 1
as_of: 2026-11-11
status: BUILT (session B, H7's hub side begun on the user's word) — tools/h7_minigame_proof.py, ROADMAP §H7's first step as a tool: load a save state, run a fixed time, read game memory, name the winner; proved on a synthetic SNES ROM (with the state P2 wins 3 / 3, from boot P1 wins 3 / 3, a missing address is an error). The real game's proof waits for the user's pick. A new tool; the companion unchanged. Nothing committed. No title, serial, code name, path or identifier in this record
---

# B93 — H7's first step: the mini-game proof (2026-11-11)

**Why:** the user: "H6 only has a few quick fixes so let's do that then into h7". ROADMAP §H7's first step: "one SNES
game, one save state, one memory-read win rule, driven by a script: load state → run a fixed time → read memory → print
the winner. Met when the script names the right winner from memory values, repeatably."
**Baseline:** HEAD `af063475`. **Design** hashed before code (`b93_2026-11-11/design.sha256`).

## Settled before (B90 / B92 benches)

§H7's "to verify before any design" item — **RetroArch's read-memory command on the cores in use: answered.**
`READ_CORE_RAM` reads snes9x's work RAM; `READ_CORE_MEMORY` and `READ_CORE_RAM` read Mupen64Plus-Next's and Beetle PSX
HW's main RAM (B90's measurement: 84 / 84 reads held the values written). `WRITE_CORE_RAM`, `SAVE_STATE_SLOT`,
`LOAD_STATE_SLOT` are in this RetroArch build's command list.

## Built — `tools/h7_minigame_proof.py`

- `--content --system snes|n64|ps1 --state FILE --seconds N --rule RULE.json` (or `--no-state`, from boot): RetroArch
  headless in temp folders (the hub's AppImage and cores; its persistent config as the base; no stream; the content
  copied, the library's file only read; the hub's saves and states untouched) → PLAYING → the state copied in and
  loaded with `LOAD_STATE_SLOT 0` (**RetroArch's own `[State]` line required**) → run N s → pause → read each player's
  value → QUIT. One JSON line: `state_loaded`, `values`, `winner` (or `tie`), or `error`.
- The rule: players (name, address, 1 / 2 / 4 bytes, endian), `max` or `min`, `ram` or `memory`.
- `--make-state OUT [--after S] [--write ADDR=HEX]`: boot, optional memory writes, save a state (for fixtures; real states
  are made at the TV).
- Answers are matched to their own command (a late answer to an earlier command is dropped — found on the first run, a
  stale status answer read as memory).

## The proof on a fixture (`tests/h7_minigame_proof/`, 5 tests)

A synthetic SNES ROM (`fixture_counters.py`, no game): two 16-bit counters in work RAM advance once per frame; a mode
byte picks which runs at double rate. The state = boot, the mode byte set to 1 by `WRITE_CORE_RAM`, saved.
- **with the state: P2 wins, 3 / 3** (the state's `[State]` line read); **from boot: P1 wins, 3 / 3**;
- an address with no memory → an error, never a winner; the rule's logic (max / min / tie, endianness, refusals).
- 3 runs: 5 / 5 each (`tests_x3.txt`; no RetroArch left). Mutations **4 / 4 caught** (`tests_mutations.txt`; the copies
  link `runtime/` read-only).

## What waits (the user's)

- **The real proof:** which SNES game, a save state made at the TV just before a two-player contest, the score (or
  lives / position) addresses — then A runs the tool with it, 3 times, and the winner must match what the TV showed.
- **Godot on the hub** and **the game repo** (the separate PrivyParty repo): both a fetch, on the user's word.

## Files

`b93_2026-11-11/`: start files, the design + hash, `tests_x3.txt`, `tests_mutations.txt`, `scripts/`, redact / title
checks, `manifest.sha256`. Code: `tools/h7_minigame_proof.py`, `tests/h7_minigame_proof/`. Patch note:
`patches/B93_H7_MINIGAME_PROOF.md`.
