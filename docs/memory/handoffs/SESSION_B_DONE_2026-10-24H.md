# SESSION B — done, 2026-10-24 H (QUEUE_2026-10-24H: B21, B22, B23; run 2026-10-25 17:43-18:25Z; baseline 13ccff5; nothing committed, nothing adopted, no stream, no restart, no adb, nothing installed; `privyhub-g4-s4` inactive (checked first); `privyhub-link-n1` untouched; A's G4-S4 / WAN-R1 files and `CURRENT.md` untouched)
1. **B21 BUILT** (inside `PRIVYHUB_LINK_RECOVERY=1`). The first `apply()` in the process is `emulator_manager`'s, which
   `plugins/games.py` imports at line 13, before its own block. The row logged a third `apply`. Now `link_recovery` keeps
   the first result. `config_row()` (it writes nothing) gives `implied` the six / `explicit` {} / `at` `import` /
   `reapply` [] under the umbrella alone, and the wire's second `apply` is removed. The predecessor reproduces CL-B12's
   row exactly. `tests/link_recovery` 16 (B20's 7 unedited); AST PROVEN. The running companion keeps the old row until
   its next restart. Record evidence/B21_LINK_RECOVERY_CONFIG_LOG_2026-10-24.md (design hashed 17:45:36Z).
2. **B22 SETTLED.**
   - **Host, 2.0-2.2 s:** the relay's per-second frame log shows the old encoder still sending ~0.78 s after the
     start's entry. `_stop_locked()` tears down the old audio (joins, the capture's wait, two `pactl` calls) before it
     kills the encoder (also the capture). Then ~0.45 s to the new encoder's first frame, then a fixed 0.75-s check and
     the new audio (~0.85 s).
   - **Client, 8.8 / 4.2 s:** the start-up gate needs a baseline + 6 clean 500-ms ticks (≥ ~3.5-4 s). Press 2 hit that
     minimum; press 1 was reset at least once (reason not logged). Press 1 also had an 854-ms codec stall at the switch.
   - **The picture itself was back ~1.3-2.0 s after `startSession`.** CL-B12's 12.0 / 6.8 s are ≈ 11.5 / 6.3 s on one
     clock (the onn's events clock is ~0.5 s behind the host's).
3. **B22 BUILT.**
   - **Host:** `PRIVYHUB_RESTART_FAST=1` (`companion/restart_fast.py`). For `guard_end=1` on Linux with an encoder
     running:
     - the response is a `status()` snapshot + `"restart_fast": {"armed": true, "old_stream_active": true}`, sent once
       a worker holds the manager's lock;
     - the worker kills the old encoder first, stops the old audio beside the new encoder, starts the new encoder as
       today's start does, runs today's 0.75-s check (≥ once), then `prepare` and the new audio;
     - the ready's `status()` waits on the lock.
   - **Client** (inside `restart_guard`, armed only by that key): a 50-ms tick releases at the first fresh frame after
     the SSRC switch, once the old report is done (cap 1 s). The rebuilt audio starts at the ready's return. Report keys
     `restart_fast_*`, including the gate's resets and reason.
   - **Tests:** host 13 (response 0.6-1 ms of 300 with a 1.0-s teardown, no two encoders, `session_ended` → report →
     `session_started`), two mutations caught; JVM 146 / 146. Proof PROVEN. Record
     evidence/B22_RESTART_FAST_2026-10-24.md (18:00:24Z).
4. **APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22)
   **`6bddafc0ac58999e200842ff482349408aefed87fa61f0a88f4f7fa19218a927`**, 9,638,278 B.
   - Built offline in /tmp/b_q24h/PrivyHub: `bash ./gradlew :app:testDebugUnitTest --rerun :app:assembleDebug --offline
     --no-configuration-cache`. `gradlew` is not executable in the tree, and no chmod was done.
   - 0 tree `PrivyHub/` files newer than the build marker. Same signer as `20e3e339…`; only `classes3.dex` differs.
   - **NOT installed;** `20e3e339…` stays CONFIRMED. Copy at /tmp/b_q24h_scratch/apk/app-debug.apk; pin in
     evidence/b22_2026-10-24/apk_sha256.txt.
   - Without `PRIVYHUB_RESTART_FAST` on the host it behaves as `20e3e339…`.
