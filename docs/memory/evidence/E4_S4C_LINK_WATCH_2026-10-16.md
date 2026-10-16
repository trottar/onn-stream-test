---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (G1-S1 / G3-S1 / G3-S2 uncommitted beside it, not touched)
---

# E4-S4C — the link watch, its record (stopped after six probes)

**Classification: MEASURED; the deferral INCONCLUSIVE (link).** The watch
ran detached (E4-S4D) from 2026-10-15 21:41:41Z to 2026-10-16 02:07:28Z.
It was stopped by its stop file, because the user parked the LAN loss row
("remote first").

- Six probes ran, at 17:41-21:26 US Eastern, Thursday.
- **None was clean:** loss ran 102-4,299 per min, and the gate is < 10.
  - So there was no control and no flagged run.
  - Grab deferral stays INCONCLUSIVE (link). E4-S4's verdict stands.
- The host side was clean in every probe: RetroArch 59.999-60.0, host CPU
  11.0-12.0 %, `flags_absent` true in the run and at the end.

Task: `handoffs/E4-S4C_WATCH_RECORD_TASK.md`, session A item 1 of
`QUEUE_2026-10-16.md`. Pre-registration:
`e4_s4d_2026-10-15/e4_s4d_preregistration.txt` (sha256 `334f7147…b738`).
Launch: `E4_S4D_LINK_WATCH_LAUNCH_2026-10-15.md`. Files:
`e4_s4d_2026-10-15/`.

## 1. The stop

- `touch ~/privyhub_link_watch/STOP` at 02:07:02Z. Probe 7 was due at
  02:11Z and never started.
- The unit went `inactive` at 02:07:28Z.
- The final status line (`status.txt`):
  `doing: EXITED (the stop file) | deferral: control: -, conc1: -, conc2: -, conc150: - [await_clean_probe] | state: adopted5 ok`.
- `watch.log`'s last line: `watch closed (the stop file); deferral state await_clean_probe`.
- `status.txt`, `history.csv` and `watch.log` are copied into
  `e4_s4d_2026-10-15/`. The originals stay in `~/privyhub_link_watch/`,
  with the six probe directories. Nothing was deleted, and the STOP file
  stays.

## 2. Every probe (E1-PS1-STREAM, 300-s window; `link_watch.jsonl`, `history.csv`)

| # | ET start | loss/min | rendered | resyncs | clean | AP: client signal dBm (median / min) | AP: tx rate Mb/s | AP: retry % | air util % (mean / max) | client RSSI dBm | client tx / rx link Mb/s | ping 40 min before: loss % / RTT median / p99 ms | client pauses | underruns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 17:41 | 1,645 | 56.08 | 25 | no | −79 / −80 | 6.5 | 21.7 | 8.2 / 20.0 | −69 | 195 / 117 | — (trace just started) | 2 | 14 |
| 2 | 18:26 | 926 | 57.63 | 12 | no | −79 / −81 | 6.5 | 32.4 | 11.0 / 20.0 | −68 | 117 / 117 | 0.50 / 4.6 / 499 | 1 | 33 |
| 3 | 19:11 | 176 | 59.22 | 0 | no | −79.5 / −81 | 6.5 | 21.4 | 13.0 / 26.6 | −69 | 195 / 117 | 0.33 / 4.7 / 274 | 0 | 40 |
| 4 | 19:56 | **4,299** | 51.19 | 70 | no | −80 / −81 | 6.5 | 30.4 | 10.1 / 26.6 | −69 | 195 / **58** | 0.38 / 4.5 / 211 | 2 | 102 |
| 5 | 20:41 | 437 | 58.94 | 6 | no | −78 / −79 | 6.5 | 14.8 | 13.7 / 83.3 | −68 | 195 / 117 | 1.29 / 4.4 / 534 | 1 | 122 |
| 6 | 21:26 | **102** | 59.30 | 0 | no | −78 / −79 | 6.5 | 13.2 | 8.1 / 16.6 | −68 | 195 / 117 | 0.13 / 4.4 / 391 | 0 | 10 |

- The air was the same in every probe: channel 36, 80 MHz, one station
  on the interface, noise −89/−90 dBm. The client reported 5 GHz,
  channel 36, and no scans in any window.
