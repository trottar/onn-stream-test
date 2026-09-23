---
memory_schema: 1
as_of: 2026-09-23
status: D-BASE-T3 — AIR (pre-registered reading): at and after the warm-state step the host sent every audio packet (0 send errors, 0 kernel send-buffer drops, 200/s exact) and the onn's audio socket and UDP stack dropped none; the packets are lost between the host's NIC and the onn's IP stack; no counter added, no code changed
---

# D-BASE-T3 — where the warm-state audio loss happens

Task: `handoffs/D-BASE-T3_TASK.md` (authorized by the user 2026-09-23),
the probe `T2` named. Evidence: `d_base_t3_2026-09-23/`, SHA-256 of every
file in `d_base_t3_2026-09-23/t3_sha256.txt`.

## What the code already counts (read before the run)

- **Host sender** (`companion/native_session_io.py`,
  `_linux_sender_loop`): one SCHED_RR/1 thread, a **non-blocking** UDP
  socket (`SO_SNDBUF` 64 KiB), a 5 ms deadline pacer. Per tick it sends
  one datagram; on `BlockingIOError`/`OSError` it counts `send_errors`
  **and still advances the RTP sequence**. So **sent + send_errors =
  sequence advance**, and `send_errors` is exactly the host's share of the
  client's `lost_packets`. A buffer underflow sends silence (counted
  `underflows`), not a gap. Exposed in `native-stream-status.audio`:
  `packets_sent`, `send_errors`, `helper_status.send.{underflows,
  intervals}`. **No counter was missing — nothing added, no code change.**
- A qdisc/sndbuf drop behind a *successful* `sendto` is invisible to the
  sender; Linux counts it in `/proc/net/snmp` `Udp SndbufErrors` — sampled.
- **Client** (`NativeAudioReceiver`): `lost_packets` from RTP sequence gaps
  on the receive thread, before queueing.

**Already on record before the session:** `T2`'s four statuses show
**`send_errors` 0** in every session (sent 241,094-241,515 against client
losses of 698-1,415), and the host's kernel had **4** `SndbufErrors`
since boot. `P8` arm A ended with **0** drops on the onn's audio socket
while losing 544.

## The session

Cold start: **65 min** after the last `session_ended` (T2's S-d,
17:39:40 UTC). One 25-minute attract-mode hold of the PS1 reference
title, zero input, adopted profile (`any_override: false`), **12/17 from
the profile**, `p9_run.sh` copied byte-for-byte, PLAYING **18:46:15 UTC**,
BACK at 19:11. Sampled:

- **onn socket**, 2 s — `P5`'s `p5_socket_sample.py` (`SAMPLER=on`): the
  audio (48101) and video (48100) rows of `/proc/net/udp6`, `rx_queue`,
  `drops` (787 rows);
- **host**, 2 s — `t3_host_sample.py`: sender sent / errors / underflows,
  kernel `Udp SndbufErrors` / `OutDatagrams`, `Ip OutDiscards`, `eno1`,
  sender-thread CPU (827 rows);
- **onn stack**, 10 s — `t3_onn_stack_sample.sh`, **added during the run**
  (started 18:45:38, before PLAYING, so the whole hold is covered): the
  onn's `/proc/net/snmp` Udp (`InErrors`, `RcvbufErrors`) and `wlan0` rx
  packets / errs / drop (162 rows);
- **heat**, 10 s — `T2`'s `t2_sample.py` (166 rows).

adb during the hold: 276 client processes, **all the samplers'** (0
other) — the cost `P8` cleared.

## Raw numbers first — per minute

| min | UTC | client audio lost | client video lost | onn audio-socket drops | onn video-socket drops | onn audio `rx_queue` max (B) | host sent | host send errors | host SndbufErrors | onn Udp RcvbufErrors | onn wlan0 rx_drop | onn cpu °C | Opal SoC °C | host Tctl °C |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 18:46 | 3 | 22 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 296 | 61.8 | 61.2 | 41.1 |
| 3 | 18:48 | 3 | 17 | 0 | 0 | 0 | 12,001 | 0 | 0 | 0 | 242 | 64.2 | 61.0 | 48.8 |
| 5 | 18:50 | 0 | 0 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 199 | 65.6 | 61.2 | 52.3 |
| 7 | 18:52 | 11 | 2 | 0 | 0 | 2,304 | 12,000 | 0 | 0 | 0 | 178 | 66.7 | 61.5 | 53.0 |
| 8 | 18:53 | 25 | 7 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 8,398 | 67.0 | 61.5 | 53.0 |
| 9 | 18:54 | 23 | 14 | 0 | 0 | 0 | 12,001 | 0 | 0 | 0 | 276 | 67.3 | 63.8 | 53.9 |
| 10 | 18:55 | 18 | 6 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 8,335 | 67.8 | 63.2 | 54.6 |
| **11** | **18:56** | **42** | 13 | **0** | 0 | 2,304 | 12,000 | **0** | **0** | **0** | 382 | **68.0** | 62.0 | 54.9 |
| 12 | 18:57 | 39 | 7 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 4,340 | 68.0 | 62.2 | 54.3 |
| 15 | 19:00 | 65 | 96 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 4,339 | 68.5 | 62.3 | 54.7 |
| 19 | 19:04 | 59 | 24 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 320 | 68.7 | 62.7 | 55.4 |
| 24 | 19:09 | 87 | 2 | 0 | 0 | 2,304 | 12,001 | 0 | 0 | 0 | 239 | 68.5 | 63.0 | 55.0 |

(Every minute of the 24 is in `t3_analysis.txt`; the omitted rows read
the same in every counter column — **0 / 0 / 0 / 0 / 0**, sent
12,000-12,401.)

