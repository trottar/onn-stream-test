# B24 — absent = the adopted G-A5 behaviour

- `companion/plugins/games.py`: 3 B24 items removed — `_restart_fast_unlock = None`; `_restart_fast is not None and (os.environ.get('PRIVYHUB_RESTART_FAST_UNLOCK') or '').strip() == '1'`; `_restart_fast_unlock is not None` (with an else: 0) → AST **identical** to HEAD 06c565e's.
- `companion/restart_fast.py` (the adopted worker): sha256 **identical** to HEAD's.
- `native_stream`, `native_session_io`, `native_fec_relay`, `audio_codec`, `restart_fast`: `git diff HEAD` empty.
- `companion/restart_fast_unlock.py`: new, imported only when `PRIVYHUB_RESTART_FAST` and `PRIVYHUB_RESTART_FAST_UNLOCK` both read `1` (`tests/restart_fast_unlock` `test_nothing_imported`, four environs).
- B22's 13 (`tests/restart_fast`) unedited and green.

Result: **PROVEN**.
