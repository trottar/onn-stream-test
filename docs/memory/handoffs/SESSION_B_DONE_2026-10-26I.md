# SESSION B — done, 2026-10-26 I (QUEUE_2026-10-26I: B24; run 03:26-03:50Z; baseline 06c565e; G-A5's record present and only the companion + `privyhub-link-n1` active, checked first; nothing committed, nothing adopted, no stream, no restart, no adb, nothing installed; G-A6 not touched; A's uncommitted G-A5 edits left as they are)

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
   - **No client change: `6bddafc0…a927` stays the APK (CONFIRMED).**
   - Record evidence/B24_RESTART_FAST_UNLOCK_2026-10-26.md (design hashed 03:32:18Z).
3. **A — CL-B14** (one attended Home cell). The APK stays `6bddafc0…` (no install).
   - **Setup:** pre-register the rows below, hashed. The onn on 5 GHz; every client property EMPTY; `e3_state.py` ok
     on eleven. The cell's drop-in: the impairment line `none@post-fec,seed=1` + **`PRIVYHUB_RESTART_FAST_UNLOCK=1`**
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
   - as CL-B13: `restart_fast_released_by` `fast`, `via_start`, no `restart_fast_failed`.
   - **Return 1-like cases are tight:** a 0.55-s new activity → entry (the first POST) leaves ~0.02 s of margin on
     R1. Record that offset per return.
5. **A — the close:** properties empty, the drop-in removed, eleven lines, `e3_state.py` ok, `flags_absent`; out of
   the watch's 04:30-05:30Z. **If every row is met at every return: the user's say-so question for G-A7:** "Adopt
   `PRIVYHUB_RESTART_FAST_UNLOCK=1` as the twelfth line? It lets the game resume at the new picture's check (~1.2-2.0 s
   after a Home return) without waiting for the old session's audio teardown." Otherwise back to B with the rows.
   B prepared no G-A7 patch (A writes it in G-A5's applied form, as before).
6. **Files:**
   - the record + `b24_2026-10-26/` (redact_check 0 FAIL; manifest);
   - `patches/B24_RESTART_FAST_UNLOCK.md`;
   - KNOWN_ISSUES (inserted under the Home / slow-return item); ROADMAP (B24);
   - `logs/b24_git_status.txt`; SESSION_B_STATUS.txt.
   - **Left in /tmp:** b_q26i (the copy), b_q26i_scratch/ (the mutation copies, the docs before the insertions),
     b_q26i_scratch_*.txt, b_q26i_sync.sh / _regress.sh, b22_* (the harness's temp roots).
   - **Disclosed:** the first test run spawned five real `ffmpeg -window_id w1` (the new module's `subprocess` not yet
     patched). Each printed its usage and exited; none remains.
