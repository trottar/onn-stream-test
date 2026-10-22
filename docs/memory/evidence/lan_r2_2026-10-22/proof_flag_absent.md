# LAN-R2 — `=bidir` absent: whole-module AST, LAN-R2 items removed, vs predecessors/

Root checked: the copy (`LANR2_ROOT`). Predecessors: `predecessors/` (lan_loss_rule.py HEAD's; native_session_io.py / plugins/games.py B7 + B1b's).

| file | functions holding a LAN-R2 statement | LAN-R2 items removed | whole module vs predecessor |
| --- | --- | ---: | --- |
| `companion/lan_loss_rule.py` | `<module>.from_environ` | 11 | **identical** |
| `companion/native_session_io.py` | `NativeControllerBridge._receive_loop` | 3 | **identical** |
| `companion/plugins/games.py` | `GamesPlugin.__init__` | 3 | **identical** |

Result: **ALL IDENTICAL**.

No new module: the rule lives in `lan_loss_rule.py` (imported, as LAN-R1, only with `PRIVYHUB_LAN_LOSS_RULE` set: `1` by the ladder, `bidir` by the plugin). `adaptive_bitrate_live.py` is untouched (its LAN-R1 test pins one guarded import). A fresh process with nothing set imports no `lan_loss_rule` and the bridge has no sink (tests/lan_loss_rule_bidir).
