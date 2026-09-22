---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# O1 — the Opal's own view of the air

## Classification

**CHARACTERIZED. Neither airtime contention nor the Opal's radio is
implicated, on the pre-registration's own third branch — and the run found
something larger than the question it was sent to answer.**

**The per-minute loss series of two independent 20-minute sessions, started
three minutes apart, agree at Pearson `0.964`.** The loss is a function of
the session's own elapsed time. No environmental account — interference,
contention, the Opal, the radio — predicts that, and it is not what this
task expected to find.

The access the previous attempt was blocked on now works: the user
installed the public half, `ssh opal` authenticates, and everything below
was read **read-only** over it.

## 1. The finding that outranks the rest

Per-minute client loss, from the `D-BASE-R5` heartbeat counters:

```text
A  4  2 214  8 123 180 121   0  84  89 188 115 272 17 90 0 242 331 148  2
B 12 30 212  3  94 173 135   4 103  80 162 121 204  0 72 2 183 251 185 14
```

| comparison | Pearson | Spearman | n |
| --- | ---: | ---: | ---: |
| per-minute loss, A vs B | **0.964** | 0.913 | 20 |
| 30 s bins, A vs B | 0.951 | 0.899 | 41 |
| 10 s bins, A vs B | 0.886 | 0.668 | 121 |
| forward-gap events, A vs B | 0.783 | 0.807 | 20 |

Minute 2 lost 214 and 212. Minute 7 lost 0 and 4. Minute 15 lost 0 and 2.
Minute 17 lost 331 and 251. **Session totals differ (2,230 against 2,040)
while the shape repeats**, so this is not one file read twice: separate
sessions, separate wall-clock windows, separate decoder reports, separate
heartbeat slices.

Both sessions stop the game and relaunch it, so **RetroArch restarts the
title from scratch and the attract loop replays identically**. The loss
follows the replay.

**What this rules out.** Anything that varies with wall-clock time rather
than with stream position — interference from a neighbour, a microwave, a
scan, a thermal ramp, a background transfer — cannot produce a shape that
reproduces at 0.964 when the stream is restarted. `D-BASE-R5` called the
loss "episodic"; it is not episodic in the sense of random bursts. **It is
reproducible.**

