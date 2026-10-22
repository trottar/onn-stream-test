# B7 (host) — flag absent = B6's files (whole-module AST, B7 items removed, vs predecessors/)

Root checked: the copy (`B7_ROOT`). Predecessors: `predecessors/` (B6's files in the tree; HEAD 144e5c7 + B6).

| file | functions holding a B7 statement | B7 items removed | whole module vs predecessor |
| --- | --- | ---: | --- |
| `companion/native_session_io.py` | `NativeControllerBridge._receive_loop` | 3 | **identical** |
| `companion/games/link_drop_recovery.py` | `LinkDropRecovery.note_input_release`, `LinkDropRecovery.note_gameplay_released` | 3 | **identical** |
| `companion/hold_rewind.py` | (module level only) | 1 | **identical** |
| `companion/plugins/games.py` | `GamesPlugin.__init__` | 3 | **identical** |

Result: **ALL IDENTICAL**.

New file `companion/stall_signal.py` is imported only with `PRIVYHUB_STALL_SIGNAL` set (`tests/stall_signal` FlagAbsent: a fresh process has no `stall_signal` in `sys.modules`; a stall datagram is a bad packet as today).
