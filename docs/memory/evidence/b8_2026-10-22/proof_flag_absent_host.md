# B8 (host) — flag absent = BENCH-R2's files (whole-module AST, B8 items removed, vs predecessors/)

Root checked: `B8_ROOT`. Predecessors: `predecessors/` (HEAD 0f4b551).

| file | functions holding a B8 statement | B8 items removed | whole module vs predecessor |
| --- | --- | ---: | --- |
| `companion/games/link_drop_recovery.py` | `LinkDropRecovery.note_input_hold`, `LinkDropRecovery.note_input_release`, `LinkDropRecovery._tick` | 4 | **identical** |
| `companion/stall_signal.py` | `StallSignal.handle` | 3 | **identical** |
| `companion/hold_rewind.py` | `Rewinder.rewind`, `<module>.config_block` | 2 | **identical** |
| `companion/plugins/games.py` | `GamesPlugin.__init__`, `GamesPlugin.handle_post_request` | 4 | **identical** |

Result: **ALL IDENTICAL**.

New file `companion/hold_ownership.py` is imported only with `PRIVYHUB_INPUT_HOLD_B8` set (and, in `hold_rewind.config_block`, only with it set); `tests/input_hold_b8` FlagAbsent: a fresh process has no `hold_ownership` in `sys.modules` and `LinkDropRecovery._input_hold_b8` is None.
