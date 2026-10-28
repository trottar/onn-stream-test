---
memory_schema: 1
as_of: 2026-10-27
baseline_commit: 2cd392c (CL-B14 committed; "G-A7 handoff; queue J"; G-A7 uncommitted beside it; the user commits)
---

# G-A7 — `PRIVYHUB_RESTART_FAST_UNLOCK=1` ADOPTED: the twelfth adopted line; the confirmation window VALID, every row met

**Classification: ADOPTED (the user's decision, 2026-10-27, "Go", after CL-B14). The adopted environ is TWELVE lines.**
- **The confirmation window was VALID**, with the host gates met. It was one E1-SNES-STREAM with no `e3_flag.conf`, no
  client property set and the twelve lines alone, on 5 GHz throughout.
- **The configs came from the drop-ins alone:** `restart_fast_config` (0.75 / 2.0), **`restart_fast_unlock_config`**
  (`kill_grace_s` 0.1, `capture_bound_s` 0.3, `audio_join_cap_s` 10, `startup_check_s` 0.75) and B21's
  `link_recovery_config` (`implied` the six, `explicit` {}, `at` `import`, `reapply` []).
- **No `restart_fast` row of any kind**, as pre-registered: there was no Home press, and the flags act only on a
  guarded start. The behaviour is CL-B14's (every row met at four returns; the picture back 1.15-1.86 s).
- **No action without a stall:** 0 `state_saved`, 0 holds, 0 stall rows.
- **The link:** 0 silences ≥ 250 ms; hitch seconds 2.6 / 10 min (3 s, the longest run 1 s). `link_notice` 0 in 345 / 345
  heartbeats, 5180 MHz in all.
- **The teardown:** `session_end_bye`, then `state_save_skipped` `client_bye` (401.1 ms), no hold.
- Nothing else adopted. Nothing committed.

Task: `handoffs/G-A7_RESTART_FAST_UNLOCK_ADOPTION_TASK.md`, session A. **No patch was prepared by B,** so A wrote the
adoption in G-A5's applied form: `patches/G-A7_RESTART_FAST_UNLOCK_ADOPTION.md`. The behaviour was measured in
`CL_B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_2026-10-26.md` and built in `B24_RESTART_FAST_UNLOCK_2026-10-26.md`. Files:
`g_a7_2026-10-27/`.

## 1. Precondition (`check_before.json`, 2026-10-27 21:01:38Z)

- `tools/e3_state.py --check` ok on eleven (`e3_check_before.txt`), **APK `fcd924c2…9b96` CONFIRMED**; no
  `e3_flag.conf`; no game, RetroArch or encoder.
- One device paired (`client_before.json`, booleans and counts). The client on the LAN: the newest `token_issued` reads
  `routing_evidence` lan, and the Hub host is empty.
- **The band 5 GHz** (5180 MHz, standard 5, RSSI −68). The seven client properties empty.
- Units: `privyhub-companion` and `privyhub-link-n1` only.
- **HEAD `2cd392c`** ("G-A7 handoff; queue J"), CL-B14 committed (`d1e29b1`). `git status --short` was empty before
  this dir was made (`git_status_at_start.txt`).
- **The clock 21:01Z.** The task's rule: the restart and the window must end before 04:15Z, and if it is later than
  03:40Z at the start, stop. Read as the night's approach to the watch; at 21:01Z the work ended at 21:19Z, about seven
  hours before 04:15Z.

## 2. The adoption

1. **The diff, written first** in a scratch copy (`/tmp/g_a7_scratch/`), then as
   `docs/memory/patches/G-A7_RESTART_FAST_UNLOCK_ADOPTION.md` (the diff and the predecessor sha256s inside).
   - `g_a7.diff` was extracted from the patch file and compared byte-equal with the scratch diff.
   - `git apply --check -p1`, then `git apply -p1`: 4 files, +11 / −5 (`g_a7_applied.diff`; `predecessor_sha256.txt` →
     `after_sha256.txt`).
   - `tools/e1_suite.py`: the comment `G-A7 (adopted 2026-10-27, the user)`; `RESTART_FAST_UNLOCK` defined and in
     `ADOPTED` (**twelve**); the preflight's `drop_in_restart_fast_unlock` and its `ok` term.
   - `tools/e3_state.py` (since G-A7, twelve … the fast restart unlocked), `tools/e1_remote.py`,
     `tools/test_e1_remote.py`: wording only. `ADOPTED_E3` is left as it is, as at G-A2..G-A5.
   - `git diff --check` was clean.
2. **Tests from the tree, green** (`tests.txt`):
   - `e1_suite.py --self-test`: `E1_SUITE_SELF_TEST_OK`;
   - `test_e1_remote` 21 OK; `test_c3_l4_nft_night` 33 OK;
   - `tests/restart_fast` 13 OK; **`tests/restart_fast_unlock` 10 OK**; `tests/link_recovery` `test_config_row` 9 OK +
     `test_link_recovery` 7 OK.
   - No file under `logs/` changed during the tests, and no ffmpeg was spawned. The harness's temp roots (`b22_*`) are
     in `/tmp`.
3. **The drop-in**, written with the file tool:
   `~/.config/systemd/user/privyhub-companion.service.d/restart-fast-unlock.conf` (`restart-fast-unlock.conf.copy`):

   ```
   [Service]
   Environment=PRIVYHUB_RESTART_FAST_UNLOCK=1
   ```

4. **`systemctl --user daemon-reload && systemctl --user restart privyhub-companion`**, a separate command, at
   **21:03:45Z** (active; no stream was running).
   - At 21:03:45.92Z the recovery log carried `link_recovery_config` (B21's row), `restart_fast_config` 0.75 / 2.0,
     **`restart_fast_unlock_config` 0.1 / 0.3 / 10 / 0.75** and the six module configs, none `ignored`
     (`restart_config_rows.jsonl`).
5. **The environ read back TWELVE lines** (`check_after_restart.json`):
   1. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`
   2. `PRIVYHUB_AUDIO_CODEC=opus`
   3. `PRIVYHUB_EPG_GUIDE_INDEX=cached`
   4. `PRIVYHUB_LINK_RECOVERY=1`
   5. `PRIVYHUB_LINK_REPORT=1`
   6. `PRIVYHUB_OVERLAY_PROVIDER=tailscale`
   7. `PRIVYHUB_RECOVERY_TRIGGER=v2`
   8. `PRIVYHUB_RESTART_FAST=1`
   9. **`PRIVYHUB_RESTART_FAST_UNLOCK=1`**
   10. `PRIVYHUB_SESSION_IDENTITY=v2`
   11. `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`
   12. `PRIVYHUB_SNES_CORE=snes9x`
   - **`--check` ok on twelve:** `drop_in_restart_fast_unlock` true, APK CONFIRMED, `link_recovery.stack` all six
     `implied 1`.

## 3. The confirmation window

- **Pre-registration** `g_a7_preregistration.txt`, sha256 **`fe61accf…6691`**, hashed at 21:04:56Z, before the run.
  The tools were hashed then too (`tools_at_preregistration_sha256.txt`).
- **The run:** `g_a7_window.py` (G-A5's runner for twelve lines; `g_a7_window_vs_g_a5.diff`) as the transient unit
  `privyhub-g-a7-window` (`--collect`), 21:04:56-21:19:08Z. It called the suite's own CLI: `run --only E1-SNES-STREAM
  --runs 1 --window 600 --gap 120 --e2`. There was **no `--plan`, no `e3_flag.conf`, no `setprop`**, and the pad was not
  touched.
  - **PLAYING attempt 1**, 4.1 s. The session ran 21:07:20.3-21:18:53.5Z (11.55 min), with one client session.
  - The suite's window ran 600 s; the suite exited 0.
- **The environ:** twelve lines, equal to the new `ADOPTED`, in **57 of 57** reads (every 15 s). After the run: twelve
  lines, `flags_absent` true, `e3_state` ok, CONFIRMED (`window_result.json`).
- **The band:** 29 of 29 reads at 5180 MHz (`band.jsonl`). Mid-window (21:11:58Z, `state_midwindow.json`): the stack
  all `implied 1`, twelve lines, the seven properties empty. `ok` read false there only by `game_active`, as at G-A5's
  mid-window read; the preflight was ok.
- **The reader:** `g_a7_read.py`, which is G-A5's reader (B6's `measure` and UX-R3's `evening` / `counts`, unedited and
  pin-asserted) plus `restart_fast_unlock_config` and the heartbeats' `link_notice` (`g_a7_read_vs_g_a5.diff`). Output
  in `record_read.json` and `record_read_console.txt`.

**The rows, as hashed:**

| row | read | |
| --- | --- | --- |
| Z1 configs by the drop-ins alone | at the suite's restart (21:04:57.2Z): `restart_fast_config` 0.75 / 2.0; **`restart_fast_unlock_config` `kill_grace_s` 0.1, `capture_bound_s` 0.3, `audio_join_cap_s` 10, `startup_check_s` 0.75**; `link_recovery_config` umbrella true, `implied` the six, `explicit` {}, `at` `import`, `reapply` []; the six module configs, none `ignored` | **met** |
| Z2 host gates | RetroArch 59.999; capture 59.998; dup+drop 0.1 / min; twelve lines in 57 / 57 | **met** |
| Z3 no Home press → no `restart_fast` row | 0 `restart_fast` / `_done` / `_audio_stop` / `_audio` / `_failed` rows | **met** (as expected) |
| Z4 no action without a stall | 0 `state_saved`, 0 holds, 0 stall rows; 0 client pauses | **met** |
| Z5 the link on 5 GHz | silences ≥ 250 ms **0.0 / 10 min** (0 in 673 s); hitch seconds **2.6 / 10 min** (3 s, longest run 1 s); 5180 MHz in 345 / 345 heartbeats, RSSI −68 / −69; **`link_notice` 0 in 345 / 345**, no notice row | stated (G-A5 0.89 / 6.1; CL-B14's sessions 0 / 0) |
| Z6 teardown | `session_end_bye` 21:18:52.513Z → `state_save_skipped` `client_bye` 21:18:53.197Z (401.1 ms) → `session_ended` 21:18:53.489Z; `input_hold_skipped_paused` after, no hold; after: `flags_absent`, twelve lines, `--check` ok, the properties empty | **met** |

**Other figures:** rendered 59.90 fps; post-FEC loss 29.7 / min in the suite's window (39.1 over the session; G-A5
51.2 / 59.7); 1 resync; 1 client session.

## 4. How to turn it off

1. Delete `~/.config/systemd/user/privyhub-companion.service.d/restart-fast-unlock.conf`.
2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
3. Take `RESTART_FAST_UNLOCK` out of `tools/e1_suite.py` `ADOPTED` (reverse `g_a7_applied.diff`); `e3_state.py` then
   reads ok on eleven.

With the flag off the host runs G-A5's worker (CL-B13 cell 1: the ready waits on the old audio's stop inside the
lock). The client has no half of its own here; the APK `fcd924c2…` is the same either way.

## 5. What stays open (to B)

- **The stray 8-byte packet** (CL-B14 §2): at each return the relay logged one 1-packet, 8-byte, unmarked "frame"
  within 1 ms of the old encoder's exit, 100-140 ms after the relay's stop. It was not in CL-B13, it is not a picture
  frame, and whether it reached the onn is not in the rows.
- `relay_stopped_ms` read 500 once at CL-B14 (50-214 at the others).
- Not exercised: the surface / process return paths.
- `ADOPTED_E3` in `tools/d7_regression.py` / `tools/c3_l4_nft_night.py` is left as it is (three names), as at
  G-A2..G-A5.
- Pausing at Home and keeping the rung, and the loss guard: the user's questions.

## 6. State (21:19:30Z, `check_end_state.json`, `check_end.json`)

- **TWELVE adopted lines; `--check` ok on twelve; APK `fcd924c2…` CONFIRMED.** The stack all `implied 1`.
- No `e3_flag.conf`, no game, no RetroArch, no encoder. One device paired. The band 5 GHz.
- **Units:** `privyhub-companion` and `privyhub-link-n1` only (`units_end.txt`). `privyhub-g-a7-window` exited and was
  collected.
- The seven client properties empty.
- No sudo, no nft. The Opal was untouched. adb for state reads only (`getprop`, `dumpsys wifi`, the CL-B4 reader). No
  address or identifier in any kept file (`redact_check.txt`). Nothing fetched or deleted. Nothing adopted but the
  twelfth line. Nothing committed. `logs/g_a7_git_status.txt`.

## 7. Files (`g_a7_2026-10-27/`)

- **The start:** `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `e3_check_before.txt`,
  `client_before.json`, `client_before_full.json`, `g_a7_state.py` (G-A5's reader, unedited but its docstring).
- **The patch:** `g_a7.diff` (from the patch file), `g_a7_applied.diff`, `predecessor_sha256.txt`, `after_sha256.txt`,
  `tests.txt`.
- **The drop-in and the restart:** `restart-fast-unlock.conf.copy`, `restart_at.txt`, `restart_config_rows.jsonl`,
  `check_after_restart.json`.
- **The window:**
  - `g_a7_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`, `tools_at_preregistration_sha256.txt`;
  - `g_a7_window.py`, `g_a7_window_vs_g_a5.diff`, `window_launched_at.txt`, `units_before_window.txt`,
    `window_console.txt`, `window_result.json`, `band.jsonl`, `state_midwindow.json`;
  - `runs/` (the suite's run, `logs_run1/` addresses masked);
  - `g_a7_read.py`, `g_a7_read_vs_g_a5.diff`, `record_read.json`, `record_read_console.txt`.
- `check_end_state.json`, `check_end.json`, `units_end.txt`, `redact_check.py` / `.txt`, `manifest.sha256`.
