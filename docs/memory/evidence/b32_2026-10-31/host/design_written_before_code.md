# B32 (host) — design, written before any code

Queue: `handoffs/QUEUE_2026-10-31L.md` §B32, the host half. Baseline HEAD 1904fe8. Copy `/tmp/b_q31l_b32h`.

## A. Settled first (read-only; the code and `ffmpeg -h`)

- **Today a step is a new encoder process with a new SSRC.** `adaptive_level_transition` (`native_stream.py:2595`) ->
  `diagnostic_c3_validated_bitrate_transition` -> `_run_c3_linux_bitrate_cycle(validated_transition=True)`
  (`diagnostics/c3_linux_actuator_probe.py:466-924`): kill the old ffmpeg, spawn a new one at the new `-b:v`, poll
  the relay's `rtp_packets` for the first new RTP (<= 2 s), hold 0.75 s. The new process's RTP muxer draws a random
  SSRC, a random starting sequence and a random RTP timestamp base; the relay (`native_fec_relay.py`) forwards bytes
  unchanged, so the onn sees an SSRC change and waits for the IDR. The gap is kill + spawn + first frame (TRIP-R2:
  140-248 ms, 426-430 ms in 3 of 32).
- **Runtime rate control: not allowed by this encoder.** ffmpeg 7.1.5 `h264_vaapi` exposes rc_mode / qp /
  max_frame_size / quality as init-time AVOptions only; VAAPI rate-control parameters are set at encoder init. The
  `zmq` / `sendcmd` filters send commands to *filters*, not encoders, and the argv runs `-nostdin` with stdin
  DEVNULL, so there is no runtime path to `-b:v`. **So the queue's fallback is the one the code allows: a new IDR at
  the new rate on the same stream** — a new encoder process is unavoidable, a new SSRC is not.
- **The RTP muxer can be told its SSRC** (`-ssrc`, and `-seq` for the start sequence) but not its timestamp base
  (random). So the relay is the place that keeps the stream's identity: it rewrites the new encoder's SSRC, sequence
  and timestamp onto the old stream's.

## B. The design, behind `PRIVYHUB_STEP_IN_PLACE=1` (`== "1"` after strip; absent / 0 / junk = today)

New module `companion/step_in_place.py`:
- **`RtpSplice`** — installed on the relay *instance* (its `_handle_rtp` wrapped by an instance attribute, the relay's
  source not edited), idle = pass-through. It keeps the output identity (`out_ssrc`, the last output sequence and
  timestamp) of the stream the onn sees.
  - `arm(new_ssrc)`: packets of `new_ssrc` are buffered (not forwarded) while the old encoder's packets still pass;
    at the first old packet carrying the RTP marker (a frame boundary) after the first new packet — or after 120 ms
    of buffering, whichever first — the splice happens: the buffered new packets are forwarded, rewritten
    (SSRC = `out_ssrc`, sequence continuing +1 from the last forwarded, timestamp = last + one frame (90 kHz / fps)
    at the new encoder's first timestamp, then the new encoder's own deltas); from then on old-SSRC packets are
    dropped and new-SSRC packets rewritten. The new encoder's first frame is its IDR (a fresh encoder starts with
    one), so the onn gets exactly one IDR at the splice and no SSRC change, no sequence gap.
  - A packet of any other SSRC (a full restart / recovery restart's random SSRC) drops the mapping: pass-through,
    today's SSRC change.
  - Counters: splices, rewritten, dropped_old, the splice's measured output gap (the time between the last old
    packet forwarded and the first new packet forwarded) — no addresses.
- **`run_in_place_transition(manager, target)`** (under the stream lock, called by `adaptive_level_transition`):
  the same preconditions as today's validated transition (target and current in the validated levels plus the remote
  ladder's actuator levels when `probe.REMOTE_LADDER` is set — LAN and remote ladders alike; a sized (1080p) level is
  not in place: today's path); the new encoder spawned **before** the old is killed (`_build_linux_ffmpeg_command`
  at the target + `-ssrc <a fresh random value>` inserted before `-f rtp`); wait <= 2 s for the splice; then the old
  killed, `_process` = the new, the 0.75 s stability window as today, `_active_bitrate_kbps` = target.
  - **If the new encoder does not splice in 2 s** (exits, or no RTP): it is killed, the splice disarmed, and today's
    restart runs (`run_c3_linux_validated_bitrate_transition`), its payload marked `in_place: false,
    in_place_fallback: <why>`.
  - Payload: today's validated-transition schema with `mode: validated_ladder_in_place` and `video`:
    `encoder_restarted: true` (a new process), `in_place: true`, `ssrc_unchanged: true`, `idr_frames: 1`,
    `ffmpeg_spawn_ms`, `first_rtp_resume_ms` (spawn -> splice), `rtp_silence_after_spawn_ms`, `splice_gap_ms`,
    `overlap_ms`, `host_verified_ms`.
