---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: 1fc2e19
---

# G4-W1 — the wire overhead, term by term

**Classification: ACCOUNTED from the files; nothing built, nothing adopted, nothing committed.**

- **The ~4.3 Mbit/s is mostly audio.** The PCM audio with its 2/4 redundancy is **3,213 kbit/s** on the tailnet
  interface at every rung: 400 datagrams/s × 1,004 B. That is 39 % of the wire at 4000 and 27 % at 7000.
- **Second: FEC parity,** 889 kbit/s at 4000 and 1,229 at 7000 (IP-level). It grows with the rung.
- **Third: per-packet headers** (RTP + UDP/IP), 179 / 292 kbit/s.
- **Control is ~10 kbit/s. Nothing fragments.**
- **The overlay's WireGuard cost is not on the tailnet counter:** the tailnet interface is a TUN device. That cost
  shows up on the underlay instead, at 69-74 B per packet: **+550 kbit/s at 4000 and +796 at 7000.** The hotspot
  carries that too.
- **The terms close against the measured totals:** a residual of 0 at 4000 (where parity and control are the
  remainder, split) and −13 kbit/s (−0.1 %) at 7000, where every term is measured independently.
- **A correction to G4-S1:** its "11.42 Mbit/s at 7000" is the sampler's KiB/s × 8 / 1000. In decimal Mbit/s it is
  **11.70**.
  - So the excess over the video is **not constant: 4.27 Mbit/s at 4000 and 4.69 at 7000.** It is audio's constant
    3.21 plus parity and headers that scale with the rung.
  - G4-S2's 8.29 was read from `tx_bytes` directly and is correct.

