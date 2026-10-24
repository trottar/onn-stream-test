---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: efa4240 (+ B15, client only; B16 uncommitted)
---

# B16 — the stall resume waited on the client's 500-ms gate and on the 2-s heartbeat; the client now sends its ready at its first decodable frame, and the saves come only from a signal ≥ 400 ms

**Classification: SETTLED + BUILT**, inside the existing flags `PRIVYHUB_STALL_RESUME=1` and
`PRIVYHUB_INPUT_HOLD_REWIND=1` (host and client).
- **Host:** `tests/stall_resume_speed`, 7 tests, 3 runs green. Every suite under `tests/` is green from the copy; B12's
  suite has one line moved (§3).
- **Client:** `FastReadyTest`, 3 tests. The JVM suite is **125 / 125**.
- **Proofs:**
  - host: `plugins/games.py` with B16's one item removed = HEAD; `stall_owner.py` is B12's module, its changes listed;
  - client: only added lines (50), all in the stated forms. The key is absent unless the host's flag is set.
- In the APK **`e2db0aa0…6b33`** (§4a), built and pinned, **NOT installed**. NOT ADOPTED; no live run; nothing
  committed.

Design `b16_2026-10-24/design_written_before_code.md`, sha256 `c05e5e36…4ff4ffaa`, hashed **06:18:01Z, before any B16
code**. The target rows are in it.

## 0. Settled from the code and the cells' logs

**`@down` (cell 3): between the downlink's return and the client's ready.**
- The ready is the client's recovery gate releasing (`requestGameplayRelease` → `native-stream-ready`). The gate is
  `updateStabilization`, run on **the 500-ms metrics tick**. In a recovery it needs, in order:
  1. **the IDR.** The 4-s gap is a forward jump ≥ 128 packets → a resync → `waitingForIdr`. The next IDR comes in
     **≤ 250 ms** (GOP 15 at 60 fps). This is the decoder's reference wait, and it is the small part;
  2. **a baseline tick, then 3 consecutive clean ticks** (`RECOVERY_CLEAN_TICKS`). Each needs: frames since the last
     tick, no new drops, an empty decoder queue, **≥ 45 fps over the tick** (a tick that spans the return is partly
     dark and fails), the latest output gap ≤ 120 ms, and receive → decode ≤ 150 ms.
  - So **~1.75-2.75 s after the first frame**, plus the POST.
- **Not the heartbeat** (it is not on the ready's path). **Not the audio cushion** (the gate reads only the host's
  audio state).
- **Blackout 1, in the rows:**
  - the heartbeat at 19:01:00.739 already read output age 2 ms;
  - the one at 02.777 read 122 frames in 2 s (full rate);
  - the ready (`resumed via client_ready_stall`) came at 19:01:03.342.
  - **That is ~2.6 s of picture flowing behind the "Reconnecting" overlay.**
- **v2's hold then owned it.** The ready came 4.9-6.8 s after the pause, so B12's 5-s hold expired first in all 5
  (`stall_handover_v2` at 5,006-5,225 ms).
- **Blackout 5's restart.** v2 acted at the handover tick (19:09:02.2; the 03.267 row is logged after the ~1-s cycle)
  on the heartbeat pair **[1,942, 3,980]**.
  - The newer heartbeat was built at ~19:09:00.5, **before the return**.
  - The next one (02.567) read 197 ms, 102 frames on.
  - The client's 50-ms stall datagrams already showed fresh output.

**`@both` (cell 2): blackout 4's 2,130 ms.**
- All 5 resumed via B8's `hold_return_stall`: the first heartbeat after the return that shows the output ≤ 300 ms.
  **The uplink side is the heartbeat's 2-s cadence:**
  - blackout 2: a heartbeat 0.2 s after the return was already fresh → 427 ms;
  - blackout 4: the heartbeat at the return (18:52:18.853) read 4,018 ms, built before it. The next one (20.891, 46 ms)
    resumed at 21.000 → **2,130 ms**.
- The client's own ready came 1.0-1.6 s after each resume.

**The saves.**
- B12's `on_stall` saved at the **first stall datagram of a client episode, whatever its age**. The client sends from
  its own 150 ms.
  - Cell 2's four extra saves were 150-163-ms stalls that never reached the host's 400 ms.
  - Cell 3's saves at 150-156 ms became the pause's load (net 9).
