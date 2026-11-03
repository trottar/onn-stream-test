<!-- B32 record, the host half (session B's B32-host worker; to be merged by the coordinator) -->

## H. The host: a step on the same stream (`PRIVYHUB_STEP_IN_PLACE=1`) and the cap beside the umbrella

**Classification (host): SETTLED + BUILT** behind `PRIVYHUB_STEP_IN_PLACE=1`; the explicit cap fixed inside the adopted
`PRIVYHUB_REMOTE=1` (no new flag). `tests/step_in_place` 15 green (three runs); every `tests/` suite as the baseline
plus the new one; two mutations caught; absent = today PROVEN. NOT ADOPTED; no live run; nothing committed.
Design `host/design_written_before_code.md`, sha256 `e35957e9…0265`, hashed **17:38:39Z, before any host code**.

### H.0 Settled: what the code allows

- **Today a step is a new process and a new SSRC.** `adaptive_level_transition` (`native_stream.py:2595`) →
  `diagnostic_c3_validated_bitrate_transition` → `_run_c3_linux_bitrate_cycle(validated_transition=True)`
  (`diagnostics/c3_linux_actuator_probe.py:466-924`): kill the old ffmpeg, spawn one at the new `-b:v`, poll the
  relay for the first new RTP (≤ 2 s), hold 0.75 s. The new RTP muxer draws a random SSRC, sequence start and
  timestamp base; the relay forwards bytes unchanged; the onn sees the SSRC change and waits for the IDR. The gap is
  kill + spawn + first frame: TRIP-R2's 140-248 ms, and 426-430 ms in 3 of 32.
- **Runtime rate control is not available.** ffmpeg 7.1.5's `h264_vaapi` (`ffmpeg -h encoder=h264_vaapi`, read-only)
  takes `rc_mode`, `qp`, `max_frame_size` and `quality` as init-time options only; VAAPI's rate-control parameters are
  set when the encoder opens. `zmq` / `sendcmd` exist, but they command *filters*, not encoders. The argv runs
  `-nostdin` with stdin DEVNULL. **So a new encoder process cannot be avoided; a new SSRC can.**
- **The queue's fallback, as the code allows it: one IDR at the new rate on the same stream.** The RTP muxer takes
  `-ssrc` (`ffmpeg -h muxer=rtp`), but no timestamp base. So the relay keeps the stream's identity.

### H.1 Built (`host/b32_host.diff`)

**`companion/step_in_place.py` (new).**
- **`RtpSplice`.** It wraps the relay *instance's* `_handle_rtp` at the first in-place step; `native_fec_relay.py` is
  not edited. Idle, it passes every packet through unchanged.
  - **Armed** with the new encoder's SSRC, it buffers the new encoder's packets while the old encoder's still pass.
  - **The splice** happens at the old encoder's next frame end (its RTP marker), or after **120 ms**. The buffered
    packets go out rewritten onto the old stream: its SSRC, the sequence +1 and the timestamp + one frame (1,500 at
    90 kHz / 60 fps). After that the new encoder's packets are rewritten the same way and the old encoder's are
    dropped.
  - **The new encoder's first frame is its IDR.** So the onn gets one IDR, no SSRC change and no sequence gap.
  - **An SSRC the splice never saw** (a full or recovery restart) drops the mapping. That is pass-through: today's
    SSRC change, byte for byte.
- **`run_in_place_transition`**, under the stream lock:
  - **The preconditions** are those of today's validated transition. The levels are `LINUX_VALIDATED` plus the remote
    ladder's actuator levels when `probe.REMOTE_LADDER` is set, so the LAN and the remote ladders alike. A precondition
    today's path would refuse goes to today's path, with its own error. The sized 1080p rung is untouched.
  - **The step:** the new encoder starts at the target with a fresh `-ssrc` (inserted before `-f rtp`) **before the
    old one is killed**. The function waits ≤ 2 s for the splice, then kills the old encoder, keeps today's 0.75 s
    stability window, and sets `_active_bitrate_kbps`.
  - **No splice in 2 s** (exited, or no RTP): the new encoder is killed, the splice disarmed (its late packets dropped)
    and today's restart runs, marked `in_place: false, in_place_fallback: <why>`.
  - **The payload** has today's schema with `mode: validated_ladder_in_place` and `video`: `in_place`,
    `ssrc_unchanged`, `idr_frames: 1`, `splice_gap_ms`, `splice_at_old_frame_end`, `overlap_ms`, and today's cycle
    timings. The encoder's log gets `B32 in-place step: …` lines.
- **`native_stream.py` (+16):** `STEP_IN_PLACE`, imported only with `== "1"`. `adaptive_level_transition`'s non-sized
  Linux branch calls it, with errors wrapped as today's `NativeStreamError`. The loopback c3 route, recovery's
  same-level restart, the sized transition and every start are unchanged.
- **`adaptive_bitrate_live.py` (+3):** the ladder's `transition_done` row (`logs/games/adaptive_bitrate_shadow.jsonl`)
  gains `in_place`, `ssrc_unchanged`, `splice_gap_ms` and `in_place_fallback`, **only when the actuator's `video`
  carries `in_place`**.
- **`remote_umbrella.py` (+12), the explicit cap (TRIP-R2 §5).**
  - **What changes:** when `PRIVYHUB_REMOTE_RUNG_CAP` is explicit and the ladder line is implied (the umbrella owns
    the ladder), the umbrella builds `RemoteCap(<the explicit value>, its ladder)`. It installs that cap on a remote
    session and puts the import-time object back on a LAN session.
  - **Rows:** `remote_cap_config` (active, the value) once; `remote_config`'s cap entry reads
    `explicit <v> on the umbrella's ladder`.
  - **Unchanged (B28):** an explicit ladder line, or no explicit cap.
  - **So the `_cowork_prompt_cap.txt` pin (4000) would now take effect** if it were applied. It is not applied, and
    A removes the file at home.

### H.2 Tests (`host/tests_step_in_place.txt`, `host/tests_mutations.txt`, `host/tests_regression_after.txt`)

**The harness:** the REAL `NativeVideoFecRelay` on loopback; a fake onn recording SSRC, sequence, timestamp and NAL
type; fake encoders at 60 fps, 4 packets a frame, the first frame an IDR, the SSRC from `-ssrc` (else random, as
ffmpeg's), random sequence and timestamp bases; a fake manager whose `diagnostic_c3_validated_bitrate_transition` is
today's restart.

**What each test shows:**
- **LAN, 7000 → 6000 → 5000 in place:**
  - one SSRC throughout (the first encoder's), the sequence continuous, timestamps +0 / +1500 only;
  - 3 IDRs (the start's + one per step);
  - each payload `in_place` / `ssrc_unchanged` / `idr_frames 1`, with the splice gap under the bound;
  - the old encoders killed and the new one `_process`; `-ssrc` before the RTP output; today's restart never called.
- **Remote, 4000 → 5000 in place:** with a real `RemoteLadder` on an overlay address. Without the remote ladder,
  4000 is today's refusal: no second encoder is spawned.
- **Fallback:** a new encoder that never sends → today's restart, `in_place: false`,
  `replacement_rtp_did_not_splice`; the silent encoder killed; the onn sees today's SSRC change.
- **A later full restart** after a splice → pass-through, byte for byte; `identity_resets` 1.
- **The splice unit:**
  - idle pass-through, byte for byte;
  - the wait for the old frame's end, with sequence and timestamp wrap-around, and the old encoder dropped;
  - the 120-ms bound;
  - `-ssrc` placed in the real start argv (G8-S2's stub `_start_linux_locked`).
- **The ladder row:** today's payload → today's 17 keys in today's order; an in-place payload → `in_place`,
  `ssrc_unchanged`, `splice_gap_ms`.
- **The flag:** `0` / empty / junk / `yes` / `true` = off in a fresh process; the actuator entry today's vs the step.
- **The cap:** B28's harness, imported unedited.
  - The umbrella with `PRIVYHUB_REMOTE_RUNG_CAP=4000` explicit and today's inactive import-time object:
    - on a remote session over 160 reports: the cap active at 4000 on the umbrella's ladder, no transition above 4000,
      `remote_cap` clamps, one `remote_cap_config` (active, 4000), and `remote_config` saying so;
    - then on a LAN session: 7000, with the import-time object back.
  - Without the line: B28's implied 7000.

**Mutations:**
- **The splice writes the new encoder's own SSRC:** 3 tests fail.
- **The explicit cap built on no ladder:** 1 test fails.

**Every suite** (`tests_regression_after.txt` against `/tmp/b_q31l_scratch/tests_regression_queue_l_baseline.txt`):
the same outcomes, plus `tests/step_in_place` OK. The four `tools/` tests fail in a copy, as at every baseline.

### H.3 Not shown by a test, for the bench (HOME-1)

- **The onn's own receiver** given an in-stream IDR with no SSRC change. The decoder is not reconfigured (the same
  720p and SPS), and a fresh IDR resets references, but the client has never seen this live.
- **Two `x11grab` + `h264_vaapi` processes at once** for ~0.2-0.4 s (the spawn → first frame → kill) on this GPU.
- **The splice gap on real frames.** The bench cell measures all three.
