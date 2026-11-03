# SESSION B — done, 2026-10-31 L (QUEUE_2026-10-31L: B32, B33, B34, B35, B36, B37; run 17:32-18:00Z; baseline 1904fe8, companion/ tools/ tests/ PrivyHub/ clean. Only the companion + `privyhub-trip-log` active, checked first. Nothing committed, nothing adopted, nothing installed, no stream, no companion restart, no adb; the trip keeper and `evidence/trip_2026-10-30/` only read)

**How it ran.** Each item was built in its own `/tmp/b_q31l_<item>` copy (B32 in two halves, client and host), each
design hashed before its code. The coordinator merged the six diffs in `/tmp/b_q31l_all` and resolved one adjacent
B32 / B34 hunk in `NativeStreamActivity.kt` (the rejected hunk kept as `evidence/queue_l_2026-10-31/merge_b34_rejected_hunk.rej`).
It fixed one cross-item mismatch (B36 read `in_place` from the wrong ladder row; B36 record §5). Then it ran every
suite on the merged copy and applied `evidence/queue_l_2026-10-31/queue_l_combined.diff` to the tree (uncommitted).
- **Host:** every `tests/` suite as the baseline (33 / 33) plus 8 new suites, all OK. The four `tools/` tests fail in
  a copy as at every baseline.
- **JVM:** 184 / 184 on the merged tree (161 + 23 new).

1. **B32 BUILT — the stream survives a brief screen loss; a step-up in place.**
   - **Client, `debug.privyhub.surface_hold=1`** (`1` = a 12-s bound; a value 10000-30000 sets the bound in ms; absent /
     empty / junk = today):
     - on `surfaceDestroyed` the receiver, the audio and the controller sender keep running; the decoder closes (it
       cannot outlive its surface);
     - the stall signal sees the growing age, so the host pauses the game as at a link stall;
     - back within the bound: the **same** session (no `native-stream-start`, no `session_ended`, no rung reset), the
       decoder rebuilt on the next IDR; past it, today's restart.
   - **Every foreground loss** is a `surface_lost` row (reason, keys and device events in the 2 s before, the bound,
     `away_ms`, outcome `held` / `restarted`), riding the next heartbeat into the recovery log.
   - **Pad guide / Home-class keys from a pad are consumed;** the remote's pass as today.
   - **Settled:** Android gives no pause reason. `KEYCODE_HOME` / `APP_SWITCH` never reach the activity. What took
     Friday's six is not knowable from the code; the rows will say.
   - **Host, `PRIVYHUB_STEP_IN_PLACE=1`:**
     - **Settled:** ffmpeg 7.1's `h264_vaapi` has no runtime rate control (options fixed at open; `-nostdin`).
     - **Built:** the new encoder starts before the old one stops. The relay splices it onto the **same SSRC,
       sequence and timestamp line**, so the onn sees one IDR and no SSRC change.
     - No splice in 2 s → today's restart (`in_place: false`). LAN and remote ladders alike.
     - The `transition_done` row carries `in_place` / `ssrc_unchanged` / `splice_gap_ms`.
   - **Inside the adopted `PRIVYHUB_REMOTE=1`:** an explicit `PRIVYHUB_REMOTE_RUNG_CAP=<kbps>` now acts on the
     umbrella's ladder. No such line is set today.
   - **Tests:** JVM `SurfaceHoldTest` 8; `tests/surface_lost` 9; `tests/step_in_place` 15 (the real relay on loopback);
     5 mutations caught. Absent PROVEN.
   - Record: `evidence/B32_SURFACE_HOLD_AND_STEP_IN_PLACE_2026-10-31.md`.
