# B4 — flag absent = B2 (whole-module AST, B4 items removed, vs predecessors/ = HEAD)

Root checked: the copy (`B4_ROOT`). Predecessors: `predecessors/` (HEAD d4c9870).

| file | functions holding a B4 statement | B4 items removed | whole module vs predecessor |
| --- | --- | ---: | --- |
| `companion/native_session_io.py` | `NativeControllerBridge._receive_loop` | 3 | **identical** |
| `companion/input_hold.py` | `HoldDispatcher.put`, `HoldDispatcher.handle` | 3 | **identical** |
| `companion/games/link_drop_recovery.py` | `LinkDropRecovery.note_input_release`, `LinkDropRecovery._maybe_exit_controller_pause` | 3 | **identical** |
| `companion/plugins/games.py` | `GamesPlugin.__init__` | 3 | **identical** |
| `companion/games/emulator_manager.py` | `EmulatorManager._prepare_retroarch_session_config`, `EmulatorManager.launch` | 4 | **identical** |

Result: **ALL IDENTICAL**.

New file `companion/hold_rewind.py` is imported only under both flags (`tests/input_hold_rewind`: a fresh process with `PRIVYHUB_INPUT_HOLD` alone, or nothing, has no `hold_rewind` in `sys.modules`). `tools/unattended_frames.py` without `--net`: the CLI output equals the predecessor's (the test `test_without_net_the_cli_output_is_the_predecessors`, and `unattended_noflag_equal.txt` on UX-R2's preserved logs).
