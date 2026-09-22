---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P5 — which queue drops the burst

## Classification

**CHARACTERIZED. The onn's receive path is not the queue; the loss is
upstream of the socket and tracks the size of the largest frames.** The
pre-registration's **second** branch fires, on both of its conditions:

| pre-registered condition | required | measured |
| --- | --- | ---: |
| loss tracks max packets per frame | \|rho\| >= 0.5 | **0.583** (10 s, n=240), **0.780** (per minute, n=40) |
| the onn's socket `drops` stay near zero | < 10 % of loss | **0.00 %** — exactly **0** of **4,349** |

The onn's UDP receive buffer **did not discard one datagram** in 40 minutes
of streaming across 240 ten-second windows, on either the video or the
audio socket.

## 1. The three instruments, and what each cost

| | what | where | cadence |
| --- | --- | --- | --- |
| 1 | packets per frame | the relay, counting only | per frame, bucketed per second |
| 2 | the onn's socket `drops` and `rx_queue` | host-side `adb shell cat /proc/net/udp6` | 2 s |
| 3 | client loss and forward gaps | the `D-BASE-R5` heartbeat counters | 2 s |

**Instrument 1 is the only code change and it is counting only.** In
`native_fec_relay.py`, `_handle_rtp` now closes a frame on the marker
packet (or on a timestamp change, counted separately as `unmarked_frames`)
and files its packet count into a one-second bucket. **Nothing forwards,
delays, reorders, drops or inspects a payload differently**; the pacing
knob stayed at **0** in both sessions, confirmed in each session's status
(`pacing.enabled: false`). Measured cost on the forwarding thread:
**0.36 us per packet**, which at the stream's ~820 packets/s is **0.03 % of
one core**. Relay `send_errors` was **0** in both sessions.

Instruments 2 and 3 are host-side reads. **Nothing was installed on the
onn and the client was not rebuilt.**

## 2. Two corrections the instruments needed first

Both were caught in smoke runs before the real sessions, and both would
have produced a confident wrong answer.

**`/proc/net/udp` alone shows nothing.** The client's socket is a Java
`DatagramSocket(port)`, so it binds the IPv6 wildcard and appears only in
**`/proc/net/udp6`**. The first sampler read `udp` alone and found the
stream's ports in **none of 76 rounds** — which, read carelessly, is
indistinguishable from "the socket never drops".

**A row has thirteen fields, not fourteen.** The header names fifteen
columns, but `tx_queue:rx_queue` and `tr:tm->when` are each printed as one
colon-joined token. A `len(parts) < 14` guard rejected **every** row of
both files. `drops` is read as the **last** field and `inode` as index 9.

Verified against captured rows before the sessions ran: a row with a known
`drops` of 17 and `rx_queue` of `0x1F400` parses to exactly those.

## 3. The onn's receive path is not the queue

Over both sessions, 240 ten-second windows, **4,349 lost packets**:

| | video socket (48100) | audio socket (48101) |
| --- | ---: | ---: |
| `drops` over 40 minutes | **0** | **0** |
| windows where `drops` advanced | **0 of 240** | **0 of 240** |

`rx_queue` — the bytes waiting in the buffer at each sample — **did back
up**: peak **480,512 bytes**, median window peak 31,744. Against the
client's requested `SO_RCVBUF` of 2 MiB (kernel `rmem_max` is **8,388,608**,
so the request is granted in full) that is roughly **a quarter of the
buffer at its worst**, with the rest never used. The receive path is under
load and has headroom; it is not overflowing.

**And nothing below the socket is dropping either.** A supplementary
read through session B (207 samples, `p5_onn_lowlevel.py`) took the
counters that a socket-buffer figure cannot see:

| counter | delta over session B |
| --- | ---: |
| `wlan0` `rx_packets` | +1,209,205 |
| `wlan0` `rx_errors` / `rx_missed_errors` / `rx_over_errors` / `rx_fifo_errors` | **+0 / +0 / +0 / +0** |
| UDP `RcvbufErrors` (whole device) | **+1** |
| UDP `InErrors` (whole device) | **+1** |
| client-reported loss | 2,233 |
| `wlan0` `rx_dropped` | +36,988 |

