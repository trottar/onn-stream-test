---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: c47073d (UX-R4 committed; this record uncommitted beside it; the user commits)
---

# LINK-R1 — the 5-GHz check: MEASURED, valid; 0 uplink silences ≥ 250 ms and 0 hitch seconds in 10 min on 5 GHz; E2 met

**Classification: MEASURED, one window, valid, host gates met.** The onn was on **5 GHz** (5180 MHz, channel 36,
802.11ac) in all 346 heartbeats. **Uplink silences ≥ 250 ms: 0 per 10 min.** The 2.4-GHz baselines were BENCH-R3 C
22.4 and BENCH-R1 cell 8 15.6. **Hitch seconds: 0 per 10 min** (C: 19.9). Post-FEC loss was 4.9 per minute (C: 33).
Rendered 59.98 fps.

The pre-registered reading applies as written: **the band was most of the room-independent flapping**. The stack's H
can be re-derived from the 5-GHz distribution (a B task). The caveats are in §5: one window, a daytime hour, and a
different drop-in from C.

The Opal's 5-GHz radio now lists the onn's station, which it did not in any of BENCH-R3's 18 rounds:
- signal −76 dBm median at the AP (the onn reads −68 at its end);
- the AP's tx rate 30-433 Mbps, moving round to round;
- **8.0 % tx retries** over the session.

`debug.privyhub.link_report` is **LEFT at 1** on the onn (§6). Nothing adopted. Nothing committed.

Task: `handoffs/LINK-R1_5GHZ_CHECK_AND_NIGHTLY_WATCH_TASK.md`, Part 1, session A. Files: `link_r1_2026-10-23/`.
Part 2, the nightly watch, is `LINK_N1_LAUNCH_2026-10-23.md`.

## 0. Precondition (15:45-15:47Z)

- **adb was not connected at the start.** The band change had dropped it.
  - It was reconnected by hand from the hub: the one neighbour-table entry with tcp/5555 open, then
    `adb connect <it>:5555`.
  - The endpoint was never printed (the helper prints counts and states only).
- **`tools/e3_state.py`: ok** (`check_before.json`):
  - eight adopted lines;
  - no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game, RetroArch or encoder;
  - **APK `bf5114a2…cf73` CONFIRMED**.
- **One device paired**, no active session (`session_status_before.json`, counts only).
- **No `privyhub-*` unit but the companion.**
- **HEAD `c47073d`.** The tree was clean except the prompt and the task file (`git_status_at_start.txt`).
- **The onn over adb** (`dumpsys wifi`, the `mWifiInfo` line parsed in memory; `adb_reads/wifi_before_window.json`;
  SSID / BSSID / MAC / IP not kept):
  - 5180 MHz, **5 GHz, channel 36**, Wi-Fi standard 5 (802.11ac);
  - RSSI −68 dBm;
  - tx 130 / rx 117 Mbps (max supported 866 / 866).
  - **The band read 5 GHz, so the run went ahead.**
- **`debug.privyhub.link_report`:** `""` → `setprop … 1` at 15:47:27Z → `"1"` (`adb_reads/link_report_property.txt`).
- In the watch's dry run, the onn's `/proc/uptime` read ~5,150 s at 16:06Z. So the onn last booted ~14:40Z, before
  this session.

## 1. The window

- **Pre-registration:** `link_r1_preregistration.txt`, sha256 **`eafb6ace…59a7`**, hashed 15:49:51Z, before the
  window. The tools' hashes are in `tools_at_preregistration_sha256.txt`.
