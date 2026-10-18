---
memory_schema: 1
as_of: 2026-10-18
status: TASK HANDOFF — G4-W1 (session B, software only): where the ~4.3 Mbit/s goes. G4-S2 measured 8.29 Mbit/s on the hub's tailnet interface at the 4000 rung and G4-S1 11.42 at 7000 — a near-constant excess over the video. This task accounts for it term by term from the files and the code, with the arithmetic written before the numbers are read, so the next task knows which term to cut. No stream, no restart
---

# G4-W1 — the wire overhead, term by term

Read first: `G4_S2_OFFSITE_REMOTE_LADDER_2026-10-17.md` §4 (the tailnet `tx_bytes` every 10 s; 458 MB in 452.6 s of play at 4000; the three candidates), `G4_S1_…` §3 (11.42 Mbit/s at 7000), `G8_S3_…` §3 (the shim's view of the video+FEC rate at 5000: ~6.04 Mbit/s; FEC parity 0.178 per data packet; audio not on the shim), `E3_S5_AUDIO_SENDER_COST_…` (400 audio datagrams/s), `D_BASE_P10_AUDIO_REDUNDANCY_…` (the 2/4 redundancy: what each datagram carries), `D_BASE_P9_…` / `P9A_…` (the audio cushion), `C4_M1_…` (FEC 8+1), `companion/native_stream.py` and the audio sender (the audio format: sample rate, channels, bytes per sample, samples per datagram; the RTP/UDP framing), `G1_S1_…` (the overlay: WireGuard framing, MTU 1280 — the per-packet cost and any fragmentation of 1,200-byte video packets inside a 1280 MTU).

## 1. The arithmetic, written before the files are read (in the record §1, hashed)

For each term, the formula and its inputs from the code, then the predicted Mbit/s at 4000 and at 7000:

1. **Video payload:** the rung (4000 / 7000 kbit/s nominal; G8-S3's measured mean at 5000 was 5,012 — state the measured mean at 4000 and 7000 if the files have it).
2. **FEC parity:** × 0.178 per data packet (G8-S3), or 8+1's 12.5 % of groups — say which the files show.
3. **Audio payload:** samples/s × channels × bytes × redundancy factor (from the code: what a 2/4 datagram carries); × 400 datagrams/s as a check.
4. **Per-packet framing on the LAN hop:** RTP + UDP + IPv4 per packet × packets/s (video ~1,000/s at 7000 from G8-S1's shim counts; audio 400/s).
5. **The overlay's per-packet cost:** WireGuard + UDP + IP per packet × packets/s; **fragmentation:** a 1,200-byte RTP packet plus framing against MTU 1280 — does it fit, or does every video packet become two on the tailnet interface? (That alone could be ~1 Mbit/s and would scale with the rung — say what it predicts.)
6. **Control, telemetry, heartbeats:** small; estimate from the status-poll and heartbeat rates.

Sum at 4000 and at 7000; compare with 8.29 and 11.42; the residual named.

## 2. The reading (files only)

- The tailnet interface's packet counts, if the sampler kept `tx_packets` beside `tx_bytes` (G4-S2 `samples.jsonl`): bytes per packet on the wire tells framing and fragmentation apart from payload.
- The shim's counters from G8-S1/G8-S3 (video+FEC packets and bytes per second at 5000 and 7000) as the LAN-side truth for terms 1–2.
- The audio sender's actual datagram size and rate: from the code, and from any recorded audio counters (the heartbeat's audio fields; `E3_S5`'s run files).
- The FEC relay's counters for parity per data packet.
- A table: term | predicted at 4000 | predicted at 7000 | measured or derived | source. The residual stated.

## 3. The record and the proposal

`evidence/G4_W1_WIRE_OVERHEAD_2026-10-18.md` + `g4_w1_2026-10-18/` (the arithmetic + hash, the reading script, the table, `redact_check.txt`, `manifest.sha256`); `logs/g4_w1_git_status.txt`; ROADMAP §G4 (a line: "wire overhead accounted: <largest term>"). **Then the proposal, for the user, not decided:** which term to cut first and what it saves per hour at 4000 and 7000 — if audio is the largest, G4-W2 (Opus behind a flag) follows in this queue; if fragmentation is, the fix is the video packet size against the overlay MTU (a different task, named, not designed here).
