---
memory_schema: 1
as_of: 2026-09-24
status: CTRL-L1 DONE — controller-transport lost_packets located: PATH (pre-registered). In three plain 20-min holds (C cold, W1, W2 warm) the counter rose +171 / +266 / +301 (8.8 / 13.6 / 15.4 per min) while every host-side counter (the controller socket's drops, Udp RcvbufErrors/InErrors/InCsum/Mem, softnet dropped, NIC rx_dropped/missed/fifo/errors) and every Opal interface counter read +0, and the onn's UDP stack sent everything (SndbufErrors +0). The counter counts sequence gaps on ONE global sequence over four players and counts a reordered pair twice; the per-player lower bound puts ≥ 40-67 % of it (these holds) and 85-95 % (the high-loss sessions of 23-24 Sep) as true non-arrival. The 60-second capture (step 1) was NOT RUN: tcpdump is not installed and there is no root. The holds ran in the low regime (9-15/min, not 213-438/min). Session 1 and 2's client send rates were equal (~25,960 / ~25,955 per min).
---

# CTRL-L1 — where the controller datagrams go missing

Task: `handoffs/CTRL-L1_CONTROLLER_LOSS_LOCATION_TASK.md` (weekend queue item
3, authorized by the user 2026-09-24). Evidence: `ctrl_l1_2026-09-24/`
(manifest `sha256_manifest.txt`).

**Scope.** Read-only instruments beside plain holds. There was no code
change anywhere and the adopted profile was confirmed before each hold.
The companion ran as its systemd unit and the Opal was read-only (`ssh
opal cat /proc/net/dev` and the `T2` sampler's reads). The onn was read
over adb between holds only, apart from the `T2` sampler's 10 s reads,
which are recorded as foreign (`runs/adb_during_hold_*.txt`: 37 / 38 / 41
adb client processes seen).

## 1. What the counter counts

Settled from source, with the capture NOT RUN.

**The receiver** (`companion/native_session_io.py`,
`NativeControllerBridge._receive_loop`):

- It keeps **one** `_last_sequence` for all players.
- A forward jump adds `seq − expected` to `lost_packets`.
- A late packet (backwards) adds nothing but **resets** `_last_sequence`
  to the late value. So the **next** packet reads as a gap again: **a
  swap of two adjacent packets adds 2, though both arrived.**
- A duplicate adds 0.
- `packets_received` and `updates_by_player` count every accepted
  datagram.

**The sender** (`NativeControllerSender.kt`):

- Every tick sends players 0-3 back to back, 36 bytes each, then sleeps
  8 ms: ~430 datagrams/s (~26,000/min, zero input).
- It uses one global sequence, and the sequence advances **even on a send
  exception**. So each client `send_errors` is one gap at the host. There
  were 4 per hold here, 12 of the 738 counted.

**The capture (step 1) was NOT RUN.** `tcpdump` is not installed on the
host, `sudo` needs a password, and no other capture path runs without
root. So reordering cannot be counted directly.

**What bounds it instead.** Every tick sends each player once, so the
per-player receive counts can differ only by non-arrival (± 1 at the
ends) or duplication. **Σ(max − nᵢ) is a lower bound on packets that
never arrived**:

| | lost_packets | true-loss lower bound | share |
| --- | ---: | ---: | ---: |
| C | 171 | 114 | 67 % |
| W1 | 268 | 106 | 40 % |
| W2 | 305 | 142 | 47 % |
| 23-24 Sep high-loss sessions (T2 Sa-Sd, T3, close-out C/W, P10, S1 H/T; `stored_sessions_scan.txt`) | 773-13,647 | — | **85-95 %** |

**So the counter is mostly true non-arrival**, not reordering: 85-95 % in
the high-loss regime and at least 40-67 % in these low-loss holds. The
rest may be reordering (counted twice) or loss spread evenly across the
players, which the bound cannot see.

**Neither mechanism reads as "REORDERING, NOT LOSS".** That reading is
not supported.

**An unexplained older pattern.** In the stored sessions of 21-23 Sep
before 09:17Z, the per-player spread exceeds `lost_packets` itself (LB >
lost). It is recorded, not explained.

## 2. Location: three holds

The holds were C (cold: 44 min after the last `session_ended`), W1 and W2,
each 20 min.

- **Harness** (`ctrl_l1_all.sh`): the close-out's `p9_run.sh`, byte for
  byte, in attract mode with zero input.
- **Samplers**: `T2` at 10 s, and `ctrl_l1_host_sample.py` at 10 s (status
  and Opal every 30 s).
- **Analysis**: `ctrl_l1_analyze.py` → `ctrl_l1_analysis.txt`, with a
  per-minute table for each hold.

| hold | lost_packets | per min | packets_received per min | socket drops | Udp RcvbufErrors / InErrors | softnet dropped | NIC rx_dropped / missed / fifo / errors | Opal wlan1 / br-lan / eth0 drop, errs | socket rx_queue max |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | ---: |
| C | +171 | 8.8 | 26,043 | **+0** | +0 / +0 | +0 | +0 / +0 / +0 / +0 | +0 all | 5,120 B |
| W1 | +266 | 13.6 | 26,102 | **+0** | +0 / +0 | +0 | +0 all | +0 all | 3,840 B |
| W2 | +301 | 15.4 | 26,071 | **+0** | +0 / +0 | +0 | +0 all | +0 all | 1,280 B |

**The onn's side**, read between holds (`runs/onn_snmp_udp.txt`): `Udp
OutDatagrams` rose +523,464 / +524,844 / +523,925. The client reported
523,128 / 524,552 / 523,684 sent at its report snapshot. **`SndbufErrors`
+0, `InErrors` +0.**

**So every datagram left the onn's UDP stack.** Nothing on the host, from
the NIC to the socket, dropped one. The Opal's interface counters did not
move.

**Reading (pre-registered): PATH**, in 3 of 3 holds. `lost_packets`
accumulated while every host-side counter read +0. This is the `T3`
outcome mirrored. The datagrams are lost between the onn's UDP stack and
the host's NIC:

- the onn's driver or radio;
- the air;
- the Opal's radio below its interface counters.

That is the same stretch `T3` located the host → onn audio loss in. The
host socket (rx_queue ≤ 5 KB of a 256 KB buffer) is ruled out.

**Relation to the warm state and to the send rate.**

- Loss per minute is flat at ~26,000 received/min. The rho against
  received per minute is +0.14 / −0.08 / +0.28.
- In the cold hold, loss rose with the onn's CPU temperature (rho +0.70;
  warm minutes 11.9/min against cool 6.7/min).
- W1 and W2 were almost entirely warm: 14.6 and 7.2/min in warm minutes.
- **The loss comes in bursts.** Most minutes lose 2-12. Five minutes over
  the three holds lost 55-62 each, i.e. ~130-140 ms of sending
  (~55-60 consecutive datagrams): short outages, not a steady drip.

**The regime.** These holds ran at **9-15/min**, like rerun sessions 2
and 3 (~3.8 and ~5.6/min). They did not run at the S1 soak's 213-438/min
or the close-out's ~650/min, on the same build, host, title and harness.
What switches the regime was not located. The stored sessions show:

- the low regime on 21 Sep through 23 Sep 09:17Z;
- the high regime from 23 Sep 15:46Z through the 24 Sep 07:52Z soak and
  rerun session 1;
- the low regime from rerun session 2 on.

**Rerun sessions 1 and 2 ran on the same companion process** (MainPID
started 03:38 local, no restart between them).

## 3. The 60× swing between rerun sessions 1 and 2

The client's send rate is taken from its decoder reports (`controller.
packets_sent / duration`):

- **Session 1**: 114,932 / 270.7 s and 348,100 / 804.5 s, i.e. **25,476
  and 25,960 per min** (two client sessions, split by the accidental
  BACK).
- **Session 2**: 432,936 / 1,000.8 s = **25,955 per min**.
- For scale, session 3 sent 448,412 / 1,035.2 s = 25,991 per min.
- `send_errors` 0 in all three.

The host's `packets_received` per minute for sessions 1-2 was not stored
(no status snapshot), so the record stops here, as the task asks. **The
send rates do not differ.**

## Beside it: the video rows of these holds (context)

| hold | spikes/min | fps | stale/min | video loss/min (post-FEC) | max gap ms | audio underruns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C | 28.2 | 59.94 | 0.30 | **14.32** | 332 | 8 |
| W1 | 30.8 | 59.94 | 0.45 | **16.54** | 383 | 20 |
| W2 | 28.1 | 59.89 | 0.85 | **24.01** | 384 | 24 |

**Video loss exceeded the close-out's < 10/min target in all three
holds**: 14-24 against 8.7 / 8.4 at close-out. The max gap was 332-384 ms
against 163 / 110. This is recorded as a fact of tonight's path, the same
path that located the controller loss. It was not investigated here.

## Files (`ctrl_l1_2026-09-24/`)

- **Harness and samplers**: `ctrl_l1_all.sh` and `ctrl_l1_all.log`;
  `p9_run.sh` and `t2_sample.py` (the close-out's); `ctrl_l1_host_sample.py`.
- **Sampler output**: `host_samples.jsonl` and `t2_samples.jsonl` (386
  rows each), and the sampler logs.
- **Analysis**: `ctrl_l1_analyze.py` → `ctrl_l1_analysis.txt`;
  `stored_sessions_scan.{py,txt}`.
- **`runs/`**: per hold, the `armcheck_*`, `status_*`, `report_*`,
  `heartbeat_*`, `frames_*` and `alpha_*` files, the journal
  `companion_*.log`, `encoder_cmd_*` and `adb_during_hold_*`; plus
  `onn_snmp_udp.txt` and `index.txt`.

**Redaction.** Every text file except the three decoder-report byte copies
was passed through `h2_prep_redact.py`, and `--check` reports 0 residual
matches. The report copies carry the one known false positive, the core
version string.

- The journals carried the client address in the access lines; the
  encoder argv carried the stream target. Both are redacted.
- The sampler script's loopback literal is written `<loopback>` in the
  stored copy.
- No address, port owner, MAC or device identifier remains in any file.
