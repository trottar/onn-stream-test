---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: c497a196
---

# B51 — PS2 SAVE / LOAD through PINE, answering as PS1 (inside `PRIVYHUB_PS2=1`)

**Result: SETTLED + BUILT; `tests/ps2_session` 65 (×3, 1.9 s); 6 mutations caught; absent = today PROVEN; NOT
ADOPTED; PCSX2 not started; no live run.** Record: `evidence/B51_PS2_SAVESTATES_PINE_2026-11-08.md`. Applied to the
tree, uncommitted.

- **Built:**
  - the SAVE / LOAD buttons for a PS2 session send PINE `0x09` / `0x0A` (PCSX2 2.8.2's codes, from its binary);
  - a save is confirmed by the completed state file in `data/games/ps2/sstates/`, a load by PCSX2's log line;
  - the PS1 slot index, the PS1 payload, PS1's messages;
  - B49's refusal removed for the buttons;
  - the `ps2_session` row's `savestates: "pine"`.
- **Files:** `companion/ps2_session.py`, `companion/games/emulator_manager.py`, `companion/plugins/games.py`,
  `tests/ps2_session/test_b51.py` (new), `tests/ps2_session/test_ps2_session.py`.
- **Live:** at the next companion restart with `PRIVYHUB_PS2=1`.
- **Rollback:** reverse `b51.diff` (the buttons then answer B49's refusal again). The state files on the hub stay as
  they are.
