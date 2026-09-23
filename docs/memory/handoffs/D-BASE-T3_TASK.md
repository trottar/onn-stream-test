---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — D-BASE-T3, locate the warm-state audio loss: the onn's audio receive socket, the host's audio sender, or the air — the probe T2 named and did not run; one cold session with the P5 socket sampler on the audio port plus a sender-side count; authorized by the user 2026-09-23
---

# D-BASE-T3 — where the warm-state audio loss happens

**What `T2` established.** From cold, audio `lost_packets` sits at 1-6/min
for 6-7 minutes and then **steps** to 30-90/min at a warm state (onn
`cpu-thermal` ≈ 67 °C, Opal SoC ≈ 61 °C, host NVMe S2 ≈ 40 °C — all
slow-cooling, all reset by a 30-minute idle). **Video loss does not
follow** (rho −0.12, no step) and **the radio does not move** (RSSI, link
speed, MCS, retry ratio flat). Every temperature rises and falls together,
so correlation cannot pick the end. The step is audio-specific, which
points at an audio-path component, not the path.

Read first: `evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`
(all; the "Not located" paragraph is this task), `evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`
(the socket sampler: the client's Java socket binds the **IPv6** wildcard
→ read `/proc/net/udp6`; a row has **thirteen** fields, `drops` is the
**last**; `p5_socket_sample.py`), `evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md`
and `companion/native_stream.py` / the audio sender (what it counts:
packets sent, send errors, timer overruns — say what exists),
`PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt` (what it
counts on receive: `lost_packets` from RTP sequence gaps, before queueing),
`d_base_t2_2026-09-23/t2_sample.py` (reuse for the thermal timeline),
`TOOLS.md`.

**No code change unless a counter is missing.** If the host audio sender
exposes no per-session sent-packet / send-error / overrun count, add one
to `native-stream-status` (diagnostic, read-only, no behaviour change),
compile, restart through systemd — say so. No client change.

## One narrow question

*At the step, do packets go missing (a) after the onn's socket received
them (its `/proc/net/udp6` `drops` for the audio port rising), (b) before
the host sent them (the sender's count falling short of the RTP sequence
advance, or send errors / timer overruns appearing), or (c) between — the
air — with neither end showing anything?*

## Design — one cold session, 25 minutes, everything sampled

Precondition: **≥ 40 minutes** with no stream (recovery log), so the step
lands inside the session as it did in S-a / S-c. Then one 25-minute
attract-mode hold of the PS1 reference title, zero input, adopted profile,
12/17 from the profile, `p9_run.sh`'s shape.

During it, every **2 s**, into one jsonl:
- **onn**: the audio port's `/proc/net/udp6` row — `rx_queue`, `drops`
  (last field) — and the video port's row beside it as the control
  (`P5`'s sampler, one `adb shell cat` per tick; note the adb cost is
  cleared by `P8`);
- **host**: the audio sender's packet count / send errors / overruns from
  `native-stream-status` (or the added counter), the encoder process CPU
  %, and `ss -u -a` / `/proc/net/udp` for the host's own audio socket
  (tx queue, drops) if it has a readable row; `eno1` tx errors/drops;
- **thermal** from `t2_sample.py` at its 10 s cadence in parallel (onn
  `cpu-thermal`, Opal SoC, host NVMe/Tctl) so the step is placed on the
  same curve as `T2`.

The heartbeat carries the client's `audio_lost_packets` every 2 s: that
is the step's clock.

## Analysis, raw first

Per 2 s tick: client audio loss delta; onn audio-socket `drops` delta and
`rx_queue`; host sent-count delta against the expected 400 packets/2 s
(5 ms cadence), send errors, overruns; the thermal readings at the tick.
Mark the step minute (first minute ≥ 30/min after the cold plateau).

**Pre-registered reading.**
- **Onn receive path** if the audio socket's `drops` delta rises at the
  step and accounts for ≥ 70 % of the client's loss delta from then on
  (video socket's drops staying ~0, as `P5` found) — the onn drops audio
  datagrams in the kernel while warm: the receive thread or its core is
  what slows. Lever named, not implemented: the receive thread's
  priority/affinity or a larger `SO_RCVBUF` for audio (a larger buffer
  was ruled out for *video* by `P5`; audio's socket is separate).
- **Host sender** if the host's sent count falls short of the sequence
  advance, or send errors / overruns appear at the step while the onn's
  socket shows no drops — the sender's timer or its core slows when warm.
  Lever named: pin or raise the audio sender; check whether it shares a
  core with the encoder (record `taskset`/`/proc/<pid>/status` Cpus_allowed
  and the per-core temperatures at the step).
- **Air** if neither end moves — the loss happens between; then the
  radio's flatness in `T2` is contradicted and the next instrument is the
  Opal's per-station **per-second** counters (not available per `O1`) —
  record as the roadmap's `host_link` first fact.
- **Not reproduced** if the step does not occur within 25 minutes from
  cold (loss stays < 10/min) — record the readings and stop.

State thresholds again from this run's curve (warn at 30/min, act at
100/min) beside `T2`'s, proposals only; nothing enforced.

## Record and memory

`evidence/D_BASE_T3_AUDIO_LOSS_LOCATION_<date>.md` (raw first, the tick
table around the step, the reading, the lever named) with the jsonl,
report, heartbeat and SHA-256s under `evidence/d_base_t3_<date>/`;
`CURRENT.md` (fixed headings, `python3 tools/check_memory_health.py`
healthy — trim; Next Action: the user's decision on the named lever, then
the roadmap list); `MEMORY.md` (where the warm-state audio loss happens,
as established); `handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`;
`KNOWN_ISSUES.md` (narrowed); `TOOLS.md` if a counter was added. Teardown
per `TOOLS.md`; companion under systemd at 12/17; nothing on the Opal
changed; no recovery file. Never retry a failing action more than twice.
No addresses, MACs, SSIDs, BSSIDs or device identifiers in any memory or
evidence file. Nothing committed.
