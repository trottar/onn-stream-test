# B9 — the stall threshold's default, and rewind SNES-only with a savestate path for PS1: design, before any B9 code

Baseline HEAD 0f4b551 + B8 (uncommitted). Queue: `handoffs/QUEUE_2026-10-22D.md` §B9. Data: BENCH-R2 §4 (d1 / d2),
§3 c1, §6 (PSX HW +16.6 points, +1.0 GB, 118 / 123 after-checks PAUSED; snes9x never exercised), its
`record/record_read.json` (silence bins per cell). D-BASE-R3C §1-2 (the paused-load caveat) read first.

## 1. `PRIVYHUB_STALL_SIGNAL=1` → 400 ms

- `stall_signal.DEFAULT_MS` 150 → **400**. `MIN_MS` stays 150, so `=150` keeps B7's behaviour by number; 150-2000
  unchanged. Absent = not imported, as today.
- **The data:** d1 at 150: 2.6 stall pauses / 10 min on a clean hour (bar ≤ 2); d2 at 400: **0** (the client sent 9
  stalls, all ended under 400 ms); c1 at 150 on a flapping hour: 77 / 10 min.
- **The cost:** a downlink-only drop pauses the core ~400-455 ms after the client's last frame instead of 150-205
  (c1): ~24-27 frames of game without a picture instead of 9-12. B4's rewind (snes9x) takes them back; on PS1 they are
  not rewound (§2).
- **The client is unchanged:** it still sends at 150 (`debug.privyhub.stall_signal=1`); the host decides. No APK.
- B7's suite asserts `parse("1") == (150, None)`: that one line becomes 400 (the queue's change), disclosed. With B8 on,
  the gate-bit-over-fresh-output rule reads "age < the threshold", now 400.

## 2. `PRIVYHUB_INPUT_HOLD_REWIND`: `1` = an allow-list, `all` = B4, `state` = the PS1 path

New module `companion/rewind_cores.py`; the hooks are guarded statements in `hold_rewind.py` and `input_hold.py`.

- **`1`** (the default meaning changes, as the queue asks): RetroArch's rewind **only for the allow-list**
  `snes9x_libretro.so`, `bsnes_libretro.so` (the launch config's core file name, B4's `_hold_rewind_core`).
  - Another core (Beetle PSX HW): **no rewind keys in the launch config** (no 1-GB buffer, no +16.6 points) and, at the
    release, one `rewind_skipped` row (core, reason, counter_before) instead of an NCI sequence. The resume as today.
  - An allowed core: B4's path exactly.
- **`all`**: B4's behaviour for every core (the PSX test later): parse treats it as B4's `1`, no B9 object is wired.
- **`state`** (§3): no rewind keys for any core; the scratch-savestate path.
- Anything else: ignored as today (`input_hold_rewind_config ignored`).
- B4's suite: its per-core-bytes test generates the config for PSX / fceumm under `1`; it now sets `all` (B4's
  behaviour) — the only change to B4's suite, its expectations unchanged. Disclosed.

## 3. `state`: a scratch savestate before the hold's pause, loaded at the release (the PS1 path, for A to measure)

**The point of timing.** A save *at* the hold's pause would restore the state the paused core already holds: nothing
gained. The save must come before the pause, inside the silence: **at a controller silence of STATE_AT = 400 ms**
(`PRIVYHUB_INPUT_HOLD_STATE_AT_MS`, 100 to H − 50; default 400), from the detector's quiet tick (every 50 ms), once
per silence, only while the core is playing.
- The save: `SAVE_STATE_SLOT 9` over the NCI (raw loopback, as B4), its acknowledgement read ≤ 100 ms, on B9's own
  worker (never the receive loop). Slot 9: not 0 (the recovery's staging slot), not 1-3 (the user's slots); every
  PrivyHub save / load names its slot, so RetroArch's current slot does not matter.
- **The load at the release** (the hold's release, B8's resume, v2's controller return, B7's stall end — B4's
  `rewind()` call sites, one owner):
  1. the pending's onset (B8's `b8_hold_onset` when B8 moved it) must match the saved silence's onset (± 5 ms), and
     the scratch file `<stem>.state9` under the session's state root must exist, be non-empty and be newer than the
     save's wall time − 1 s. Otherwise `rewind_skipped` ("no scratch state for this pause"), nothing sent, the
     resume as today (a B7-only pause has no save: skipped).
  2. **D-BASE-R3C's caveat:** a mid-FMV state loaded into a PAUSED Beetle PSX HW loops; loaded into a RUNNING core it
     plays; a gameplay state loaded paused plays. So the load goes **into a running core**: input masked (B4's
     mask), then `PAUSE_TOGGLE` (unpause) and `LOAD_STATE_SLOT 9` in the same instant (the core may run 0-1 frame
     with neutral input before the load lands; the load overwrites it), then `GET_STATUS` and the load's
     acknowledgement read ≤ 150 ms (a 16-MB state; B4's 2-frame window is for REWIND). Confirmed = the ack names
     the slot and the status is PLAYING; unmask; then the caller's resume as B4 (resume() on a playing core).
  3. The row: `input_release` (method `state`, `slot`, `save_after_onset_ms`, `frames_restored` = the frames from
     the save to the confirmed pause, less B4's 4, `net_unattended_frames` = the frames from the onset to the save)
     or `rewind_failed` (the reason, the ack / status text). Never raises; a failure never blocks the resume.
- **The cost, stated:** one savestate write per silence ≥ 400 ms, not per hold: PSX HW 16.8 MB, snes9x 0.8 MB. From
  BENCH-R2's bins: 0.9-6.2 such silences / 10 min on the quiet cells (d1 d2 e1 e3 f1-f4) → ≤ ~105 MB / 10 min on
  PSX; 14-52 / 10 min on the bad hours (a1 a2 c1) → up to ~880 MB / 10 min. No rewind buffer (0 MB RAM, 0 CPU when
  idle). The save's own stall of the core's frame (RetroArch serializes on its main thread) is not known: A measures
  the hitch rate in a `none` cell with `state`.
- **What it buys:** the unattended frames per hold become the frames from the onset to the save (~24 at 400 ms + the
  save's latency) instead of ~57; snes9x's rewind takes them to ~0.

## 4. Tests

- `stall_signal.parse("1") == (400, None)`, `"150"` → 150; the host acts at 400 with `1` (a fake client's 300-ms
  stall: no pause; 450: a pause).
- `1` + snes9x: B4's config block; `1` + Beetle PSX HW: none; `all` + PSX: B4's block (bytes as B4); `state`: none;
  the release under `1` + PSX: `rewind_skipped`, no NCI datagram, the resume.
- `state` with a fake core on loopback (SAVE_STATE_SLOT writes the scratch file, LOAD_STATE_SLOT acknowledges,
  GET_STATUS answers): the mark at 400 ms once per silence, never while paused, never twice; the release sends
  PAUSE_TOGGLE then LOAD_STATE_SLOT 9 (the core running at the load), confirmed; a stale / missing file or another
  silence → skipped, nothing sent; a refused load → `rewind_failed`, the resume proceeds; the frame counts.
- Flag absent / `all`: no `rewind_cores` import; the AST proof (B9 items removed = the predecessors); B2 / B4 / B6 /
  B7 / B8 suites green (with the two disclosed test lines).
