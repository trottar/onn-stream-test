---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
status: GROUP A RUN 2026-09-20 (A1, A2, A3 complete; A4 — host side measured 09-20, onn side read 09-21 by B2). B2 RE-SCOPED and RUN 2026-09-21, INDETERMINATE; B1, B3-B5 and Group C not authorized.
---

# Seamless local play — test battery

## Group A status — run 2026-09-20

Record: `../evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`. Raw data and
re-runnable scripts: `../evidence/group_a_2026-09-20/`. The run had file
access to the host and **no shell on it**, so every live step is
INDETERMINATE for that reason; nothing was started or left running.

| test | status | one-line result |
| --- | --- | --- |
| A1 | COMPLETE | On the wire (10 s production-command sample, 2026-09-20): I 40 / P 560 / **B 0**; SPS `bitstream_restriction_flag=1`, `max_num_reorder_frames=0`, `max_dec_frame_buffering=1`, `pic_order_cnt_type=2`; picture-timing SEI `dpb_output_delay=0` on every frame. The bitstream does not ask for the hold. **Hypothesis falsified; fix, if any, is client-side.** |
| A2 | COMPLETE | 128 sessions on disk, not 47 (the 47 were the newest 50 files). Loss is bursty and undercounted 2-3x (resync jumps excluded from `lost_packets`). Spike rate flat with time. Stale drops track latency (rho 0.87), not in-flight (0.04). Stall tail = outage jumps + IDR wait, in every epoch; Step 1's premise falsified. Audio underruns are a per-session burst; steady state ~17/min. |
| A3 | COMPLETE | Encoder emitted 924,385 frames / 15,408 s = 59.995 fps over 160 sessions (on disk). Live `framemd5` (30 s, Tekken 3 attract demo): PTS delta exactly 1/60 on all 1,799 intervals; 7 duplicate hashes in 27 s of motion (99.57 % unique). **Host capture is 60 fps clean; hypothesis falsified.** |
| A4 | PARTIAL | Host measured 2026-09-20: wired (`eno1`, `r8169`), no radio present — one wireless hop by role, the production topology. The onn's association (which Opal radio) still unread. Per-session `host_link` field specified, not implemented. |

Everything below this line is the battery as proposed, unchanged.

---

Supports `BASELINE_STREAM_HEALTH.md`. Does not replace it. Steps 1-5 there
remain the spine; this file adds the tests that come *before* them and the
ones they do not cover.

**Objective, in the user's words:** the stream should feel like playing
directly on the Linux host, over LAN. Remote play is unreachable without it.

**Ordering principle:** every test that costs nothing runs before every test
that costs a session, and every test that needs no code change runs before
every test that does. The current plan begins at a code change (Step 1). Four
free tests sit upstream of it and one of them is a candidate root cause.

**Privacy:** no network addresses are collected or recorded by any test here.
"Link type" means wired versus wireless. "Alternate AP" means a different
access point, identified by role, not by address.

---

## Group A — Free. No new sessions, no code, no device.

These run against artifacts already on disk. Do them first.

### A1 — Encoder bitstream audit. **Highest priority in this file.**

**Question:** does the host emit a bitstream that *requires* the client to
buffer deeply?

The decoder holds 11-13 frames in flight while `latest_feed_delay_ms` is 0 and
`input_waits` stays in the tens. That has been read as a decoder policy
choice. There is a second explanation that has never been checked: the decoder
may be obeying the bitstream.

Two mechanisms, both host-side:

- **B-frames.** Any B-frame forces the decoder to hold frames for reorder.
  Low-latency streaming requires zero. Check `_build_linux_ffmpeg_command`
  for `bf` / `max_b_frames`, and confirm against the actual stream rather
  than the intent.
- **VUI bitstream restriction.** If the SPS carries no
  `bitstream_restriction_flag`, or carries `max_num_reorder_frames` /
  `max_dec_frame_buffering` above 0, MediaCodec is entitled to allocate a deep
  DPB and will. Setting these to 0 is the explicit instruction to the decoder
  that no reordering occurs.

**Method:** capture a short sample of the produced stream to file, then
inspect it. `ffprobe -show_frames` for actual frame types; a bitstream
analyzer or `ffmpeg -debug` trace for the SPS VUI fields. No device needed,
no session needed.

**Why this is first:** if either is present, every client-side decoder
experiment to date has been fighting the bitstream, and `C3.L2c`'s partial
result — low-latency flag on, still 12 frames in flight — is explained
without invoking a decoder defect at all. This is a host-side fix to a fault
currently attributed to the client.

**Falsifies:** "the onn decoder is the ceiling", if the bitstream is the
cause.

### A2 — Re-score the 47 sessions.

