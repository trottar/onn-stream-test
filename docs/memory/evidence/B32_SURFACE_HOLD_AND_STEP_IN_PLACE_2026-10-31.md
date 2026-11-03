---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8 (B32 uncommitted; built in /tmp copies, integrated by the coordinator)
---

# B32 — the stream survives a brief loss of the screen; every foreground loss logged; pad system keys kept; a step-up in place

**Classification (client): SETTLED (what the code can see) + BUILT** behind `debug.privyhub.surface_hold=1`.
- **Tests:** JVM `SurfaceHoldTest` 8 green, the whole JVM suite 169 / 169 (161 + 8) three runs; host
  `tests/surface_lost` 9 green three runs; every host suite in the copy (`tests_regression_after.txt`); three
  mutations caught.
- **Proof:** absent = today, PROVEN (`proof_flag_absent.md`, 0 unclassified lines).
- NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b32_2026-10-31/design_written_before_code.md`, sha256 `73fb9604…d91e`, hashed **17:40:28Z, before any B32
client code**. Precondition: only the companion and `privyhub-trip-log` active (`units_at_start.txt`).

## 0. Settled: what took the foreground, and what the client can say about it

- **Today the client logs nothing about it.** `onPause` keeps one time (B11's `notePause`), so a restart's cause has
  `paused_before_loss_ms` and `away_ms` only. No key, focus or device event is kept.
- **Android gives no pause reason.** What the activity can observe:
  - `onWindowFocusChanged(false)`: another window took focus (a system panel, the TV side panel, a dialog);
  - `onTopResumedActivityChanged(false)` (API 29+): another activity became top-resumed (the launcher, an
    assistant, a settings activity);
  - `onUserLeaveHint()`: the user's own navigation (Home, or a launch from a notification). A system panel or an
    activity started by something else does not call it;
  - `PowerManager.isInteractive` at the loss (screen off, HDMI-CEC standby);
  - `InputManager.InputDeviceListener`: added / removed / changed (a Bluetooth pad dropping and reconnecting);
  - keys at `dispatchKeyEvent`.
- **What never reaches the activity:** the keys the window-manager policy intercepts — `KEYCODE_HOME`,
  `APP_SWITCH`, `POWER`, and on most builds `ASSIST` / `ALL_APPS` / `NOTIFICATION`. A pad Home that maps to
  `KEYCODE_HOME` can only show as `user_leave` with no key.
- **What does reach it:** a pad guide button that maps to `KEYCODE_BUTTON_MODE` (the generic layout for most pads'
  PS / Xbox / Home button). Today the sender does not map it (`handleKeyEvent` returns false), so it goes to
  `super.dispatchKeyEvent`, i.e. the system's default handling.
- **Which it was in each of the six cannot be settled from the code;** the onn's event log needs adb.
  - Inference only: a pause 0.8-4.5 s before the surface went is a pause then a stop. That is what an activity
    coming on top does (a panel activity, the launcher). A Home press stops within ~0.5 s.
  - The `surface_lost` rows below settle it at the next loss.

## 1. Built (client; `b32_2026-10-31/b32_client.diff`)

**`SurfaceHold.kt` (new)** holds the flag, the hold's state, the 2-s event ring, the rows and the counters.
- `debug.privyhub.surface_hold=1` gives the **12,000-ms bound**; an integer 10000-30000 gives that bound.
- Absent / empty / `0` / junk / out of range is off.

**The bound.** The five restarts with a report were away (surface lost → surface back) 1,039 / 1,188 / 1,787 /
2,027 / 8,582 ms.
- The sixth (05:19:35) has no report, so **no bound can be proven to cover all six**.
- 10 s covers the five with 1.4 s over the kart's 8.6 s. **12 s** gives a 3.4-s margin and stays below the 15-s
  test case.
- The hold counts from `surfaceDestroyed`. A paused activity keeps its surface, and the pipeline already runs
  through a pause today.

**`NativeStreamActivity.kt`, every hook `surfaceHold?.…`.** On `surfaceDestroyed`, if a session is started, the
activity is not finishing and the flag is on:
- the report is cached (today's call);
- the sender's state goes neutral and it **keeps sending**; the RTP and audio receivers **keep running**;
- **the decoder is closed.** `close()` joins the codec's thread, so the codec lets go of the surface before the
  callback returns. A codec cannot be kept without a live output surface, and there is none until `surfaceCreated`;
- with the flag, the parameter-set callback builds a decoder only on a live surface;
- an expiry is posted at the bound.
- **No `RestartGuard.onSurfaceLost`, no pending; `sessionStarted` stays true.**

**The stall signal during the hold.** B7's signal, on by default, is fed `age at the loss + time since`. The decoder
is gone, so its own age is -1, which the monitor reads as "no frame yet".
- From ~150 ms the host's stall path pauses the game, as at a link stall, so the game does not run unseen.
- The uplink never goes silent, so the host takes no `input_hold`.
- No heartbeat goes while no decoder exists (today's early return).

**`surfaceCreated` within the bound:** the expiry is cancelled and the new surface recorded.
- **No `startSession`, no `native-stream-start`, no `guard_end`, no `session_ended`, no rung reset.**
- The next in-band SPS/PPS builds the decoder on the new surface. Every IDR carries them, and the GOP is 15 frames,
  ≤ 250 ms.
- Its first rendered frame ends the synthetic age, so the monitor sends `stall_end` and the host releases as after
  a link stall.
- No keyframe request is needed: B10 found the host has no runtime IDR, and the next IDR is ≤ 250 ms away.

**Past the bound:** today's surface-loss path, deferred (`RestartGuard.onSurfaceLost` with the report cached at the
loss, `stopLocalPipeline()`, `sessionStarted = false`).
- The next `surfaceCreated` is today's restart (`trigger: surface`, `guard_end=1`).
- That restart's `away_ms` counts from the expiry; the row carries the true away time.

**Ending inside the hold:**
- The activity ending (`onDestroy`): the expiry is cancelled and today's `stopSession` runs (report +
  `native-stream-stop`).
- A recreation: B15's hand-over, with `sessionLive` true.

**`NativeControllerSender.neutralize()`**, appended: every player's state neutral, with the loop and the device map
kept.
- It is called at `onPause` (no input reaches a paused activity, so nothing stays held) and at the loss.

**Pad system keys.** With the flag, first in `dispatchKeyEvent`:
- these keys, **from a device whose sources include `SOURCE_GAMEPAD` or `SOURCE_JOYSTICK`**, are consumed: neither
  the sender nor the system sees them:
  - `BUTTON_MODE`, `GUIDE`, `MENU`, `SEARCH`, `SETTINGS`;
  - `HOME`, `ALL_APPS`, `ASSIST`, `VOICE_ASSIST`, `NOTIFICATION`, `APP_SWITCH` (if they arrive at all);
- from any other source (the onn remote) they pass as today;
- every key-down is noted for the rows (code, pad / remote / other, consumed or passed), and the report counts both.
- `BACK` is today's.

**The report:** a `surface_hold` object with `bound_ms`, `losses`, `held`, `restarted`, `ended_in_hold`,
`decoders_built`, `rendered_before_reattach`, `pad_system_keys_consumed`, `system_keys_passed`, `rows_queued`,
`rows_sent` and `rows_dropped`.
- `rendered_before_reattach` is there because a held session's decoder counters restart at the re-attach.
- **Disclosed:** the heartbeat's `rendered_frames` drops back once at a re-attach, for the same reason.

## 2. The `surface_lost` row

One row per loss:
- **When it is queued:** `held` at the first frame after the re-attach; `restarted` at the expiry.
- **When it is sent:** at most 8 are queued (older dropped and counted), **one per heartbeat** as
  `&surface_lost=<url-encoded compact JSON>`. A held row goes on the first heartbeat after the picture is back; a
  restarted row on the new session's first heartbeat. A row whose heartbeat is lost is not re-sent.

**The fields.** Numbers, booleans and fixed words only, never a name or id:
- `seq`, `outcome`, `reason`, `bound_ms`, `away_ms`;
- `paused_before_ms`, `focus_lost_before_ms`, `top_lost_before_ms`, `user_leave`, `interactive`;
- `keys`: ≤ 8 in the 2 s before, `"<keycode>:<pad|remote|other>:<c|p>"`;
- `devices`: ≤ 4, `"<added|removed|changed>:<class>:<ms before>"`;
- `first_frame_ms`.

**`reason`** is the first that applies: `pad_system_key` / `remote_system_key` / `user_leave` / `screen_off` /
`input_device` / `top_lost` / `focus_lost` / `unknown`.

**Host** (`companion/surface_lost_row.py` new; `companion/plugins/games.py` +5): only when the heartbeat carries
`surface_lost` is the module imported.
- The value is parsed against a whitelist: ≤ 1,024 chars, the keys, their types, the fixed words, the list shapes.
  Anything else is dropped, never echoed.
- One recovery-log row is written: `{"event": "surface_lost", "heartbeat_sequence": …, …}`.
- The heartbeat log's whitelist is untouched, so its row is today's.

## 3. Tests

**JVM** (`tests_jvm.txt`, `tests_surface_hold.xml`): B15's style. The activity's paths are modelled as the activity
calls them, against the real `SurfaceHold`, `RestartGuard` (file store), `RtpH264Receiver` on loopback,
`NativeControllerSender` to a loopback socket and `StallMonitor`, with a fake host.
- **A 3-s loss → one session.**
  - The posts are `["start"]` only; the guard's pending is none.
  - **The sender is the same object, and the uplink's largest gap across the loss is < 100 ms.**
  - The stream keeps arriving with no decoder.
  - The next IDR builds the decoder on the new surface.
  - ≥ 20 stall datagrams during the hold, then `stall_end`.
  - The row is `held`: `away_ms` 2,900-3,300, `paused_before_ms` ≥ 150, `first_frame_ms` measured.
  - The report: `decoders_built` 2, `rendered_before_reattach` 15.
- **A 15-s loss → today's restart.** Still holding at 11.9 s; the expiry at 12 s runs today's path.
  - The next surface posts `start&guard_end=1` with `trigger: surface`.
  - The row is `restarted`, `away_ms` 12,000.
- **Absent:** a 3-s loss is today's restart. The sender stops (gap > 250 ms), `start&guard_end=1` is posted,
  `away_ms` 3,000.
- **Keys:**
  - a pad's `BUTTON_MODE` down and up are consumed;
  - the remote's `BUTTON_MODE` / `HOME`, a pad's A and BACK are passed;
  - the counts are 1 consumed, 2 passed; the row `reason: pad_system_key` with the exact `keys` list.
- **The reason order** (seven cases, and a key older than 2 s is not the cause).
- **The row's bounds:** 10 losses → 8 kept, 2 dropped, `seq` from 3, ≤ 1,024 chars, 8 keys / 4 devices,
  `interactive: null`, no free text.
- **`neutralize()`** keeps the sender running (gap < 100 ms) with neutral state.
- **The flag's parse.**

**Host** (`tests_surface_lost_host.txt`, `tests/surface_lost/`):
- the parser: the whole held row; junk and overlong → nothing; unknown keys, text and bad values dropped (no
  address-shaped text survives);
- the real `LinkDropRecovery` writes one `surface_lost` row with `heartbeat_sequence`, and junk writes none;
- **games.py's own block, run from its AST:** key → one row, no key → none, the block after the heartbeat is
  written;
- a fresh process importing `plugins.games` has no `surface_lost_row`;
- the heartbeat whitelist does not mention it.

**Mutations** (`tests_mutations.txt`):
1. `onSurfaceBack` never continues → the 3-s test and the key test fail (2);
2. the consume ignores the source → 2 fail;
3. the host keeps any reason text → the parser test fails.

All restored byte-equal.

**Every host suite** (`tests_regression_after.txt`, in `/tmp/b_q31l_b32c`) against the queue's baseline: the
baseline's outcomes plus `tests/surface_lost`.

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

*(Merged by the coordinator from `b32_2026-10-31/host/` — the host worker's text, unedited.)*

## 4. Files

- **`b32_2026-10-31/`** (client, top level):
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` (the activity, the sender, games.py), `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b32_client.diff`;
  - `proof_flag_absent.py` / `.md` / `_output.txt`;
  - `tests_jvm.txt`, `tests_surface_hold.xml`, `tests_surface_lost_host.txt`, `tests_mutations.txt`,
    `tests_regression_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **In the diff:**
  - `PrivyHub/app/src/main/java/streaming/SurfaceHold.kt` (new), `NativeStreamActivity.kt`,
    `NativeControllerSender.kt`;
  - `PrivyHub/app/src/test/java/streaming/SurfaceHoldTest.kt` (new);
  - `companion/surface_lost_row.py` (new), `companion/plugins/games.py`;
  - `tests/surface_lost/` (new).
- **Left in /tmp:** `b_q31l_b32c` (the copy), `b_q31l_b32c_scratch/`, `b_q31l_b32c_gradle1.txt`.
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft, the Opal untouched;
  - `privyhub-trip-log` and `trip_2026-10-30/` untouched;
  - nothing of A's touched; nothing fetched, deleted, adopted or committed;
  - the tree's code untouched: the coordinator applies.

## Note, 2026-11-02 (queue M, B39)

HOME-1 C1 found two things in the client half above:
- **The report's `surface_hold` read 0 after a held loss:** the report snapshot was cached at the first loss and never
  replaced. Fixed in B39.
- **The pad's guide key never reaches the activity on the onn:** the system turns it into Home. §1's "consumed in the
  stream activity" is dropped in B39; the hold covers a guide press as a Home press.

See `B39_HOLD_COUNTER_2026-11-02.md`.
