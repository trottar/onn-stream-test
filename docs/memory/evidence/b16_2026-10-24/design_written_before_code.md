# B16 — the stall resume's speed, and the saves: design, written before any B16 code

Baseline HEAD efa4240 + B15 (client only, uncommitted). Queue: `handoffs/QUEUE_2026-10-24F.md` §B16. Data: CL-B10 §2-§3
(`cl_b10_2026-10-23/runs/2_snes_blackout_both_state_stall/`, `runs/3_snes_blackout_down_state_stall/`: the recovery
and heartbeat logs).

## 0. Settled from the code and the cells' logs

**`@down` (cell 3): what the client does between the downlink's return and its ready.** The client's ready is its
recovery gate's release (`requestGameplayRelease` → `native-stream-ready`), and the gate is `updateStabilization`, run
on the **500-ms metrics tick**. In a recovery (`recoveryActive`) it needs, in order:
- no waiting phase: the host's metadata, the receiver, the decoder, and **the receiver not waiting for an IDR**. The
  4-s gap is a forward jump ≥ 128 packets → a resync → `waitingForIdr` until the next IDR: **≤ 250 ms** (GOP 15 at
  60 fps). This is the decoder's reference wait, and it is the small part;
- one **baseline tick**, then **3 consecutive clean ticks** (`RECOVERY_CLEAN_TICKS`), each with: frames rendered since
  the last tick, no new drops / overflows, the decoder's queue empty, **≥ 45 fps over the last 500-ms tick** (the RTP
  frame count's delta: a tick that spans the return is partly dark and fails), the latest output gap ≤ 120 ms and
  receive → decode ≤ 150 ms. So ≥ 4 ticks after the first frame: **~1.75-2.75 s**, plus the POST.
- **Not the heartbeat** (the 2-s heartbeat is not on the ready's path) and **not the audio cushion** (the gate reads
  only the host's audio state from the start response).
- **The rows agree.** Blackout 1: the heartbeat at 19:01:00.739 already read output age 2 ms (3 frames on), the one at
  02.777 read 122 frames in 2 s (full rate), and the ready → `resumed via client_ready_stall` came at 19:01:03.342:
  **~2.6 s of picture held behind the "Reconnecting" overlay while frames were flowing.**
- **v2's hold then owned it.** The ready came 4.9-6.8 s after the pause, so B12's 5-s hold expired first in all 5
  (`stall_handover_v2` held 5,006-5,225 ms). In blackout 5 v2 restarted the encoder at the handover tick (19:09:02.2;
  the row at 03.267 is logged after the ~1-s cycle) on the heartbeat pair **[1,942, 3,980]**. The newer one was built
  at ~19:09:00.5, **before the downlink's return**; the next heartbeat (02.567) read 197 ms, 102 frames on. The
  client's stall datagrams (every 50 ms, the gate bit) showed its output fresh at that moment. The restart pushed the
  ready to 19:09:04.1 (7.2 s).
- **What v2's 5-s hold should be given the client's ready:** §1.4.

**`@both` (cell 2): blackout 4's 2,130 ms, the same question on the uplink side.** All 5 resumed via B8's
`hold_return_stall`: the first heartbeat after the return (the first controller packet back) that shows the output
≤ 300 ms. **The uplink side is the heartbeat's cadence:**
- blackout 2: a heartbeat came at 18:48:19.037, 0.2 s after the return, already fresh → 427 ms;
- blackout 4: the heartbeat at 18:52:18.853 came at the return itself with age 4,018 (built before it), so the next one
  (18:52:20.891, age 46) resumed at 18:52:21.000 → **2,130 ms**.
- The client's own ready (its gate, as above) came 1.0-1.6 s after each resume (`client_ready_after_hold`).

**The saves (cell 2's four extra, cell 3's at 150 ms).** B12's `StallOwner.on_stall` asks B9 for a save at the **first
stall datagram of a client episode** while the core plays and the gate bit is clear, **whatever its age**. The client
sends from its own 150 ms (`stall_signal_ms` 150), so every client stall ≥ 150 ms is saved once:
- cell 2's four `state_saved` kind stall at 150-163 ms outside the blackouts (stalls that never reached the host's 400
  ms, so no pause followed);
- cell 3's five stall saves at 150-156 ms, which became the pause's load (net 9).
- **The cost per save** (B12's): snes9x 823,536 B; the acknowledgement 4-11 ms after the send (BENCH-R3 D's PS1 rows);
  the fake core's request → ack → row ~10 ms. RetroArch writes the file in its own task.

## 1. The design — inside `PRIVYHUB_STALL_RESUME=1` (and `PRIVYHUB_INPUT_HOLD_REWIND=1` for the saves); absent = today byte for byte

1. **The client's ready as soon as a decodable frame is in hand** (client; armed only by the host):
   - the host's `native-stream-start` response carries `"stall_resume": {"fast_ready": true}` **only when B12's owner
     is wired**. The key is absent = today's gate, so the APK changes nothing against a host without the flag;
   - with it, during a **recovery** gate (`recoveryActive`, not released), a 50-ms UI tick (started at the recovery's
     entry, stopped at its release) releases at once when:
     - a frame has been rendered since the recovery began;
     - the receiver is not waiting for an IDR;
     - the last output is ≤ 100 ms old;
     - the host's metadata is complete.
   - The release is today's `requestGameplayRelease()`: the same POST, the overlay dropped on the host's confirmation.
     **The startup gate (6 clean ticks) is unchanged.**
   - The report: `fast_ready_releases`, and `fast_ready_frame_to_post_ms` for the last release (the first frame since
     the recovery → the POST).
