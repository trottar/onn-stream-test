# B28 — `PRIVYHUB_REMOTE` absent = today

- `companion/plugins/games.py`: 4 B28 items removed — `_remote_umbrella = None`; `(os.environ.get('PRIVYHUB_REMOTE') or '').strip() == '1'`; `_remote_umbrella is not None`; `_remote_umbrella is not None and getattr(self, '_remote_umbrella', None) is not None` (with an else: 0) → AST **identical** to HEAD 42a2ab6's.
- `companion/start_rung.py`: sha256 **identical** to HEAD's.
- `companion/remote_ladder.py`: sha256 **identical** to HEAD's.
- `companion/remote_cap.py`: sha256 **identical** to HEAD's.
- `companion/wan_telemetry.py`: sha256 **identical** to HEAD's.
- `companion/link_recovery_wan.py`: sha256 **identical** to HEAD's.
- `companion/adaptive_bitrate_live.py`: sha256 **identical** to HEAD's.
- `companion/native_stream.py`: sha256 **identical** to HEAD's.
- `companion/privyhub_service.py`: sha256 **identical** to HEAD's.
- those and the actuator probe: `git diff HEAD` empty.
- `companion/remote_umbrella.py`: new, imported only when `PRIVYHUB_REMOTE` reads `1` (`tests/remote_umbrella` `test_nothing_imported_without_the_line`: absent, `0`, `yes` → not imported).
- With the line, a LAN-class session: every hook's global None (today's code path); `test_a_lan_session_is_todays_in_every_reader` (argv and ladder rows field for field as with no umbrella).

Result: **PROVEN**.
