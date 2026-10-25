# B23 — absent = today

- `companion/plugins/games.py`: 4 B23 items removed — `_link_recovery_wan = None`; `(os.environ.get('PRIVYHUB_LINK_RECOVERY_WAN') or '').strip() == '1'`; `_link_recovery_wan is not None`; `_link_recovery_wan is not None and getattr(self, '_link_recovery_wan', None) is not None` (with an else: 0) → AST **identical** to the predecessor's (HEAD + B21 + B22).
- the modules B23 sets or reads (`input_hold`, `hold_tuning`, `stall_signal`, `stall_owner`, `rewind_cores`, `remote_ladder`, `overlay/`, `native_stream`): `git diff HEAD` empty.
- `companion/link_recovery_wan.py`: new, imported only under the flag (`tests/link_recovery_wan` `test_nothing_imported`).

Result: **PROVEN**.