- **`native_stream.py`**: `STEP_IN_PLACE = None`, imported only with the flag (as `START_RUNG` / `ENCODER_RC`); in
  `adaptive_level_transition`, the non-sized Linux branch calls it when set. The loopback c3 route, recovery's
  same-level restart, the sized transition and every start are untouched.
- **`adaptive_bitrate_live.py`** `_actuate`: the `transition_done` row gains `in_place`, `ssrc_unchanged`,
  `splice_gap_ms` (and `in_place_fallback`) **only when the actuator's `video` carries `in_place`** — today's
  actuator never does, so the row is byte for byte today's.

## C. The explicit cap beside the umbrella (inside the adopted `PRIVYHUB_REMOTE=1`; no new flag)

- **Today:** an explicit `PRIVYHUB_REMOTE_RUNG_CAP` is built at import with no ladder (the ladder line is implied
  by the umbrella, not set) -> `remote_ladder_flag_absent`, inactive; and the umbrella, seeing the line explicit,
  builds no cap of its own. So `=4000` beside the umbrella does nothing.
- **Built:** in `RemoteUmbrella.__init__`, when the cap line is explicit **and** the ladder line is implied (the
  umbrella owns the ladder), the umbrella builds `RemoteCap(<the explicit value>, its ladder)` and installs it on a
  remote session / restores the import-time object on a LAN session exactly as it does the implied 7000. Its
  `remote_cap_config` row (active, the value) written once at the first remote session; `remote_config`'s cap entry
  `explicit <value> on the umbrella's ladder`, in force on remote. An explicit ladder line, or no explicit cap line:
  B28 byte for byte.

## D. Tests (`tests/step_in_place/`, new; `tests/remote_umbrella` unedited and green)

- The REAL `NativeVideoFecRelay` on loopback, a fake onn (UDP socket recording SSRC / sequence / timestamp / IDR),
  fake encoders (threads sending 60-fps RTP frames to the relay's port; the first frame's NAL type 5 IDR; SSRC from
  the argv's `-ssrc` or random), a fake manager with `_build_linux_ffmpeg_command` / `_kill_managed_process`:
  - **LAN 7000 -> 6000 and 5000 -> 5500 in place:** the onn sees one SSRC throughout, a continuous sequence, one IDR
    after the step, monotonic timestamps; the payload `in_place` / `ssrc_unchanged`; `_active_bitrate_kbps` the
    target; the old encoder killed; one process at the end.
  - **Remote ladder:** 4000 -> 5000 in place with `probe.REMOTE_LADDER` set (remote path); 4000 refused without it
    (as today).
  - **Fallback:** a new encoder that never sends -> today's restart called, `in_place: false`.
  - **A later full restart (an unknown SSRC):** pass-through, the onn sees the new SSRC (today).
  - **The ladder row:** `_actuate` with an in-place actuator payload -> `transition_done` carries `in_place: true`,
    `ssrc_unchanged: true`; with today's payload -> no such keys (field for field).
  - **Absent:** `adaptive_level_transition` calls today's validated transition; a fresh process without the flag
    imports no `step_in_place`; `0` / empty / junk = off.
- **The cap:** the umbrella with `PRIVYHUB_REMOTE_RUNG_CAP=4000` explicit, a remote session: the cap active 4000 on
  the umbrella's ladder; the ladder's increase above 4000 refused `remote_cap` (never climbs past 4000); a LAN session
  -> the import-time object back; without the explicit line -> B28's 7000 (unchanged).
- Mutations: the splice not rewriting the SSRC (the onn sees two SSRCs: fails); the cap built on `None` (inactive:
  fails).
- Every `tests/` suite green in the copy.