- **The run:** `link_r1_window.py` started the Opal sampler and then ran one **E1-SNES-STREAM** through
  `link_r1_suite_call.py` (BENCH-R3's wrapper; only the pre-registration name changed). It used `run_suite`
  unedited, with runs 1, window 600, gap 120 and e2 on.
  - The suite launched the title: PLAYING at **15:52:18Z**, attempt 1, 3.1 s.
  - The window ran 15:53:48.7-16:03:48.7Z.
  - The client session ran 15:52:18.4-16:03:50.1Z (11.53 min).
- **The drop-in `e3_flag.conf` = `PRIVYHUB_LINK_REPORT=1` only.**
  - **Nine lines were read back** in 57 of 58 environ reads (every 15 s; the first read was before the restart).
  - **After the run:** eight lines, the drop-in removed, `flags_absent` true (`runs/final_state.json`).
- **The Opal:** B's copy of `o1_opal_sample.sh` from BENCH-R3, byte for byte with `o1_redact.py` / `o1_parse.py`
  (same sha256).
  - It sampled `wlan1` every 60 s: **15 rounds**, 15:50:00-16:04:00Z, exit 0.
  - Read-only; every byte went through `o1_redact.py`.
- **The reader:** `link_r1_read.py` (`record_read.json`, `record_read_console.txt`).
  - B6's `gap_distribution.py` `measure` and UX-R3's `evening` / `counts` are exec'd unedited; their sha256s are
    asserted against the hashed list.
  - Heartbeats are placed by BENCH-R3's map: sequence order, the client's elapsed time on the host clock. There was
    one client session, and no heartbeat arrived > 2 s late.

## 2. Validity and the host gates

| | value |
| --- | --- |
| outcome | playing, attempt 1, 3.1 s to PLAYING; valid |
| environ at stream / after | 9 (with `PRIVYHUB_LINK_REPORT=1`) / 8; `flags_absent` true |
| RetroArch fps | 59.999 |
| capture fps / dup+drop per min | 59.995 / 0.1 |
| the ladder (status poll) | 7000 kbit/s throughout (min = max = 7000) |
| rendered fps (heartbeat) | 59.977 |
| post-FEC loss | **4.9 / min** over the session (57 `lost_packets` in the client report; the suite's window read 2.3 / min); resyncs 0 |
| max output gap | **120 ms** |
| stale drops / ≥ 50-ms / ≥ 80-ms spikes | 2.6 / min / 36 / 24 per session |
| audio underruns (report) / audio lost | 6 / 0 |
| host CPU / encoder / RetroArch | 8.2 % / 28.7 % / 9.4 % (RSS 144 MB) |
| client pauses | 0; recovery log: `session_started`, `session_ended` only |

## 3. The silences, the hitches, the link

**Uplink silences ≥ 250 ms (B6's `measure`, 672 streaming s):**
- **0 silences: 0.0 per 10 min**, every bin 0, max 0 ms.
- `native_stream_ctrl_gaps.log` holds **no row** in the session.
- That log is on: `PRIVYHUB_RECOVERY_TRIGGER=v2` is adopted, and the log holds 1,136 rows from earlier sessions, the
  last at 2026-10-23T05:06Z. The 0 is a reading, not a missing log.

| | silences ≥ 250 / 10 min | hitch s / 10 min | post-FEC loss / min | band |
| --- | --- | --- | --- | --- |
| **LINK-R1 (this)** | **0.0** (0 of 0 bins) | **0.0** (longest 0) | **4.9** | 5 GHz ch 36, 11ac |
| BENCH-R3 C (2026-10-22 20:53Z) | 22.4 (25; 250-300 15 · 300-400 7 · 400-500 3) | 19.9 | 33 | 2.4 GHz ch 1, 11n |
| BENCH-R1 cell 8 (`08_none_hold`) | 15.6 | — | — | 2.4 GHz |

**The link report** (all 346 in-session heartbeats carried all five keys):
- **frequency 5180 MHz in 346 of 346; standard 5 (802.11ac) in 346.**
- **RSSI:** −68 dBm (314), −69 (32). On 2.4 GHz in BENCH-R3 it was −67…−70, median −68. So the onn's RSSI is
  unchanged.
- **tx Mbps:** 195 (308), 260 (23), 130 / 175 / 234 (5 each). There is **no heartbeat ≤ 54**; on 2.4 GHz, 1.7 % read
  27-54.
- **rx Mbps:** 117 (317), 234 (11), 175 (7), 58 (6), 87 (4), 29 (1). On 2.4 GHz, 5 % read 6-27.

| min (UTC) | hb | MHz | std | RSSI med / min | tx med / min | rx med / min | post-FEC lost | FEC-unrec | fps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15:52 | 23 | 5180 | 5 | −68 / −69 | 195 / 130 | 117 / 29 | 30 | 0 | 59.9 |
| 15:53 | 30 | 5180 | 5 | −68 / −69 | 195 / 175 | 117 / 58 | 4 | 1 | 60.0 |
| 15:54 | 30 | 5180 | 5 | −68 / −69 | 195 / 175 | 117 / 117 | 1 | 0 | 60.0 |
| 15:55 | 30 | 5180 | 5 | −69 / −69 | 195 / 130 | 117 / 58 | 2 | 1 | 60.0 |
| 15:56 | 29 | 5180 | 5 | −68 / −68 | 195 / 195 | 117 / 58 | 0 | 0 | 60.0 |
| 15:57 | 30 | 5180 | 5 | −68 / −68 | 195 / 130 | 117 / 117 | 2 | 1 | 60.0 |
| 15:58 | 30 | 5180 | 5 | −68 / −68 | 195 / 195 | 117 / 87 | 0 | 0 | 60.0 |
| 15:59 | 30 | 5180 | 5 | −68 / −68 | 195 / 195 | 117 / 117 | 0 | 0 | 60.0 |
| 16:00 | 30 | 5180 | 5 | −68 / −68 | 195 / 195 | 117 / 117 | 4 | 1 | 59.9 |
| 16:01 | 30 | 5180 | 5 | −68 / −68 | 195 / 195 | 117 / 117 | 5 | 1 | 60.0 |
| 16:02 | 30 | 5180 | 5 | −68 / −68 | 195 / 175 | 117 / 87 | 7 | 1 | 59.9 |
| 16:03 | 24 | 5180 | 5 | −68 / −68 | 195 / 195 | 117 / 117 | 2 | 1 | 60.0 |

(15:52's 30 lost are the stream's first seconds.)

## 4. The Opal's 5-GHz view

**The radio:** `wlan1`, channel 36, 80 MHz.
- Utilization 3.3-10.0 % (median 6.6).
- Noise −82…−90 dBm.
- 0 log events in all 15 rounds.

**The station:**
- **One station associated in every round.** It is the onn's, told by behaviour, not by identifier: its AP→station
  bytes rose from 0.02-0.05 to **8.8 Mbit/s** while the stream ran (O1's method).
- It was followed between rounds by connected-time continuity. It had been connected ~22 min at 15:50Z, which fits
  the user's swap.
- **The onn's station per round** (deltas to the next round; `tx failed` moves with `tx retries` on this driver, as
  O1 found, so it is not a separate figure):

| round (UTC) | in session | signal / avg dBm | AP tx Mbps (MCS, NSS, MHz) | AP rx Mbps | AP→onn Mbit/s | tx pkts Δ | retries Δ | retry rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15:50 | – | −76 / −77 | 117 (1, 2, 80) | 260 | 0.02 | 174 | 1 | 0.6 % |
| 15:51 | – | −76 / −77 | 351 (8, 1, 80) | 260 | 0.05 | 358 | 102 | 28.5 % |
| 15:52 | starts | −77 / −77 | 81 (4, 1, 40) | 175.5 | 7.2 | 56,560 | 9,107 | 16.1 % |
| 15:53 | yes | −78 / −77 | 130 (1, 2, 80) | 195 | 8.81 | 69,391 | 7,277 | 10.5 % |
| 15:54 | yes | −77 / −77 | 87.8 (2, 1, 80) | 195 | 8.85 | 69,665 | 5,966 | 8.6 % |
| 15:55 | yes | −78 / −78 | 108 (5, 1, 40) | 195 | 8.83 | 69,525 | 5,796 | 8.3 % |
| 15:56 | yes | −76 / −76 | 32.6 (0, 1, 80) | 195 | 8.85 | 69,595 | 4,627 | 6.6 % |
| 15:57 | yes | −76 / −76 | 234 (5, 1, 80) | 195 | 8.84 | 69,578 | 4,789 | 6.9 % |
| 15:58 | yes | −76 / −76 | 65 (1, 1, 80) | 195 | 8.83 | 69,535 | 6,282 | 9.0 % |
| 15:59 | yes | −76 / −77 | 433.3 (9, 1, 80) | 195 | 8.83 | 69,461 | 7,524 | 10.8 % |
| 16:00 | yes | −76 / −76 | 216 (5, 2, 40) | 195 | 8.84 | 69,551 | 3,971 | 5.7 % |
| 16:01 | yes | −76 / −77 | 175.6 (2, 2, 80) | 195 | 8.85 | 69,525 | 6,421 | 9.2 % |
| 16:02 | yes | −76 / −76 | 30.0 (0, 2, 40) | 195 | 8.84 | 69,537 | 4,922 | 7.1 % |
| 16:03 | yes | −76 / −77 | 120 (3, 2, 40) | 195 | 7.41 | 57,817 | 2,720 | 4.7 % |
| 16:04 | – | −77 / −76 | 324 (8, 2, 40) | 260 | – | – | – | – |

**In session:**
- signal median −76, min −78;
- AP rx 195 Mbps, which is the onn's tx and matches its own report;
- **retry rate 8.0 %** (O1, 2026-09-21, the client on this radio: 10.3 %).
- **The AP's tx rate is a single snapshot per round and swings from 30 to 433 Mbps** (MCS 0-9, 40 / 80 MHz). The onn's
  rx in its own heartbeats was 117 in 92 % of them. The two views differ in time base: the AP's last frame against
  the onn's report. This is stated, not reconciled.

## 5. The expectations and the reading, as hashed

- **E1, the band is 5 GHz in every heartbeat with the link keys:** **met** (346 / 346, 5180 MHz).
- **E2, silences ≥ 250 ms per 10 min ≤ 7:** **met** (0.0; the baselines were 22.4 and 15.6).
- **E3, RSSI and the tx rate as measured:**
  - the onn read RSSI −68 median (−69 min), tx 195 median (130 min), rx 117 median (29 min);
  - the AP read signal −76, tx 30-433, rx 195.
- **The reading (pre-registered):** the silences fell by more than two thirds, to none, so **the band was most of the
  room-independent flapping, and the stack's H can be re-derived from the 5-GHz distribution (a B task).**
- **What this one window does not settle, disclosed:**
  - **One 10-min window, at 15:52Z** (11:52 EDT, a weekday daytime hour). BENCH-R3 C ran at 20:53Z and BENCH-R1 cell 8
    on 2026-10-22's night. The room's hour differs.
  - **The drop-in differs.** C carried `PRIVYHUB_WAN_TELEMETRY=1`, `PRIVYHUB_IMPAIRMENT=none` and the hold / stall
    stack; this run carried the link report only. That is a cross-config, cross-day comparison, not a paired A/B.
  - **With 0 silences, there is no 5-GHz distribution yet to derive H from.** B's re-derivation needs more 5-GHz
    session time. Every play session now carries the link report (§6). The nights are Part 2's.

## 6. State at the end (16:11Z)

- **The drop-in was removed. Eight lines.** `tools/e3_state.py` **ok** (`check_end.json`): APK CONFIRMED, no game,
  RetroArch or encoder.
- One device paired, no active session (`session_status_end.json`).
- **`debug.privyhub.link_report` LEFT at `1`** (read back `1` at the end), on the user's say-so of 2026-10-23.
  - It is diagnostics only: the client adds the link keys to its heartbeats. It changes no stream behaviour.
  - The host logs them only with `PRIVYHUB_LINK_REPORT=1`, which is not adopted. So outside a run, the client sends
    them and the host keeps none of them.
  - **It clears on the onn's next reboot.** To set it again: `adb shell setprop debug.privyhub.link_report 1`.
- **Units:** the companion, and `privyhub-link-n1` (Part 2, launched 16:10:56Z).
- No sudo, no nft. The Opal was read-only. adb was used for the one `setprop` and for state reads only.
- No address or identifier in any kept file (`redact_check.txt`: 0 IPv4 / MAC / IPv6 hits).
- Nothing fetched, deleted, adopted or committed. `logs/link_r1_git_status.txt`.

## 7. Files (`link_r1_2026-10-23/`)

- **The start:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `check_before.json`, `session_status_before.json`;
  - `adb_reads/` (the band read, the property).
- **The pre-registration:**
  - `link_r1_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`, `tools_at_preregistration_sha256.txt`.
- **The run:**
  - `link_r1_window.py`, `link_r1_suite_call.py`, `window_console.txt`, `window_result.json`;
  - `runs/`: the suite's run directory, `suite.log`, `final_state.json`, and `logs_run1/` (the five logs over the
    span, addresses masked by BENCH-R3's `logs_copy`).
  - The client report stays in `logs/games/decoder_sessions/native_decoder_20261023_160350_059.json`.
- **The Opal:**
  - `o1_opal_sample.sh`, `o1_redact.py`, `o1_parse.py`;
  - `opal/air.jsonl` (15 rounds), `opal/air.jsonl.inventory.txt`, `opal/opal_sampler.log`.
- **The read:**
  - `link_r1_read.py`, `record_read.json`, `record_read_console.txt`;
  - `check_end.json`, `session_status_end.json`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
