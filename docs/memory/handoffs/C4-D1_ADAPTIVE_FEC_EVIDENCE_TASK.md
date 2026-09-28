---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C4-D1: decide adaptive FEC on the evidence already on disk — offline analysis of every stored decoder report and heartbeat series on the adopted build (loss burst structure vs the 8+1 XOR's recoverability, whether loss ever looks like capacity pressure), ending in a decision record: DEFER WITH EVIDENCE or BUILD, per the roadmap's own rule; no runtime, no code change; authorized by the user 2026-09-24 for the weekend queue
---

# C4-D1 — adaptive FEC, decided on evidence

**Why.** `docs/ROADMAP.md` C4: "Only after bitrate adaptation is stable.
Distinguish random packet loss from capacity pressure. Do not blindly
increase parity during congestion. If fixed 8+1 remains the better
engineering choice, explicitly defer dynamic FEC with evidence rather than
adding complexity for its own sake." `D-BASE` produced the evidence: the
loss was the encoder's frame-size tail and is capped (`P6`/`P6a`/`S3`);
the residual on the adopted build is single-packet (98-99 % one-packet
gaps, `P10`), episodic, and lost between the ends (`T3`); 8+1 recovers
14-16 packets/min in the close-out sessions; unrecoverable groups are
0-15 per session. Nobody has asked the one C4 question of that data: how
much of what 8+1 fails to recover would a different parity have
recovered, and did any of it coincide with capacity pressure?

Read first: `evidence/D_BASE_CLOSEOUT_2026-09-23.md`,
`D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md`, `D_BASE_P5_WHICH_QUEUE_2026-09-21.md`,
`D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`, `D_BASE_S3_CAP_SOAK_2026-09-22.md`,
`D_BASE_T3_AUDIO_LOSS_LOCATION_2026-09-23.md`, `companion/native_fec_relay.py`
(the 8+1 XOR: what one group is, what it can and cannot recover),
`PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt` (how the client
counts `fec_recovered_packets`, `fec_unrecoverable_groups`, forward gaps),
`architecture/ADAPTIVE_BITRATE.md` §Signal interpretation.

**Scope.** Offline analysis only: read `logs/games/decoder_sessions/`,
the heartbeat logs and their archive, the evidence copies. No session, no
companion / client / profile change, nothing under `logs/` modified.

## The analysis — pre-registered

Population: every decoder session on the adopted build (from `P6a`'s
adoption, 2026-09-22, with cap 90,000 — take the profile fields from each
report's host metadata where present; otherwise by date) of ≥ 5 minutes,
split into **holds** (no SSRC change) and **transition sessions**. List
them.

1. **What 8+1 recovers and what it cannot.** Per session:
   `fec_recovered_packets`, `fec_unrecoverable_groups`, `lost_packets`
   (post-FEC), `lost_packets_in_resyncs`, forward-gap events and
   `max_forward_gap_packets`; per minute from the `R5` heartbeat series
   where available. An 8+1 group recovers exactly one lost packet; a group
   with two or more lost is unrecoverable. So from the gap-size
   distribution (packets per gap event) compute how many unrecoverable
   groups a **k+2** scheme (two parity, any two lost) would have
   recovered, and how many a **4+1** (smaller groups, same overhead
   ratio doubled) would — as an upper bound, ignoring interleaving. Report
   the post-FEC loss/min the corpus would have had under each, beside
   the actual, and the overhead each costs (+12.5 % → +25 %; 4+1 = +25 %).
2. **Is any of it capacity pressure?** For every minute with
   `lost_packets_delta` > 0: the same minute's `queue_depth`,
   `output_gap_ms`, `recent_fps`, `interarrival_jitter_ms`, and the
   host's send-call timing (`send_call_avg_us`, `send_call_max_us`)
   from the telemetry/heartbeat rows; Spearman across minutes, and the
   bucketed table (loss 0 / 1-5 / 6-20 / > 20 per minute) of those
   columns. Pre-registered reading: **capacity pressure is absent** if
   the loss-minute buckets show no monotone rise in queue depth or
   output gap and |rho| < 0.3 on every column; **present** if either
   rises across all buckets. (`P5`/`S3` already found the residual
   tracks nothing; this is the C4 restatement on the current corpus.)
3. **The warm state specifically.** Split minutes by the `T2` threshold
   where thermal data exists (onn cpu-thermal ≥ 67.5 °C) and repeat 1
   and 2: the warm-state single-packet loss is exactly what 8+1 is built
   for; say whether any warm minute had a multi-packet gap that 8+1 lost.
4. **Cost of the alternative in latency.** A larger group means more
   packets before the parity arrives (group completion delay at 7 Mbps
   ≈ group size × mean packet interval — compute from the frame-size
   series); state it beside the 8+1 figure.

## The decision — `decisions/C4_ADAPTIVE_FEC_<date>.md`

Pre-registered: **DEFER WITH EVIDENCE** if the extra recoverable loss
under k+2 or 4+1 is under 2 packets/min on the corpus median **and**
capacity pressure is absent; **BUILD (static k+2 first)** if a fixed
alternative recovers ≥ 5 packets/min more at the median with no pressure
signal (then it is a profile field, not adaptation); **BUILD ADAPTIVE**
only if pressure is present and loss rises with it, which is the one case
where parity must not be raised blindly. Write the numbers, the rule and
the outcome; C4 closes on DEFER or moves to a design task on BUILD.

## Record and memory

`evidence/C4_D1_FEC_EVIDENCE_<date>.md` with the tables and the scripts
(`c4_d1_*.py`, verdict rules in their docstrings) and outputs under
`evidence/c4_d1_<date>/` with a manifest; the decision record;
`docs/ROADMAP.md` C4 line; `docs/PROJECT_STATUS.md`; `CURRENT.md` one
line; `investigations/ACTIVE.md`; the daily file. No addresses. Nothing
committed.
