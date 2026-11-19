# G6-HM3 — pre-registration of the tablet run (written and hashed before the run)

Candidate APK `1d658a3fb96a3281816e1900af54c00479bff74d19fa4281281c0e186d9cf64e`
(`PrivyHub/app/build/g6_hm3_candidate/app-debug.apk`), built from the working tree recorded in `after_sha256.txt`.
It goes on the **tablet only**, sideloaded as a file (no adb). **The onn keeps `ca53df0d…`.** This run confirms
nothing for the onn: replacing the onn's APK needs its own pre-registered confirmation there (CL-B7 §6), and the pins
in `tools/` move only in that task.

**When:** no other session running, the onn not streaming, and outside 03:45–05:30Z (plan §3).

## The run (the user, on the tablet)

1. Install the candidate over today's PrivyHub, as an update. If the installer refuses, do not uninstall (that would
   lose the pairing); report it.
2. PrivyHub → Settings → tick "Handheld game screen (portrait, touch buttons)" → Save.
3. Hold the tablet upright and start a PlayStation game. No controller is needed.
4. Touch the drawn buttons a few times. Try Back once (a swipe in from the left or right edge, or the Back button).
5. Leave the game running for at least a minute, then tap **End**.

## The cells (read from the session's decoder report in `logs/games/decoder_sessions/`, the run's newest file)

G6-S1 session 10 is the reference (`../G6_S1_TABLET_FIRST_INSTALL_2026-11-19.md` §5).

| Cell | Read | Met when |
|---|---|---|
| G6-HM3.c1 decode | `decoder.codec_name`, `hardware_accelerated`, `low_latency_enabled` | a hardware decoder (`hardware_accelerated` true) and `low_latency_enabled` true |
| G6-HM3.c2 rate | `video.recent_fps` | ≥ 58 |
| G6-HM3.c3 drops | `decoder.dropped_frames` / `decoder.queued_frames`; `video.dropped_frames` / `video.frames` | each ≤ 1 % (reference 0.37 % and 0 %) |
| G6-HM3.c4 latency | `decoder.max_rx_to_decode_ms`; `decoder.max_output_gap_ms` | ≤ 100 ms; ≤ 250 ms (reference 55; 136) |
| G6-HM3.c5 the box | `handheld.mode`, `video_box`, `pad_region` | `portrait`; `W x W·9/16` with W the window's width; the pad region's height = window height − box height, > 0 |
| G6-HM3.c6 the inert pad | `handheld.touch_live`, `touch_events`, `touch_writes`, `touch_slot`, `pointer_exempted_events` | `false`; > 0; 0; −1; > 0 (the touchscreen reached the pad through the B70 guard) |
| G6-HM3.c7 Back and End | `handheld.back_swallowed`, `end_presses`; the recovery log's `session_end_bye` | ≥ 1 if the user tried Back; 1; one bye after a PLAYING session ≥ 60 s |

**Not cells (the user's remarks, recorded as said):** the picture's place and shape, the overlays' fit in the box,
the drawn buttons, End's ease of use, the portrait paused screen (B73's bar), and whether an edge swipe did anything.

**Context, not cells:** `video.lost_packets`, `fec_unrecoverable_groups` and the link notice belong to the Wi-Fi
link, not the portrait screen.

**Verdict rule:** G6-HM3 is met when c1–c6 are met, and c7 is met for End. A missed cell is reported with its value.
The fix goes into a new candidate, and no threshold changes after this hash.
