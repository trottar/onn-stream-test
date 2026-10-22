# B6 — flag absent = B2 + B4 (whole-module AST, B6 items removed, vs predecessors/ = HEAD)

Root checked: the copy (`B6_ROOT`). Predecessors: `predecessors/` (HEAD 144e5c7).

| file | functions holding a B6 statement | B6 items removed | whole module vs predecessor |
| --- | --- | ---: | --- |
| `companion/input_hold.py` | `InputHoldDetector.on_quiet` | 2 | **identical** |
| `companion/hold_rewind.py` | `<module>.config_block` | 1 | **identical** |
| `companion/games/link_drop_recovery.py` | `LinkDropRecovery.note_input_hold`, `LinkDropRecovery.note_input_release`, `LinkDropRecovery.note_gameplay_released`, `LinkDropRecovery._tick` | 5 | **identical** |
| `companion/plugins/games.py` | `GamesPlugin.__init__` | 3 | **identical** |

Result: **ALL IDENTICAL**.

New file `companion/hold_tuning.py` is imported only with `PRIVYHUB_INPUT_HOLD` and `_B6` set (`tests/input_hold_b6` FlagAbsent: a fresh process with nothing, the hold only, or the hold + B4's rewind, has no `hold_tuning` in `sys.modules`).
