# B93 — H7's first step, the mini-game proof (design, written before code; 2026-11-11)

**The user:** "H6 only has a few quick fixes so let's do that then into h7". ROADMAP §H7's first step, as written:
"**a proof; no board, no graphics:** one SNES game, one save state, one memory-read win rule, driven by a script: load
state → run a fixed time → read memory → print the winner. Met when the script names the right winner from memory
values, repeatably. Nothing perceptual is a gate."

**Already settled (B90 / B92 benches, recorded there):** RetroArch's read-memory commands answer on every core in use —
`READ_CORE_RAM` on snes9x (work RAM), `READ_CORE_MEMORY` / `READ_CORE_RAM` on Mupen64Plus-Next and Beetle PSX HW — the
"to verify before any design" item of §H7.

## What is built (`tools/h7_minigame_proof.py`, a new tool; nothing in the companion changes)

- **Input:** the content, the core (by system: `snes` → the hub's snes9x), a save state file, the seconds to run, and a
  **win rule** (JSON): `{"players": [{"name": "P1", "address": "0x0100", "bytes": 2, "endian": "little"}, …],
  "winner": "max" | "min", "memory": "ram" | "memory"}`.
- **Run:** RetroArch headless in temp folders (the hub's AppImage and cores; its persistent config as the base; the
  joypad driver null; no stream; the hub's own saves untouched): start → GET_STATUS PLAYING → **the state copied into the
  temp states folder and loaded (`LOAD_STATE_SLOT`), RetroArch's own log line as the evidence** → run the given seconds
  → pause → read every player's value → QUIT. `--no-state` runs from boot (a control).
- **Output:** one JSON line: the state loaded (yes / no, from the log), each player's value, the winner (a tie named
  "tie"), the seconds. Exit code 0 when a winner (or tie) was read.
- **A helper for making states (`--make-state`):** run the content, optionally write bytes (`WRITE_CORE_RAM`), save a
  state to a given file — for the fixture only; real states are made by the user at the TV (A's task).

## The proof on a fixture (`tests/h7_minigame_proof/`)

A synthetic SNES ROM (no game): two 16-bit counters in work RAM, one frame each (the vertical-blank flag polled); a
mode byte decides which counter runs at twice the rate (0: P1, 1: P2). The state is made by the helper (boot, set the
mode byte to 1, save). **Met:** with the state → **P2** wins, 3 / 3; from boot (`--no-state`) → **P1** wins, 3 / 3; a
wrong address in the rule → an error, not a winner. Run with RetroArch headless (B61's form); skipped when RetroArch or
the display is absent; temp dirs removed.

## Not in scope

The real game's proof (the user's pick: which SNES game, its state, its score addresses — A at the TV); Godot (a fetch:
the user's word); the board; N64 / PS1 rules (the same tool by system, once SNES is met).