Full audio-loss series: 3 2 3 4 0 1 **11 25 23 18 42** 39 24 52 65 31 25
46 59 35 56 34 54 87. **The step reproduced** from cold — the rise begins
at minute 7 (onn 66.7 °C) and crosses 30/min at minute 11 (onn 68.0 °C),
the same thermal state as `T2` (onn 66.5-67.6 °C).

Totals: **host sent 301,482, send errors 0**; client received 300,453,
lost 848 (the 181 unaccounted are packets sent before the client's socket
opened and after BACK, as in `P9`). One host tick below 390 packets, at
18:46:12 (stream start); **none after**.

## The reading — AIR

After the step (minutes 11-24): the client lost **649** audio packets.

| where | counted | share |
| --- | ---: | ---: |
| onn audio socket `drops` | **0** | 0 % |
| onn video socket `drops` | 0 | — |
| host `send_errors` + kernel `SndbufErrors` | **0** | 0 % |
| host timer overruns | 0 | — |
| onn kernel `Udp RcvbufErrors` / `InErrors` | **0** / 0 | — |

**Neither end loses them.** The sender emits every sequence number on its
5 ms grid, the host kernel accepts every one, and the onn's IP/UDP stack
and socket never drop one (the audio socket never held more than two
datagrams — the receive thread keeps up). **The packets are lost between
the host's NIC and the onn's IP stack: the wired hop, the Opal, the air,
or the onn's Wi-Fi driver/firmware below `wlan0`'s counters.**

`wlan0` rx_drop moves in blocks of ~4,000-12,000 every few minutes
(Android counts frames it discards before IP there) and **does not track
the loss**: 2,276/min before the step, 2,328 after, rho +0.20; rx_errs 0.

**This contradicts `T2`'s reading of the radio as flat** — at 10 s
averages RSSI, MCS and retry ratio did not move, but something between
the ends drops audio packets at the warm state. The Opal's SoC
temperature (`T2`: the highest rho, +0.644) is the one thermal signal
that sits inside "between". **Not located further**: the next instrument
is the Opal's per-station per-second counters, which this AP does not
expose (`O1`) — recorded as the roadmap's `host_link` first fact.

## Not in the rule, noted

- **Video loss rose after the step here** (9.1 → 17.5 per minute, one
  minute of 96), unlike `T2` (rho −0.12, no step). One session; the audio
  step is the larger and cleaner effect.
- The step was softer than `T2`'s (a rise from minute 7, 30/min crossed
  at 11); the thermal state at the rise matches.

## Thresholds — proposals only, beside `T2`'s

First minute ≥ 30/min: onn cpu **68.0 °C** (`T2`: 67.6), Opal SoC
**62.0 °C** (61.0), host NVMe S2 **40.4 °C** (40.0), host Tctl **54.9 °C**
(53.9). No minute reached 100/min in 25 minutes (`T2`: act 67.8 / 62.3 /
42.4 / 54.7). **The lever is not at either end**: no receive-thread,
`SO_RCVBUF` or sender change would recover packets that neither end
sees. A `native-stream-status` flag on the onn's cpu-thermal ≥ ~67.5 °C
remains the only proposal; **none enforced**.

## State at the end

Companion under systemd, MainPID owns 8765, 12/17 from the profile, 0
`PRIVYHUB_*` in its environ or the manager's, `any_override: false`,
game inactive, banner cleared, all samplers stopped. **No recovery file
created.** No code changed. Nothing on the Opal changed.

## Corrections (Cowork verification, 2026-09-23)

1. The sentence above originally added "the one on disk is `R3b`'s
   Tekken 3 file of 2026-09-22" — out of date, as in `T2`: no
   `.state.recovery` exists on disk; the only copy of the N150 save is
   `d_base_r3c_2026-09-22/recovery_copy/`.
2. **The loss is not audio-only — video's FEC hides its share.** Video
   `lost_packets` is counted *after* FEC recovery. Recomputed per minute
   from the heartbeats, `fec_recovered_packets` steps up with the audio
   loss: `T3` 1-4/min cold → 11-21/min warm (Spearman with audio loss
   **+0.51**); `T2` S-c 2-6 → 8-16 (**+0.79**); S-a +0.50; S-b (warm
   throughout) flat at 12-24 as its audio was. So the path drops video
   packets at the warm state too; the 8+1 XOR recovers most of them and
   the post-FEC counter stays flat. The "audio-specific" reading in `T2`
   and above should read: **path-wide at the warm state, visible on audio
   because audio has no FEC.** Per packet the two are still not equal —
   `T3` audio 848 of 301,482 (0.28 %) against video ≈ 250 recovered + 338
   lost of 1,240,579 (≈ 0.05 %), packets of similar size (962 B audio
   mean, ~1,066 B video) — so audio is also lost ~5x more often, which
   remains unexplained (traffic pattern: one isolated 962-byte datagram
   every 5 ms against video's per-frame bursts, is the candidate).
3. **There is therefore a lever at the ends**: the "AIR" reading rules
   out recovering the *same* packet at either end, but not sending it
   twice. Audio redundancy — a delayed duplicate of every audio datagram
   with sequence-based de-duplication on the client, or an XOR group like
   video's — recovers packets lost between the NIC and the onn's stack at
   a cost of +1.5 Mbps (duplication) on a 260 Mbps link. `T3`'s
   `crossfaded_packets` 843 ≈ `lost_packets` 848: every lost audio packet
   is currently concealed by a crossfade; redundancy would replace those
   with the real audio. Proposed as the next task (`P10`), the user's
   decision.

## Privacy

Private addresses in the companion journal / report / status replaced
with `<IP_REDACTED>`; no MAC anywhere; the onn-stack sampler drops the
`wlan0` line's name and keeps numbers; `h2_prep_redact.py --check` passes
on every sampler file and the analysis.
