# B2 design — the fast input hold (written before any B2 code edit, hashed; session B, 2026-10-22)

## 0. Settled first, from the code: the client sends continuously

`PrivyHub/app/src/main/java/streaming/NativeControllerSender.kt`, `sendLoop()`: `while (running)`, for **each of the 4
players, unconditionally**, one 36-byte `PHI1` packet (the whole state: buttons, sticks, triggers), then
`Thread.sleep(8)`. There is no change test.
- That is ~4 × ~107 / s ≈ 430 packets / s with or without input.
- The host's own comment agrees (`native_session_io.py`, `_receive_loop`: "the client sends ~430 packets/s even with
  no input").
- **So a controller silence means the link (or the client) is gone, not a still player. B2 proceeds.**

## 1. The flag

`PRIVYHUB_INPUT_HOLD=<H ms>`:
- an integer 100-4000 = H;
- `1` or `on` = the default **250**;
- absent or empty = today, byte for byte: nothing imported;
- `0`, out of range or anything else = ignored: no hold, one `input_hold_config` row in the recovery log.

## 2. One owner: recovery v2's own state machine (`companion/games/link_drop_recovery.py`)

The hold is a **second, faster trigger inside `LinkDropRecovery`**, with reason `input_hold`. There is no second actor
and no raw `PAUSE_TOGGLE`.
- **`note_input_hold(age_ms)` → `_enter_recovery(trigger="input_hold")`.** It is the same transition as v2's
  `controller_silence`:
  - only from `PLAYING`;
  - state `PAUSED_RECOVERING`, the pause through the plugin's `pause_game` = `EmulatorManager.pause()` (which reads
    RetroArch's state and confirms `PAUSED`);
  - **one `desync_pause` row, `trigger: input_hold`**.
- **`note_input_release(held_ms)`:** only while `PAUSED_RECOVERING` *and* the reason is still `input_hold`.
  - It resumes through `resume_game` = `EmulatorManager.resume()` (confirms `PLAYING`), sets `PLAYING`, and logs
    `resumed` with `via: input_release` and `held_ms`.
  - If the resume fails, it hands over to `controller_silence`, so v2's own controller-return exit applies, and logs
    `input_release_failed`.
  - Otherwise (the hold was handed over, or something else resumed) it does nothing.
