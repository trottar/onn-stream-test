# B10 (host) — flag absent = the predecessors (whole-module AST, B10 items removed)

| file | B10 items removed | whole module vs predecessor |
| --- | --- | --- |
| `companion/native_session_io.py` | 3: `_keyframe_request: Any = None`; `def set_keyframe_request(self, requests: Any) -> None:`; `if self._keyframe_request is not None and self._keyframe_request.on_datagram(data, time.monotonic())` | **identical** |
| `companion/plugins/games.py` | 5: `_keyframe_request = None`; `_LOSS_GUARD_FIELDS = None`; `if (os.environ.get('PRIVYHUB_LOSS_GUARD') or '').strip():`; `if _keyframe_request is not None:`; `if _LOSS_GUARD_FIELDS is not None:` | **identical** |
| `companion/games/native_stream_heartbeat.py` | 3: `LOSS_GUARD_FIELDS = None`; `if (os.environ.get('PRIVYHUB_LOSS_GUARD') or '').strip():`; `if LOSS_GUARD_FIELDS is not None:` | **identical** |

Result: **ALL IDENTICAL**.

New file `companion/keyframe_request.py` is imported only with `PRIVYHUB_LOSS_GUARD` set; `tests/keyframe_request` FlagAbsent: a fresh process has no `keyframe_request` in `sys.modules`, the bridge's attribute and `LOSS_GUARD_FIELDS` are None; a `PHK1` datagram is a bad packet as today.