2. **The host resumes on that ready, through the existing owners:**
   - B12's `ready_resume`: a stall-owned pause → `resumed via client_ready_stall`, with the stall's load;
   - B8's `ready_resume`: the hold's episode handed to the stall → `client_ready_hold`, with the hold's load. Both are
     already called by the plugin's ready action before its own resume.
   - **No new resume path.** A resume on the client's stall datagrams was considered and rejected: with an APK without
     the fast ready, the game would run behind the client's overlay for its 2-s gate.
3. **The saves only from a signal ≥ 400 ms.**
   - B12's stall save moves to the first stall datagram of the episode **with age ≥ the stall signal's threshold**
     (400 ms with `1`).
   - It is taken **synchronously on B7's worker, before B7's pause** (B9's `save` skips a paused core). The pause
     follows the save's acknowledgement: ≤ `SAVE_ACK_S` (100 ms); 4-11 ms measured.
   - **No save for a stall under 400 ms.** B9's silence save (the hold path, a 400-ms controller silence) is unchanged.
   - **Cost, stated:** a `@down` drop's net rises from 9 to ~24 frames (the save 400 ms after the client's last frame,
     as `@both`'s silence save). The saves per 10 min fall to one per stall-signal pause plus B9's per silence ≥ 400 ms.
4. **v2's hold, set from the measured ready, with a stated margin:**
   - `V2_MS` stays **5,000 ms from the pause**. A 4-s `@down` drop returns 3.57 s after the pause (paused at 423-430
     ms). The fast ready comes **≤ 0.55 s** after the return: one GOP (250 ms) + decode (≤ 170 ms cold, ~20 warm) + one
     50-ms tick + the POST and the load (≤ 80 ms). That makes ≤ 4.12 s, so **the margin is ≥ 0.88 s**.
   - **v2 takes a stall-owned pause only while the newest stall datagram (≤ 300 ms old) shows the client still stalled
     (age ≥ the threshold).** It never acts on a heartbeat read before the return (blackout 5). If the client has fresh
     frames, its ready follows within ≤ 0.55 s; if its datagrams stop, B7's 300-ms quiet rule applies.

**Target rows (hashed with this design):**
- **R1:** a 4-s `@down` drop resumes **≤ 1.0 s after the downlink returns**, with **no `encoder_restart` and no
  `stall_handover_v2`**.
- **R2:** a 4-s `@both` drop resumes **≤ 1.0 s after the packets return**.
- **R3:** **zero saves outside signals ≥ 400 ms.**
- Absent = today byte for byte. B8 / B9 / B12 suites green. B12's one net assertion (8-14 frames, the 150-ms save)
  moves with item 3; that is disclosed, as B12 moved B9's three lines.

## 2. Tests

- **Client JVM (`FastReadyTest`):**
  - the decision table;
  - **the real `RtpH264Receiver` on loopback across a 4-s gap:** P-frames, a forward jump (the resync), P-frames
    rejected while waiting for the IDR, then the IDR. Against a fake decoder's frame count and age, with 50-ms ticks:
    no release before the IDR's frame, the release at the first tick after it;
  - the key absent → never (today's gate); the startup gate → never; once per recovery.
- **Host (`tests/stall_resume_speed/`, B9's loopback fake core, the real recovery / B7 / B8 / B12 / B9):**
  - **R1:** stalls in real time from 150 ms; no save before 400; one save at 400, before the pause. The dark goes on to
    4.0 s with v2 ticks on blackout 5's stale heartbeats (pause ages 2.5 / 3.5 / 4.5): no restart. At 4.0 s the
    downlink returns; the client's first frame comes one GOP (0.25 s) later; its fast ready → the plugin's order (B8,
    B12, then today's note). **Resumed via `client_ready_stall` ≤ 1.0 s after the return**, the state loaded. A v2 tick
    at 5.5 s does nothing: **no `encoder_restart`, no `stall_handover_v2`**.
  - **R2:** B9's silence save at 400 ms, the hold's pause at 950 (B2's entry, B6, B8). At 4.0 s the stall datagrams
    and the packets return (the handover, B8's return). The client's frame one GOP later, its fast ready → **resumed
    via `client_ready_hold` ≤ 1.0 s after the packets**, the hold's state loaded.
  - **R3:** a session's client stalls of 150-399 ms → zero saves; one stall to 450 → one save, then the pause.
  - **v2's rule:** a long stall with the newest datagram stalled → one handover; with it fresh or stale (> 300 ms) → none.
  - the start response's key with the owner wired, none without; the flag absent → nothing imported.
- **Regression:** every suite under `tests/` from the copy (B8 / B9 / B12 green). The JVM suite. The host proof (AST:
  B16's items removed = the predecessors); the client proof (added lines only, in the allowed forms).

## 3. Files

Record `evidence/B16_STALL_RESUME_SPEED_2026-10-24.md` + `b16_2026-10-24/`; `patches/B16_STALL_RESUME_SPEED.md`
(host and client); `logs/b16_git_status.txt`.