**Question:** what do the existing sessions already say that has not been
asked of them?

All 47 are on disk. No new runs. Ask:

- **do audio underruns and decode spikes co-occur within a session, or move
  independently?** Co-occurrence implicates a shared pacer or shared
  scheduling pressure and makes Step 4 a joint investigation rather than a
  separate one. Independence separates them cleanly.
- **is loss bursty or uniform?** Uniform loss is a link budget. Bursty loss
  with gaps is the signature already recorded in the deferred UDP pathology.
  This distinguishes them without any router-side capture.
- **does spike rate rise with elapsed session time?** A rise implicates
  thermal or a leak. Flatness rules both out and is worth knowing before
  anyone chases them.
- **does `stale_output_drops` track in-flight depth, or track loss?** These
  are different faults with the same symptom.

**Cost:** one script over existing JSON. Nothing installed.

### A3 — Capture cadence, host-side.

**Question:** is the host producing 60 distinct frames per second before
anything is encoded?

Every metric on record is client-side. No host-side frame cadence measurement
exists in the evidence tree. If `x11grab` is delivering fewer than 60 unique
frames per second, or delivering them unevenly, the client can never render
60 and no client-side work will ever close the gap.

**Method:** encoder-side frame timing from the existing ffmpeg process — PTS
deltas of emitted frames, and duplicate-frame count. If x11grab is duplicating
to hit cadence, that is a capture fault, not a stream fault.

**Falsifies:** the entire client-side fault model, if the source is not 60 fps
clean.

### A4 — Confirm which AP the onn is associated to.

**Question:** how many wireless hops are in the current path, and through
which device?

Stated in this conversation: the onn is permanently wireless; the Linux host
is temporarily wireless for room-layout reasons and will be wired to the Opal.
Production is therefore one wireless hop. The current measurement path is two.

**Answered 2026-09-21 by `B2`**, host-side and on the onn: the onn holds its
address on its **wireless** interface, the host is **wired**, and both sit on
one subnet behind the Opal — **one wireless hop, the production topology**.
(The 2026-09-20 reading of this was withdrawn: the host's cable then ran to
the Windows PC.) The onn carries no default route, only its on-link subnet;
local streaming does not need one.

**The per-session `host_link` field is still unimplemented**, so this is
recorded once here and not per report. Record it as a field: it costs nothing
and it stops every future reading from being ambiguous about its own
topology.

---

## Group B — One session each. No PrivyHub code change.

### B1 — Host-local decode. Network removed entirely.

**Question:** is the encoder output itself clean?

Decode the produced stream on the Linux host, no network hop, no Android. If
the stream stalls here, the fault is upstream of transport and upstream of the
client, and Groups C onward are chasing a symptom.

If it is clean at 60 fps with shallow latency, the encoder is exonerated and
the search collapses to transport plus client.

### B2 — **RE-SCOPED and RUN 2026-09-21. INDETERMINATE.**

**As written:** is the loss column a property of the Opal? — one session
with host and onn on any other access point, against the 47-session
baseline of 199 median.

**As corrected by the user 2026-09-21 and actually run:** the host's
Ethernet had been running to the **Windows PC**, not the Opal, so the whole
corpus was measured on host -> PC -> Opal -> onn. B2 became the opposite
test — move the host onto the **production** topology (wired directly into
the Opal, onn wireless, one hop) and ask whether the burst loss **follows
the PC or stays**. The alternate-AP question is not answered and is still
owed; the Opal is not exonerated by anything below.

**Result — INDETERMINATE.** Six attract-mode sessions, 120 s, zero input,
no code change, gate-checked on the host first (the gateway answers as the
Opal by vendor OUI and Dropbear / nginx / local-DNS banners; host and onn
on one subnet; adb reaching the onn). Against the PC-path arm
(`D-BASE-P1` A60/B60/C60, `P2a` Q1-Q5, `C5a` R1-R3): loss/min median
**16.6** against **46.3**, packets per gap **4.46** against **11.17**,
forward-gap events 7 against 11. The pre-registration asked for an order of
magnitude **and** a burst collapsing toward 1; it got 2.8x and 4.46.
**The arms overlap** — the PC arm spans 0.0-206.7 loss/min and contains the
whole Opal range of 7.0-24.1, with three PC sessions quieter than all six
Opal ones — so **no verdict is claimed on the Windows PC**. Every transport
column did move together and the Opal arm is far tighter, but Group A's
day-to-day swing is 12.6x.

**`C5a`'s durable fact fell out of the same session**: a 3 s `SIGSTOP`
produced a 690-packet `sequence_resync` with **0 restarts and 0 SSRC
changes**, off a measured resume burst — so a stalled encoder *can* make a
sequence gap, and the boundary is the burst's size, not a restart.