5. **B23 RAN** (WAN-R1 present when reached: A's record, 17:58Z, with its manifest). `PRIVYHUB_LINK_RECOVERY_WAN=1`
   (`companion/link_recovery_wan.py`), per session at the stream's start, by the overlay address test and the overlay
   provider's path (a daemon thread, re-read every 10 s):
   - `lan` as wired (950 / 400);
   - **`remote-direct` H 450 / stall 200** (WAN-R1 direct: ≥ 250 / ≥ 200; H clamped so the silence save stays at 400,
     50 ms before the hold);
   - `remote-relayed` / `remote-unknown` as wired;
   - **addendum 1** (hashed after the first replay): a guard reverts a direct session at its first non-drop hold.
   - `link_recovery_config` per set applied (`at` `session`, `wan` {set, path_class, path, hold_ms, stall_ms, why}),
     plus `link_recovery_wan_config` at the wire.
   - **The replay through the real detector:** G4-S4 0 false holds at 950 and at 450. G4-S1 run 2 (direct → no-peer):
     18 at a fixed 450, 2 with the guard. The LAN would hold falsely at 450, which is why it keeps 950.
   - Tests 22; AST PROVEN. Record evidence/B23_LINK_RECOVERY_WAN_THRESHOLDS_2026-10-24.md (18:15:45Z; addendum
     18:18:39Z).
6. **A — CL-B13 setup.**
   - Pre-register the rows below, hashed before the install. Preserve `20e3e339…`
     (PrivyHub/app/build/cl_b12_installed/). `adb install -r` the APK in item 4 and read its sha256 back.
   - The onn on **5 GHz**; every client property EMPTY (the defaults are the test).
   - Host: the ten adopted lines (`e3_state.py` ok on ten); each cell's drop-in adds **`PRIVYHUB_RESTART_FAST=1`** (and
     **`PRIVYHUB_LINK_RECOVERY_WAN=1`** for cell 3) plus its impairment line.
   - **B21 after the restart:** `link_recovery_config` `implied` the six / `explicit` {} / `at` `import` / `reapply` [];
     `restart_fast_config` (`startup_check_s` 0.75, `lock_wait_s` 2.0).
7. **A — CL-B13 cell 1, B22's return cell** (`none@post-fec,seed=1`): the Home press on both return paths the user can
   produce, as CL-B12 item 8 (the menu; the tile / recents). Tell the user plainly first: "Press Home, wait about 5
   seconds, then come back. The game should be moving again within about 3 seconds of the stream reopening." Per
   return, expect:
   - `restart_fast` with `response_ms` ≤ 300, and its `at_utc` ≤ 300 ms after the start's `session_ended`;
   - `restart_fast_done` (`released_ms`, `spawned_ms`, `checked_ms`, `done_ms`); the journal's start response before
     the old report;
   - the relay's frame log: the old encoder's last frame ≤ entry + 0.3 s;
   - the report: `restart_fast_released_by` `fast`, `_response_to_release_ms`, `_gate_resets`; `restart_cause`
     `via_start`;
   - **the picture back: new activity → `session_started` ≤ 3.0 s.** On one clock: `startSession` (heartbeat 1 less
     its `elapsed_ms`) less `create_to_start_ms`. The events read is the onn's clock (~0.5 s behind; disclose it);
   - the first 2-s interval after `session_started` ≤ 15 underruns; no `restart_fast_failed`.
   - If the tile / recents again goes through `MainActivity`, record `surface` / `process` as not produced, as CL-B12
     did.
8. **A — CL-B13 cell 2, the same Home cell without `PRIVYHUB_RESTART_FAST`** (the APK's absent-key path): CL-B12's
   rows again, no `restart_fast*` row or report key, `session_started` ~4-12 s after the new activity as CL-B12. Then
   cell 3 if B23 is to be read.
9. **A — CL-B13 cell 3, B23's remote class on the bench** (the shim's WAN profile, `PRIVYHUB_LINK_RECOVERY_WAN=1`
   beside the umbrella, `blackout-4s@both,every=120s,seed=1` then `@down`, 600 s each).
   - **The class needs the onn's overlay address as the client's.** Over the LAN the rows read `lan` / 950 / 400,
     which is itself a row: the LAN unchanged.
   - Over the overlay, direct: `link_recovery_config` `wan.set` `remote-unknown` (`pending`), then `remote-direct` 450 /
     200;
   - `desync_pause` `input_hold` at `age_ms` ≈ 450 with the silence save before it (~400); the `@down` stall pause from
     ~200 ms;
   - 0 false holds outside the blackouts, and no `WHY_GUARD` row (a guard trip means a non-drop silence ≥ 450 on
     direct).
10. **The close and the files.**
    - **A — the close:** properties empty, the drop-in removed, ten lines, `e3_state.py` ok, `flags_absent`; out of
      the watch's 04:30-05:30Z. With every cell valid, CL-B7 §6 CONFIRMS `6bddafc0…` and the pin moves.
      `PRIVYHUB_RESTART_FAST` / `_LINK_RECOVERY_WAN` become candidates for the user's say-so (G-A5 / G-A6, not
      prepared here).
    - **Files:** three records + dirs (redact_check 0 FAIL; manifests); patches B21-B23; KNOWN_ISSUES (inserted:
      queue H under the LAN-R1 item, one line under G4-S4's Home item); ROADMAP (B21-B23); logs/b21_|b22_|b23_git_status.txt;
      SESSION_B_STATUS.txt.
    - **Left in /tmp:** b_q24h (the copy and its build), b_q24h_scratch/ (the APK, the mutation copies, the doc
      copies from before the insertions), b_q24h_scratch_*.txt, b_q24h_sync.sh / _regress.sh / _junit.py,
      b_q24h_build_marker, b21_pred_* (B21's proof scratch).
    - **Not done:** CL-B12's 30-underrun interval at press 2's Home (not in this queue); G4-S4's Home questions (pause
      at Home, keep the rung) stay the user's.
