# G4-W1 — the arithmetic, written before the files are read

Written 2026-10-18, session B, baseline `1fc2e19`. Inputs: the task file and the
records it names, read as prose only (G4-S2 §4, G4-S1's wire row, G8-S3 §3,
D-BASE-P10's change paragraph and its wire row, E3-S5's packetization line,
G1-S1's provider contract). **Not yet read:** any data file (G4-S2 `samples.jsonl`,
the shim's `impairment_run*.jsonl`, the frame logs, the audio counters), and
**not the code** (the audio sender, the FEC relay, `native_stream.py`). Every input
taken from a record is marked as such so the code reading can confirm or refute it.
This file is hashed before the first data or code file is opened; it is not edited
after (any correction goes in the record's §2).

Units: kbit/s = 1,000 bit/s. "IP-level" = an IPv4 packet including its 20-B
header, as an interface's `tx_bytes` counts it.

## Inputs (from the records)

- **Video RTP data packet:** 12-B RTP header + H.264 payload ≤ 1,188 B
  (`pkt_size=1200`; G8-S3 §3, "code").
- **FEC parity datagram:** 23-B FEC header + the group's largest payload; groups
  of ≤ 8 data packets, closed at each frame's end (G8-S3 §3). Measured at 5000:
  0.178 parity per data packet, 1.81 per frame, 1,115 B per parity datagram,
  10.15 data packets per frame (G8-S3 §3).
- **Audio:** 5-ms packetization, 200 originals/s + 200 duplicates/s = 400
  datagrams/s with 2/4 (E3-S5; D-BASE-P10: a duplicate carries the same sequence,
  timestamp and payload). D-BASE-P10 measured 1.60 Mbps per copy on the wire,
  3.21 with 2/4. **Assumed format** (to be confirmed in the code): 48,000 Hz ×
  2 ch × 2 B (s16le) = 192,000 B/s = 960 B per 5 ms. 1.60 Mbps / 200 = 1,000 B
  per datagram = 960 + 40, which is exactly RTP 12 + UDP 8 + IPv4 20 — so
  D-BASE-P10's figure is taken to be IP-level.
- **Overlay:** a WireGuard-based overlay with its own interface (G1-S1; path
  direct / relayed). Assumed (to be confirmed): the "tailnet interface" is a TUN
  device, so its `tx_bytes` counts the **inner** IP packets handed to it, before
  WireGuard encapsulation. MTU 1280 (the task).
- **Measured totals to explain:** 8,286 kbit/s at 4000 (G4-S2, steady median),
  11,420 at 7000 (G4-S1 run 1, window mean).

## The packet model for video (used by terms 1, 2, 4)

Mean frame at rung R (60 fps): R × 1000 / 8 / 60 bytes.
Data packets per frame ≈ frame / 1,188 + 1.36. The +1.36 is G8-S3's own offset
(10,442 B → 8.79 full packets, measured 10.15), from per-frame rounding and NAL
boundaries, assumed rung-independent.

| rung | mean frame | data pkts / frame | data pkts / s |
| --- | ---: | ---: | ---: |
| 4000 | 8,333 B | 8.37 | **502** |
| 7000 | 14,583 B | 13.64 | **818** |

Parity groups per frame = ceil(pkts / 8), averaged over the frame-size spread.
With a mean of 8.37 at 4000 roughly half the frames cross 8 → **≈ 1.45 per frame**;
with 13.64 at 7000 most frames take 2 and the large ones 3 → **≈ 2.15 per frame**
(5000: measured 1.81 at 10.15, between the two). Parity datagram ≈ **1,150 B**
UDP payload (≤ 23 + 1,188 = 1,211; measured 1,115 at 5000).

| rung | parity / s (model) | parity / s (× 0.178 per data pkt, the alternative) |
| --- | ---: | ---: |
| 4000 | 87 | 89 |
| 7000 | 129 | 146 |

## The terms

1. **Video payload** (H.264 bytes in RTP, no header): the rung's target. G8-S3
   measured 5,012 at 5000 (the target within 0.3 %); no measured mean at 4000 or
   7000 in the records read → predicted **4,000** and **7,000**.
2. **FEC parity** (UDP payload of parity datagrams): parity/s × 1,150 B × 8.
   **4000: 87 × 1,150 × 8 = 800 kbit/s. 7000: 129 × 1,150 × 8 = 1,187 kbit/s.**
   (Alternative ratio: 819 / 1,343.) The files are expected to show 0.178 per data
   packet near 5000, not 8+1's nominal 12.5 % — and the ratio itself to move with
   the rung (lower at 4000, higher at 7000).
3. **Audio** (IP-level, all 400 datagrams): 192,000 B/s × 2 copies = 3,072 kbit/s
   payload; + 400 × 40 B × 8 = 128 kbit/s RTP/UDP/IP → **3,200 kbit/s at both
   rungs** (check: 400 × 1,000 B × 8 = 3,200; D-BASE-P10 3.21). Rung-independent.
4. **Per-packet framing on the LAN hop, video and parity** (audio's is inside
   term 3):
   - RTP 12 B × data pkts/s: **4000: 48 kbit/s; 7000: 79.**
   - UDP 8 + IPv4 20 = 28 B × (data + parity) pkts/s:
     **4000: 28 × 589 × 8 = 132 kbit/s; 7000: 28 × 947 × 8 = 212.**
5. **The overlay's per-packet cost and fragmentation:**
   - WireGuard data message: outer IPv4 20 + UDP 8 + WG header 16 + Poly1305 tag
     16 = 60 B, plus padding of the inner packet to a 16-B multiple (mean ~8 B)
     → ~68 B per packet. **On the tailnet interface's own `tx_bytes`: 0** (a TUN
     counts the inner packet). It lands on the underlay interface instead:
     4000: (589 + 400) × 68 × 8 ≈ 538 kbit/s; 7000: (947 + 400) × 68 × 8 ≈ 733 —
     **not part of 8.29 / 11.42** if the assumption holds.
   - **Fragmentation at MTU 1280:** video data inner packet = 20 + 8 + 12 + 1,188 =
     **1,228 B ≤ 1,280**; parity = 20 + 8 + 23 + 1,188 = **1,239 ≤ 1,280**;
     audio 1,000. **Predicted: nothing fragments on the tailnet interface.** The
     outer packet (≤ 1,239 + 60 + pad ≈ 1,307) fits a 1,500 underlay. If video did
     fragment, each data packet would become two (an extra ~20 + 8 B header and a
     second packet per data packet: +~110 kbit/s at 4000 and the packet count
     nearly doubled for video) — visible as tx_packets ≈ 2× video + audio.
   - **If the sampler kept `tx_packets`:** predicted ≈ 589 + 400 = **~990 pkt/s
     at 4000** (mean ~1,046 B per packet) and 947 + 400 = **~1,350 at 7000**
     (mean ~1,080 B).
6. **Control, telemetry, heartbeats** (status polls, heartbeats, the ladder's
   reports' replies): a few small messages per second → **~10 kbit/s** at both
   rungs (≤ 50 as a bound).

## The sums

| term | 4000 | 7000 |
| --- | ---: | ---: |
| 1 video payload | 4,000 | 7,000 |
| 2 FEC parity | 800 | 1,187 |
| 3 audio (2/4, IP-level) | 3,200 | 3,200 |
| 4a video RTP header | 48 | 79 |
| 4b video+parity UDP/IP | 132 | 212 |
| 5 overlay on the tailnet counter | 0 | 0 |
| 6 control | 10 | 10 |
| **predicted total** | **8,190** | **11,688** |
| measured (tailnet `tx_bytes`) | 8,286 | 11,420 |
| **residual (measured − predicted)** | **+96 (+1.2 %)** | **−268 (−2.3 %)** |
| predicted excess over the video | 4,190 | 4,688 |

**The prediction:** the ~4.3 Mbit/s excess is mostly **audio (3.2 Mbit/s,
constant)**, then **parity (0.8-1.2, grows with the rung)**, then per-packet
headers (~0.2-0.3). The overlay's own framing is not on this counter and nothing
fragments. Audio is the largest term at both rungs; parity is second. If this
holds, G4-W2 runs.