Record: `../evidence/B2_HOST_ON_OPAL_2026-09-21.md`; reports, harness and
SHA-256s in `../evidence/b2_2026-09-21/`.

**Still owed here:** the alternate-AP arm, which is the only thing that
would speak to the Opal itself.

The Opal is a GL-SFT1200 — a pocket travel router on a Siflower SoC, carrying
the entire trust domain. D080-D083 established that its standard capture
points are blind during confirmed traffic, that disabling exposed
flow-offload flags did not restore visibility, and that burst/gap
transformation with same-stamp duplication reproduces bidirectionally while
idle.

`DEFERRED.md` paused that investigation and names its own reopen condition:
*a single bounded measurement would change a product/roadmap decision.* Step 5
is that decision. If the loss is the Opal and the onn is retired on Step 5's
criterion, the wrong component is replaced and the fault persists.

This test satisfies the condition without any reverse engineering: no
router-side capture, nothing installed on the Opal, existing client telemetry
only.

### B3 — Wired onn. Diagnostic only.

**Question:** what do the decode numbers look like with the air removed?

USB Ethernet adapter on the onn, one session. This is a measurement, not a
topology proposal — the onn stays wireless in production.

Its value is separation: it splits "the onn's decoder is the ceiling" from
"the wireless path is the ceiling", which Step 5 currently cannot distinguish.
If the decode column barely moves, the decoder is the ceiling and Step 3 can
be deprioritized. If it collapses, Step 3 is the main event.

### B4 — Moonlight/Sunshine reference measurement.

**Question:** can *any* implementation reach seamless play on this onn over
this link?

Sunshine on the Linux host, Moonlight on the onn, one session at the 7000 kbps
reference, read the overlay stats.

This is a control, not a product direction. Phase B removed Moonlight and
Sunshine deliberately and the B6 clean-native checkpoint is correct policy.
Run this as an explicitly temporary reference measurement with its own
evidence record, then restore the checkpoint state.

Its value is that it answers Step 5 by reference rather than by exhaustion:

- **Moonlight holds 60 fps with shallow decode** — the ceiling is the PrivyHub
  client implementation, the onn is not the limit, and Step 5 must not retire
  it. Moonlight's Android client also becomes a legitimate reference for the
  specific decoder in question.
- **Moonlight stalls the same way** — the ceiling is the device or the link,
  and Step 5's conclusion is supported by an independent implementation rather
  than by one codebase's numbers.

Either outcome is decisive, which is rare and worth one session.

**Secondary reading:** Moonlight uses Reed-Solomon FEC where the native path
uses XOR. At 199 lost packets/min that difference is material — RS recovers
multiple losses per block where XOR recovers one. If Moonlight's loss-visible
behavior is markedly better at comparable raw loss, FEC scheme becomes a
candidate work item in its own right.

### B5 — Second decoder. Different silicon.

**Question:** is the fault specific to `c2.realtek.video.avc.decoder`?

Run the existing PrivyHub Android client on any Qualcomm-based Android phone
on the same link. No handheld purchase required; a phone is sufficient for the
measurement.

This is the cheapest possible input to Step 5 and to any future client
decision. It compares the same client code against different decoder silicon,
holding everything else constant. `FEATURE_LowLatency` support can be read
directly from the device at the same time.

---

## Group C — Code changes. Existing plan, with two additions.

C1 through C4 are `BASELINE_STREAM_HEALTH.md` Steps 1, 2 and 4 unchanged, in
their existing order. Two amendments:

### C1 amendment — Step 1 is still correct, but may be reordered.

The `C3.L2b` revert answers the tail regression, which is a real and separate
fault. But it is second in importance to the chronic decode fault, which
predates it and which A1 may explain outright. If A1 finds B-frames or an
unrestricted VUI, fix that first and re-measure before spending sessions on
the tail.

### C2 amendment — `C3.L2c` reopen is correct, and its scope should widen.

Reopening on the distribution rather than on one `max_output_gap_ms` sample is
right. Add: the low-latency flag alone left 12 frames in flight, so the flag
was never going to be sufficient on its own. Pair the reopen with whatever A1
finds, and judge the combination.

### C5 — Receiver resync and IDR-acceptance policy. **COMPLETE 2026-09-20; the `C5a` probe answered it 2026-09-21: the completeness-gate cost is FALSIFIED.**

Read: `C5_RESYNC_IDR_ACCEPTANCE_READ_2026-09-20.md`. Analysis only; no code
changed.

