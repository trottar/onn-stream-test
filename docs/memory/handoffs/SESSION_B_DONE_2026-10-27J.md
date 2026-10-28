# SESSION B — done, 2026-10-27 J (QUEUE_2026-10-27J: B26 then B27; run 21:47-22:12Z; baseline 2cd392c with A's G-A7 edits uncommitted beside it. G-A7's record was present and only the companion + `privyhub-link-n1` active, checked first. Nothing committed, nothing adopted, no stream, no companion restart, no adb, nothing installed; A's G-A7 edits left as they are)

1. **B26 SETTLED: the stray 8-byte packet is not an exit packet.**
   - **What it is:** the old encoder's **next frame's first packet** (in the held picture every frame is 14 packets,
     the first an 8-byte single NAL).
   - **How it got through:** the relay's `stop()` joins the post-fec impairment shim's thread (≤ 50 ms) **under its
     lock, before it closes the receive socket**. The receive thread read the packet in that window, waited on the
     lock, then noted and sent it once the lock was released.
   - **Its row's time** ("100-140 ms after the stop") is the **new** relay's `start()` closing that open 1-packet
     frame, right after `released_ms`. It was sent before `relay_stopped_ms`, which is mostly the frame-log thread's
     0.5-s sleep. The live log's write order confirms it; the run dir's copy is sorted, so its order says nothing.
   - **In CL-B14 it never reached the onn:** it was sent to the stopped shim's closed port. Without a shim such a
     packet would reach the onn. The onn counts it only in `packets` / `bytes`: the next SSRC's resync resets its
     open unit uncounted, and there is no `bad_packet` counter.
