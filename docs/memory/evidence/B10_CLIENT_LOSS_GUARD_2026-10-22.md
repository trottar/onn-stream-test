---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 0f4b551 (+ B8 / B9 uncommitted)
---

# B10 — the client under loss: freeze on the last good frame, ask for a keyframe, count the corrupted frames

**Classification: BUILT** behind `debug.privyhub.loss_guard=<1|count>` (client) and `PRIVYHUB_LOSS_GUARD=1` (host).
- **The client:** 8 JVM tests, including the real `RtpH264Receiver` on loopback with a fake decoder; the suite is
  **99 / 99**.
- **The host:** 10 tests with a fake encoder control through the real receive loop, 3 runs.
- **The APK (B5 + B7 + B10) `bf5114a2…cf73`** built offline and pinned, **NOT installed**.
- **Proofs:** client: only added lines, all in the allowed forms. Host: AST identical with the B10 items removed,
  3 / 3.
- **The settled finding:** **the host cannot force an IDR on demand.** The requests are counted and rate-limited, and
  today they force nothing (§0).
- NOT ADOPTED; no live run; nothing committed.

Design `b10_2026-10-22/design_written_before_code.md`, sha256 `be12b314…6ae2`, hashed **19:12:11Z, before any B10
code**.

## 0. Settled from the code

1. **What the client does on a dropped access unit today** (`RtpH264Receiver.parseRtpPacket`):
   - **Two drop points:**
     - an AU whose packets carried a sequence gap is dropped at its marker (`sequence_gap_au_drops`);
     - an AU cut off by the next timestamp is dropped there (`incomplete_au_drops`).
   - **`waitingForIdr` is set only by a stream resync** (a forward jump ≥ 128 packets, or an SSRC change). An
     ordinary drop never sets it.
   - **So the next complete P-frame is queued to MediaCodec** and decoded against a reference it never received.
     Every frame up to the next IDR inherits the damage. The decoder *renders* them, and no counter marks them.
   - That is BENCH-R2 e1's "missing faces and a coloured band" under `loss-1`, with "rendered" on every counter.
2. **The IDR cadence today:** every profile has `gop_frames=15` (`h264_vaapi -g 15 -bf 0`): **one IDR every 15
   frames, 250 ms**.
   - e1 measured 41,365 / 2,706 = 15.3 frames per IDR. The record's "≤ 41" was the longest gap, when IDRs were lost
     too.
   - So a drop corrupts ≤ 14 frames, mean ~7.
3. **Can the host insert an IDR on demand? No.**
   - The encoder is an `ffmpeg` process; `-g` / `-force_key_frames` are fixed at launch.
   - ffmpeg 7.1's CLI has no runtime keyframe command: `sendcmd` / `zmq` reach filters, not the encoder (checked on
     this host's ffmpeg's help, nothing fetched).
   - The actuator's "IDR path" (C3.L2a-E2) **is an encoder restart.** Its first IDR is accepted 27 ms after the SSRC
     change, but **a restart costs a 287-318-ms decoder output gap** (C3.L1R1 / C3.L1). That is longer than the
     ≤ 250-ms wait for the next natural IDR.
   - **A forced IDR through the existing path would always freeze longer than waiting.**
   - So the host part is built as a seam: `control.force_idr()`. Today's control `NoRuntimeIdr` forces nothing and
     says why. The restart was not wired as the control: by design §0.3 it is strictly worse.

## 1. What was built (`b10.diff`)