- **The handover:** in `_enter_recovery`, one inserted guarded statement. When a different trigger (v2's
  `controller_silence` at 5.35 s, the client's `client_output_silence` / desync) arrives while an `input_hold` pause
  is in force:
  - the reason becomes that trigger, and v2's exit state is cleared;
  - one `input_hold_handover` row is written (not a pause row);
  - there is no second `pause_game` call.

  So:
  - one pause row per episode;
  - `GIVE_UP_MS` counts from the hold's pause (one paused state);
  - v2's controller-return exit, the encoder-restart path and the client's ready gate all apply as today;
  - `input_release` no longer acts.
- **The client's ready gate** (`note_stream_ready`) resumes any `PAUSED_RECOVERING`, the hold included, as today. A
  later `input_release` finds `PLAYING` and does nothing.
- **Absent = today:** the reason `input_hold` is only ever set by `note_input_hold`, which only the flag wires. The
  handover statement is unreachable without it. Proof: `_enter_recovery`'s AST with that statement removed equals the
  predecessor's; the two new methods are additive.

## 3. The detector, where the silence is measured (`native_session_io.py`, the controller receive loop)

- A class attribute `NativeControllerBridge._input_hold = None` (not in `__init__`) and a new setter
  `set_input_hold(detector)`.
- **Two guarded statements in `_receive_loop`:**
  - in the timeout branch (it wakes every 50 ms on a quiet socket, and on B1's dropped packets):
    `if self._input_hold is not None: self._input_hold.on_quiet(now, self._last_any_packet_at)`;
  - on each accepted packet, after `_silence_reported = False`:
    `if self._input_hold is not None: self._input_hold.on_packet(now_packet)`.
- **The detector (`companion/input_hold.py`, `InputHoldDetector`, pure, injectable clock):**
  - `on_quiet`: no hold in force, a packet has been seen, and `now − last_any ≥ H`. Then: one hold, `age_ms`, and the
    silence start remembered.
  - `on_packet`: a hold in force → one release with `held_ms` = now − silence start.
  - **Never blocks the loop:** each event goes onto a single worker (`HoldDispatcher`), which calls the recovery
    methods in order. The pause / resume, RetroArch round trips, run there, not in the receive loop. (v2's own
    silence callback pauses inline today; that is unchanged.)
- **Detection latency:** H to H + 50 ms, the loop's wake.

## 4. Rate limits (stated)

- **Minimum hold 50 ms** (≥ 2 frames at 60 fps, plus margin): a release waits until 50 ms after the hold's pause
  returned, so RetroArch is never asked to resume a pause it has not confirmed. `EmulatorManager.pause()` /
  `resume()` already wait for the state they asked for, so the worker serialises them.
- **At most 6 holds in any rolling 60 s.** A silence past the cap is not held; v2's 5.35-s trigger still protects.
  The exhaustion is logged once per window (`input_hold_cap`).
- **The user's own pause wins:** the worker does not hold if the emulator is already paused (`EmulatorManager`'s
  `_paused`, read through a callable). That episode is skipped and logged once (`input_hold_skipped_paused`).
  `input_release` then has nothing to release.

## 5. The wiring (`plugins/games.py`)

- A guarded module-level import (`PRIVYHUB_INPUT_HOLD`).
- One guarded statement in `__init__`, after v2's wiring: `if _input_hold is not None: _input_hold.wire(…)`. It
  builds the detector and the dispatcher from the environment, and hands them to the controller bridge and to
  `self._recovery`, with `game_paused=` the emulator's `_paused`.
- Absent = not imported; `__init__`'s AST with that statement removed equals the predecessor's (B1's edited file).

## 6. What it costs the player (stated, not measured)

- **Up to H + ≤ 50 ms of game without input** (≈ 18 frames at 250 ms) before the freeze, instead of the whole outage
  (UX-R3: ~4 s), plus `EmulatorManager.pause()`'s own round trip.
- **The picture during a hold.** The encoder captures the RetroArch window with `x11grab` at a fixed `-framerate`
  and encodes VBR (`-b:v` / `-maxrate` / `-bufsize`, no filler; `native_stream.py`). A paused RetroArch keeps its
  last frame on screen, so the stream keeps sending that frozen picture as small P-frames plus the periodic IDR (`-g`).
  On a dead link the client sees nothing until it returns, then the current, frozen frame. **From the code; not
  measured here.**
- **On release:** the game resumes after `EmulatorManager.resume()`'s round trip, a few frames late.
- **False holds on a clean link:** every host-side controller gap ≥ H becomes a pause / resume pair. The baseline
  (§7) counts them per 10 min from the recorded gap logs.

## 7. The measure A will use: "unattended frames" (`tools/unattended_frames.py`)

- **Definition:** host frames emitted while no controller packet had arrived for ≥ 250 ms.
- **The inputs:**
  - the control-gap log (`native_stream_ctrl_gaps.log`: every gap > 250 ms, start / end);
  - the frame-size log (`native_frame_sizes.jsonl`: frames per wall-clock second).
- **Unattended span of a gap** = [start + 250 ms, end]. Frames in it = the per-second frame counts, prorated by
  overlap.
- **Per blackout:** gaps grouped into episodes (gaps < 500 ms apart, the gap log's own burst rule).
- **Per 10 min:** unattended frames / streaming seconds (seconds with frames) × 600.
- **Also, per H in {250, 500, 1000}:** the episodes that would have been held, per 10 min (the false-hold rate on
  clean minutes).
- Reads its arguments only: a directory, a UTC span and named windows. It writes stdout and an optional JSON.
- **The baseline:** run over UX-R1's and UX-R2's preserved copies (their spans; the death 04:54:55-04:54:59Z; Sunday's
  bursts).

## 8. Proof (no live run)

- **Unit tests with a fake clock and fake callbacks:**
  - silence < H → nothing; ≥ H → exactly one hold; repeated quiet → still one; the first packet → one release with
    `held_ms`;
  - a hold reaching v2's threshold → v2 owns it: one `pause_game` call, one `desync_pause` row, one
    `input_hold_handover`, the release ignored, v2's exit resumes once;
  - the client's desync during a hold → a handover;
  - the client's ready gate during a hold → resumed once;
  - a resume failure → a handover to `controller_silence`;
  - the cap (the 7th in 60 s not held, logged once); the minimum hold; the user's pause wins;
  - the flag table;
  - the guarded imports and hook shapes;
  - the real receive loop with B1's gate: a 1-s uplink blackout → one hold ~250 ms in, one release on return.
- **Flag absent:**
  - the AST of the hooked functions (`_receive_loop`, `_enter_recovery`, the plugin's `__init__`) with the guarded
    statements removed equals the predecessors';
  - a fresh process imports no `input_hold`;
  - the recovery suite (E3-R2's) and the impairment suite green.