- Task: `handoffs/G4-W1_WIRE_OVERHEAD_BREAKDOWN_TASK.md` (queue `QUEUE_2026-10-18.md` #1), session B, software only.
  **Baseline `1fc2e19`.**
  - The tree carried 4 files not committed at the start (`g4_w1_2026-10-18/git_status_at_start.txt`): `_cowork_prompt_b.txt`
    and the queue and its two task files. None were touched.
- No companion restart, no stream, no game, no adb. Not touched: `~/.config/privyhub/`, the audit log, the drop-ins,
  `companion/session_identity.py`, `companion/overlay/`. No code changed. Nothing in `logs/` was written. The one log
  read, the relay's frame log, was copied first (below).

## 1. The arithmetic (written before the files)

`g4_w1_2026-10-18/arithmetic_written_before_files.md`, sha256 `a91a63a2…3010c`, hashed at 18:31:00Z.

- **What it was written from:** only the task file and the prose of the records it names.
- **What was not read before the hash:** no data file, and no code (the audio sender, the FEC relay,
  `native_stream.py`).
- **The prediction:**
  - audio 3,200 kbit/s at both rungs, then parity 800 / 1,187, then headers 180 / 291;
  - the overlay's per-packet cost 0 on the tailnet counter (a TUN), about 68 B per packet on the underlay;
  - no fragmentation (the largest inner packet 1,239 B ≤ 1,280);
  - totals 8,190 / 11,688 kbit/s against 8,286 / 11,420;
  - "audio the largest term at both rungs, parity second".

## 2. The reading (files only)

`g4_w1_2026-10-18/read_files.py` → `reading.json` (console `reading_console.txt`). Read only.

**The inputs:**

| input | what it gave |
| --- | --- |
| G4-S2 run 1 `samples.jsonl` | per second, both interfaces' tx KiB/s and packets/s. Window 18:03:10-18:08:30Z at 4000 (320 s). |
| G4-S1 run 1 `samples.jsonl`, `telemetry.jsonl` | the same at 7000, window 22:52:26-23:02:26Z (600 s), and the client's received / lost video packets |
| the relay's frame log `logs/games/native_frame_sizes.jsonl` | per second, the H.264 payload bytes and the RTP data packets. **Copied first** to `g4_w1_2026-10-18/inputs/` (sha256 `8a5fceea…5ed3`, equal to the source). It covers 10-17 04:23Z → 10-18 18:08Z, so G4-S2's window and two 7000 segments, but not G4-S1. |
| G8-S1 cell 22 `impairment_run1.jsonl` | the shim (post-FEC) at 7000, aligned to the frame log's 04:23-04:30Z by packet count (lag 290 s, score 0.027, 407 s) |
| G8-S3 cell 1 `impairment_run1.jsonl` | the same method at 5000 as a check: it reproduces G8-S3 §3 (parity 108.9 pps, 0.179 per data packet, 1.82 per frame, 1,119 B) |
| G5-S3's LAN smoke `samples.jsonl` (16:00:30-16:10:00Z) | the LAN interface at 7000 against the frame log |

**The code, read after the hash:**

- **Audio** (`companion/native_session_io.py`, `NativeAudioStreamer`):
  - 48,000 Hz × 2 ch × s16 → 240 frames = **960 B per 5-ms datagram**;
  - the header is **PHA1 `<4sBBHII` = 16 B, not RTP's 12**;
  - each tick sends the original and then the stored copy of n − 4;
  - an empty buffer sends **silence**, so the rate is 400/s whatever the game plays;
  - the IP size is 960 + 16 + 28 = **1,004 B**, so 400 × 1,004 × 8 = **3,212.8 kbit/s** (D-BASE-P10: 3.21).
- **FEC** (`companion/native_fec_relay.py`):
  - a 23-B `PHF1` header plus the group's largest payload;
  - groups of ≤ 8 data packets of one RTP timestamp;
  - `xor8_1` only (C4-M1's `xor8_2` is env-only and off);
  - ffmpeg's `pkt_size=1200` → data payload ≤ 1,188 B.
- **The sampler** (`tools/e1_sampler.py:479`): `tx_kBps` is bytes / **1024** / dt.
  - **eno1 is an Ethernet device, so its counter includes the 14-B Ethernet header.** `tailscale0` is a TUN and counts
    the inner IP packet only.

**The table** (kbit/s; "measured" = from the files above, "derived" = a remainder split under a stated assumption):

| term | predicted 4000 | measured / derived 4000 | predicted 7000 | measured / derived 7000 | source |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 video payload (H.264) | 4,000 | **4,011** (496.8 data pkt/s, 8.29 / frame) | 7,000 | **7,007** (821.8 data pkt/s, 13.71 / frame) | frame log, G4-S2 window; 7000: the log's two 7000 segments (G4-S1 not covered) |
| 2 FEC parity (UDP payload) | 800 (87 pkt/s) | **869** (89.7 pkt/s; 0.181 / data pkt; 1.50 / frame), derived | 1,187 (129 pkt/s) | **1,199** (131.1 pkt/s; 0.159 / data pkt; 2.18 / frame; 1,144 B) | 4000: tailnet remainder split, assuming parity 1,239 B IP and control 100 B; 7000: shim cell 22 − frame log |
| 3 audio, 2/4 (IP-level) | 3,200 | **3,212.8** (400 × 1,004 B) | 3,200 | **3,212.8** | the code; packets close (below); D-BASE-P10 3.21 |
| 4a video RTP header | 48 | **47.7** | 79 | **78.9** | 12 B × data pkt/s |
| 4b video + parity UDP/IP | 132 | **131.4** (111.3 + 20.1) | 212 | **213.5** (184.1 + 29.4) | 28 B × pkt/s |
| 5 overlay, on the tailnet counter | 0 | **0** (TUN; 1,034.6 B / pkt; packets close) | 0 | **0** (1,081.0 B / pkt) | the counter's device type; pkt/s closure |
| 5′ overlay, on the underlay (not in the total) | ~538 (~68 B / pkt) | **550** (68.7 B / pkt) | ~733 | **796** (73.6 B / pkt; 31 s relayed in the window) | (eno1 − tailnet − eno1's idle median − 14 B Ethernet) per tailnet packet |
| 5″ fragmentation | none | **none** — tailnet 1,000.8 pkt/s = 496.8 + 400 + 89.7 + 14.3; eno1 +16.7 pkt/s over the tailnet beyond idle | none | **none** — 1,352.7 = 821.8 + 400 + 131.1 − 0.2 | pkt/s closure; largest inner packet 1,239 B ≤ 1,280 |
| 6 control, telemetry, heartbeats | 10 | **11.4** (14.3 pkt/s), derived | 10 | **≈ 0** (−13 ± error; remainder after the shim's parity) | remainder |
| **total** | **8,190** | **8,283** (sampler mean; the record's 8,286 median) | **11,688** | **11,698** (decimal; G4-S1's "11.42" is KiB-based) | tailnet tx |
| **residual vs the prediction** | | **+93 (+1.1 %)** | | **+10 (+0.1 %)** | |
| **residual vs the measured terms** | | 0 by construction (2 + 6 are the remainder) | | **−13 (−0.1 %)** | |
| excess over the video | 4,190 | **4,272** | 4,688 | **4,691** | |

**Cross-checks:**

- **At 4000,** the client counted 487.3 video packets/s received + 0.1 lost (relay: 496.8). Its `recent_mbps` median
  was 4.04.
- **At 7000 (G4-S1),** the client counted 766.7 received + 35.8 lost = 802.5. With that count instead of the frame
  log's, parity solves to 120.9 pkt/s and control to 29 pkt/s. The total closes either way.
- **The LAN at 7000** (G5-S3's smoke, eno1 less 14 B per packet): 11,764 kbit/s IP-level, 1,405 pkt/s, against the
  same terms (7,016 video, 823.6 data pkt/s). The LAN host also carries other traffic: the remainder of 182 pkt/s
  splits to ~124 parity + ~58 other.

**Where the prediction was wrong (disclosed):**

- **The audio header** is PHA1's 16 B, not RTP's 12: +12.8 kbit/s.
- **The parity ratio:** predicted lower at 4000. It is 0.181 at 4000, 0.179 at 5000 and 0.159 at 7000. Per frame it
  is 1.50 / 1.82 / 2.18, against the predicted 1.45 / — / 2.15. Large frames fill their groups; small ones leave a
  part-filled group.
- **The 7000 target in the arithmetic, 11,420,** was G4-S1's KiB-based figure. In decimal it is 11,698. The
  arithmetic's −268 "residual" was that unit.

**Limits:**

- G4-S1's window has no frame log. Its video payload and packet rate come from the log's other 7000 sessions:
  7,003-7,016 kbit/s, 13.71-13.73 per frame.
- At 4000 no shim ran. The parity / control split rests on two sizes, parity 1,239 B and control 100 B. Parity
  ± 10 B moves it by < 1 kbit/s.
- One 4000 window (320 s), one 7000 window (600 s), one title (PS1 reference).

## 3. The proposal (for the user, not decided)

**Cut the audio term first.** It is the largest at both rungs and does not shrink with the rung.

| | 4000 | 7000 |
| --- | ---: | ---: |
| tailnet total today | 8,283 kbit/s = **3.73 GB/h** | 11,698 kbit/s = **5.26 GB/h** |
| what the hotspot carries (+ the overlay's 5′, IP-level) | 8,833 = **3.97 GB/h** | 12,494 = **5.62 GB/h** |
| audio today (PCM 2/4) | 3,213 = **1.45 GB/h (39 %)** | 3,213 = **1.45 GB/h (27 %)** |
| parity today (IP) | 889 = 0.40 GB/h (11 %) | 1,229 = 0.55 GB/h (11 %) |

1 kbit/s for an hour = 0.45 MB.

**Example saving: Opus at 128 kbit/s in 10-ms frames, keeping the 2/4 duplicate.** G4-W2 states the final parameters
and their numbers.

- Per datagram: 160 B + 16 header + 28 UDP/IP = 204 B. At 200 datagrams/s that is **326 kbit/s**.
- **The saving is −2,887 kbit/s = 1.30 GB/h at either rung.** That is 35 % of the tailnet total at 4000 and 25 % at
  7000.
- Plus 200 fewer packets/s on the underlay: −110 kbit/s, 0.05 GB/h.
- At 4000 the tailnet would carry ~5.4 Mbit/s, ~2.4 GB/h.

**Not proposed:** copies 1 (PCM without redundancy). It saves 0.72 GB/h but gives up D-BASE-P10's 96-98 % loss cut.

**Second (named, not designed here):** parity, 11 % of the wire. That is C4's adaptive-FEC question: parity only when
loss justifies it. Fragmentation is not a term, so the video packet size against the overlay MTU needs no task.

**So G4-W2 runs** (audio among the two largest terms: it is the largest).

## 4. Files

`g4_w1_2026-10-18/`:

- the arithmetic, its hash and the time it was hashed: `arithmetic_written_before_files.md`,
  `arithmetic_written_before_files.sha256`, `arithmetic_hashed_at.txt`;
- the reading: `read_files.py`, `reading.json`, `reading_console.txt`;
- the copied input: `inputs/native_frame_sizes.jsonl`;
- the baseline and the tree: `baseline_head.txt`, `git_status_at_start.txt`;
- `redact_check.txt`, `manifest.sha256`.

Also `logs/g4_w1_git_status.txt` and ROADMAP §G4 (one line).