**Client** (`LossGuard.kt` new, 151 lines; `RtpH264Receiver.kt` +12, `NativeStreamActivity.kt` +20,
`NativeControllerSender.kt` +9, added lines only):
- **`1`, the guard:**
  - On a dropped AU (either drop point, outside a resync's own wait), the receiver **queues no non-IDR frame** until
    the next complete IDR. The surface keeps the last complete frame.
  - The IDR is queued and ends the episode.
  - **One `keyframe_request` per episode:** 24 bytes, `PHK1`, B7's layout. It goes out on the controller socket from
    the sender's 8-ms loop.
  - **The freeze is capped at 600 ms.** If no IDR has come by then, frames pass as today, counted
    (`loss_guard_timeouts`). So the guard never trips the client's own 1-s output-silence recovery.
- **`count`:** nothing held or sent, only the counter. This is today's behaviour, measured: the guard-off cell.
- **The counter `frames_after_dropped_reference`:** the non-IDR frames between a drop and the next IDR.
  - With `count`: the frames drawn corrupted.
  - With `1`: the frames that would have been (`loss_guard_frames_held`). Any queued after a timeout are the
    difference.
- **The report** (property set only): `loss_guard_mode`, `frames_after_dropped_reference`, `loss_guard_episodes`,
  `loss_guard_frames_held`, `loss_guard_timeouts`, `loss_guard_max_wait_ms`, `keyframe_requests_sent`.
- **The heartbeat:** the first three.

**Host** (`companion/keyframe_request.py` new, 154 lines; `native_session_io.py` +10, `plugins/games.py` +16,
`games/native_stream_heartbeat.py` +15):
- **The receive loop:** one guarded statement before the 36-byte check parses and queues. Absent: a `PHK1` datagram
  is a bad packet, as any unknown datagram today (tested).
- **One worker:**
  - every request is counted, and **at most one per 500 ms is acted on**;
  - acting = `control.force_idr()`. A forced IDR is logged `keyframe_forced` (client seq, request → forced ms, via);
  - `NoRuntimeIdr`: unforced, with §0.3's reason;
  - a per-minute `keyframe_requests` row (received / acted / rate_limited / forced / unforced, the reason).
- **The heartbeat fields** are recorded with `PRIVYHUB_LOSS_GUARD` set (as B3's link fields). So a record can say
  "N corrupted frames" from the host's own log.

## 2. The cost, stated

- **The freeze:** each drop freezes the picture until the next natural IDR: ≤ 14 frames (233 ms), mean ~7
  (~117 ms), up to the 600-ms cap if the IDR is lost.
  - At e1's rate (~42 drops per minute, ≤ 42 episodes) that is up to ~5 s per minute of held picture.
  - Those are the same frames that today are drawn corrupted: ~42 × 7 ≈ 300 frames per minute.
  - **The trade is a stutter for a wrong picture.** The counter says how many frames either way.
- **The interaction with B7 / B9:** a 150-600-ms freeze makes the client send stalls (at 150). The host acts at 400
  (B9), so a long freeze can also pause the core until the IDR. Stated, not changed.
- **A forced IDR, if one existed:** the wait would shrink to one round trip + one frame (~20-30 ms on the LAN).
  - Its bytes: ≤ 90,000 B (the frame cap, D-BASE-P6a) against a ~14.6-KB P-frame at 7 Mbps.
  - That is ≤ +75 KB per request, ≤ 150 KB/s at the 500-ms limit (+1.2 Mbps worst case).
  - **Not available today** (§0.3).
- **The request on the wire:** 24 bytes per episode on the uplink.

## 3. Tests

**Client, `LossGuardTest`: 8.** The suite is **99 / 99** (91 + 8). LossGuardTest re-ran twice more: 8 / 8, 8 / 8.
- the flag table (off-device: off); the 24-byte encoding;
- the guard on a fake clock:
  - held until the IDR; one request per episode, taken once;
  - the max wait; the query string;
- `count` (nothing held or sent, the same count); the 600-ms cap;
- **the real receiver on loopback, a fake decoder** (the AUs it was asked to queue), the stream
  I P P [lost] P P P P I P:
  - **no guard = today:** I P P P P P I P — the three after the loss are queued, from a lost reference;
  - **the guard:** I P P I P — nothing queued until the IDR; counter 3, held 3, one request;
  - **`count`:** today's list, counter 3, no request.

**Host, `tests/keyframe_request`: 10 OK, 3 runs:**
- the parse / decode (B7's `PHS1` is not a request);
- one request → one `keyframe_forced` (a fake control);
- **ten in 360 ms → one forced, nine rate-limited; another at 550 ms → forced**;
- `NoRuntimeIdr` → unforced, the per-minute row with the reason, no row when nothing changed;
- through the real receive loop: counted, not a controller packet; absent → bad packets as today;
- the wire / config rows; the heartbeat fields only with the flag;
- FlagAbsent (no import, attributes None); the hook shapes.

**Regression:** every suite under `tests/` is green from the copy. The four `tools/` tests are as on HEAD (B8 §3).

**Proofs:**
- `proof_flag_absent_client.md` **PROVEN**:
  - RtpH264Receiver 0 removed / 12 added, the activity 0 / 20, the sender 0 / 9, all in the allowed forms;
  - the receiver's `} else if (lossGuard?.deliver(isIdr) == false) {` is `null == false` = false without the
    property, so the original `else` runs.
- `proof_flag_absent_host.md` **ALL IDENTICAL** (3 / 3).

## 4. The APK (`apk_sha256.txt`, `build_console.txt`, `tests_apk.txt`)

**`bf5114a2d257f1246374b05e3d79b24f0382afe1c66b2c6acb3a37fa6e58cf73`**, 9,615,746 B. It carries B5 + B7 + B10.
- **The build:**
  - offline in `/tmp/b_q22d/PrivyHub` with `--no-configuration-cache`, only `privyhub-companion` active;
  - the copy holds no `.gradle` / `build` from the tree;
  - **0 tree files newer than the build marker.**
- **The contents:**
  - the same 944 entries as the CONFIRMED `cb0935c8…`; only `classes3.dex` differs, and it carries
    `debug.privyhub.loss_guard` and `PHK1` beside the B5 / B7 properties;
  - the ~140-KB smaller file is ZIP / signing-block overhead: the entries' compressed total is within 4 KB.
- **The signer:** the same as `cb0935c8…` (certificate digests compared, not printed). `apksigner verify` OK.
- **NOT installed.**

## 5. CL-B9, sketched (session A, with the user if present)

1. **Install** `bf5114a2…` (`adb install -r`, after preserving the CONFIRMED `cb0935c8…`). Read it back.
2. **The host:** `PRIVYHUB_SNES_CORE=snes9x`, `PRIVYHUB_LOSS_GUARD=1`, `PRIVYHUB_LINK_REPORT=1`;
   `setprop debug.privyhub.link_report 1`.
3. **Cell L-off:** `PRIVYHUB_IMPAIRMENT=loss-1@post-fec,seed=1`, `setprop debug.privyhub.loss_guard count`, ~10 min.
   - Read `frames_after_dropped_reference` per minute: the corrupted frames today. Expected ~300 per minute at e1's
     rate.
   - The user notes the picture (missing parts, bands).
4. **Cell L-on:** the same with `setprop debug.privyhub.loss_guard 1`.
   - Expect: `loss_guard_frames_held` ≈ the counter; `loss_guard_timeouts` ≈ 0; `loss_guard_max_wait_ms` ≤ 600;
     `keyframe_requests` rows with `forced` 0 and the reason.
   - The user says whether the picture stutters instead of corrupting, and which is better.
   - Read the hitch seconds (the freezes are hitches by construction), the client's max output gap (≤ ~600 ms), and
     any `desync_pause client_stall` if B7 is on.
5. Clear the properties. `--check`.
6. **Bars to pre-register:**
   - L-on: 0 frames queued after a drop before an IDR (held = counter − timeouts' frames);
   - L-on's hitch rate against L-off's, stated;
   - the property-empty behaviour = the CONFIRMED APK's.

## 6. Files

- **`b10_2026-10-22/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b10.diff`, `proof_flag_absent_host.py` / `.md`, `proof_flag_absent_client.py` / `.md`;
  - `tests_keyframe_request.txt`, `tests_regression.txt`;
  - `build_started_at.txt`, `build_console.txt`, `tests_apk.txt`, `tests_apk_console.txt`, `apk_sha256.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/keyframe_request.py` (new), `native_session_io.py`, `plugins/games.py`,
    `games/native_stream_heartbeat.py`, `tests/keyframe_request/` (new);
  - `PrivyHub/app/src/main/java/streaming/LossGuard.kt` (new), `RtpH264Receiver.kt`, `NativeStreamActivity.kt`,
    `NativeControllerSender.kt`, `PrivyHub/app/src/test/java/streaming/LossGuardTest.kt` (new);
  - `docs/memory/patches/B10_CLIENT_LOSS_GUARD.md`, `logs/b10_git_status.txt`.
- **Left in /tmp:**
  - `b_q22d` (the copy);
  - `b_q22d_head` (an untouched HEAD copy for the tools-test comparison);
  - `b_q22d_scratch` (the APK copy, build logs, the marker).
- **The rules held:**
  - no stream, no restart, no adb, no sudo, no nft; the Opal untouched;
  - gradle offline with only the companion active;
  - nothing fetched, deleted, adopted or committed; nothing of A's touched.
