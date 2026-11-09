# B72 — each item's off switch (or its scope) = today, hunk by hunk (`b72.diff`)

| item | file / hunk | off switch, or the scope that keeps today | proof |
| --- | --- | --- | --- |
| (a) the card at the top | `N64LayoutCard.kt` (`PROPERTY_TOP`, `overlayTopPadding`, `gravity`, `parseTop`, `topFromSystem`); `NativeStreamActivity.kt`: the gravity and the layout listener, plus the padding put back at the card's dismissal | `debug.privyhub.n64_card_top=0` → B67's centre gravity, no listener, no padding change. The card exists only with the player prompt on (B67's) | `B72ClientTest`; M1 / M2 caught |
| (b) `fps (min)` | `diag_read.py`: `self.fps_reset` filled where a delta is negative; `summarize`'s min over the seconds that are neither a reset nor a hold-resume second, clamped at ≥ 0 | a session with no reset and no hold-resume second gets today's min. The median, the per-second table and every other column are today's | `FpsMin.test_today_without_a_reset`; the HOME-9 evening re-read: every session without a hold reads the same (`home9_diag_reread.txt`); M1 caught |
| (c) the dolphin window | `diag_read.py`: `gc_hold_onset()`, used for a `resumed` row | only a session whose core is `dolphin` with a `desync_pause` ≤ 60 s before. Every other core: B66's window, byte for byte | `DolphinSplit.test_the_same_rows_on_another_core_are_today`; the re-read: the PS1 / N64 rows identical; M2 caught |
| (d) `gc_frames` | `SEGMENT_RATES`, `snap(…, rates)`, `own_rate`, `vi_seconds`; render's `vblank_ms`; main passes `--vblank` to the render | the runs are still cut on today's 30 / 60 (`RATES` unchanged). A segment is reclassed only where its own median snaps to another rate. VIs only with both files | `Frames.test_sixty_only_is_today`, `test_a_hitch_second_stays_in_its_run`; C34 / C35 / C36's files re-read (`c34_c36_gc_frames_reread.txt`: the 60-only launches identical); M3 / M3b caught |
| (e) SDL off the pads | `gamecube_session.py`: `PAD_USB_ID`, `SDL_HINTS`, `launch_env()`; the Dolphin Popen's `env=` | only a Dolphin launch (`PRIVYHUB_GAMECUBE=1`). **`PRIVYHUB_GC_SDL_PADS=1` → the environment returned unchanged** (today's `dict(os.environ)`) | `SdlPads.test_the_knob_is_today`; M4 caught |
| (f) one save per stall | `rewind_cores.py`: `GC_CHECK_SKIP`, `gc_check_idle`, `_gc_idle()`. `_save_gc` returns early only while a check runs. `_release_gc` clears the event before it spawns. `_verify_gc` is now try/finally around `_verify_gc_check` (the old body, unchanged) | only a Dolphin session's slot-9 save, and only while a GameCube picture check runs. RetroArch / PCSX2 / N64 paths never reach `_save_gc` | `CheckWindow.test_after_the_check_a_stall_saves_as_today`; the 54 B69 tests green; M5 caught |
| (g) `state_reply` rows | `plugins/games.py`: `STATE_REPLY_KEYS`, `_state_reply_row`, called after SAVE / LOAD (and on their errors, then re-raised) | **`PRIVYHUB_STATE_REPLY_ROWS=0` → no row.** The reply to the onn is unchanged in every case: the row never touches the payload, an error is re-raised as before, and the helper swallows its own errors | `StateReply.test_the_knob_is_today`; M6 caught |
| — | `tests/b65_n64_continue/test_b65.py` | **disclosed:** B65's plugin test pinned the exact list of rows of a refused N64 load. It now filters out the `state_reply` row and keeps its assertion | `tests/b65_n64_continue` 7 green |

**Disclosed (d), a refinement after a test finding.** The design put 20 into the per-second classes. B69's own suite
then showed that a real hitch second in a 30-fps run (≈ 23 presents) would snap to 20, cut the run and hide the hitch.
So the per-second cut stays on today's 30 / 60, and the 20 class applies only when a segment is classed by its own
median. That still covers C34's case: a "30" run whose median is 21 is classed 20. Mutation M3b, the design's first
form, is caught by the new `test_a_hitch_second_stays_in_its_run` and by B69's two metric tests.

**What goes live at the companion's next restart (no drop-in):**
- (b) / (c) / (d) are tools run by hand;
- (e) / (f) apply in GameCube sessions (G-A16 adopted);
- (g) applies in every session's SAVE / LOAD;
- (a) comes with the new APK.