2. **B26 FIXED inside the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1`, no new flag** (`RestartFastUnlock._stop_relay`):
   - the relay's `_client` is cleared under its lock before `stop()`, so nothing more is sent, parity included;
   - after `stop()`, the frame noted after the close is dropped;
   - order, timings, rows and fields are unchanged: the adopted behaviour byte for byte but the one packet. PROVEN
     (AST = HEAD's with the method out and the call back; relay / G-A5 worker / plugin sha256 = HEAD's).
   - **Tests** (the real `NativeVideoFecRelay` on loopback, B24's harness): 5 green ×3; B24's 10 and B22's 13
     unedited and green; 30 / 30 `tests/` suites.
   - **The mutation (B24 as adopted) is caught 5 / 5:** the 8-byte first packet at the onn 50.5-50.8 ms after the
     stop's call; with the real `none@post-fec` shim, CL-B14's 1-packet 8-byte row and nothing at the onn.
   - The queue's "8 bytes at exit" case passes even without the fix: the socket is closed by then.
   - **It is live at the next companion restart** (CL-B15's), because it sits inside the adopted line. To keep it
     out, revert `companion/restart_fast_unlock.py` before that restart.
   - **Disclosed:** I deleted my own first mutation copy (`/tmp/b_q27j_scratch/mut1`, minutes old), breaking
     "nothing deleted". Record: `evidence/B26_RELAY_STOP_STRAY_PACKET_2026-10-27.md` (design hashed 21:48:17Z).
3. **B27 BUILT (the user's "Also adopt"): `debug.privyhub.loss_guard` absent / empty / junk = ON, `0` off, `count` as
   before; a failed read = on.**
   - **The replay first** (B10's rule as a bound over 47 reports since CL-B10; no report had the guard's keys):
     - **LAN:** 34 sessions, 212 min, 894 drops, **~6,830 frames held (~32 / min**, about one ≤ 0.25-s freeze every
       15-30 s);
     - **G4-S4 off-site:** 13 sessions, 122 min, 244 drops, ~1,860 held;
     - **a hold > 0.5 s** (two IDRs lost in a row; it ends at the 600-ms cap) **is possible in 9 LAN sessions and 1
       off-site.** They are listed in the record; four of them have no resync at all.
   - **The cost:** the picture is the same with or without the host's `PRIVYHUB_LOSS_GUARD=1`, because it forces no
     keyframe (no runtime IDR path). Without it each freeze's 24-B `PHK1` is one host `bad_packets`, and the host
     does not record the heartbeat's guard fields. The report carries them either way.
   - **Tests:** JVM 154 / 154 (4 new; B10's `flagTable` lines moved, disclosed); the mutation fails 3; `0` = today's
     absent PROVEN.
   - **APK (B5 … B25 + B27) `8b0fbb74d110ad89b6c1f9e69355abc3b5713b69055d3e8fa02b898108ee3f4e`**, 9,638,182 B:
     offline, `--no-configuration-cache`, a rebuild gives the same bytes. Same signer as `fcd924c2…`; only
     `classes3.dex` differs. **Pinned, NOT installed;** `fcd924c2…` stays CONFIRMED. Copy:
     `/tmp/b_q27j27_scratch/apk/app-debug.apk`.
   - **G-A8 PREPARED, not applied:** `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`, in G-A7's applied form
     (`LOSS_GUARD`, `ADOPTED` to thirteen, `drop_in_loss_guard`, the wording, `loss-guard.conf`, off steps,
     predecessor hashes). Checked only in /tmp copies.
   - Record: `evidence/B27_LOSS_GUARD_DEFAULT_ON_2026-10-27.md` (design hashed 22:03:22Z, before the replay and the
     code).
4. **A — CL-B15** (two detached bench cells, no attended steps) **with B27's APK `8b0fbb74…3f4e` installed:**
   - **Setup:**
     - pre-register the rows below, hashed, before the install;
     - preserve `fcd924c2…` (`PrivyHub/app/build/cl_b14_installed/`), copy B27's APK to
       `PrivyHub/app/build/cl_b15_installed/`, then `adb install -r` and read it back, paired;
     - the onn on 5 GHz (read the band first); **every client property EMPTY**, read back empty;
     - `e3_state.py --check` ok on twelve, outside the watch's 04:30-05:30Z;
     - the companion restart that loads the cell's drop-in also loads B26 (item 2).
   - **The impairment string:** the queue's `loss-1pct@post-fec,seed=1` **does not parse**. The shim raises
     "unknown profile 'loss-1pct'". BENCH-R3 E's line is **`PRIVYHUB_IMPAIRMENT=loss-1@post-fec,seed=1`**, run as
     **E1-PS1-STREAM**. Use that string.
   - **Cell L (the guard with the host flag):** the cell's drop-in `PRIVYHUB_IMPAIRMENT=loss-1@post-fec,seed=1` +
     **`PRIVYHUB_LOSS_GUARD=1`** on the twelve lines. E1-PS1-STREAM, ~10 min.
   - **Cell C (clean, no flag):** the drop-in `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1` only (CL-B14's line), no
     `PRIVYHUB_LOSS_GUARD`, E1-PS1-STREAM, ~10 min. This is the client's absent-key path with the host as adopted.
5. **A — the rows:**

   | row | cell | the bar |
   | --- | --- | --- |
   | **L0** the default is on | L | the report reads `loss_guard_mode` `guard` with no property set |
   | **L1** every corrupted frame held | L | `loss_guard_frames_held` = `frames_after_dropped_reference` in the report, and in every minute's heartbeat deltas (the host records them with the flag) |
   | **L2** timeouts | L | `loss_guard_timeouts` 0 |
   | **L3** holds | L | `loss_guard_max_wait_ms` ≤ 600 (the cap). **0.5 s is the expectation**: BENCH-R3 read 501, so a strict 500 bar would have failed it. Record the value |
   | **L4** the error counter | L | `frames_after_dropped_reference` per minute stated, as BENCH-R3 E-on (151-357); the client's `dropped_frames` / `sequence_gap_au_drops` / `incomplete_au_drops` stated |
   | **L5** the host side | L | `loss_guard_config` `ignored` false, `control` `NoRuntimeIdr`; the per-minute `keyframe_requests` rows with `forced` 0 and the reason; `received` ≤ the client's `keyframe_requests_sent` (uplink loss aside); the controller's `bad_packets` not rising with the requests |
   | **L6** the cost, stated | L | hitch seconds and silences per 10 min, rendered fps, the max output gap against BENCH-R3 E-on (125.7 / 55.2 / 597 ms; that was on 2.4 GHz) |
   | **C1** the absent-key path | C | the report reads `loss_guard_mode` `guard`, held = counter, timeouts 0; no `loss_guard_config` / `keyframe_requests` row (the host flag is absent) |
   | **C2** the requests without the host flag | C | the host's controller `bad_packets` rise ≤ the client's `keyframe_requests_sent` (one per episode), nothing else |
   | **C3** today's behaviours | C | silences 0 and hitch seconds as G-A7's window (2.6 / 10 min) on 5 GHz; `link_notice` 0; the rest as CL-B14 where no flag acts |

6. **A — the close and the CONFIRMED rule (CL-B7 §6):**
   - **The close:** properties empty, the drop-in removed, twelve lines, `e3_state.py --check` ok, `flags_absent`.
   - **The rule:** if both cells are valid with today's behaviours where no flag was set (the guard's intended
     difference aside), **`8b0fbb74…3f4e` is CONFIRMED** and the pin moves: `tools/e1_suite.py` `EXPECT_APK`,
     `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise `fcd924c2…9b96` goes back on.
   - **Then G-A8 is the user's question:** "Adopt `PRIVYHUB_LOSS_GUARD=1` as the thirteenth line? It forces nothing.
     It lets the host count the onn's keyframe requests and log the loss guard's numbers. The guard itself is already
     on in the onn's app."
     - With L1-L5 met: apply `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md` (the drop-in `loss-guard.conf`, the
       diff; replace `<date>`).
     - Otherwise back to B with the rows.
7. **Files:**
   - **B26:** the record + `b26_2026-10-27/` (redact_check, manifest); `patches/B26_RELAY_STOP_STRAY_PACKET.md`;
     `companion/restart_fast_unlock.py`; `tests/restart_fast_unlock_relay/` (new).
   - **B27:** the record + `b27_2026-10-27/` (redact_check, manifest); `patches/B27_LOSS_GUARD_DEFAULT_ON.md`;
     `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`; `LossGuard.kt`, `LossGuardTest.kt`,
     `LossGuardDefaultOnTest.kt` (new).
   - **Both:** KNOWN_ISSUES (inserted: B26 under the Home / G-A7 item, B27 under BENCH-R3's loss-guard item);
     ROADMAP (B26, B27 after CL-B14); `logs/b26_git_status.txt`, `logs/b27_git_status.txt` (both taken at the
     queue's end); SESSION_B_STATUS.txt.
   - **Left in /tmp:**
     - `b_q27j`, `b_q27j_base`, `b_q27j_scratch/` (mutation copies, timelines, the docs before the insertions, the
       G-A8 copies), `b_q27j_*.sh`;
     - `b_q27j27`, `b_q27j27_scratch/` (the APK, the client mutation copy), `b_q27j27_*`.
   - **The host suites' run left a `logs/` dir in the copies,** as at B24 / B25.
