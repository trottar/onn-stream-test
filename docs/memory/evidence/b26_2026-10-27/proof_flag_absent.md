# B26 — the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1` but the one packet; absent unchanged

- `companion/restart_fast_unlock.py`: `_stop_relay` removed (1), its call put back as `m._fec_relay.stop()` (1) → AST **identical** to HEAD 2cd392c's.
- `companion/native_fec_relay.py`: sha256 **identical** to HEAD's.
- `companion/restart_fast.py`: sha256 **identical** to HEAD's.
- `companion/plugins/games.py`: sha256 **identical** to HEAD's.
- `native_fec_relay`, `restart_fast`, `plugins/games`, `native_stream`, `impairment`: `git diff HEAD` empty.
- Absent the flag `restart_fast_unlock` is not imported (B24's `test_nothing_imported`, four environs, green).
- With `=1`: the only change is `_stop_relay` (the send target cleared under the relay's lock before `stop()`; the frame noted after the close dropped after it). Order, timings, rows and fields unchanged.

Result: **PROVEN**.
