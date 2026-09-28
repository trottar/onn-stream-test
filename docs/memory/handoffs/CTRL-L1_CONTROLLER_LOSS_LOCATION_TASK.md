---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — CTRL-L1: locate the controller transport's 1-2 % lost_packets (onn → host input datagrams, ~25,700/min at zero input): host receive-socket drops vs the path, plus what the counter actually counts (loss vs reordering) — read-only instruments on the host beside plain holds; no code change; authorized by the user 2026-09-24 for the weekend queue
---

# CTRL-L1 — where the controller datagrams go missing

**Why.** `docs/KNOWN_ISSUES.md` (2026-09-24): the controller transport
(`udp_full_state`, client → host, port from `native-stream-status`)
reports 213-438 `lost_packets` per minute with **zero input** in every
`S1` hold, ~650/min in the close-out sessions, ~225/min in rerun session
1 (real play), and **~3.8/min in rerun session 2** — a 60× swing between
two play sessions on the same afternoon. `bad_packets` 0 always. Nobody
has looked at where the datagrams are lost or whether "lost" is loss or
reordering. It is the reverse direction to everything `D-BASE` located
(`T3`: host → onn, between the NIC and the onn's IP stack). An input path
losing 1-2 % is worth one bounded measurement before Phase E.

Read first: `companion/native_session_io.py` (the controller receiver:
what increments `lost_packets` — sequence gap on arrival? does a late
packet decrement it, or count as `rejected`? what is a "full state"
datagram, its size and rate), the client's sender
(`PrivyHub/app/src/main/java/…` — the controller/input sender: rate, size,
whether it sends at a fixed tick or on change), `evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`
(`p5_socket_sample.py`: `/proc/net/udp{,6}` `drops` sampling — reuse it
for the **host** socket on the controller port), `evidence/D_BASE_T3_AUDIO_LOSS_LOCATION_2026-09-23.md`
(the host-side NIC/stack counters it read; read the same ones for
receive), `evidence/O1_OPAL_AIR_VIEW_2026-09-21.md` (Opal read-only
counters), `TOOLS.md`.

**Scope.** Read-only instruments and plain holds; **no code change**
anywhere; adopted profile; companion under systemd; Opal read-only. If
the receiver's counting cannot be settled from source without a change,
say so and stop at the location question.

## Do

1. **What the counter counts** (source, then a 60-second capture): read
   the receiver; then during one hold run a packet capture on the host
   for the controller port (`tcpdump` on the host's own interface,
   60 s, headers only, written to the evidence dir **with addresses
   stripped** — capture to a pcap, extract only sequence numbers and
   arrival times with a script, then delete the pcap; the record carries
   no address). From the sequence series: true gaps (never arrived),
   reordering (arrived late), duplicates; datagram rate and size. Say
   what `lost_packets` counted in that minute against the capture.
2. **Location**, three 20-minute holds (cold, warm, warm), `T2` sampler
   on: per minute beside the companion's `lost_packets`/`packets_received`
   deltas (`native-stream-status` every 30 s):
   - host socket: `/proc/net/udp{,6}` `drops` and `rx_queue` for the
     controller port (the `P5` sampler pointed at the host);
   - host NIC/stack: `rx_dropped`, `rx_errors`, `rx_missed`, softnet
     drops, `UdpInErrors`/`RcvbufErrors` from `/proc/net/snmp` — deltas;
   - Opal (read-only): the same interface counters `O1` read;
   - the onn: `dumpsys`/`/proc/net/udp` for the client's send socket if
     readable over adb (0 foreign adb rule: adb reads only between
     holds, or accept and record them as foreign).
   Pre-registered reading: **HOST SOCKET** if socket `drops` deltas
   account for ≥ 80 % of `lost_packets` deltas in ≥ 2 of 3 holds; **HOST
   STACK/NIC** if the NIC/stack counters do; **PATH** if all host-side
   counters are +0 while `lost_packets` accumulates (the `T3` outcome,
   mirrored); **REORDERING, NOT LOSS** if step 1 shows the counter
   counting late arrivals; **INDETERMINATE** otherwise. Also report the
   per-minute rate's relation to the warm state (the `T2` threshold) and
   to `packets_received` rate.
3. **The 60× swing**: from the stored status snapshots of rerun sessions
   1 and 2 (`evidence/c3_l3a_r1…`, `…r2…`, the `conditions_before/after`
   in their states) and the journal, whether anything differs in the
   client's send rate (`packets_received` per minute) between them; the
   record states the two rates and stops there.

## Record and memory

`evidence/CTRL_L1_CONTROLLER_LOSS_LOCATION_<date>.md`, evidence dir with
the sequence-series extract (no pcap kept), the per-minute tables, the
sampler outputs, thermal jsonl, manifest; `docs/KNOWN_ISSUES.md` (the
item: located or not, and what the counter counts); `CURRENT.md` one
line; `investigations/ACTIVE.md`; the daily file. No addresses, MACs or
device identifiers in any file; `h2_prep_redact.py --check` on every text
file. Nothing committed.