**Answered.** The base cost is one GOP — the receiver must wait for the
encoder's next scheduled IDR and has no way to ask for one — and on top of
that the completeness gate (`RtpH264Receiver.kt` 2118) discards any IDR
access unit that lost a packet, costing a further GOP each time. Over 104
sequence resyncs since 2026-09-16: p50 **204.5 ms**, p90 **484.2 ms**, max
**2,555 ms**, with **32 beyond one GOP and 10 beyond two** — impossible if
the receiver simply took the next in-GOP IDR. The 47 actuator
`ssrc_change` IDRs in the same corpus read p50 **27 ms**, none above 76 ms.

Two candidates are **falsified**: it is not waiting for parameter sets (the
A1-live capture counted 41 SPS and 41 PPS against 40 IDRs in 10 s, so they
repeat with every IDR), and it is not stale-dropped decoder output (the
wait is entirely upstream of the decoder, which is never flushed or
reconfigured on resync).

**The §4 probe is built and installed** (`C5a`, 2026-09-21): session
counters `idr_aus_rejected_waiting_for_idr` /
`non_idr_aus_dropped_waiting_for_idr` and per-discontinuity
`rejected_idr_aus` / `dropped_non_idr_aus`, counting only. Its verdict is
**INDETERMINATE** — not because the counters are wrong (a control session
drove the resync path four times and every row carried the new fields) but
because no injection available without root produces a sequence resync. A
short SIGSTOP of the encoder makes a gap in *time*, not in *sequence*: a
stopped encoder burns no RTP sequence numbers. Largest forward gap across
three sessions was 47 packets against a 128 threshold. The counters stay in
to accumulate against natural resyncs. Record:
`../evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md`.

**Answered 2026-09-21 by `D-BASE-S2`.** A 3-hour session on a degrading
link produced 94 natural sequence resyncs and fired the counters for the
first time. Of the seven retained resyncs over 250 ms, **six rejected zero
IDRs** (longest 1,340 ms), and one at **240 ms rejected one** — impossible
if a rejection costs a further GOP. The long tail tracks
`dropped_non_idr_aus` (40-67 on the longest rows): the receiver is waiting
for an IDR to *arrive* on a link losing 389 packets/min, not discarding
damaged ones. p50 resync-to-IDR in that corpus is **71 ms**. **The read's
§5 bounded fallback is retired** — it was a remedy for a cause that does
not exist. Record:
`../evidence/D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`.

### C6 — new. Reference frame invalidation, or its absence.

If a lost packet currently forces a full IDR and a visible hitch, then at
199 losses/min the stream is being repeatedly reset by design. Establish what
the current loss-recovery path actually does before deciding whether it needs
changing. Audit only; no change proposed here.

---

## Acceptance

The existing target table stands as the gate:

| metric | target |
| --- | ---: |
| decode spikes >20 ms / min | < 200 |
| rendered fps | >= 59.5 |
| max output gap | <= 100 ms |
| stale output drops / min | < 20 |
| lost packets / min | < 10 |
| audio underruns / min | < 5 |

**One tension to resolve deliberately.** The acceptance criteria are
instrumentation-only by explicit instruction, and that instruction is sound —
`C3.L2c` is the standing proof that a single timing statistic and a perceptual
verdict can point opposite ways. But the stated objective is perceptual:
*feels like playing directly on the host.*

Proposed resolution, which does not weaken the gate: keep every numeric target
as the entry criterion, and add one confirmatory play session **after** the
table is met, recorded as confirmation rather than as a gate. If the numbers
are met and it still does not feel seamless, that is a finding worth having —
it would mean the metric set is incomplete, and that is better learned then
than assumed now.

**Production-representative configuration, for Step 5.** Step 5 currently
reads "a healthy decode path **on a wired link**". The onn is permanently
wireless, so as written the condition cannot be satisfied and the client would
be judged against a criterion it was never eligible to meet. The
representative configuration is: **host wired to the Opal, onn wireless to the
Opal, one wireless hop.** Restate it in Step 5 and in `D-BASE` now, before the
data arrives — amending an acceptance criterion after seeing results is the
failure mode this project has otherwise avoided.

---

## Suggested order

1. **A1** — encoder bitstream audit. Free, host-side, candidate root cause.
2. **A2, A3, A4** — free re-scoring, capture cadence, topology field.
3. **B1** — host-local decode. Exonerates or implicates the encoder.
4. **B2** — alternate AP. Exonerates or implicates the Opal.
5. **B5** — second decoder. Cheapest Step 5 input.
6. **B4** — Moonlight reference. Decisive either way.
7. **B3** — wired onn, if B2 and B4 have not already settled the link question.
8. **Group C** — code changes, informed by everything above.

Groups A and B together cost roughly five sessions and zero PrivyHub code
changes, and they can collapse the search space before a single line is
modified. The current plan opens with a code change; this reorders that.
