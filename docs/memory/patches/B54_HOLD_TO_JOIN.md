---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 0eb115d9
---

# B54 — hold-to-join replaces the chooser; a third pad brings the multitap at once

**Result: SETTLED + BUILT; JVM 228 / 228, host suites green ×3; 11 mutations caught; `0` / no request = today
PROVEN.** Record: `evidence/B54_HOLD_TO_JOIN_2026-11-08.md`.

- **Files:**
  - client: `PlayerPrompt.kt`, `NativeStreamActivity.kt`, `MainActivity.kt`, `PlayerChoiceStoreAndroid.kt`,
    `NativeControllerSender.kt` (a comment), `PlayerPromptTest.kt`;
  - host: `companion/relaunch_ports.py` (new), `players_session.py`, `pad_slots.py`, `plugins/games.py`,
    `games/emulator_manager.py`, `games/native_stream_heartbeat.py`;
  - tests: `tests/players_session/test_b54.py` (new), `tests/relaunch_ports/` (new), the `_tmp_cleanup` imports.
- **Apply:** `git apply evidence/b54_2026-11-08/b54.diff` (or `evidence/b56_2026-11-08/queue_t_combined.diff`, applied
  to the tree).
- **Live:** the host at the next companion restart (inert without the client's keys); the client in APK `9aa00ba2…`
  (queue T), not installed.
- **Rollback:** reverse it; or `debug.privyhub.player_prompt 0` on the onn (no prompt at all).