The last row is the one that needs care, and it is **not our loss**. It is
**16.6x larger** than the session's loss, and it **does not track it**:
per minute, Spearman **0.040**, Pearson **−0.123**, ranging 203 to 8,154 a
minute against a loss range of 0 to 293. Every hardware error counter beside
it is zero. This is the ordinary Android broadcast/multicast filter counter
on a busy home network, and reading it as stream loss would have been the
third trap of the run.

**So: socket drops zero, driver error counters zero, device-wide UDP
buffer errors one in twenty minutes. The onn's receive path is excluded.**

## 4. What the loss does track: the size of the largest frames

Pooled over both sessions. Counters are differenced per window; instants
are maxed — the two are never mixed.

**10-second windows, n = 240** (loss 0–144 per window, median 0):

| reading | rho vs loss | rho vs forward gaps | spread |
| --- | ---: | ---: | --- |
| **max packets per frame** | **0.583** | **0.584** | 25 – 208 |
| **frames >= 80 packets** | **0.569** | **0.584** | 0 – 37 |
| frames >= 40 packets | 0.195 | 0.214 | 0 – 78 |
| mean packets per frame | −0.344 | −0.336 | 12.96 – 14.20 |
| the onn's `drops` delta | — | — | **constant 0** |
| the onn's `rx_queue` peak | 0.026 | 0.013 | 0 – 480,512 |
| frames in the window | 0.067 | 0.057 | 599 – 601 |

**Per minute, n = 40** (loss 0–293, median 117):

| reading | rho vs loss | rho vs forward gaps |
| --- | ---: | ---: |
| **max packets per frame** | **0.780** | 0.778 |
| **frames >= 80 packets** | **0.779** | 0.771 |
| frames >= 40 packets | 0.217 | 0.146 |
| mean packets per frame | −0.407 | −0.309 |
| the onn's `drops` delta | — | — |
| the onn's `rx_queue` peak | 0.048 | 0.143 |

Three things in that table matter beyond the headline.

- **The frame rate is constant and the mean frame is constant.** 599–601
  frames per 10 s in every window, mean 12.96–14.20 packets. Nothing about
  the *volume* of traffic moves. Only the **tail** of the frame-size
  distribution moves, and the loss moves with it.
- **`frames >= 80` correlates as strongly as the maximum** and is the
  better statistic: a per-window maximum is an extreme value and saturates,
  while a count does not. Both land at ~0.78 per minute.
- **`rx_queue` is flat against loss** (0.026 at 10 s). The buffer's depth
  is not what decides whether a window loses packets — which is the same
  conclusion as the zero `drops`, reached independently.

## 5. The control: does each series reproduce across sessions?

The task made this the check that could falsify the frame-size account —
if frame size did not repeat across sessions while loss did, frame size
could not be what drives loss. Per minute, session A against session B:

| series | Pearson | Spearman |
| --- | ---: | ---: |
| **frames >= 80 packets** | **0.996** | 0.985 |
| **frames >= 40 packets** | **0.991** | 0.968 |
| mean packets per frame | 0.939 | 0.914 |
| max packets per frame | 0.930 | 0.664 |
| **lost packets** | **0.890** | 0.800 |
| forward-gap events | 0.767 | 0.721 |

**Frame size reproduces more tightly than the loss does** — 0.996 against
0.890 — which is the right way round for the account to survive, and is
what a fixed attract loop driving a CBR encoder should do.

**One honest miss:** the task pre-registered "the two sessions' per-minute
loss should again agree at Pearson > 0.9", and this pair came out at
**0.890**, just under. `O1`'s pair was 0.964. The content-lock is confirmed
but the loss series is the *noisier* of the two, which is itself consistent
with frame size being the driver and the loss being a probabilistic
consequence of it.

## 6. What this means, stated at the confidence it has earned

