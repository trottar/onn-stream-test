---
memory_schema: 1
as_of: 2026-10-26
baseline_commit: 06c565e (CL-B13 committed; "G-A5 handoff and queue I"; G-A5 uncommitted beside it; the user commits)
---

# G-A5 — `PRIVYHUB_RESTART_FAST=1` ADOPTED: the eleventh adopted line; the confirmation window VALID, every row met; G-A6 SHELVED

**Classification: ADOPTED (the user's decision, 2026-10-26, "Go", after CL-B13). The adopted environ is ELEVEN lines.**
- The confirmation window was VALID, with the host gates met: one E1-SNES-STREAM, **no `e3_flag.conf`, no client
  property set**, the eleven lines alone, 5 GHz throughout.
- **The configs by the drop-ins alone:** `restart_fast_config` (`startup_check_s` 0.75, `lock_wait_s` 2.0) and B21's
  `link_recovery_config` (`implied` the six, `explicit` {}, `at` `import`, `reapply` []).
- **No `restart_fast` row**, as pre-registered: there was no Home press, and the flag acts only on a guarded start.
- **No action without a stall:** 0 `state_saved`, 0 holds, 0 stall rows.
- **The link:** silences ≥ 250 ms 0.89 / 10 min (one of 297 ms); hitch seconds 6.1 / 10 min.
- **The teardown:** `session_end_bye`, then `state_save_skipped` `client_bye` (401.5 ms), no hold.
- **G-A6 (`PRIVYHUB_LINK_RECOVERY_WAN`) SHELVED** by the same decision (§6). It stays built and off.
- Nothing else adopted. Nothing committed.

Task: `handoffs/G-A5_RESTART_FAST_ADOPTION_TASK.md`, session A. **No patch was prepared by B,** so A wrote the
adoption in G-A4's applied form: `patches/G-A5_RESTART_FAST_ADOPTION.md`. The behaviour was measured in
`CL_B13_RESTART_FAST_AND_WAN_CLASS_2026-10-25.md` (§2, §5). Files: `g_a5_2026-10-26/`.

## 1. Precondition (`check_before.json`)

- **The first read, 02:59:20Z: the onn on 2.4 GHz** (2412 MHz, Wi-Fi 4; three re-reads to 02:59:50Z the same,
  `adb_band_rereads.txt`). **Stopped there, nothing changed.** The user moved it ("Should be good now").
- **The read at 03:06:22Z:**
  - `tools/e3_state.py` ok on ten, **APK `6bddafc0…a927` CONFIRMED**; no `e3_flag.conf`, no game, RetroArch or
    encoder;
  - one device paired (`client_before.json`, booleans and counts); the client on the LAN (the newest `token_issued`
    `routing_evidence` lan, Hub host empty);
  - **the band 5 GHz** (5180 MHz, standard 5, RSSI −68); the seven client properties empty;
  - units: `privyhub-companion` and `privyhub-link-n1` only;
  - **the clock 03:06Z**, before the 03:40Z cut-off. The restart and the window ended at 03:22Z, before 04:15Z.
- **HEAD `06c565e`** ("G-A5 handoff and queue I"), CL-B13 committed. `git status --short` printed only this task's new
  dir (made just before the read). The prompt and the task file are tracked, unmodified.

## 2. The adoption

1. **The diff, written first** as `docs/memory/patches/G-A5_RESTART_FAST_ADOPTION.md` (the diff and the predecessor
   sha256s inside). `g_a5.diff` was extracted from the patch file and compared byte-equal with the scratch diff.
   `git apply --check -p1`, then `git apply -p1`: 4 files, +10 / −5 (`g_a5_applied.diff`; `predecessor_sha256.txt` →
   `after_sha256.txt`).
   - `tools/e1_suite.py`: the comment `G-A5 (adopted 2026-10-26, the user)`; `RESTART_FAST` defined and in
     `ADOPTED` (**eleven**); the preflight's `drop_in_restart_fast` and its `ok` term.
   - `tools/e3_state.py` (since G-A5, eleven … the fast restart), `tools/e1_remote.py`, `tools/test_e1_remote.py`:
     wording only.
   - `git diff --check` was clean.
2. **Tests from the tree, green** (`tests.txt`):
   - `e1_suite.py --self-test`: `E1_SUITE_SELF_TEST_OK`;
   - `test_e1_remote` 21 OK; `test_c3_l4_nft_night` 33 OK;
   - `tests/restart_fast` 13 OK; `tests/link_recovery` `test_config_row` 9 OK + `test_link_recovery` 7 OK.
3. **The drop-in**, written with the file tool:
   `~/.config/systemd/user/privyhub-companion.service.d/restart-fast.conf` (`restart-fast.conf.copy`):

   ```
   [Service]
   Environment=PRIVYHUB_RESTART_FAST=1
   ```

4. **`systemctl --user daemon-reload && systemctl --user restart privyhub-companion`**, a separate command, at
   **03:07:29Z** (active).
   - The recovery log carried `link_recovery_config` (B21's row), **`restart_fast_config` 0.75 / 2.0** and the module
     configs at 03:07:30Z (`restart_config_rows.jsonl`).
5. **The environ read back ELEVEN lines** (`check_after_restart.json`):
   1. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`
   2. `PRIVYHUB_AUDIO_CODEC=opus`
   3. `PRIVYHUB_EPG_GUIDE_INDEX=cached`
   4. `PRIVYHUB_LINK_RECOVERY=1`
   5. `PRIVYHUB_LINK_REPORT=1`
   6. `PRIVYHUB_OVERLAY_PROVIDER=tailscale`
   7. `PRIVYHUB_RECOVERY_TRIGGER=v2`
   8. **`PRIVYHUB_RESTART_FAST=1`**
   9. `PRIVYHUB_SESSION_IDENTITY=v2`
   10. `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`
   11. `PRIVYHUB_SNES_CORE=snes9x`
   - **`--check` ok on eleven:** `drop_in_restart_fast` true, APK CONFIRMED, `link_recovery.stack` all six `implied 1`.

## 3. The confirmation window

- **Pre-registration** `g_a5_preregistration.txt`, sha256 **`f96bb119…384f`**, hashed at 03:08:19Z, before the run.
  The tools were hashed then too (`tools_at_preregistration_sha256.txt`).
- **The run:** `g_a5_window.py` (G-A4's runner for eleven lines) as the transient unit `privyhub-g-a5-window`
  (`--collect`), 03:08:19-03:22:32Z. It called the suite's own CLI: `run --only E1-SNES-STREAM --runs 1 --window 600
  --gap 120 --e2`. There was **no `--plan`, no `e3_flag.conf`, no `setprop`**, and the pad was not touched.
  - **PLAYING at 03:10:44Z, attempt 1**, 5.1 s. The session ran 03:10:44.7-03:22:16.9Z (11.54 min); the suite's window
    was 03:12:14-03:22:14Z.
- **The environ:** eleven lines, equal to the new `ADOPTED`, in **57 of 57** reads (every 15 s). After the run: eleven
  lines, `flags_absent` true, `--check` ok (`window_result.json`).
- **The band:** 29 of 29 reads at 5180 MHz (`band.jsonl`). Mid-window (03:15:22Z, `state_midwindow.json`): the stack
  all `implied 1`, eleven lines, the seven properties empty.
- **The reader:** `g_a5_read.py`. It is G-A4's reader (B6's `measure` and UX-R3's `evening` / `counts`, unedited and
  pin-asserted) plus `restart_fast_config` and the `restart_fast*` rows. Output in `record_read.json` and
  `record_read_console.txt`.

**The rows, as hashed:**

| row | read | |
| --- | --- | --- |
| Z1 configs by the drop-ins alone | `restart_fast_config` 0.75 / 2.0; `link_recovery_config` umbrella true, `implied` the six, `explicit` {}, `at` `import`, `reapply` []; `input_hold_config` 250, `_b6` 950, `_b8`, `_rewind` 30 + `_cores` mode `state`, `stall_signal_config` 400, `stall_resume_config` `fast_ready` / `save_from_signal` true; none `ignored` | **met** |
| Z2 host gates | RetroArch 59.999; capture 59.998; dup+drop 0.1 / min; the ladder at 7000 throughout; eleven lines in 57 / 57 | **met** |
| Z3 no Home press → no `restart_fast` row | 0 `restart_fast` / `_done` / `_failed` rows | **met** (as expected) |
| Z4 no action without a stall | 0 `state_saved`, 0 holds, 0 stall rows; 0 client pauses | **met** |
| Z5 the link on 5 GHz | silences ≥ 250 ms **0.89 / 10 min** (1 in 672 s, 297 ms); hitch seconds **6.1 / 10 min** (7 s, longest run 2 s); 5180 MHz in 345 / 345 heartbeats, RSSI −69 / −70 | stated (G-A4 0 / 0; CL-B13 cells 1-2: 0-3.2 / 0-17.5) |
| Z6 teardown | `session_end_bye` 03:22:16.059Z → `state_save_skipped` `client_bye` 03:22:16.808Z (401.5 ms) → `session_ended` 03:22:16.939Z; no hold; after: `flags_absent`, eleven lines, `--check` ok, the properties empty | **met** |

**Other figures:** rendered 59.85 fps; post-FEC loss 51.2 / min in the suite's window (59.7 over the session; G-A4
13.8, CL-B13 cell 2 49.9); 1 resync; 1 client session.

## 4. How to turn it off

1. Delete `~/.config/systemd/user/privyhub-companion.service.d/restart-fast.conf`.
2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
3. Take `RESTART_FAST` out of `tools/e1_suite.py` `ADOPTED` (reverse `g_a5_applied.diff`); `e3_state.py` then reads
   ok on ten.

With the flag off, the APK `6bddafc0…` behaves as CL-B13 cell 2 (B17's order, no `restart_fast` key; the picture back
6.7-7.5 s after a Home return). The client half has no property of its own: it is armed only by the host's response
key, inside `restart_guard` (`debug.privyhub.restart_guard 0` turns the guard and it off).

## 5. What stays open (to B)

- **The slow return:**
  - CL-B13's return 1 took 3.12 s: the old audio's stop took 2.2 s inside the worker, and the ready waits on the lock;
  - the old encoder's last frame at +0.35 / +0.39 s at two returns.
  - The user accepted these with the adoption; B has them (queue I).
- Not exercised: the surface / process return paths.
- `ADOPTED_E3` in `tools/d7_regression.py` / `tools/c3_l4_nft_night.py` is left as it is (three names), as at
  G-A2..G-A4.

## 6. G-A6 shelved

- **The decision (the user, 2026-10-26):** shelve G-A6. `PRIVYHUB_LINK_RECOVERY_WAN=1` (B23) is not adopted.
  `companion/link_recovery_wan.py` stays in the tree, built and off (absent = nothing imported).
- **The reason** (CL-B13 §4-§5):
  - the class reads the onn on the home Wi-Fi through the overlay as `remote-direct`. It cannot tell a direct path
    across the internet from the home radio, so on the bench 450 held falsely once (the guard then reverted the
    session);
  - it gains at most ~0.5 s per real drop (the hold at 450 instead of 950).
- **What would reopen it:**
  - a way to tell a remote path from the home radio (for example, the client's own report of the network it is on);
  - off-site data on a relayed path (WAN-R1: 0.5 min).

## 7. State (03:22:53Z, `check_end.json`)

- **ELEVEN adopted lines; `--check` ok on eleven; APK `6bddafc0…` CONFIRMED.** The stack all `implied 1`.
- No `e3_flag.conf`, no game, no RetroArch, no encoder. One device paired.
- **Units:** `privyhub-companion` and `privyhub-link-n1` only. `privyhub-g-a5-window` exited and was collected.
- The seven client properties empty. The band 5 GHz.
- No sudo, no nft. The Opal was untouched. adb for state reads only (`getprop`, `dumpsys wifi`, the CL-B4 reader). No
  address or identifier in any kept file (`redact_check.txt`). Nothing fetched or deleted. Nothing adopted but the
  eleventh line. Nothing committed. `logs/g_a5_git_status.txt`.

## 8. Files (`g_a5_2026-10-26/`)

- **The start:** `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `client_before.json`,
  `adb_band_rereads.txt`, `g_a5_state.py` (G-A4's reader plus the routing class).
- **The patch:** `g_a5.diff` (from the patch file), `g_a5_applied.diff`, `predecessor_sha256.txt`, `after_sha256.txt`,
  `tests.txt`.
- **The drop-in and the restart:** `restart-fast.conf.copy`, `restart_at.txt`, `restart_config_rows.jsonl`,
  `check_after_restart.json`.
- **The window:**
  - `g_a5_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`, `tools_at_preregistration_sha256.txt`;
  - `g_a5_window.py`, `window_launched_at.txt`, `units_before_window.txt`, `window_console.txt`, `window_result.json`,
    `band.jsonl`, `state_midwindow.json`;
  - `runs/` (the suite's run, `logs_run1/` addresses masked);
  - `g_a5_read.py`, `record_read.json`, `record_read_console.txt`.
- `check_end.json`, `redact_check.py` / `.txt`, `manifest.sha256`.
