# B47 — `debug.privyhub.vod_retry=0` (or `off`) = `8ba4d996…`'s absent

- `VodRetryFlag.parse("0")` / `parse("off")` is false → `VodRetryController.wanted(false, isLive)` false →
  `MainActivity`'s `vodRetry` is **null** (its one construction site unchanged), every `vodRetry?.` call a no-op, today's
  "Playback error" at once (JVM `absentIsOnAndZeroOrOffIsTodaysNoController`, `VodRetryTest.theFlag`).
- The other client hunks (`onReady`'s unconditional clear and cancel, `showMark` only while open, the tagged sweep)
  live inside `VodRetryController` / `VodRetryAndroid`, which are not built.
- Host: `flush_open` and the SIGTERM handler exist only inside `PRIVYHUB_VOD_LOG=1` (`range_server.py`'s existing
  block); without the line the process keeps Python's default SIGTERM action and writes nothing
  (`test_sigterm_without_the_line_is_todays_default_action`, exit −15, no `logs/`). With the line and nothing open, a
  SIGTERM writes no row; a request that closes normally writes its row as before.
- **Absent / empty / junk is now ON (the user's "Reconnect by default yes"): disclosed, as B42.** `VodRetryTest.theFlag`
  moved; `test_vod_drop_test.Absent.test_the_module_minus_the_guarded_block_is_the_base` (B40's structural check) now
  also allows the changed `PRIVYHUB_VOD_LOG` block; B40's two nodes are checked as before.