2. **B33 BUILT — no rewind without loss** (inside the adopted `PRIVYHUB_LINK_RECOVERY=1`; **off:
   `PRIVYHUB_REWIND_NEEDS_LOSS=0`**).
   - **The rule:** a release under 1 s whose window shows no client loss, no unrecoverable FEC, no audio gap ≥ 250 ms
     and no uplink loss resumes without loading the save. The save still happens. Every other case loads as today.
   - **`input_release` carries `why`:** `no_loss_under_1s`, or `long` / `loss` / `dark_span` / `uplink_loss` /
     `uplink_unknown` / `no_heartbeat` / `counter_reset`.
   - **Replay:** 4 of Friday's 5 state loads would have resumed (the three golf stalls, the hockey step-up); the onn's
     departure at 05:28 still loads.
   - **Live at the next companion restart** (B26's convention).
   - **Tests:** 14 tests; B9 / B12 / B16 unedited and green; 2 mutations caught; absent PROVEN.
   - **"Live again" settled, not built:** five options; the worker's pick is a 1-s corner mark.
   - Record: `evidence/B33_NO_REWIND_WITHOUT_LOSS_2026-10-31.md`.
3. **B34 BUILT — stable player slots, gamepads only** (`debug.privyhub.pad_slots=stable`).
   - **Eligible:** a gamepad / joystick source with at least one gamepad button. The remote and an air mouse get no
     slot.
   - **Assignment:** a 6-hex hash of vendor:product:descriptor; Android's controller-number order at a start. A late pad
     takes the lowest free slot; a pad that leaves keeps its slot; slots last for the process's life.
   - **Rows:** the map in every report and heartbeat; the host writes a `pad_slots` recovery row at each start
     (`when: start`, from the start query) and on a change, plus `updates_by_player` on the heartbeat row.
   - **Tests:** JVM 7; host 5; 3 mutations caught; absent PROVEN.
   - **Settled, read-only, nothing changed:**
     - Friday made **four** changes to the football title (multitap on, off, DualShock, back to digital);
     - the final state is multitap off and digital on both ports;
     - the right two-player setting without multitap is exactly that, with the two real pads on P1 / P2.
   - Record: `evidence/B34_STABLE_PAD_SLOTS_2026-10-31.md`.
4. **B35 BUILT — the movie player retries** (client `debug.privyhub.vod_retry=1`; host `PRIVYHUB_VOD_LOG=1`).
   - **Client:**
     - on Media3 IO / load errors (a movie only, never live TV), back off 1, 2, 4, 8, 15, 15 … s for up to 150 s;
     - each attempt seeks to the error's position with "reconnecting…"; past the bound, today's "Playback error",
       then a Retry dialog (new, flag only);
     - rows `vod_error` / `vod_retry` / `vod_resumed` / `vod_gave_up` to `POST /diagnostics/vod-client` →
       `logs/vod_client.jsonl` (an opaque 12-hex id, no title or path).
   - **Host:** `logs/vod_range.jsonl`, one row per range request (Range, status, length, bytes sent, duration,
     `closed` = complete / short / client_reset / broken_pipe / error / no_body).
   - **Tests:** JVM 8 (the fake server drops 1 h 50 min in → resumed at that byte); host 9; 4 mutations caught;
     absent PROVEN.
   - Record: `evidence/B35_VOD_RETRY_2026-10-31.md`.
5. **B36 BUILT — the always-on diagnostics keeper** (new files only; nothing runs until A installs it).
   - `tools/diag_keeper.py` (unit `tools/privyhub-diag.service`):
     - copies every 5 min into `~/privyhub_diag/<UTC date>/`, redacted;
     - **30-day retention** that deletes only `^\d{4}-\d{2}-\d{2}$` day-dirs directly under the root;
     - the 60-s samples;
     - a `sessions.jsonl` row ~2 min after each `session_ended`.
   - `tools/diag_read.py <range>` (`last night` / `today` / `2026-10-30 21:00..05:00` / `trip`) →
     `evidence/reads/`.
   - `tools/diag_check.py` (the six lines, the keeper line `privyhub-diag`). **`tools/trip_check.py` and
     `tools/trip_log_keeper.py` unchanged:** the runbook uses the first, `diag_keeper` imports the second.
   - **Dry run over the trip keeper's copies, read-only:** TRIP-R2 §1's restart table 47 / 48 cells (one label: the
     04:34:41 start never PLAYING); `sessions.tsv` 900 / 900 cells.
   - **Tests:** 28; 6 mutations caught.
   - Record: `evidence/B36_DIAG_KEEPER_2026-10-31.md`.
6. **B37 READ — where the 125 ms go.**
   - **`control_round_trip_ms` is not a control echo.** It is the 2-s health POST's HTTP round trip: a new TCP
     connection plus the hub's synchronous handler. The controller datagrams are one-way and never echoed.
   - **The LAN floor:** p50 45-66 ms against ~4.4 ms ICMP, so ~33-43 ms is fixed handler and stack cost.
   - **The path:** Friday's R ≈ 28-47 ms; G4-S4's R ≈ 6-15 ms. A press's one-way delay is ~15-25 ms Friday, not 125.
   - **Designed, not built:** D3 (host-only uplink delay from the packet timestamps), D1 (a true echo), D2 (fix the
     POST), D4 (send on the input event, run-ahead, the Wi-Fi lock). Input → photon is measured nowhere.
   - CAPABILITY_MODEL §7 has the row. Record: `evidence/B37_CONTROL_ECHO_BUDGET_2026-10-31.md`.
7. **The APK (B5 … B25 + B32 + B34 + B35; B27 / B29 out)
   `554ccf61a87ad061320740adfa830b6fe726e794dfccbe544873bd621b939902`**, 9,675,856 B.
   - **How it was built:** the tree with `b29.diff` then `b27.diff` reversed (the reversed files equal B27's / B29's
     recorded predecessors), then queue L's diff. Offline, `--rerun-tasks --no-configuration-cache`; JVM 173 / 173
     (184 less B27's 4 and B29's 7).
   - **Checks:** a rebuild gives the same bytes; `apksigner verify` OK; same signer as `fcd924c2…`.
   - **Pinned, NOT installed** (`PrivyHub/app/build/queue_l_built/app-debug.apk`; `/tmp/b_q31l_scratch/apk/`).
     `fcd924c2…` stays CONFIRMED on the onn. Files: `evidence/queue_l_2026-10-31/`.
8. **Live at the next companion restart** (any restart, for any reason):
   - **B33's rule** (inside `PRIVYHUB_LINK_RECOVERY=1`);
   - **B32's cap fix**, only if an explicit `PRIVYHUB_REMOTE_RUNG_CAP` line exists (none does).
   - Everything else needs a new line or a property.
   - The running companion has its modules loaded and runs today's code until then. The range server is a separate
     process; its new code is today's without `PRIVYHUB_VOD_LOG=1`.

## A — HOME-1 (when the user is home; the user at the TV for the hand steps)

1. **Housekeeping:**
   - remove `_cowork_prompt_cap.txt` (its 4000 pin was never applied; B32 makes such a line act, so it must not be
     applied by mistake);
   - **the trip keeper's close:** `privyhub-trip-log` stops at its cap (2026-11-01T23:59Z), or by STOP. Confirm
     `status.txt` reads stopped and the manifest checks, then commit `evidence/trip_2026-10-30/`.
2. **"Read the trip":** `python3 tools/diag_read.py trip`, the whole weekend from the keeper's copies (read-only) →
   `evidence/reads/diag_trip_<UTC>.md`. It must show Friday's six restarts as TRIP-R2 §1 has them, plus anything
   played since.
3. **`privyhub-diag` enabled and started:**
   ```
   mkdir -p ~/.config/systemd/user && cp tools/privyhub-diag.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now privyhub-diag
   python3 tools/diag_check.py
   ```
   - **Pass:**
     - `systemctl --user is-active privyhub-diag` = `active`, and `diag_check`'s sixth line reads `… unit privyhub-diag
       active`;
     - chunks under `~/privyhub_diag/<UTC date>/raw/` within 5 min;
     - after the first session ends, one `~/privyhub_diag/sessions.jsonl` row within 90-150 s.
4. **The companion restart** (outside 04:30-05:30Z; brings B33 live). Then **the APK installed with every property
   empty:**
   - preserve `fcd924c2…` (`cl_b14_installed/`);
   - copy `PrivyHub/app/build/queue_l_built/app-debug.apk` to `PrivyHub/app/build/home1_installed/`, `adb install -r`,
     and read back `554ccf61a87ad061320740adfa830b6fe726e794dfccbe544873bd621b939902`, paired;
   - the seven properties read empty, plus the three new ones `debug.privyhub.surface_hold`, `debug.privyhub.pad_slots`,
     `debug.privyhub.vod_retry`.
5. **The bench cells** (pre-register the rows, hashed, before the install; 5 GHz; the overlay at home where noted):
   - **C1, the surface loss.**
     - **Do:** `adb shell setprop debug.privyhub.surface_hold 1`; in a game, the user presses the onn remote's Home and
       returns to PrivyHub within 3 s.
     - **Pass:**
       - one host session: no `restart_fast` and no `session_ended` at the return;
       - a recovery row `"event": "surface_lost"` with `"outcome": "held"`, `away_ms` < 12000 and a `reason`;
       - the report's `surface_hold.held` 1; the picture back within ~0.5 s; the game paused through the loss.
     - **Also:**
       - a pad guide press → `"reason": "pad_system_key"`, keys containing `110:pad:…`, and the stream stays;
       - a 15-s away → today's restart and a `"restarted"` row.
     - **Off:** `setprop debug.privyhub.surface_hold ""`.
   - **C2, the step in place.**
     - **Do:** `PRIVYHUB_STEP_IN_PLACE=1` in a drop-in and restart; a remote-class session over the overlay at home
       climbing from 4000, at least two step-ups.
     - **Pass:**
       - each `transition_done` in `logs/games/adaptive_bitrate_shadow.jsonl` reads `in_place: true`,
         `ssrc_unchanged: true`, `splice_gap_ms` < 40;
       - the encoder log reads `B32 in-place step: … active on the same stream`;
       - the client report shows no SSRC change at the steps, and no `client_stall` within 2 s of a step.
     - **Fail signal:** `in_place: false` with `in_place_fallback`.
     - **Afterwards:** remove the drop-in and restart.
   - **C3, the no-rewind stall.**
     - **Do:** B33 live, no `PRIVYHUB_REWIND_NEEDS_LOSS` line, a PS1 title; one ~0.5-s stall with no loss (a C1 loss
       under 1 s, or a step-up without C2's line).
     - **Pass:**
       - the recovery log reads `state_saved` (stall) → `desync_pause` → `input_release` with `method` `resume`, `why`
         `no_loss_under_1s`, `held_ms` < 1000 → `resumed`;
       - no `LOAD_STATE_SLOT 9` in the game log;
       - one `rewind_needs_loss_config` row at the plugin's start.
     - **Contrast** (optional): an impairment-shim loss run loads with `why` `loss`.
   - **C4, two pads swapped.**
     - **Do:** `setprop debug.privyhub.pad_slots stable`, two pads paired, a two-player PS1 title. Press pad B first,
       then pad A; exit and relaunch; press pad A first.
     - **Pass:**
       - both starts write `"event": "pad_slots", "when": "start"` with the same two `{slot, pad, class}`;
       - the lower controller number is slot 0 both times;
       - `updates_by_player` rises on slots 0 and 1 only; the remote takes no slot;
       - with the property empty, no `pad_slots` row or key.
   - **C5, the VOD drop.**
     - **Do:** `setprop debug.privyhub.vod_retry 1`; `PRIVYHUB_VOD_LOG=1` in a drop-in and restart; a movie; the
       connection closed mid-play (the shim, or the onn's Wi-Fi off ~10 s).
     - **Pass:**
       - "reconnecting…" shows, and the movie resumes at the same position within 150 s with no "Playback error";
       - `logs/vod_client.jsonl` reads `vod_error` → `vod_retry`×n → `vod_resumed`;
       - `logs/vod_range.jsonl` has the broken request `client_reset` / `broken_pipe` with bytes < length, then
         `bytes=<P>-`.
     - **Down case:** > 150 s unreachable → `vod_gave_up`, then "Playback error", then Retry.
6. **The close and the CONFIRMED rule (CL-B7 §6):**
   - **The close:** properties empty, the drop-ins removed, thirteen lines, `e3_state.py --check` ok, `flags_absent`.
   - **The rule:** if the cells are valid and today's behaviours hold wherever no flag was set (B33's intended
     difference aside), **`554ccf61…9902` is CONFIRMED** and the pin moves: `tools/e1_suite.py` `EXPECT_APK`,
     `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise `fcd924c2…` goes back on.
7. **G-A10..13, the user's questions** (only for cells that were met; otherwise back to B with the rows):
   - **G-A10:** "Adopt `PRIVYHUB_STEP_IN_PLACE=1` as the fourteenth line? Each bitrate step then keeps the same stream
     (no new SSRC, no ~0.4-s gap)." (C2)
   - **G-A11:** "Turn the screen-loss hold on by default in the next APK (`debug.privyhub.surface_hold`, as B25 did for
     the link notice)? A Home press or a system panel of up to 12 s then keeps the session." (C1)
   - **G-A12:** "Turn stable player slots on by default (`debug.privyhub.pad_slots=stable`)? Pads keep their player
     number across launches, and only real gamepads get one." (C4)
   - **G-A13:** "Turn the movie retry on by default (`debug.privyhub.vod_retry`) and adopt `PRIVYHUB_VOD_LOG=1`? A
     dropped movie reconnects and resumes by itself for 2.5 min." (C5)
   - **Not a question:** B33 is inside the adopted line; `PRIVYHUB_REWIND_NEEDS_LOSS=0` is its off switch if C3 shows
     harm.

