# G6-HM4 — pre-registration of the tablet run (written and hashed before the run)

> **G6-JOIN1's pre-registration.** This is G6-STICK1's (`../g6_stick1_2026-11-20/preregistration_v2.md`,
> `3cb6fe05…`) copied exactly, changing only: the candidate's hash (and its sha8 file name); "Which session" (a report
> with `p1_join_via`: this candidate); step 2 (hold ✕ to join); c5 (the join by the hold); and one added remark. The
> change: holding any touch control for a real pad's join hold (0.5 s) makes the touch pad P1 at once; the 5-s
> countdown stays as the fallback (`../G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md`). Every other cell keeps its bound.

**The candidate:** APK `6d2fff764d4380d4d03b52d64cd1379de13085ab7526bde1634bbf96aacaf207`
(`PrivyHub/app/build/g6_join1_candidate/app-debug.apk`, also as `PrivyHub-handheld-preview-6d2fff76.apk`). It is built
from the tree in `after_sha256.txt`.
- **The tablet only,** sideloaded as a file (no adb).
- **The onn keeps `ca53df0d…`.** This run confirms nothing for the onn; the pins in `tools/` do not move.

Task: `../../handoffs/G6-HM4_TOUCH_LIVE_TASK.md`. Layout: the amendment G6-HM1a (`2272705f…`) with the shoulders as
addendum B2 (`layout_addendum_b.md`, `775f77c7…`).

## Conditions

- No other session running, the onn not streaming, and outside 03:45–05:30Z.
- **The companion already runs G6-SCREEN1b's commit** (`b2716e17`, committed 08:18:57Z; the unit active since
  08:19:07Z; no companion file changed since): no restart is needed. G6-STICK1 changes nothing on the hub.
- **The tablet connects over Tailscale from the home Wi-Fi**, with **Wi-Fi scanning and Bluetooth scanning off**. The
  network's name and every address are kept out of this record.
- **The session's class**, `remote-direct` or `lan`, whichever the hub logs (the recovery log's `remote_config`
  row), is recorded as context, not a cell.
- PrivyHub's "Handheld game screen" on.
- **A PS2 game.**
- No controller paired to the tablet (Q-PAD (b)).

## The user's steps

1. Install the candidate as an update over PrivyHub. If the tablet refuses, do not uninstall; report it.
2. Start the PS2 game. When the line under the buttons shows the countdown, hold ✕ until it reads 'Touch buttons:
   Player 1' (about 0.5 s: the physical hold time).
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
   16. **End**: not now; it is step 7
4. Push each stick to its edge and hold a moment: up, down, left, right. The left stick first, then the right.
5. Push the left stick into each diagonal corner and hold a moment (up-left, up-right, down-right, down-left); then
   circle it slowly twice, and then the right stick the same.
6. Play freely for at least 2 minutes.
7. Tap **End** (control 16).
8. After End, hold the tablet upright on the main screen. Look at the catalog (2 columns of cards?) and at Settings
   (anything cut off?).

## Which session

The first tablet game session that starts after this file's hash time (`preregistration_hashed_at.txt`) and whose
decoder report has a `handheld` block with `layout` `ps2` **and a `p1_join_via` key** (this candidate). A session on
an older app (no `p1_join_via`) is noted and skipped. A false start (a session with no
`session_end_bye`, or under 60 s) is noted and skipped; the next one counts.

## The cells (read from that session's decoder report and the recovery log)

| Cell | Read | Met when |
|---|---|---|
| G6-HM4.c1 decode | `decoder.codec_name`, `hardware_accelerated`, `low_latency_enabled` | hardware, low latency (as G6-HM3) |
| G6-HM4.c2 rate | `video.recent_fps` | ≥ 58 |
| G6-HM4.c3 drops | `decoder.dropped_frames` / `queued_frames`; `video.dropped_frames` / `video.frames` | each ≤ 1 % |
| G6-HM4.c4 latency | `decoder.max_rx_to_decode_ms`; `decoder.max_output_gap_ms` | ≤ 100 ms; ≤ 250 ms |
| G6-HM4.c5 the join | `handheld.touch_slot`; `handheld.p1_join_via`; `handheld.p1_join_after_release_ms` | 0; `"hold"`; < 5000 |
| G6-HM4.c6 every control | `handheld.controls_pressed` | holds all 16: `DPAD`, `TRIANGLE`, `CIRCLE`, `CROSS`, `SQUARE`, `L2`, `L1`, `R1`, `R2`, `L3`, `R3`, `SELECT`, `START`, `LSTICK`, `RSTICK`, `END` |
| G6-HM4.c7 sticks | `handheld.stick_max_deflection.left` / `.right`: `up`, `down`, `left`, `right` | each ≥ 0.9 |
| G6-HM4.c8 End | `handheld.end_presses`; the recovery log's `session_started` → `session_end_bye` | 1; one bye after ≥ 60 s PLAYING |
| G6-SCREEN1.c9 the box | `handheld.video_box`; `handheld.pad_region` | `1200x900`; `1200x1100` |
| G6-SCREEN1.c10 the crop (PS2) | `handheld.video_crop`; `handheld.video_source_rect` | `"4:3"`; `"160,0,960x720"` |
| G6-SCREEN1b.c11 the hub's handheld launch | the session's PS2 game log (`logs/games/<launch>-ps2.log`, the launch before the session) | holds the line `PS2 handheld: widescreen patch off for this launch only` |
| G6-STICK1.c12 the diagonals | `handheld.stick_diag_max.left.end_to_end`; `.right.end_to_end` | each ≥ 0.95 |
| G6-STICK1.c13 the mapping | `handheld.stick_mapping` | `"ds2-square-0.75-c1.33"` |

**Context, not cells:**
- `touch_writes` (> 0 expected) and `takeovers` (0 expected: no pad);
- `back_swallowed`;
- `video.lost_packets`, the sequence resyncs and the link rows;
- the session's class (`remote_config.class`).

**The verdict rule:** G6-HM4 is met when c1–c13 are all met. A missed cell is reported with its value; the fix goes
into a new candidate, and no threshold changes after this hash.

**The user's remarks, recorded as said and not cells:**
- whether each control is reachable without moving the grip (the shoulders above all);
- the stick feel;
- the countdown;
- the status panel (not expected to show here: no controller);
- the main app's 2 columns and Settings, upright;
- whether the shorter throw suits driving;
- whether the bigger picture looks right, with nothing cut off that matters;
- whether End's new place is ever pressed by mistake;
- if a PS1 game is also played (optional): whether its stretched picture looks right; its `video_crop` (`"stretch"`
  expected) is recorded, not a cell;
- whether turning through the diagonals now feels right;
- whether it feels like a DualShock 2;
- anything too twitchy;
- whether holding to join feels right.
