# B32 (client) — flag absent = today: the proof

**PROVEN (source + behaviour), 0 unclassified lines.**

- **The flag:** `SurfaceHoldFlag.parse` is null for absent / empty / `0` / junk / out-of-range, and `fromSystem()` is
  null when the property cannot be read (`SurfaceHoldTest.theFlagIsOffUnlessOneOrABoundInRange`). The activity's
  `surfaceHold` is `by lazy { SurfaceHoldFlag.fromSystem()?.let { SurfaceHold(it) } }`: null without the property.
- **The activity** (`proof_flag_absent.py predecessors /tmp/b_q31l_b32c` → `proof_flag_absent_output.txt`, exit 0):
  - the one removed line is today's `if (decoder == null) {`, kept word for word as the `else if` branch after
    `if (surfaceHold != null)`;
  - every other added line is behind `surfaceHold?.` / `surfaceHold != null` / `surfaceHold?.let`, or inside the new
    declaration block (the lazy, three fields, the expiry runnable, five private functions — each used only from a
    guarded line — and three framework overrides, `onWindowFocusChanged` / `onTopResumedActivityChanged` /
    `onUserLeaveHint`, that call `super` first and then only `surfaceHold?.…`, i.e. the framework's own behaviour);
  - so with the property absent: no listener registered, no key consumed or noted, `surfaceDestroyed` /
    `surfaceCreated` / `onPause` / `onDestroy` / the parameter-set callback / the heartbeat / the report run today's
    code, and no `surface_lost` / `surface_hold` key exists.
- **The sender:** `neutralize()` is appended at the class's end (nothing else in the file changed) and is called only
  from the guarded `onPause` line and inside `beginSurfaceHold`.
- **Behaviour:** `SurfaceHoldTest.absentAThreeSecondLossIsTodaysRestart` — the model with no hold: the sender stops
  with the surface (uplink gap > 250 ms), the next surface posts `start&guard_end=1`, `restart_cause.away_ms` 3,000.
- **The host:** `games.py`'s block runs only `if "surface_lost" in query:` (an old or flag-absent client sends no such
  key); `tests/surface_lost` runs the block from games.py's own AST with no key → no row, and a fresh process
  importing `plugins.games` has no `surface_lost_row` in `sys.modules`; the heartbeat log's whitelist
  (`games/native_stream_heartbeat.py`) is untouched, so the heartbeat row is byte for byte today's.
