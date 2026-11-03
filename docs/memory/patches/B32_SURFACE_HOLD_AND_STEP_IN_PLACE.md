---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8
---

# B32 — the stream survives a brief loss of the screen; a step-up in place

**Result (client): SETTLED + BUILT behind `debug.privyhub.surface_hold=1`.**
- **Tests:** JVM `SurfaceHoldTest` 8 green, the suite 169 / 169; host `tests/surface_lost` 9 green; 3 mutations
  caught.
- **Proof:** absent = today, PROVEN.
- No live run; NOT installed. Nothing committed.

Record: `evidence/B32_SURFACE_HOLD_AND_STEP_IN_PLACE_2026-10-31.md`. Diff (client):
`evidence/b32_2026-10-31/b32_client.diff`.

- **Settled:** Android gives no pause reason, and the client logged nothing about it.
  - Under the flag the activity records focus loss, top-resumed loss, the user-leave hint, the screen state,
    input-device events and the keys in the 2 s before.
  - The keys the system intercepts (`HOME`, `APP_SWITCH`, …) never reach it.
- **Built (client):**
  - **The hold.** On `surfaceDestroyed` the receiver, the audio and the controller sender keep running and the
    decoder is closed, for up to **12 s**.
  - A surface back within it continues the **same session**: no `native-stream-start`, no `session_ended`, no
    rung reset. The next IDR (≤ 250 ms) builds the decoder on the new surface.
  - The stall signal reads the held age, so the host pauses the game during the hold and releases it at the first
    frame.
  - Past 12 s: today's restart.
  - **`surface_lost` rows** (cause, keys, devices, away, outcome), one per heartbeat.
  - **Pad guide / Home-class keys are consumed** when they come from a pad; the remote's pass.
  - `surface_hold` in the report.
- **Built (host):** `companion/surface_lost_row.py`; `plugins/games.py` +5. The heartbeat key gives one
  recovery-log `surface_lost` row. No key: nothing imported.
- **Apply:** `git apply evidence/b32_2026-10-31/b32_client.diff`. Client: the APK with B32, then
  `adb shell setprop debug.privyhub.surface_hold 1`. The host part needs no line.
- **Rollback:** the property empty (`adb shell setprop debug.privyhub.surface_hold ""`) or a reboot gives today.
  Or revert the files.

## Host: the step in place and the cap (B32-host)

- **Host, settled:** ffmpeg 7.1's `h264_vaapi` has no runtime rate control; `zmq` / `sendcmd` reach filters only, and
  the argv is `-nostdin`. So a new encoder process is unavoidable. The fallback the queue names is built: one IDR at
  the new rate on the **same stream**.
- **Host, built** behind `PRIVYHUB_STEP_IN_PLACE=1` (`companion/step_in_place.py`, new;
  `native_stream.py` +16; `adaptive_bitrate_live.py` +3):
  - **The step:** the new encoder (`-ssrc` fresh) starts before the old one is killed. The relay instance's splice
    switches at the old encoder's frame end (≤ 120 ms) and rewrites the new encoder's SSRC, sequence and timestamp onto
    the old stream. The onn sees no SSRC change and one IDR.
  - **No splice in 2 s:** today's restart (`in_place: false`).
  - **The ladder's `transition_done` row** carries `in_place` / `ssrc_unchanged` / `splice_gap_ms`.
  - **The LAN and the remote ladder** alike.
- **Host, the explicit cap beside the umbrella** (`remote_umbrella.py` +12; inside the adopted `PRIVYHUB_REMOTE=1`):
  an explicit `PRIVYHUB_REMOTE_RUNG_CAP=<kbps>` now acts on the umbrella's ladder on remote sessions.
- **Tests:** `tests/step_in_place` 15 green ×3; 2 mutations caught; every suite as the baseline; absent PROVEN (AST).
- **Diff:** `evidence/b32_2026-10-31/host/b32_host.diff` (5 files).
- **Apply:** `git apply` it from the repo root. It acts only with `PRIVYHUB_STEP_IN_PLACE=1` in the service's
  environment, or for the cap, an explicit `PRIVYHUB_REMOTE_RUNG_CAP` beside `PRIVYHUB_REMOTE=1`.
- **Rollback:** no `PRIVYHUB_STEP_IN_PLACE` line, which is today's step. Or `git apply -R` the diff. The relay is not
  edited.

*(Merged by the coordinator from `b32_2026-10-31/host/` — the host worker's text, unedited.)*
