# G6-HM4 — pre-registration of the tablet run (written and hashed before the run)

> **G6-HM4b's pre-registration.** This is G6-HM4's (`../g6_hm4_2026-11-19/preregistration.md`, `0fbaf9f2…`) copied
> exactly, changing only: the candidate's hash (and its path), the steps, and one added remark. The sticks' throw is
> 0.875 × G6-HM4's (`../G6_HM4B_SHORTER_STICKS_2026-11-19.md`). The cell ids keep their G6-HM4 names.

**The candidate:** APK `965d4f197213a639fd0277dbbd06f1db2b9c25f1899a5eaace879dabc83d66e5`
(`PrivyHub/app/build/g6_hm4b_candidate/app-debug.apk`, also as `PrivyHub-handheld-preview-965d4f19.apk`). It is built
from the tree in `after_sha256.txt`.
- **The tablet only,** sideloaded as a file (no adb).
- **The onn keeps `ca53df0d…`.** This run confirms nothing for the onn; the pins in `tools/` do not move.

Task: `../../handoffs/G6-HM4_TOUCH_LIVE_TASK.md`. Layout: the amendment G6-HM1a (`2272705f…`) with the shoulders as
addendum B2 (`layout_addendum_b.md`, `775f77c7…`).

## Conditions

- No other session running, the onn not streaming, and outside 03:45–05:30Z.
- The tablet on the **travel router's 5 GHz network**, with **Wi-Fi scanning and Bluetooth scanning off**. The
  network's name is kept out of this record.
- **The tablet within about 1 m of the travel router**, where the link was fine in G6-PLACE P1.
- PrivyHub's "Handheld game screen" on.
- **A PS2 game.**
- No controller paired to the tablet (Q-PAD (b)).

## The user's steps

1. Install the candidate as an update over PrivyHub. If the tablet refuses, do not uninstall; report it.
2. Start the PS2 game. Wait, without touching anything, until the line under the buttons reads "Touch buttons: P1 in
   5…" and counts down to "Touch buttons: Player 1".
3. Press each control once, in this order, and tick each one off:
   1. the D-pad
   2. △
   3. ○
   4. ✕
   5. □
   6. L2
   7. L1
   8. R1
   9. R2
   10. L3
   11. R3
   12. **SELECT**: the game may pause; tap START again to go on
   13. **START**: the game may pause; tap START again to go on
   14. the left stick (touch it)
   15. the right stick (touch it)
   16. **End**: not now; it is step 6
4. Push each stick to its edge and hold a moment: up, down, left, right. The left stick first, then the right.
5. Play freely for at least 2 minutes.
6. Tap **End** (control 16).
7. After End, hold the tablet upright on the main screen. Look at the catalog (2 columns of cards?) and at Settings
   (anything cut off?).

## Which session

The first tablet game session that starts after this file's hash time (`preregistration_hashed_at.txt`) and whose
decoder report has a `handheld` block with `layout` `ps2`. A false start (a session with no `session_end_bye`, or under
60 s) is noted and skipped; the next one counts.

## The cells (read from that session's decoder report and the recovery log)

| Cell | Read | Met when |
|---|---|---|
| G6-HM4.c1 decode | `decoder.codec_name`, `hardware_accelerated`, `low_latency_enabled` | hardware, low latency (as G6-HM3) |
| G6-HM4.c2 rate | `video.recent_fps` | ≥ 58 |
| G6-HM4.c3 drops | `decoder.dropped_frames` / `queued_frames`; `video.dropped_frames` / `video.frames` | each ≤ 1 % |
| G6-HM4.c4 latency | `decoder.max_rx_to_decode_ms`; `decoder.max_output_gap_ms` | ≤ 100 ms; ≤ 250 ms |
| G6-HM4.c5 the join | `handheld.touch_slot`; `handheld.p1_join_after_release_ms` | 0; in 5000–5300 |
| G6-HM4.c6 every control | `handheld.controls_pressed` | holds all 16: `DPAD`, `TRIANGLE`, `CIRCLE`, `CROSS`, `SQUARE`, `L2`, `L1`, `R1`, `R2`, `L3`, `R3`, `SELECT`, `START`, `LSTICK`, `RSTICK`, `END` |
| G6-HM4.c7 sticks | `handheld.stick_max_deflection.left` / `.right`: `up`, `down`, `left`, `right` | each ≥ 0.9 |
| G6-HM4.c8 End | `handheld.end_presses`; the recovery log's `session_started` → `session_end_bye` | 1; one bye after ≥ 60 s PLAYING |

**Context, not cells:**
- `touch_writes` (> 0 expected) and `takeovers` (0 expected: no pad);
- `back_swallowed`;
- `video.lost_packets`, the sequence resyncs and the link rows.

**The verdict rule:** G6-HM4 is met when c1–c8 are all met. A missed cell is reported with its value; the fix goes
into a new candidate, and no threshold changes after this hash.

**The user's remarks, recorded as said and not cells:**
- whether each control is reachable without moving the grip (the shoulders above all);
- the stick feel;
- the countdown;
- the status panel (not expected to show here: no controller);
- the main app's 2 columns and Settings, upright;
- whether the shorter throw suits driving.
