---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G8-S1 resume (session A): relaunch the detached envelope driver for the 17 cells not run (6–22), as the partial record's §6 describes — the STOP file removed, a new cap, the same unit name, the pre-registration unchanged. Code launches, confirms the first resumed cell, and exits. Session B runs software tasks in parallel (QUEUE_2026-10-17). Measurement only; nothing adopted; nothing committed
---

# G8-S1 — resume

Read first: `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-16.md` §6 (the resume: the driver skips the cells in `done`; what a resume needs), `G8_S1_LAUNCH_2026-10-16.md` (the launch command, the status file, the busy skip), `G4_S1_…` §8 (adb to the onn was lost when it changed networks).

## 1. Precondition

1. **adb back to the onn:** reconnect as earlier sessions did (the stored LAN host; never written anywhere), then `tools/e3_state.py --check` **ok**: the seven adopted lines, no `e3_flag.conf`, no game, no stream, one device paired, APK CONFIRMED (`59f736d2…`). If adb cannot reach the onn, stop and tell the user: the onn must be on the home Wi-Fi with the app installed; nothing else is changed.
2. `~/privyhub_g8_s1/status.txt` reads `EXITED (the stop file)`; `g8_s1_state.json` `done` holds the five cells, all `valid`; `systemctl --user status privyhub-g8-s1` → not found. Session B's status (`SESSION_B_STATUS.txt`) is read and quoted; B never restarts the companion, so it does not block this.

## 2. The two disclosed changes

1. **Remove `~/privyhub_g8_s1/STOP`** (the driver never removes it; present, it exits at once). Record the removal time.
2. **The cap:** `CAP` in `g8_s1_2026-10-16/g8_s1_driver.py` from `2026-10-17T06:00:00Z` to **`2026-10-17T14:00:00Z`** — one constant, nothing else. The diff to `g8_s1_resume_driver.diff`; the driver's new sha256 beside the old one in `tools_at_preregistration_sha256_resume.txt`. **The pre-registration is unchanged** (its hash `b2e02fa0…dcf73` re-read); the suite's `--prereg` check still passes.

## 3. Launch

- The same command as the launch record §4: `systemd-run --user --unit=privyhub-g8-s1 --collect -p WorkingDirectory=<repo> /usr/bin/python3 -B …/g8_s1_driver.py`; not a child of this session.
- Wait for the first resumed cell's status line — **cell 6 (loss-5, on)** — up to 15 min; `systemctl --user status` into the resume record. If the status line names a cell other than 6, or the driver exits, write what it says and stop.
- **Note for the record:** session B edits companion modules behind flags while this driver restarts the companion once per cell; flag absent = inert by B's proof, but a cell that fails validity during the night is read against B's status file's timestamps before anything else is blamed. The driver's own validity rule (replace once) stands.

## 4. Write and exit

`evidence/G8_S1_RESUME_2026-10-17.md` (precondition, the two changes, the launch, cell 6's status line, the expected end — 17 × ~14.6 min from the launch), `logs/g8_s1_resume_git_status.txt`, the redactor over what this session wrote; `CURRENT.md` Next Action: "G8-S1 resumed; its final record when it ends (`cat ~/privyhub_g8_s1/status.txt`); B's queue; the user's commit". **Exit**; do not wait for the driver. The envelope's final record is a later one-line task over all 22 cells.

No sudo (systemd --user is not sudo), no nft, the Opal read-only, adb only to reconnect and read state, no addresses or identifiers anywhere; nothing fetched, nothing deleted; nothing adopted; nothing committed.
