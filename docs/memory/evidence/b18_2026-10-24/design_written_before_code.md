# B18 — no save at the session's end: design, written before any B18 code

Baseline HEAD 7f3f71d + B17 (uncommitted). Queue: `handoffs/QUEUE_2026-10-24G.md` §B18. Data: CL-B11 cells 2 and 3
(`cl_b11_2026-10-24/runs/2_…`, `3_…`: the recovery logs, the journals, the decoder report file names).

## 0. Settled from the logs and the code

**The rows at each window's end** (the decoder report's file name carries its receive time to the ms):

| cell | `state_saved` (kind silence) | the client's report received | `session_ended` (the stop's entry) | the hold |
| --- | --- | --- | --- | --- |
| 2 | 10:47:14.071 (400.9 ms in) | 10:47:14.225 (+154 ms) | 10:47:14.276 (+205) | `input_hold_skipped_paused` at 952.7 ms, state ENDED |
| 3 | 11:01:29.086 (401.0 ms in) | 11:01:29.267 (+181 ms) | 11:01:29.293 (+207) | the same at 952.5 ms |

- **The order on the client** (the suite's teardown is an adb BACK):
  - BACK → the paused-frame capture → `finish()`;
  - `surfaceDestroyed`: `stopLocalPipeline()`. **The controller sender stops here: the silence's onset;**
  - `onDestroy` → `stopSession` → the report POST (~50 KB), then `native-stream-stop`.
- **So the host hears of the end ~550-600 ms after the controller went silent, and B9's silence save fires at 400 ms.**
  Nothing the host receives today arrives in time. At 400 ms a session's end and a two-way drop look the same to the
  host: no controller packets, no stall datagrams, no heartbeat.
- **The hold is already skipped:** the stop has ENDED the session before the hold's 950 ms
  (`input_hold_skipped_paused`, state ENDED).
- **The save cannot simply wait.** It saves the core's state at the moment it is written: a later save restores a
  later point, and costs every real drop frames.
- **So the end has to be said before the silence:** the client knows at `surfaceDestroyed` that the activity is
  finishing (`isFinishing`); a Home press is not finishing.

## 1. The design (absent = today byte for byte)

**Client** (inside B7's stall monitor, `debug.privyhub.stall_signal`; B19 makes it default-on):
- `surfaceDestroyed` with `isFinishing`, before `stopLocalPipeline()`: `stallMonitor.requestBye()`. The controller
  loop's next ticks send **`PHS1` kind 3 (`bye`)** three times (~8 ms apart), whatever the stall state.
- The UI thread waits ≤ 60 ms for the first to be sent, then stops the pipeline as today.
- **Not on a Home press** (not finishing): the guard's return path is untouched, and the hold and save at a Home press
  stay (the player left mid-game).

**Host, inside `PRIVYHUB_INPUT_HOLD_REWIND=1`** (`state`; the object lives in B9's module, wired by its `wire`). A
`SessionEnd` on the recovery knows the session's end from:
- **the client's `bye`.** B7's worker decodes kind 3 and hands it over. It holds for the same PLAYING period, keyed to
  the recovery's `_state_since`, so a new session clears it, for ≤ 30 s;
- **the stop request / `native-stream-stop` / B17's `guard_end`** (the recovery's state ENDED), and any other state
  but PLAYING;
- **the stream no longer produced** (the game's exit, the stream stopped): the host's video packets sent
  (`session_io`'s counter) have not advanced in the last **N = 250 ms** (15 frames at 60 fps; the encoder sends
  continuously while it runs).

Then:
- **No save:** B9's `StateMark.on_quiet` checks `SessionEnd.ending()` before it asks for the save. On an end it logs
  one `state_save_skipped` (`reason`) per silence and saves nothing.
- **No hold:** `note_input_hold` checks it first. On the client's `bye` the hold is skipped
  (`input_hold_skipped_ending`); the ENDED / not-PLAYING cases are skipped already today.
- **Without the client's `bye`** (today's APK), the end is still known only from the stop, after the 400-ms save. The
  row below needs the client's half.

**Target row (hashed):** **zero `state_saved` outside the blackouts in a 600-s cell with a normal teardown.**

Absent:
- `PRIVYHUB_INPUT_HOLD_REWIND` unset → B9's module is not imported. The recovery's class attribute `_session_end` stays
  None, so its one hook is false.
- B7 without B9: a `bye` is decoded and ignored.
- The client without the property (before B19): no `bye`.
- B8 / B9 / B12 / B16 suites green.

## 2. Tests

- **Host (`tests/session_end/`, B9's loopback fake core, the real recovery, B7's worker by hand):**
  - **a normal teardown:** the client's `bye`, then the controller silent; at 400 ms no save
    (`state_save_skipped` client_bye); at 950 ms no hold; the stop → ENDED. **Zero `state_saved`.**
  - **a blackout** (no `bye`): B9's save at 400 ms as today.
  - **the stream stopped** (the packet counter flat for 250 ms): skipped `stream_stopped`.
  - **a new session after a `bye`:** saves again.
  - B7's decode of kind 3; `bye` without B9 ignored; the flag absent: nothing imported, the hook false.
- **Client JVM (`StallSignalTest` style):** `requestBye()` → kind-3 datagrams on the next three ticks, whatever the
  state; then today's ticks.
- **The suites:** every `tests/` suite from the copy; B8 / B9 / B12 / B16 green; the JVM suite.

## 3. Files

Record `evidence/B18_NO_SAVE_AT_SESSION_END_2026-10-24.md` + `b18_2026-10-24/`; `patches/B18_NO_SAVE_AT_SESSION_END.md`;
`logs/b18_git_status.txt`.
