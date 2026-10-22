# B4 — corrections to the hashed design (found after the hash, before the install)

The design (`design_written_before_code.md`, sha256 `ca9cc18a…bdaf`, 04:25:28Z) stays as hashed. Two corrections, both
in §3 "the frame counter", found by measurement and by the fake core:

1. **§3 said the confirmed pause trails the real pause by "0-1 frame typically, ≤ ~4 frames".**
   - Measured: ~4 frames, every time.
   - In the companion's own command log (`logs/games/retroarch_control_probe.txt`, read-only;
     `pause_confirm_lag.py` → `pause_confirm_lag.json`), **39 of 39 toggles: the first `GET_STATUS` after
     `PAUSE_TOGGLE` (+13-19 ms) answers the OLD state**, and the second (+70-83 ms, after `pause()`'s 50-ms sleep)
     the new one.
   - Pauses: 61.0-66.8 ms between the two = 3.66-4.01 frames. Resumes: 52.1-71.4 ms.
   - So RetroArch answers a `GET_STATUS` read in the same poll as the toggle before the toggle takes effect, and
     `pause()` always confirms on its second poll.
2. **The frame that reads the toggle runs no core frame.** The fake core (which models the measured reply order)
   showed it:
   - with 3 subtracted, the rewind landed 2 frames before the onset, deterministically.
   - **`hold_rewind.PAUSE_CONFIRM_LAG_FRAMES = 4` = floor(3.66 + 1)**: `counter_before = round((pause − onset) × 60)
     − 4`, logged on every row (`pause_confirm_lag_frames`).
   - The fake now lands 1 frame before the onset in every trial.
   - If the real toggle's frame does run a core frame, the rewind lands 0-1 frame after the onset. Within ±1 either
     way.

This is a deviation from the task's literal "frames_to_rewind = the difference": it is that difference less a
measured constant lag. Disclosed in the record (§3).