**Positively established:** the loss is not in the onn's receive path, at
the socket or below it; and it rises and falls with the count of large
frames, in two independent sessions, at 10-second and per-minute
resolution.

**By elimination, the remaining location is the wireless hop itself — the
AP's per-station queue or the air during the burst.** That is what
`O1` left standing, and P5 does not observe a drop there directly. It
cannot: `O1` established that this AP's **`tx failed` counter is a copy of
`tx retries`** (their difference held at 6,790 → 6,792 across four hours),
so retry exhaustion — the air's own way of discarding a frame — is
unreadable on this driver. **The case is: everything else on the path now
reports zero, and the one thing that moves with the loss is how big the
burst is.**

Consistent with, and now explaining, three earlier results:

- **`D-BASE-P3`'s bounded null.** Its 8 ms frame budget clamps spacing
  above **53 packets per frame**. This run measures **4.0 % of frames above
  40 packets and 1.0 % above 80** — so the frames the account blames are
  exactly the ones P3 refused to spread. P3 tested pacing hardest where it
  applied least, and said so at the time.
- **`O1`'s audio-versus-video split.** Video loses 3–7x what audio loses
  over the same radio in the same second; audio is evenly paced and never
  builds a burst. Here again: video 0.214 % / 0.226 %, audio **0.024 % /
  0.031 %**.
- **`O1`'s content-lock.** The attract loop replays, the frame-size tail
  replays with it at 0.996, and the loss follows.

## 7. The distribution a fix has to flatten

Per the pre-registration for this branch. Both sessions, ~72,600 frames
each, CBR 7000 kbps, GOP 15:

| | session A | session B |
| --- | ---: | ---: |
| frames | 72,560 | 72,770 |
| mean packets per frame | 13.63 | 13.64 |
| **p50** | **11** | **11** |
| **p90** | **29** | **29** |
| **p99** | **82** | **78** |
| **max** | **207** | **208** |
| frames >= 40 packets | 2,894 (**3.99 %**) | 2,931 (**4.03 %**) |
| frames >= 80 packets | 734 (**1.01 %**) | 726 (**1.00 %**) |
| frames ended without a marker | 114 | 111 |

**The shape is the problem, not the rate.** The median frame is 11 packets
and the mean 13.6, but one frame in a hundred is **80 or more** and the
worst is **207** — a nineteen-fold spread between the median and the p99,
emitted back to back at line rate into a wireless queue. A fix has to pull
the p99 and the maximum down; it does not need to touch the median.

## 8. Levers, and their costs — the user's decision

**Choosing among these is the user's call, and each carries a real cost.**
Nothing here was implemented.

- **Encoder VBV: `-maxrate` with a matching `-bufsize`.** The direct lever
  on the p99. A `bufsize` near one frame's worth of bits caps how large any
  single frame can be. **Cost: quality dips on scene changes**, where the
  encoder must now spend fewer bits on the frame that needs most.
- **A smaller IDR spike** — more frequent, smaller keyframes, or
  periodic intra-refresh instead of full IDRs. Intra-refresh in particular
  spreads a keyframe's cost across a GOP and would flatten exactly this
  tail. **Cost: lower compression efficiency for the same quality, and a
  recovery model change the resync path would need re-testing against.**
- **A pacing budget that actually spreads a 60–80-packet frame**
  (`D-BASE-P3`, currently off with an 8 ms budget). **Cost: latency,
  directly** — the budget *is* the added delay, and P3 measured **+41 %
  spike rate** at 8 ms.
- **Not a fix: a larger client receive buffer.** The socket dropped
  nothing and used a quarter of what it already has. This run rules that
  out, which is worth as much as what it rules in.

## 9. Sessions and artifacts

Two 20-minute attract-mode sessions of the PS1 reference title, **zero
input**, BACK to end, teardown between, all three instruments through each.
Four smoke sessions preceded them (90 s, 60 s, 100 s, 70 s) to validate the
instruments; their data is not part of the analysis.

