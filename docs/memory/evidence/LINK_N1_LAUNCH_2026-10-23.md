---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: c47073d (uncommitted beside it; the user commits)
---

# LINK-N1 — the nightly watch on the 1-am quarter-hour, launched detached

**Classification: LAUNCHED** at 2026-10-23T16:10:56Z (a first launch at 16:08:07Z was stopped and relaunched, §3.6), as
the `systemd --user` transient unit **`privyhub-link-n1`**.
- It sleeps until **00:30 EDT = 04:30Z** each night and samples, with no stream, until 01:30 EDT = 05:30Z.
- **Its first sleep target is tonight, 2026-10-24T04:30:00Z.**
- It runs until the cap **2026-10-31T06:00:00Z** (written in its pre-registration) or the STOP file.
- This record covers the launch only. The nights' record is a later one-line task: **"read LINK-N1's nights"**.

Task: `handoffs/LINK-R1_5GHZ_CHECK_AND_NIGHTLY_WATCH_TASK.md`, Part 2, session A. Files: `link_n1_2026-10-23/`.
Part 1: `LINK_R1_5GHZ_CHECK_2026-10-23.md`.

## 1. How to read it, and how to stop it

- **Status:** `cat ~/privyhub_link_n1/status.txt`. One line holds the UTC time, what the watch is doing (sleeping
  until … / sampling night … / EXITED / CRASHED), the next night, the nights done, the last night's figures, the cap,
  and the stop command.
  - The line is rewritten at every transition and every 5 min. A timestamp older than ~6 min means the watch is not
    running.
- **Beside it:**
  - `~/privyhub_link_n1/watch.log`, and `journalctl --user -u privyhub-link-n1`;
  - the Opal sampler's raw (already redacted) output and its inventory, `~/privyhub_link_n1/opal_<date>.*`.
- **In the repo:**
  - `link_n1_2026-10-23/nights/<local date>.jsonl`, one per night;
  - `summary.md`, one row per night;
  - `watch_state.json`: the nights done, and the onn's station anchor as [epoch, connected time], no identifier.
- **Unit state:** `systemctl --user status privyhub-link-n1`.
- **Stop:** `touch ~/privyhub_link_n1/STOP`. It is checked every ≤ 30 s, including mid-night: the night in flight is
  closed and summarized, a final status line is written, and the watch exits. It never removes the file, so remove
  the file before any restart.
- **Restart** (nights already done are skipped):
  `systemd-run --user --unit=privyhub-link-n1 --collect -p WorkingDirectory=/home/privyhub/Projects/onn-stream-test /usr/bin/python3 /home/privyhub/Projects/onn-stream-test/docs/memory/evidence/link_n1_2026-10-23/link_n1_watch.py`
- **Linger is off** for the user. The unit lives as long as the user's login session, like the companion's; a logout
  or reboot ends it, and the restart above resumes it.
- **If the user is playing at 00:30-01:30 EDT,** the watch samples anyway (reads only) and every row carries
  `stream_active: true`. It never starts or stops a stream, restarts the companion, or launches a game.

## 2. What it reads each night (read-only; the pre-registration's §3)

- **Ping, hub → onn, once a second for the hour:** `ping -D -O -n -i 1 -W 2`, unprivileged (no sudo). The 1-s rows hold
  RTT ms and lost only.
  - A reply after ping's 1-s "no answer yet", but within 2 s, is kept as a separate `ping_late` row. The summary
    counts it as answered.
  - **The address, disclosed:** the task says to take it "from the companion's paired-device store". That store
    (`~/.config/privyhub/paired_devices.json`) holds no address, by G3-S1's design: id, name, key, permissions. The
    watch therefore reads the address from adb's device list, as E4-S4D did, **into memory only**. It is never
    written, and no row carries it.
- **The onn over adb, every 30 s (state reads only):**
  - `dumpsys wifi | grep -m1 '^mWifiInfo'`, parsed to frequency, band, channel, standard, RSSI, link / tx / rx speed;
  - `/proc/net/udp6` drops on the stream ports 48100 / 48101 if such a socket exists (D-BASE-P5's parse; the port role
    and drops only);
  - `/proc/uptime`.
  - No `adb connect`, no `setprop`, no write. **If adb drops overnight, the onn rows read empty.** The ping keeps the
    address held in memory.
