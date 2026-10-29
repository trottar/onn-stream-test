# B29 — design, written before any code (QUEUE_2026-10-28K item 2): the guard's holds and the stall signal

## Settled first (the code; CL-B15 cell L's rows)

1. **Why a guard hold reaches the stall signal.**
   - The client's monitor (`StallMonitor.tick`, B7 / B19, on by default at 150 ms) reads `outputAgeMs`, the age of
     the decoder's last rendered output (`decoder.lastOutputAgeMs()`).
   - A held frame is never queued to the decoder, so during a hold the output ages exactly as in a real stall.
   - At 150 ms the client sends `PHS1` stall datagrams every 50 ms. The host's stall signal (adopted through
     `PRIVYHUB_LINK_RECOVERY=1`, B9's 400) acts once the age is ≥ 400: B12's state save, `client_stall`,
     `desync_pause`, then `stall_end`, B4's 2-3-frame rewind and `resumed`.
   - CL-B15 cell L: 9 holds of 406-433 ms did exactly that. Neither side knows the picture is frozen on purpose
     while frames still arrive.
2. **Why one hold "ran 685 ms past the 600-ms cap."**
   - **`loss_guard_max_wait_ms` is not the hold's length.** It is the episode's span, from the first drop to the
     next complete IDR (set at the IDR, `deliver(true)`).
   - B10's own test `theFreezeIsCappedAt600Ms` records 640 for a hold capped at 600.
   - The hold itself ends at the cap, but the cap is checked **only when a complete frame arrives**
     (`deliver(false)`): at 600 ms plus up to one frame, later if the frames after 600 ms are dropped.
   - So at 01:41:43Z the hold ended at the cap (`loss_guard_timeouts` 1), then **7 corrupted frames passed** before
     the IDR that came 685 ms after the drop.
   - For the hold to reach 600 ms, the IDRs every 250 ms were not delivered complete: at least two in a row after
     the drop, dropped as corrupt at 1 % loss (an IDR is 57-77 packets).
   - The overrun was the 7 shown frames, which is what the cap is for (the client's own 1-s output-silence recovery
     must not trip). It was not a late cap.

## The design (the client only; inside the default-on guard and stall signal)

`debug.privyhub.loss_guard=0` (no guard object) and `debug.privyhub.stall_signal=0` (no monitor) still turn each off,
and then each reads as today.

1. **A guard hold is not counted as a stall: suppressed, while frames still arrive.**
   - The guard records the time of the last access unit it saw during an episode (a held frame or a dropped one:
     either way, the link delivers). `holdingAgeMs(now)` is the time since then while it holds, and −1 otherwise.
   - `StallInputs` gains `holdingAgeMs` (default −1). The monitor decides on `decideAge = min(outputAgeMs,
     holdingAgeMs)` when `holdingAgeMs ≥ 0`, else `outputAgeMs` as today.
   - The datagram's age field carries `decideAge`.
   - **So during a hold with frames arriving, no stall datagram is sent.**
   - **A real stall during a hold** (no frame arrives): `holdingAgeMs` grows, and at 150 the datagram goes out as
     today, carrying the time since the last frame received.
   - **The host is unchanged.** It sees no datagram for a guard hold, and for a link stall it acts at 400 of
     no-frames-arriving, exactly today's sensitivity.
   - **Its one consequence:** for a stall that begins inside a hold, B4's rewind onset (`rx − age`) is the last
     frame received, not the last frame shown. The rewind can be short by up to the hold so far (≤ 600 ms, mean
     ~0.13 s). Stated, not changed.
   - **"Holding" (a flag in the datagram) was not chosen.** It would need a host change, for no gain: the host never
     needs to act on a hold.
2. **The cap enforced on the hold's own clock.**
   - The guard's `tick()` runs on the controller sender's ~8-ms loop, through today's `keyframeTick`: the cap check,
     then the episode's request as before.
   - The hold ends at 600 ms whether or not a frame arrives (`loss_guard_timeouts` +1).
   - A new counter **`loss_guard_max_hold_ms`** (the hold's own length, ≤ 600 + one loop) sits in the report beside
     `loss_guard_max_wait_ms`, which is unchanged (the drop-to-IDR span).
   - `deliver` / `onDrop` / `tick` are synchronized on the guard: the receive thread and the controller loop.
3. **Unchanged:** the 600-ms cap, B10's rule, the request, `count`, the stall threshold 150, the monitor's cadence
   and bye.

**Target rows (CL-B16 cell 3, measured, not promised):**
- at 1 % loss, 0 stall pauses drawn by guard holds;
- every corrupted frame held but those after a cap, and 0 timeouts where no two IDRs in a row are lost. A hold whose
  next good IDR is > 600 ms away still times out by design (CL-B15 1 / 320, BENCH-R3 0 / 394);
- the clean LAN as CL-B15 cell C.

## Tests (JVM, `GuardQuietStallTest`, new; B10's `LossGuardTest`, B27's `LossGuardDefaultOnTest`, B7's `StallSignalTest` unedited)

- **A 450-ms hold:** frames arriving every 16 ms and held, output age 450 → **no stall datagram.**
- **A real stall with no hold:** output age 450, `holdingAgeMs` −1 → the datagram as today (age 450).
- **A hold, then the frames stop:** a datagram once the holding age reaches 150, its age = the time since the last
  frame.
- **The cap at 600 on the hold's clock:** the drop at 0, frames held to 584, then none; `tick` at 600-608 ends the
  hold (timeouts 1, `maxHold` ≤ 608); the next frame passes; the IDR at 700 → `max_wait` 700.
- **B10's harness:** the real receiver on loopback with the guard → I P P I P as before.
- **No guard (`loss_guard=0`):** `holdingAgeMs` −1 → the monitor's datagrams over a scripted sequence equal today's,
  byte for byte.
- **A mutation** (the decision back to `outputAgeMs`) must fail the hold test.

**Proof:**
- `StallSignal.kt`'s change is `StallInputs`' defaulted field and the decision age;
- `LossGuard.kt`'s is the new clock, `tick` and `holdingAgeMs`, plus the synchronization;
- the activity's is three lines (the input, the tick, the report key);
- with no guard the input is −1 and the tick is not wired, so the monitor is today's (JVM).

**APK:** B5 … B27 + B29, built offline with `--no-configuration-cache`, pinned, NOT installed.
