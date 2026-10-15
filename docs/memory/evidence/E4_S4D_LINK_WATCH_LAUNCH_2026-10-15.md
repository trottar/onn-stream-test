---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 7331184 (E4-S1..S5D uncommitted)
---

# E4-S4D — the link watch, launched detached

**Classification: LAUNCHED** (2026-10-15 21:41:41Z). E4-S4C's link
watch, and its grab-deferral set on the first clean window, now runs as
the `systemd --user` transient unit **`privyhub-link-watch`**. It does
not live inside a Code session.

- It probes every 45 min until **2026-10-20T04:00:00Z**, or until the
  stop file appears.
- This record covers the launch only. The watch's own record is a later
  one-line task: "write E4-S4C's record from the watch's files".

Task: `handoffs/E4-S4D_LINK_WATCH_DETACHED_TASK.md`, session A item 2
of `QUEUE_2026-10-15.md`. Files: `e4_s4d_2026-10-15/`.

## 1. How to read it, and how to stop it

- **Status:** `cat ~/privyhub_link_watch/status.txt`. One line holds:
  - the UTC time, the probe number;
  - the last result (loss/min, rendered, resyncs, clean / dirty / busy /
    no_play);
  - what it is doing and what comes next, and when;
  - the deferral set's progress (`control: -, conc1: -, conc2: -,
    conc150: -`);
  - the adopted state (`adopted5 ok`), the cap, and the stop command.
- **Idle or dead:** the line is rewritten after every probe and run, and
  every 5 min as a heartbeat.
  - A timestamp older than ~6 min means the watch is not running.
  - `CRASHED: …` or `EXITED (…)` on the line says why it stopped.
- **Beside it:** `history.csv` (one row per probe, E4-S4C's fields) and
  `watch.log`.
  - The probe directories are `probe_<n>/`, outside the repo.
  - The log also goes to the journal:
    `journalctl --user -u privyhub-link-watch`.
- **In the repo:** `e4_s4d_2026-10-15/` holds:
  - `link_watch.jsonl`, `ping.jsonl` (60-s bins), `watch_state.json`,
    `deferral.json`;
  - `probes/<n>/` (summary, encoder, title);
  - `runs/` (the control and the flagged runs, in full).
- **Unit state:** `systemctl --user status privyhub-link-watch`.
- **Stop:** `touch ~/privyhub_link_watch/STOP`.
  - The probe or run in flight finishes with its own teardown.
  - A final status line is written, then the watch exits.
  - The watch never removes the file, so remove it before any restart.
- **Restart (resumes from `watch_state.json`):**
  `systemd-run --user --unit=privyhub-link-watch --collect -p WorkingDirectory=/home/privyhub/Projects/onn-stream-test /usr/bin/python3 /home/privyhub/Projects/onn-stream-test/docs/memory/evidence/e4_s4d_2026-10-15/e4_s4d_watch.py`
- **Busy:** if a game session is active at probe time (the user
  playing), the probe is skipped and logged `busy`. The ping trace
  continues through it.
- **Linger is off** for the user. The unit lives as long as the user's
  login session does, like the companion's own unit. A logout or reboot
  ends it, and the restart above resumes it.

## 2. What was done

1. **The driver.** `e4_s4d_watch.py` is `e4_s4c_watch.py` plus E4-S4D's
   changes (diff: `e4_s4d_watch_vs_e4_s4c.diff`). The probe, readings,
   gates, deferral runs, bar and storage are unchanged. The changes:
   - the status line and its 5-min heartbeat;
   - `history.csv`, and `watch.log` beside the journal;
   - the STOP file, checked between probes and runs and during the
     guide-read wait;
   - the busy skip;
   - the cap `2026-10-20T04:00:00Z`;
   - the adopted state read back at start and after each probe: the
     suite's preflight, five lines;
   - a crash written to the status line;
   - `--dry`.

   O1's sampler (`o1_opal_sample.sh`, `o1_redact.py`, `o1_parse.py`) and
   D-BASE P4's `p4_harvest.py` are copied byte for byte from
   `e4_s4c_2026-10-10/`. The Opal stays read-only.
2. **The dry run**, twice, under `systemd-run --user
   --unit=privyhub-link-watch-dry`, so the unit's environment was tested
   too (`dry_run/`):
   - the preflight read the five-line state (`adopted5 ok`, no game);
   - the unprivileged ping ran (first bin: 56 sent, 0 lost);
   - the heartbeat rewrote the status line;
   - it exited after 2 min.
   - Between the two runs, one cosmetic change: the status line names the
     stop file as `~/…` instead of the absolute path. The hashed driver
     is the second dry run's.
3. **The pre-registration** (`e4_s4d_preregistration.txt`, made by
   `fill_preregistration.py`):
   - E4-S4C's draft §0-§9 verbatim, its placeholders filled with the
     sha256 of the files at the hash;
   - an E4-S4D addendum that governs where it differs: A the cap, B the
     stop file, C the busy skip, D the status file, E the five-line
     state, F the driver's sha256, G the execution.
   - **sha256 `334f714758bf5d77379d0c5152dc925ce522005f1579dd9165545e3597b1b738`**,
     hashed 2026-10-15T21:41:34Z (`.sha256`,
     `preregistration_hashed_at.txt`, `tools_at_preregistration_sha256.txt`).
   - The runner refuses to run without that hash.
4. **The launch** (21:41:41Z, `launch_console.txt`, `launched_at.txt`):
   `systemd-run --user --unit=privyhub-link-watch --collect -p WorkingDirectory=<repo> /usr/bin/python3 …/e4_s4d_watch.py`.
   - Not `nohup`, and not a child of the Code session.
   - Probe 1 started at once: next start = max(now, last + 45 min).
5. **The first probe's status line** (`first_probe_status.txt`):

   ```
   2026-10-15T21:51:10.895Z heartbeat | probe 1 | last: probe 1 loss/min 1645.01 rendered 56.08 resyncs 25 dirty (at 2026-10-15T21:51:10.893Z) | doing: idle | next: probe 2 at 2026-10-15T22:26Z | deferral: control: -, conc1: -, conc2: -, conc150: - [await_clean_probe] | state: adopted5 ok | cap 2026-10-20T04:00:00Z | stop: touch ~/privyhub_link_watch/STOP
   ```

   - Probe 1 was dirty: loss 1,645/min, rendered 56.08, resyncs 25.
   - RetroArch read 59.999 and host CPU 11.4 %.
   - The Opal gave 30 air rounds; client RSSI and ping were read.
   - `flags_absent` was true in the run and at the end.
   - Probe 2 is due at 22:26Z.
   - `systemctl --user status privyhub-link-watch` at that moment
     (`unit_status_after_first_probe.txt`): active (running) since
     21:41:41Z, 27.6M memory.

## 3. State

- The five-line adopted state (E4-S5D), with the watch running on it.
  `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1` is set by the watch only, for
  its flagged runs, through `e3_flag.conf`, which is removed at each
  teardown.
- Nothing adopted by this task. Nothing committed.
- No sudo, no nft. No addresses or identifiers written: the client's
  address is read from adb into memory only.
- `logs/e4_s4d_git_status.txt`; `redact_check.txt`.