- **The cost per save** (B12's): snes9x 823,536 B; acknowledged 4-11 ms after the send (BENCH-R3 D, PS1); the fake core's
  round trip is 10.1 ms (measured again here).

## 1. Built (`b16.diff`)

**Client** (`FastReady.kt` new; `NativeStreamActivity.kt` +50, added lines only):
- **The host's `native-stream-start` response arms it:** `"stall_resume": {"fast_ready": true}`. The key is absent
  against a host without the flag, which means today's gate.
- With it, a recovery starts a **50-ms UI tick**. The tick sends the ready at once when:
  - a frame has been rendered since the recovery began;
  - the receiver is not waiting for an IDR;
  - the last output is ≤ 100 ms old;
  - the host's metadata is complete.
- The ready is today's `requestGameplayRelease()`: the same POST, the overlay dropped on the host's confirmation.
- **The startup gate is unchanged** (6 clean ticks).
- The report gains `fast_ready_releases` and `fast_ready_frame_to_post_ms`.

**Host** (`stall_owner.py`, B12's module, +34 −3; `plugins/games.py` +4):
1. **The key in the start response, only when B12's owner is wired:**
   `if getattr(self._recovery, "_stall_owner", None) is not None:` → `payload["stall_resume"] = …client_hint()`.
2. **The resume on that ready, through the existing owners.** B12's `ready_resume` gives `client_ready_stall` with the
   stall's load; B8's gives `client_ready_hold` with the hold's load. **No new resume path.**
   - A resume on the client's stall datagrams was considered and rejected. With an APK without the fast ready, the
     game would run behind the client's overlay for its 2-s gate.
3. **The stall's save only from the stall signal:**
   - at the first datagram of the episode **with age ≥ the threshold** (400 with `1`);
   - **synchronously on B7's worker, before B7's pause** (B9's `save` skips a paused core). The pause follows the
     acknowledgement: ≤ 100 ms (`SAVE_ACK_S`), 4-11 ms measured;
   - a failed save never holds the pause;
   - B9's silence save (the hold path, a 400-ms controller silence) is unchanged.
4. **v2's hold, set from the measured ready:**
   - `V2_MS` stays **5,000 ms from the pause**. A 4-s `@down` drop returns 3.57 s after the pause. The fast ready comes
     ≤ 0.55 s after the return: one GOP 250 + decode ≤ 170 cold / ~20 warm + one 50-ms tick + POST and load ≤ 80.
     That makes ≤ 4.12 s: **a margin ≥ 0.88 s.**
   - **v2 takes a stall-owned pause only while the newest stall datagram (≤ 300 ms old) shows the client still stalled
     (age ≥ the threshold).** It never acts on a heartbeat built before the return (blackout 5).
5. The `stall_resume_config` row gains `fast_ready`, `save_from_signal`, `v2_newest_s`.

**Costs, stated:**
- **A `@down` drop's net rises from 9 to 24 frames.** The save now lands 400 ms after the client's last frame, as
  `@both`'s silence save does. That is the price of "no save under 400 ms".
- The release skips the gate's 1.5-s stability check in a recovery: a flapping link can pause again. That is counted
  by the existing rows.

## 2. The target rows (hashed with the design) — the tests

| row | result (`tests_stall_resume_speed.txt`, 3 runs) |
| --- | --- |
| **R1** a 4-s `@down` drop resumes ≤ 1.0 s after the downlink returns, no `encoder_restart`, no `stall_handover_v2` | **met: 301 ms** (the GOP and the client's tick simulated, the host's ready → resume with the load measured); v2 ticks on blackout 5's stale pair at pause ages 2.5 / 3.5 and after the resume: **0 restarts, 0 handovers**; `resumed via client_ready_stall`, `state` loaded into a running core, net 24 |
| **R2** a 4-s `@both` drop resumes ≤ 1.0 s after the packets return | **met: 301 ms** `via client_ready_hold`, the hold's silence save loaded, net 24 (today: 427-2,130 ms on the heartbeat) |
| **R3** zero saves outside signals ≥ 400 ms | **met:** four client episodes of 150-350 ms → **0 saves, 0 pauses**; one stall to 400 → one save **before** the pause (`saves_skipped_paused` 0) |
| v2's rule | the newest datagram stalled (5,200) → one handover, one restart; fresh (12 ms, gate) or older than 300 ms → none |
| the key | `client_hint()` = `{"fast_ready": true}`; one plugin hook of that shape; the class attribute None without the flag |

**The client half** (`FastReadyTest`, the real `RtpH264Receiver` on loopback):
- 4 frames played; the recovery entered; a 4-s forward jump; 3 P-frames rejected (`waitingForIdr` true).
- **Five 50-ms ticks over one GOP: no release.**
- The IDR: **the first tick after its frame releases** (`fast_ready_frame_to_post_ms` 0-50), once.
- With the decision table and the key's names, **3 tests.** The suite is 125 / 125.
- **The end-to-end ≤ 1.0 s on the onn is CL-B11's to measure** (§4). Here the client's part and the host's part are
  each measured, and the IDR wait is the encoder's GOP.

## 3. Regression and proofs

- **`tests_regression.txt`: every suite under `tests/` green** from `/tmp/b_q24f`, 23 suites, B8 / B9 / B12 among
  them. The four `tools/` tests fail in the copy with the same four tests as the baseline run before any B15 / B16
  code (`tests_regression_baseline.txt`, 06:08Z). They read `docs/` files the copy does not hold; one looks for a
  plugin string that is gone at HEAD.
- **B12's suite, one line moved (disclosed):** `test_down_pause_at_400_…`'s net, `8 <= net <= 14` (the 150-ms save)
  → `20 <= net <= 30`. That is item 3's stated change; the rest of B12's suite is unchanged.
- **Caught by the regression, fixed before this record:** the first plugin guard read `self._recovery._stall_owner`
  directly. `tests/remote_ladder`'s fake recovery has no such attribute, so `native-stream-start` raised
  (`tests_regression_first_run_remote_ladder_error.txt`). It is now `getattr(…, None)`, and the re-run is green.
- **Host proof** `proof_flag_absent_host.md`: **PROVEN**.
  - `plugins/games.py`'s AST with the one `if` removed = HEAD's. Without the flags the class attribute is None, so the
    response has no key, byte for byte.
  - `stall_owner.py` +34 −3 is listed; it is not imported without the flag (`test_not_imported_absent`).
- **Client proof** `proof_flag_absent_client.md`: **PROVEN**, 0 removed / 50 added.
  - The one gate is `json.optJSONObject("stall_resume")?.optBoolean("fast_ready") == true`, and `FastReady()` is
    built only inside it.
  - Every other line is a `fastReady?.let` no-op, a null-to-null assignment, or a declaration reached only through a
    FastReady.

## 4. For CL-B11 (A)

- **Host, every bench cell:**
  - `PRIVYHUB_SNES_CORE=snes9x`;
  - `PRIVYHUB_INPUT_HOLD=1 PRIVYHUB_INPUT_HOLD_B6=1 PRIVYHUB_INPUT_HOLD_B8=1 PRIVYHUB_INPUT_HOLD_REWIND=1
    PRIVYHUB_STALL_SIGNAL=1 PRIVYHUB_STALL_RESUME=1`.
- **Client:** `debug.privyhub.stall_signal 1`.
- **`@down`** (`blackout-4s@down,every=120s,seed=1`), per blackout:
  - one `state_saved` kind stall, `save_after_onset_ms` ≈ 400 (not 150), **before** the `desync_pause` (at 400-460 ms);
  - **`resumed via client_ready_stall` ≤ 1.0 s after the downlink's return;**
  - **no `encoder_restart`, no `stall_handover_v2`**, no `recovery_escalation`;
  - net ≈ 24;
  - the client report's `fast_ready_releases` = 5.
- **`@both`** (`blackout-4s@both,every=120s,seed=1`), per blackout:
  - `state_saved` kind silence ~0.40 s, the hold at ~950 ms;
  - **`resumed via client_ready_hold` ≤ 1.0 s after the packets return** (not `hold_return_stall`);
  - net ≈ 24.
- **Both cells:** **zero `state_saved` outside the blackouts.**
- **The return times:** the shim's `impairment_run1.jsonl` gives the dark spans per second. The resume's distance from
  the return is the `resumed` row against the span's end (`@down`), or `packets_back_to_resume_ms` / the first
  controller packet (`@both`).

## 4a. The APK (`apk_sha256.txt`, `build_console.txt`, `tests_jvm_apk_build.txt`)

**`e2db0aa0f09d8eab26783e2c4a757ccc83c12da34ca750c8a182c4d762816b33`**, 9,631,698 B.
- It carries B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16, and supersedes `da09e154…` as the candidate.
  `da09e154…` stays CONFIRMED on the onn.
- Built offline in `/tmp/b_q24f/PrivyHub` (`:app:testDebugUnitTest --rerun :app:assembleDebug --offline
  --no-configuration-cache`), only `privyhub-companion` and `privyhub-link-n1` active. **0 tree files newer than the
  build marker.** JVM 125 / 125 in the same run.
- **The same signer as `da09e154…`** (cert digests compared, not printed); `apksigner verify` OK (v2).
- 944 entries as `da09e154…`; **only `classes3.dex` differs** (358,904 → 374,604 B). The file is 72,835 B smaller
  from packaging: a fresh build, not `da09e154…`'s incremental one.
- **NOT installed.** A copy is at `/tmp/b_q24f_scratch/apk/`.

## 5. Files

- **`b16_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b16.diff`, `proof_flag_absent_host.py` / `.md`, `proof_flag_absent_client.py` / `.md`;
  - `tests_stall_resume_speed.txt`, `tests_regression.txt`, `tests_regression_baseline.txt`,
    `tests_regression_first_run_remote_ladder_error.txt`, `tests_jvm.txt`, `tests_fast_ready.xml`;
  - the APK: `apk_sha256.txt`, `build_console.txt`, `tests_jvm_apk_build.txt`;
  - the session's one line in A's record: `then_a_record/` (the record before, `one_line.diff`, the hashes);
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/stall_owner.py`, `companion/plugins/games.py`;
  - `PrivyHub/app/src/main/java/streaming/FastReady.kt` (new), `NativeStreamActivity.kt`,
    `PrivyHub/app/src/test/java/streaming/FastReadyTest.kt` (new);
  - `tests/stall_resume_speed/` (new), `tests/stall_owner/test_stall_owner.py` (one line);
  - `docs/memory/patches/B16_STALL_RESUME_SPEED.md`, `logs/b16_git_status.txt`.
- **Disclosed:** quick iterations of the hold / stall suites also ran from the tree. They write only to temp dirs; no
  tree file changed (checked). The recorded runs are the copy's.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