- **The Opal, every 60 s:** LINK-R1's copy of B's `o1_opal_sample.sh` on `wlan1`, read-only; every byte goes through
  `o1_redact.py` and `o1_parse.py`.
  - Each round is kept whole (channel, utilization, noise, every station's labelled row).
  - The onn's station is marked per round: by **connected-time continuity** from the anchor, which was seeded from
    LINK-R1's last round, where the station carrying the stream's 8.8 Mbit/s was the onn. If continuity is lost (the
    onn reassociated), it falls back to **the closest tx / rx rate and signal** to the onn's own adb read. The method
    is recorded in every round.
- **The hub:** `/proc/loadavg` every 30 s.
- **The summary row:**
  - ping loss %, RTT p50 / p95 / max, the longest run of lost pings and when;
  - RSSI min / median, the tx-rate minimum and when, the bands;
  - the Opal's rounds (with the onn marked), and the onn station's retry rate over the hour;
  - any `stream_active` span.

## 3. What was done

1. **`link_n1_watch.py`** was written new for this task. It reuses E4-S4D's ping parse and status-line pattern, and
   D-BASE-P5's `udp6` parse; it imports `tools/e1_suite.py` only for `games_status`.
2. **The pre-registration** `link_n1_preregistration.txt`, sha256 **`23e8953c…bed2`**, hashed 16:05:43Z:
   - the cap line `CAP_UTC: 2026-10-31T06:00:00Z`;
   - the schedule, the rows, the summary, the reading.
   - The runner refuses to start without the hash. The tool hashes are in `tools_at_preregistration_sha256.txt`.
   - **Disclosed in it:**
     - the address source (above);
     - **the cap admits 8 windows** (local dates 10-24 … 10-31; the last ends 05:30Z), where the task names 7 nights.
       The cap as written governs, and an 8th night is reported like the others.
     - EDT holds through every window (it ends 2026-11-01). The UTC target is computed with `zoneinfo`, not
       hard-coded.
3. **The dry run** ran as the unit `privyhub-link-n1-dry` (`--wait --collect`; 2 min 6 s; exit 0), so the unit's
   environment was tested too (`dry_run/`):
   - **122 pings:** 1 lost (the first), RTT p50 4.97 / p95 166 / max 212 ms;
   - **4 onn reads:** 5 GHz, RSSI −66…−67, tx ≥ 260, no PrivyHub `udp6` socket (no stream);
   - **2 Opal rounds,** both with the onn marked by continuity;
   - the summary row written;
   - `redact_check.txt`: no IPv4 / MAC / IPv6 in any file.
4. **The launch** (16:10:56.7Z; `launched_at.txt`, `launch_console.txt`):
   `systemd-run --user --unit=privyhub-link-n1 --collect -p WorkingDirectory=<repo> /usr/bin/python3 …/link_n1_watch.py`.
5. **Confirmed up** (`first_status.txt`, `unit_status_after_launch.txt`): `active (running)` since 12:10:56 EDT.
   The status line read:

   ```
   2026-10-23T16:10:56.931Z | doing: sleeping until 2026-10-24T04:30:00.000Z (2026-10-24 00:30 America/New_York, UTC-0400) | next: night 2026-10-24: sample 04:30-05:30Z | nights done: 0 | last: - | cap 2026-10-31T06:00:00Z | stop: touch ~/privyhub_link_n1/STOP
   ```
6. **The first launch, and why it was relaunched (disclosed).**
   - The first launch, at 16:08:07Z, came up sleeping toward the same 04:30Z target (`launched_at_first.txt`,
     `launch_console_first.txt`, `first_status_first_launch.txt`).
   - Re-reading the driver afterwards showed that the STOP file was checked only between nights and while sleeping.
     **A STOP touched during a night would have waited for the hour to end.** The pre-registration says "checked every
     <= 30 s".
   - The driver gained `stop_watch()`. It sets the stop event within ~10 s of the file or the cap, so a night in
     flight is closed and summarized.
   - The unit was then stopped (`systemctl --user stop`, while sleeping; no night had begun) and relaunched with the
     same command at 16:10:56Z.
   - The pre-registration text and its hash are unchanged. `tools_at_preregistration_sha256.txt` now holds the
     amended driver (`f4f3ce5a…`); the first launch's list is kept as `tools_at_preregistration_sha256_first_launch.txt`
     (`c02caa67…`).
   - The dry run ran on the first driver, and the change touches only the stop path. **The mid-night STOP itself is
     not exercised:** testing it would mean touching and then removing the STOP file, and nothing is deleted.

## 4. The reading, as pre-registered

- **If something recurs:** ping loss / RTT spikes, an RSSI dip, a tx-rate collapse or an Opal retry rise recurring in
  the same minutes on ≥ 2 of the nights means **the hour has a cause on the air or the onn, and its minute is known**.
  The next task is then to name the device (the user's hand; the Opal's client list at that minute, read-only).
- **If nothing recurs with no stream,** the 1-am pattern either needed a stream to show, or was the 2.4-GHz band.
  - If it needed a stream, the watch becomes "the link report on during every play session". That is in force on the
    client after LINK-R1; the host keeps the keys only in a run with `PRIVYHUB_LINK_REPORT=1`.
  - Whether it was the 2.4-GHz band: LINK-R1 Part 1's 0 silences in 10 min point there.

## 5. State

- Eight adopted lines, no `e3_flag.conf`, `--check` ok. Units: the companion and `privyhub-link-n1`.
- `debug.privyhub.link_report` = 1 on the onn (LINK-R1 §6).
- No sudo, no nft. The Opal is read-only. adb is used for state reads only.
- No addresses or identifiers in any kept file. Nothing fetched, deleted, adopted or committed.
- `logs/link_n1_launch_git_status.txt`. `link_n1_2026-10-23/manifest.sha256` covers the launch files; the files the watch keeps
  writing (`nights/`, `summary.md`, `watch_state.json`) are outside it. `redact_check.txt`: 0 hits.
