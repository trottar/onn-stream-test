<!-- B32 patch file, the host half (to be merged by the coordinator) -->
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
