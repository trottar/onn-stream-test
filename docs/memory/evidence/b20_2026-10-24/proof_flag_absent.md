# B20 — absent = today

| file | B20 items removed | AST then = predecessor |
| --- | --- | --- |
| `companion/plugins/games.py` | 3: `_link_recovery = None`; `if (os.environ.get('PRIVYHUB_LINK_RECOVERY') or '').strip():`; `if _link_recovery is not None:` | **identical** |
| `companion/games/emulator_manager.py` | 1: `if (os.environ.get('PRIVYHUB_LINK_RECOVERY') or '').strip():` | **identical** |
| `tools/e3_state.py` | 1: `if any((x.startswith('PRIVYHUB_LINK_RECOVERY=') for x in d['preflight']['environ'])):` | **identical** |

`companion/link_recovery.py` is new, imported only under the umbrella's tests (`tests/link_recovery` `test_absent_nothing_read_nothing_imported`).

Result: **PROVEN**.