**What it does not yet rule in.** Elapsed-time-locked is consistent with
two mechanisms and this run does not separate them: the *content* driving
the encoder (the attract loop's scene changes), or a *client- or host-side
periodic process* that happens to key off session start. The irregular,
non-periodic shape (zeros at minutes 7, 13, 15 and a peak at 17) argues for
content over a fixed-interval timer, and the encoder evidence below argues
the same way, but neither is decisive.

## 2. The encoder side, as far as the existing logs reach

Read out of `logs/games/native_video_alpha.log` — the encoder's own
progress line carries a cumulative `size=` and `time=` about twice a
second, so a per-minute rate and a sub-second spread come out of it with no
new instrument.

- **Average bitrate is flat and is not the driver.** 6,901-6,957 kbps
  across all 40 minutes (a 0.8 % band; the encoder is CBR at 7000). Against
  loss, Pearson **−0.192** (A) and **−0.313** (B) — if anything the
  opposite sign.
- **Sub-second burstiness is itself content-locked.** The spread of the
  ~0.5 s rate inside each minute reproduces across sessions at Pearson
  **0.911**.
- **And it tracks the loss, weakly.** Against loss, Pearson **0.396**
  (Spearman 0.351); against forward-gap events, **0.519** (Spearman 0.451);
  peak 0.5 s rate against loss **0.331**.

So the burstiness proxy explains part of the shape, not the whole of it —
0.40 against the 0.964 the shape itself reproduces at. **0.5 s is far too
coarse to see the mechanism**: the packets of one frame leave back to back
in well under a millisecond, which is the micro-burst `D-BASE-P3` tried to
pace away and whose 8 ms budget refused to spread exactly the large frames
that matter. This is a consistent account, **not a demonstrated one**.

## 3. What the Opal actually exposes — absences first

Inventory in `o1_2026-09-21/inventory_A.txt`. Every reading redacted before
storage.

**The check that outranked everything in the task, answered: `iw dev sta0
link` and `iw dev sta1 link` both return `Not connected`.** Neither
managed-mode interface has an uplink, in both sessions' inventories. **The
5 GHz radio is not time-shared.** That possibility is closed.

The AP: channel **36** (5180 MHz), **80 MHz**, tx power **23 dBm**, one
associated station on the 5 GHz interface, the streaming client (identified
by behaviour — its tx rate goes 40 → 1,156 packets/s when the stream opens
— not by any identifier). Configured `channel 'auto'`, `htmode VHT80`,
country US, `noscan '0'`, allowed list 36/40/44/48/149/153/157/161.

**What is populated:**

| reading | state |
| --- | --- |
| station `tx retries` | **live**, cumulative, 10.3 % of tx packets |
| station `tx packets` / `tx bytes` / `rx packets` | live |
| station `signal` / `signal avg` | live, −70 to −71 dBm |
| station tx/rx bitrate, MCS, NSS, width | live |
| `channel utilization` (`iw dev <if> info`) | live, but see below |
| `noise` | live, −89 to −90 dBm |
| per-interface rx/tx packets | live |

**What is absent or is not what it looks like — three traps, in the
`D-BASE-P4` style, each of which would have been read as a measurement:**

1. **`survey dump` does not accumulate on this driver.** `channel active
   time` reads a fixed **29-30 ms** on every call — after 46 hours of
   uptime — and `channel receive time`, `channel transmit time` and
   `extension channel busy time` are **absent entirely**. It is an
   instantaneous 30 ms window, **not a counter**, and must never be
   differenced. Non-in-use frequencies carry no data at all.
2. **`channel utilization` is that same window, rounded.** 3.3 % is exactly
   1 ms of 30; 6.6 % is 2 of 30. The figure is quantised in **3.33 %
   steps** and the radio is observed for **30 ms in every 10,000 — a 0.3 %
   duty cycle**. Its *mean* over many rounds is a fair estimate of mean
   occupancy; it **cannot see a contention burst shorter than seconds**, and
   adding rows does not change that. The user's first look, "5 GHz 3.3 %,
   2.4 GHz 23.3 %", was **utilization, not idle** — 3.3 % is one quantum
   above zero, i.e. a quiet channel, the opposite of the worry it raised.
3. **`tx failed` is not independent of `tx retries`.** Their difference
   held at **6,790 → 6,792 across four hours and 240,000 retries** — so
   `d_tx_failed` is a copy of `d_tx_retries` plus a term that advanced by
   **2** in that whole span. Differencing `tx failed` measures retries, not
   failures. **The counter that would show retry exhaustion — the air's own
   way of dropping a frame — is therefore unreadable on this driver.** That
   is the single most important gap in this run.

Also absent: `/proc/net/wireless` is **all zeros on the Opal too**, exactly
as on the onn; `iw list` advertises no survey capability; `hostapd_cli` is
not installed (`iwinfo` and `ubus` are).

## 4. The Opal beside the loss — the pre-registered test

40 minutes, 269 sampling rounds at 10 s, 1,196 heartbeats. Full tables in
`analysis_per_minute.txt` and `analysis_ten_second.txt`.

Spearman of per-minute client loss against each Opal reading, n = 40:

| reading | rho | spread over the 40 minutes |
| --- | ---: | --- |
| `channel utilization` | **−0.434** | 6.05 – 8.28 % |
| busy fraction | −0.435 | 0.061 – 0.083 |
| station `tx retries` delta | **+0.219** | 2,931 – 9,858 |
| station `tx failed` delta | +0.221 | (a copy of the above) |
| station `rx drop misc` delta | — | **constant 0** |
| signal / signal avg | +0.058 / +0.110 | −71.5 – −70.2 dBm |
| tx bitrate | −0.278 | 94 – 200 Mbps |
| noise | −0.102 | −90.2 – −88.8 dBm |
| `wlan1` / `br-lan` / `eth0` / `eth0.1` rx+tx dropped, rx+tx errors | — | **all constant 0** |

At the sampler's own 10 s cadence, n = 241 windows, loss 0 – 174 per
window with 59 % of windows at zero:

| reading | rho |
| --- | ---: |
| `tx retries` delta | +0.296 |
| retry *rate* | +0.296 |
| `channel utilization` | **−0.008** |
| signal | +0.013 |
| noise | −0.161 |

And the sharpest form of the question — **the 24 worst windows against the
141 that lost nothing at all:**

| reading | worst (mean loss 98.2) | zero-loss |
| --- | ---: | ---: |
| `tx retries` per window | 1,301 | 1,088 |
| retry rate | 11.3 % | 9.4 % |
| `channel utilization` | **6.78 %** | **6.94 %** |
| signal | −70.3 dBm | −70.7 dBm |
| tx bitrate | 137.5 Mbps | 154.1 Mbps |
| station tx packets | 11,478 | 11,569 |

**Against the pre-registration.** Airtime contention is implicated only at
`|rho| ≥ 0.5` over ≥ 40 minutes *and* visibly worse readings in the burst
minutes: the largest magnitude is **0.435, on the wrong sign** (a busier
channel goes with *less* loss), it collapses to **−0.008** at 10 s where
the instrument is read directly rather than averaged, and the worst windows
read **6.78 % against 6.94 %**. Not met. The Opal's radio is implicated if
loss tracks Opal-side tx failed or rx drops: `tx failed` is a copy of
retries at **+0.221**, and `rx drop misc` is **constant 0**. Not met.
**The third branch is the one that fires: all Opal readings are flat
through a loss swing of 0 to 331 per minute.**

**Neither is implicated.**

## 5. Airtime, in absolute terms

The correlation is only half the answer; the level is the other half.

| | channel utilization | station tx rate |
| --- | ---: | ---: |
| idle, before each session | **2.9 – 3.3 %** | 40 – 47 pkt/s |
| streaming | **6.86 / 6.90 %** | 1,156 / 1,158 pkt/s |
| after each session | 2.75 % | 1 pkt/s |

**The stream costs about 3.6 points of airtime and the channel sits ~93 %
idle while it runs.** Sustained contention is not merely uncorrelated with
the loss — on this measurement it is **not present**. The 0.3 % duty cycle
leaves sub-second contention unobserved, and that caveat stands, but 240
samples put the mean occupancy where it is.

Retries are the counterweight and are **not** reassuring: **10.15 % and
11.32 %** of transmitted packets are retries, on a link at −70 dBm running
MCS 1-3. That is a mediocre link with plenty of capacity — 94-200 Mbps
carrying a 7 Mbps stream — and the retries do not track the loss.

## 6. Which remaining suspect the interface counters point at

The pre-registration asks the record to say. It cannot say cleanly, and the
reason is trap 3.

**Every Opal interface counter is zero for 40 minutes.** `rx_dropped`,
`tx_dropped`, `rx_errors`, `tx_errors` on `wlan1`, `br-lan`, `eth0` and
`eth0.1` (the LAN VLAN the host is wired into) never move, and the
station's `rx drop misc` never moves. The only counter that advances
anywhere is `eth0.2`'s `rx_dropped`, ~145 per minute — the **WAN** VLAN,
not on the path between the host and the onn.

**So the Opal does not report dropping anything.** Read literally that
points away from the Opal's store-and-forward path and toward the air or
the onn's receive path. **But a zero here is weak evidence**: these are
netdev-level software counters, and a frame discarded inside the wifi
driver's per-station queue, or abandoned after retry exhaustion, need not
increment `wlan1 tx_dropped` — and trap 3 means the retry-exhaustion
counter itself cannot be read on this driver. **The instrument that would
settle air-versus-forwarding is precisely the one this hardware does not
provide.**

One independent line does discriminate, and it is in the client's own
report. **Audio and video cross the same radio, the same AP and the same
station at the same moment, and lose at different rates:**

| | video | audio |
| --- | ---: | ---: |
| session A | 2,230 of 989,789 = **0.225 %** | 185 of 241,399 = **0.077 %** |
| session B | 2,040 of 989,783 = **0.206 %** | 67 of 241,509 = **0.028 %** |

**Video loses 2.9x and 7.4x the rate audio does**, on one radio, in one
second. Audio is low-rate, small-packet and evenly paced; video arrives in
per-frame micro-bursts. A degraded-air account predicts both streams suffer
together. A burst-meets-a-queue account predicts exactly this split. **That
is the strongest single piece of evidence in this run for where the loss
happens**, and it is consistent with the content-lock in §1 and the
burstiness correlation in §2.

**The reading, stated at the confidence it has earned:** the loss is
reproducible from stream position, it selects the bursty stream over the
paced one, and nothing the Opal measures moves with it. That points at a
**burst meeting a queue somewhere between the encoder's output and the
onn's decoder** — the AP's per-station wireless queue and the onn's receive
path are both still live candidates and **this run does not separate
them**. What would: a receive-side socket-drop counter on the onn
(`/proc/net/udp` `drops` column for the stream's socket, sampled per
minute), which is a client-side read and costs no new hardware.

## 7. Levers, and whose call they are

None of these follows from this run as a fix; the run found the air is not
the problem, so the air levers have lost most of their motivation.

- **Channel and width** (36, 80 MHz; the Opal's `channels` list offers
  40/44/48/149/153/157/161, and `channel 'auto'` is configured). Airtime at
  ~7 % says there is nothing to escape. **A narrower width — 40 MHz — is
  the one with a real rationale left**: it raises per-MCS robustness at
  −70 dBm and would cut the 10-11 % retry rate, at the cost of ceiling the
  stream does not use.
- **Placement / tx power.** −70 dBm with MCS 1-3 is a mediocre link and
  placement is the honest fix for it; it buys retry headroom, and on this
  evidence **not** less loss.
- **A different access point.** Nothing here indicts this one.
- **Sender-side pacing with a larger frame budget** (`D-BASE-P3`'s bounded
  null) is now the lever with the most support, and it costs latency.

**Choosing among them is the user's decision.** Each is a single setting
except the last, which is a product trade.

## 8. Method, access and privacy

`ssh opal`, an alias in the host user's `~/.ssh/config` outside this
repository. **Read-only without exception**: `iw dev|info|link|list|station
dump|survey dump`, `iwinfo`, `uci show wireless`, `cat` of `/proc` and
`/sys/class/net/*/statistics/*`, `logread`, `uptime`, `date`. No `uci set`,
no `uci commit`, no `wifi`, no `reboot`, no `opkg`, no write to `/etc`.
Nothing was installed on the Opal and nothing was written to it.

Sampling: one `ssh opal` per **10 s** round, **1,661-1,727 ms** per round
(median 1,692). **The Opal's load did not rise from sampling** — 1.08-1.18
idle, and a two-minute sampling-only run with no stream open saw it *fall*
1.33 → 1.08. Through the sessions the per-minute mean ran 1.05-1.81, median
**1.13**, the rise belonging to the stream and to RetroArch's launch. The
task's "thin to 20 s if load rises by more than 0.3" rule never triggered.

**`logread` produced zero wifi, hostapd, deauth, disassoc, DFS, channel or
beacon events inside either session.** (Before them, the log shows ordinary
2.4 GHz client churn and a WPA group rekey on the 5 GHz interface — the
configured `wpa_group_rekey` of 36,000 s — none of it inside a session.)

**Privacy.** `o1_redact.py` runs on every byte the Opal prints, before it
is displayed or stored: MACs and BSSIDs become stable per-run labels
(`sta-A`, …), SSIDs, WPA keys, IPv4/IPv6 and hostapd accounting session ids
are replaced. **Two redaction defects were found and fixed during this
run**, and both had already leaked once into a terminal before the fix:

- the IPv6 pattern matched a bare `HH:MM:SS` clock, so every timestamp the
  Opal printed became `<redacted-ip>`;
- the SSID/secret patterns matched `option ssid '…'` but **not** `uci
  show`'s `wireless.default_radio1.ssid='…'` or `.key='…'`, so one
  `uci show wireless` printed both SSIDs and both WPA passphrases in clear.

Both are closed, the fix is in `o1_redact.py`, and **no address, MAC,
BSSID, SSID, key or device identifier appears in this record or in any
stored artifact.** The leak reached a terminal only; nothing was written.

## 9. Sessions and artifacts

Two 20-minute attract-mode sessions of the PS1 reference title, **zero
input**, BACK to end, teardown between, the sampler running 60 s before and
60 s after each. FEC pacing **off** in both (`PRIVYHUB_FEC_PACING_US`
`enabled=false`), 7000 kbps, GOP 15, FEC group 8.

| | A | B |
| --- | --- | --- |
| window (UTC) | 23:03:33 – 23:23:33 | 23:26:31 – 23:46:31 |
| heartbeats | 598 | 598 |
| sampling rounds | 135 | 134 |
| video loss | 2,230 (0.225 %) | 2,040 (0.206 %) |
| forward-gap events | 149 | 163 |
| max forward gap | 85 packets | 75 packets |
| sequence resyncs / SSRC changes | 0 / 0 | 0 / 0 |
| fps (rendered / duration) | 59.76 | 59.71 |
| `spike_20_ms` per minute | 41.9 | 50.1 |
| stale output drops | 8 | 23 |
| max output gap | 155 ms | 463 ms |

**Session A's heartbeat series totals 2,230 — the report's `lost_packets`
exactly**, a second confirmation of `D-BASE-R5`'s accounting.

**`video.recent_fps` read 49.80 for session B** — a spot reading taken at
BACK, the `D-BASE-P2b` trap. Rendered-frames-over-duration gives 59.71.

Under `evidence/o1_2026-09-21/`, SHA-256s in `o1_sha256.txt`:
`o1_opal_sample.sh`, `o1_redact.py`, `o1_parse.py`, `o1_run.sh`,
`o1_analyze.py`, `o1_fine.py`, `o1_encoder_burst.py`; `air_A/B.jsonl`,
`heartbeat_A/B.jsonl`, `report_A/B.json`, `inventory_A/B.txt`,
`per_minute_*.json`, `fine_windows.json`, `index.txt`, and the four
`analysis_*.txt`.

No patch record: **no code changed.** The only files written outside
`docs/memory/` are none.
