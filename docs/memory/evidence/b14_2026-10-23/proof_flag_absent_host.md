# B14 (host) — flag absent = the predecessors (whole-module AST, B14 items removed)

| file | B14 items removed | whole module vs predecessor |
| --- | --- | --- |
| `companion/plugins/games.py` | 5: `_link_notice = None`; `if (os.environ.get('PRIVYHUB_LINK_REPORT') or '').strip() == '1':`; `if _link_notice is not None:`; `if _link_notice is not None and 'link_notice' in query:`; `if _link_notice is not None and 'link_notice' in values:` | **identical** |
| `companion/games/native_stream_heartbeat.py` | 1: `if 'link_notice' in values and LINK_FIELDS is not None:` | **identical** |

Result: **ALL IDENTICAL**. New file `companion/link_notice.py` is imported only with `PRIVYHUB_LINK_REPORT=1` (`tests/link_notice` FlagAbsent).