## Files
- **Records:** `evidence/B32_SURFACE_HOLD_AND_STEP_IN_PLACE_2026-10-31.md` (the host half merged in),
  `B33_NO_REWIND_WITHOUT_LOSS_2026-10-31.md`, `B34_STABLE_PAD_SLOTS_2026-10-31.md`, `B35_VOD_RETRY_2026-10-31.md`,
  `B36_DIAG_KEEPER_2026-10-31.md`, `B37_CONTROL_ECHO_BUDGET_2026-10-31.md`.
- **Their dirs:** `b32_2026-10-31/` (host under `host/`) … `b37_2026-10-31/`.
- **Integration:** `evidence/queue_l_2026-10-31/` (combined diff, the baselines, the merged runs, the APK).
- **Patch files:** `patches/B32_…` … `B36_….md`. Logs: `logs/b32_` … `b37_git_status.txt`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md`, `docs/CAPABILITY_MODEL.md` (§7, the remote
  RTT row).
- **Left in /tmp:**
  - `b_q31l_base`, `b_q31l_all`, `b_q31l_apk`, `b_q31l_apk_pre`, `b_q31l_jvmbase`, `b_q31l_treecheck*`;
  - the item copies `b_q31l_b32c` / `b32h` / `b33` / `b34` / `b35` / `b36` and their `_scratch/`;
  - `b_q31l_scratch/` and the scripts `b_q31l_*.sh` / `b_q31l_junit.py`.
