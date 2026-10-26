# SESSION B — done, 2026-10-26 I (QUEUE_2026-10-26I: B24 then B25. B24 run 03:26-03:50Z, baseline 06c565e, committed by the user in f114dee. B25 run 03:50-04:05Z, baseline da48629 (clean). At each run G-A5's record was present and only the companion + `privyhub-link-n1` active, checked first; nothing committed, nothing adopted, no stream, no restart, no adb, nothing installed; G-A6 not touched; A's uncommitted G-A5 edits left as they are at B24)

1. **B24 SETTLED.**
   - **Return 1's 2,088-ms old-audio stop** (the audio timing snapshot's mtime is the stop's end; the others ran
     203-352 ms) is the audio capture's 2-s SIGTERM `wait` expiring, then SIGKILL. The sender leaves in ≤ 10 ms; the
     reader at the capture's EOF; `pactl` would show 3 s.
   - **The new ready needs only the new encoder's check and `prepare`.** The client waits ≤ 3 s for its first audio
     packet without underruns.
   - **The old encoder's flushed frames (+0.35 / +0.39 s) were forwarded** because G-A5 stops the relay only after its
     exit.
2. **B24 BUILT:** `PRIVYHUB_RESTART_FAST_UNLOCK=1`, inside the adopted `PRIVYHUB_RESTART_FAST=1`
   (`companion/restart_fast_unlock.py`, `RestartFastUnlock(RestartFast)`).
   - **Under the lock:**
     - the old audio's stop started first (a watchdog SIGKILLs its capture at 300 ms);
     - **the relay stopped**; the old encoder SIGTERMed, the capture target selected meanwhile, SIGKILL after 100 ms;
     - the new encoder, `prepare`, the 0.75-s check;
     - **the lock released: the ready answers.**
   - **After:** `restart_fast_audio_stop` (`restart_fast_audio_stop_ms`, `capture_returncode`,
     `capture_killed_at_bound`), then the new audio (`restart_fast_audio`).
   - **Tests:** 10 green, B22's 13 unedited and green, every `tests/` suite green (29), two mutations caught. With
     return 1's slow capture faked, the ready came at 1,160 ms (G-A5's worker: ~2.3 s). Absent = the G-A5 worker,
     PROVEN.
   - **No client change from B24.** (B25's APK follows.)
   - Record evidence/B24_RESTART_FAST_UNLOCK_2026-10-26.md (design hashed 03:32:18Z).
2b. **B25 BUILT (the user's "Yes"): `debug.privyhub.link_notice` absent / empty / junk = ON, `0` off** (as B13 / B19;
   only `LinkNoticeFlag`'s parse and catch changed; B14's rule, wording, once-a-session and 30-s clear unchanged).
   - **The replay first** (B14's rule over every heartbeat with the link keys since G-A3, 45 sessions, plus the live
     log, which added none): **3 / 3 on 2.4 GHz show it** (CL-B10 c4, reason band, at the first tick), **0 / 42 on 5
     GHz.** The port matches the real client's bits in CL-B10, with 0 disagreements in 9 sessions.
   - **For the user (not changed):** the lowest RSSI any 5-GHz session held 10 s is −70 dBm, 2 dB above −72. **−71** is
     the loosest threshold that keeps them all quiet. tx: 130 Mbps held 10 s against 54.
   - JVM 150 / 150 (4 new; B14's and B19's flag lines moved, disclosed); a mutation back to B14's flag fails 5; `0` =
     B14's absent PROVEN; host suites 29 / 29 (no host change).
   - **APK (B5 … B19 + B22 + B25) `fcd924c2…9b96`, 9,638,234 B, pinned, NOT installed.** Same signer as `6bddafc0…`;
     only `classes3.dex` differs.
   - Record: `evidence/B25_LINK_NOTICE_DEFAULT_ON_2026-10-26.md` (design hashed 03:53:39Z, before the replay and the
     code).
3. **A — CL-B14** (one attended Home cell) **with B25's APK `fcd924c2…9b96` installed.**
   - **Setup:** pre-register the rows below, hashed. Install `fcd924c28cbf70a85bb9a886caabcb07873eee2d028b6538284fce5a7ae39b96`
     (B5 … B19 + B22 + B25; the pin moves only by the CONFIRMED rule). The onn on 5 GHz; **every client property EMPTY**
     (read back empty); `e3_state.py` ok on eleven. The cell's drop-in: the impairment line `none@post-fec,seed=1` + **`PRIVYHUB_RESTART_FAST_UNLOCK=1`**
     (the eleven lines carry `PRIVYHUB_RESTART_FAST=1`). E1-SNES-STREAM.
   - **Expect at the start:** `restart_fast_config` and **`restart_fast_unlock_config`** (`kill_grace_s` 0.1,
     `capture_bound_s` 0.3, `audio_join_cap_s` 10).
   - **Four returns:** two through the PrivyHub menu, two through recents or the tile. Tell the user plainly first:
     "Press Home, wait about 5 seconds, then come back. Twice through the PrivyHub menu, twice through recents or the
     PrivyHub tile. The game should be moving again within about 2 seconds."
4. **A — the rows per return** (CL-B13 §2's methods):
   - **R1:** the picture back (new activity → `session_started`, one clock) **≤ 2.0 s**;
   - **R2:** the old encoder's last frame forwarded (the relay's per-second rows) **≤ entry + 0.3 s**;
   - **R3:** `restart_fast_done` `unlocked_ms` − `checked_ms` **≤ 20**, with `relay_stopped_ms`, `released_ms`
     (≈ 100-150), `spawned_ms`, `checked_ms`;
   - **R4:** no second after the kill with both encoders' frames (one relay row per second beyond the switch);
   - **R5:** `session_ended` → the old report → `session_started`;
   - **R6:** `restart_fast_audio_stop` (`restart_fast_audio_stop_ms`; a `capture_killed_at_bound` true / −9 means a
     capture that would have taken the 2-s wait) and `restart_fast_audio` `started` true; the first 2-s interval after
     `session_started` ≤ 15 underruns;
   - as CL-B13: `restart_fast_released_by` `fast`, `via_start`, no `restart_fast_failed`;
   - **R7 (B25), with no property:** every heartbeat carries `link_notice` and it reads **0** on 5 GHz (armed, not
     shown); no `link_notice_shown` row; the diagnostics page shows "Link notice: none shown". If the onn is found on
     2.4 GHz, the notice at the first tick plus one `link_notice_shown` (reasons 1): record it, and do not switch the
     band without the user.
   - **Return 1-like cases are tight:** a 0.55-s new activity → entry (the first POST) leaves ~0.02 s of margin on
     R1. Record that offset per return.
5. **A — the close:** properties empty, the drop-in removed, eleven lines, `e3_state.py` ok, `flags_absent`; out of
   the watch's 04:30-05:30Z. **The CONFIRMED rule (CL-B7 §6):** if the cell is valid with today's behaviours where no
   flag was set, `fcd924c2…` is CONFIRMED and the pin moves (`tools/e1_suite.py` `EXPECT_APK`,
   `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test). Otherwise `6bddafc0…` goes back on. **If every row is met at every return: the user's say-so question for G-A7:** "Adopt
   `PRIVYHUB_RESTART_FAST_UNLOCK=1` as the twelfth line? It lets the game resume at the new picture's check (~1.2-2.0 s
   after a Home return) without waiting for the old session's audio teardown." Otherwise back to B with the rows.
   B prepared no G-A7 patch (A writes it in G-A5's applied form, as before).
6. **Files:**
   - the record + `b24_2026-10-26/` (redact_check 0 FAIL; manifest);
   - `patches/B24_RESTART_FAST_UNLOCK.md`;
   - KNOWN_ISSUES (inserted under the Home / slow-return item); ROADMAP (B24);
   - `logs/b24_git_status.txt`; SESSION_B_STATUS.txt.
   - B25: the record + `b25_2026-10-26/` (redact_check, manifest); `patches/B25_LINK_NOTICE_DEFAULT_ON.md`;
     KNOWN_ISSUES (inserted under the LAN-R1 / band item); ROADMAP (B25); `logs/b25_git_status.txt`. Left in /tmp:
     b_q26i25 (the copy), b_q26i25_scratch/ (the APK copy, the docs before the insertions), b_q26i25_scratch_*.txt,
     b_q26i25_sync.sh / _regress.sh / _junit.py / _build_marker.
   - **Left in /tmp:** b_q26i (the copy), b_q26i_scratch/ (the mutation copies, the docs before the insertions),
     b_q26i_scratch_*.txt, b_q26i_sync.sh / _regress.sh, b22_* (the harness's temp roots).
   - **Disclosed:** the first test run spawned five real `ffmpeg -window_id w1` (the new module's `subprocess` not yet
     patched). Each printed its usage and exited; none remains.