- The client's cpu-thermal read 64-70 °C.
- The AP's columns come from O1's read-only sampler: 10-s rounds,
  redacted before storage. The client station was picked by behaviour
  (the one whose tx packets advanced most), never by identifier.

## 3. The ping trace (1 echo/s host → client, unprivileged; `ping.jsonl`, 60-s bins)

| hour (ET, 10-15) | bins | sent | lost | loss % | RTT median of bins (ms) | worst p99 (ms) | worst bin (lost) | what ran |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | 19 | 1,097 | 13 | 1.19 | 4.7 | 1,176 | 6 | probe 1 |
| 18 | 60 | 3,595 | 8 | 0.22 | 4.6 | 1,760 | 5 | probe 2 |
| 19 | 60 | 3,594 | 13 | 0.36 | 4.3 | 895 | 4 | probes 3-4 |
| 20 | 60 | 3,593 | 34 | 0.95 | 4.35 | 5,073 | 21 | probes 4-5 |
| 21 | 60 | 3,594 | 12 | 0.33 | 4.2 | 337 | 5 | probe 6 |
| 22 | 7 | 420 | 0 | 0 | 4.1 | 208 | 0 | idle |
| **all** | 266 | 15,893 | 80 | **0.50** | | | | |

- **Idle vs a probe running:**
  - idle bins: 0.14 % lost (18 of 12,639);
  - bins with a probe streaming: **1.66 %** (65 of 3,912).
  - RTT medians were the same, 4.4 and 4.3 ms.
- The trace started at the launch and stopped at the stop. It had one
  generation, with no restart.

## 4. The deferral

- **No clean probe**, so no control and no flagged run (`deferral.json`:
  `await_clean_probe`, closed by the stop file).
- **Grab deferral: INCONCLUSIVE (link).** E4-S4's verdict stands: the
  host evidence only.
- The flag was never set. `e3_flag.conf` was never written by the watch.

## 5. The reading, as seen (no cause claimed)

- **What moved with the loss** (Spearman's ρ across six probes; six
  points, so read loosely):
  - **AP retry % +0.77**: the two lowest-retry probes (14.8, 13.2 %) had
    437 and 102 loss/min; the two highest (32.4, 30.4 %) had 926 and
    4,299.
  - The client's pauses +0.96.
  - AP-side signal −0.59: the worst probe at −80 dBm, the best two at
    −78.
  - The client's rx link rate −0.65: it was 58 Mb/s only in the worst
    probe, and 117 in the others.
  - Hour of day −0.67: the loss fell through the evening, but it is
    not monotone (4,299 at 19:56).
- **What did not move:**
  - the AP's tx rate to the client, **6.5 Mb/s in every probe**;
  - air utilisation (ρ −0.03; 8-14 % mean);
  - the client's own RSSI (−68/−69 throughout);
  - the client's tx link rate (195, once 117);
  - the ping loss in the 40 min before a probe (ρ +0.09);
  - the channel, width and station count.
- **The asymmetry, quoted:**
  - the client reports the AP at **−68 / −69 dBm**;
  - the AP reports the client at **−78 to −80 dBm**, about 10 dB weaker
    in the other direction;
  - the AP's tx rate to the client reads 6.5 Mb/s while the client
    reports a 117-195 Mb/s link.
  - These are the two ends' own reports, and they disagree.
- **Ping:** loss on the idle link was low (0.14 %). With a stream on it,
  it was about 12× higher, and RTT p99 reached seconds in the worst hour.
  The stream's loss and the echo loss rise together while a stream runs.

## 6. Files

In `e4_s4d_2026-10-15/`:

- `link_watch.jsonl`, `ping.jsonl`, `history.csv`, `status.txt`,
  `watch.log`, `watch_state.json`, `deferral.json`;
- `probes/001-006/` (summary, encoder, title);
- `manifest.sha256` over the directory;
- `redact_check.txt` (appended for this record).

Also `logs/e4_s4c_git_status.txt`. The probes' full run directories stay
in `~/privyhub_link_watch/probe_00{1-6}/`, outside the repo.

## 7. State at the end

- The five-line adopted state. The watch unit is inactive (collected).
- No flag, no constraint. Nothing adopted; nothing committed.
- The LAN loss row is **parked** (the user: remote first). See
  `docs/KNOWN_ISSUES.md` LINK.