| | A | B |
| --- | --- | --- |
| window (UTC) | 00:44:21 – 01:04:20 | 01:06:57 – 01:26:57 |
| heartbeats | 598 | 598 |
| frame-size seconds | 1,201 | 1,201 |
| socket samples | 632 | 633 |
| video packets / loss | 986,693 / **2,116** (0.214 %) | 989,647 / **2,235** (0.226 %) |
| audio packets / loss | 240,875 / 58 (**0.024 %**) | 241,464 / 75 (**0.031 %**) |
| forward-gap events | 158 | 158 |
| max forward gap | 70 packets | 81 packets |
| sequence resyncs | 0 | 0 |
| fps (rendered / duration) | 59.74 | 59.74 |
| `spike_20_ms` per minute | 47.2 | 46.8 |
| max output gap | 181 ms | 273 ms |
| relay `send_errors` | 0 | 0 |

Host send path, checked once: `eno1 tx_dropped` **14 lifetime**,
`tx_errors` 0, host UDP `SndbufErrors` **0**. The loss is not on the way
out of the host either.

Under `evidence/d_base_p5_2026-09-21/`, SHA-256s in `p5_sha256.txt`:
`p5_run.sh`, `p5_socket_sample.py`, `p5_onn_lowlevel.py`, `p5_analyze.py`,
`test_frame_sizes.py`; `frames_A/B.jsonl`, `socket_A/B.jsonl`,
`socket_head_A/B.json`, `heartbeat_A/B.jsonl`, `report_A/B.json`,
`status_A/B.json`, `lowlevel_B.jsonl`, `p5_windows_pooled_10s.json`,
`p5_windows_pooled_60s.json`, `index.txt`, `analysis_full.txt`.

`test_frame_sizes.py` is the counting test — 40 assertions over synthetic
RTP covering the marker, the unmarked frame, the percentiles, the bucket
roll, the ring bound, the log line and the no-log path. All pass.

Patch: `patches/D-BASE-P5_RELAY_FRAME_SIZE_COUNTERS.md`.

## 10. Privacy

No address, MAC, SSID or device identifier appears in this record or in any
stored artifact. The socket sampler records only the two stream ports'
rows, and only their queue depths, drop counts and inode — never the local
address. `ss -uanm` output carries addresses and is **not stored**: only
whether it exposes `skmem` (it does not — see below) and its row count.

**The socket's granted receive buffer could not be read on this device.**
`/proc/net/udp6` does not carry `SO_RCVBUF`; `ss -uanm` would, in `skmem`,
but does not emit it here. Recorded as `granted_rcvbuf_obtainable: false`
rather than substituting a number. What is known: the client requests
**2 MiB** and the kernel's `rmem_max` is **8,388,608**, so the request is
not capped.

## Correction, appended 2026-09-21 (found while running `D-BASE-P6`)

**Session A's `rx_queue` peak was 986,880 bytes — about 47 % of the 2 MiB
buffer — not the 480,512 reported in §3 and §4 above.**

The larger sample is at `2026-09-22T00:44:17.751Z`, a few seconds *before*
the session's own `T0` of `00:44:21`, during stream start-up. The analysis
windowed on the heartbeat clock and so began after it; 480,512 was the
highest sample inside the windows, not the highest of the session. The raw
row was in `d_base_p5_2026-09-21/socket_A.jsonl` the whole time.

**The conclusion is unchanged, and the correction slightly strengthens it.**
The buffer went half full rather than a quarter full and **still discarded
nothing**: `drops` is 0 across all 603 samples of that session and all 240
windows of both. "The receive path is under load and has headroom, not
overflowing" reads the same at 47 % as at 23 %.

Where the figure appears above — "`rx_queue` peaked at **480,512 bytes of a
2 MiB buffer**, a quarter used at its worst" (§3) and "the onn's `rx_queue`
peak | 0.026 | 0 - 480,512" (§4) — read **986,880** and **47 %**. The §4
correlation is unaffected: it is computed per window and the sample outside
them was never in it.
