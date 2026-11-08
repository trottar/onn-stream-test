---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: d618a20a
---

# B57 — the PS2 multitap relaunch through PINE's slot 7 (inside `PRIVYHUB_PS2=1`); the `PrivyHub-Import/` ignore line

**Result: SETTLED + BUILT; `tests/relaunch_ports` 19 green ×3 (B54's 10, one moved to B57's meaning, + B57's 9);
`tests/ps2_session` 93 green; 12 mutations caught, none survived; absent = today PROVEN.** Record:
`evidence/B57_PS2_RELAUNCH_STATE_2026-11-08.md`.

- **Files:** `companion/relaunch_ports.py`, `companion/games/emulator_manager.py`, `companion/ps2_session.py`
  (`RELAUNCH_SLOT = 7`), `tests/relaunch_ports/test_b57.py` (new), `tests/relaunch_ports/test_relaunch_ports.py` (the
  PS2 test moved), `.gitignore` (`PrivyHub-Import/`).
- **Apply:** `git apply evidence/b57_2026-11-08/b57.diff` (applied to the tree, uncommitted).
- **Live:** at the next companion restart (the adopted `PRIVYHUB_PS2=1`): a third pad holding in a PS2 game →
  the game back where it was (`relaunch_ports` `state: loaded`). No client change; no APK.
- **Rollback:** reverse it; a PS2 relaunch then restarts the title (B54's `ps2_no_relaunch_state`). The slot-7 file
  in `data/games/ps2/sstates/` is then unused.
