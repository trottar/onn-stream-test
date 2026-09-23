---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
---

# Baseline stream health — CLOSED 2026-09-23: MET

**Status: MET (2026-09-23)**, pre-registered close-out on the adopted build,
cold and warm: `../evidence/D_BASE_CLOSEOUT_2026-09-23.md`. Every
numeric-target row passes in both sessions; max output gap (163 / 110 ms)
is the transport's open row, inside the close-out's 250 ms bound. The
Step 5 client decision is **not triggered**. Phase C resumed.

Decision: `../decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`
Evidence: `../evidence/BASELINE_STREAM_HEALTH_2026-09-20.md`

**Question:** can the Linux host -> onn client native game stream reach
seamless local play, and if not, what is the ceiling and where is it?

Phase C adaptive-bitrate work is suspended until this closes.

## Target (entry criteria for resuming Phase C)

**Now (close-out 2026-09-23, cold / warm):** spikes 32.8 / 26.0 per min;
rendered fps 59.90 / 59.91; max output gap 163 / 110 ms; stale drops
1.1 / 0.8 per min; video loss 8.7 / 8.4 per min (post-FEC; audio after
de-duplication 0.25 / 1.44); audio underruns 17 / 14 per session.

| metric | target | median, 127 sessions (Group A) | median, 47-session record |
| --- | --- | ---: | ---: |
| receive->output spikes >= 20 ms / min | < 200 | 2,535 | 2,506 |
| rendered fps | >= 59.5 | 55.5 | ~56 |
| max output gap, per session | <= 100 ms | 287 | 345 |
| stale output drops / min | < 20 | 193 | 181 |
| lost packets / min | < 10 | 196 reported (undercounted 2-3x; counter fixed by `D-BASE-R1`, runtime-confirmed 2026-09-20, see Step 3) | 199 — **and 16.6 on the production path**, `D-BASE-B2`, six sessions, range 7.0-24.1; still FAILS |
| audio underruns / min | < 5 | 113 — **not a rate**, see below | **~19 per session** (`D-BASE-P2b`) |

**The audio row is closed and the metric was misread.** `D-BASE-P2`
(2026-09-20) showed a median **98.7 %** of a session's underruns fall in
the first three seconds, ending the tick the audio queue first fills, so
the per-minute figure is a fixed startup burst divided by a short session —
`underruns` is flat at 116-162 from the 0-40 s duration bucket to 300 s+
while starvation and concealment scale ~20x. `D-BASE-P2a` (2026-09-21) then
held the AudioTrack until real PCM arrives: **`audio.underruns` per session
0 / 6 / 21 / 20 / 3, median 6, against a pre-fix median of 207**, with 0-3
in the first three seconds. **Read the per-session total, not a rate**; on
that reading the row now reads ~6 per session and the target's "< 5 / min"
wording no longer describes anything the stream does. Records:
`../evidence/D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md`,
`../evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md`.

**The fix is RUNTIME VALIDATED as of 2026-09-21** (`D-BASE-P2b`,
`../evidence/D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`). Its one
open objection — `prolonged_starvation_events` 138 → 151 — was tested
against a build with the hold compiled out, which measures **125-157,
median 151**: the same band, so not the fix. Five matched pairs put
hold-on above hold-off in only 3 of 5, pooled Spearman against run index is
-0.036, and `avg_queue_residence_ms` is unmoved (27.70 off, 27.62 on). The
underrun result replicated at median **276** off against **19** on, so the
row's measured value on the current build is **~19 per session**.
`prolonged_starvation_events` remains a separate, unexplained phenomenon
and is not part of this row.

All distributional. No perceptual gate, by explicit instruction. The
"spikes" line counts frames whose receive-to-output latency is >= 20 ms
(`AvcLowLatencyDecoder.drainOutputs`), not decode time and not the 16.7 ms
frame period.

## Order of work, re-sequenced 2026-09-20 (evening) on the Group A live half

Host-side causes are closed (`../evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`,
"Live half"): A1-live — the SPS and SEI on the wire are correct and
explicit (no B-frames, `max_num_reorder_frames 0`, `max_dec_frame_buffering
1`, `dpb_output_delay 0`); A3-live — x11grab is 60 fps clean (exact 1/60
PTS, 99.6 % unique frames); A4 host half — the host is wired, and **`B2`
confirmed the one-hop production path on 2026-09-21**. What remains, in
order:

1. ~~Confirm the loss counter on the device~~ **DONE 2026-09-20 (night)**:
   `evidence/D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md`. The
   transport column is readable from any report carrying
   `lost_packets_in_resyncs`.
2. ~~Step 2, `C3.L2c` reopened~~ **RUN 2026-09-20 (evening), DECISION
   PENDING**: `evidence/C3_L2C_DISTRIBUTION_2026-09-20.md`. Three sessions,
   spikes 203/107/119 per minute against a corpus median of 2,535, stale
   32.9/8.7/7.3 against 192, fps 58.30/58.65/59.13 against 55.5, frames
   under 20 ms 36.4 % -> 94.3-97.0 %. `max_output_gap_ms` still misses its
   target and is an arrival gap in all three. The build is installed and the
   source change is in the tree; **the keep/revert call is the user's.**
3. **Step 2, the 60 ms stale threshold** — decided on the evidence from (2),
   which is now on disk. Note the deficit it can still buy is small: the
   client-side fps gap is down to 0.22-0.67 fps.
4. ~~**Step 3, transport**~~ — **CLOSED 2026-09-22 by adoption**
   (`P6a`). Located by `O1`/`P5`, controlled by `P6`, adopted after the
   user's own perceptual check: the frame cap is a profile parameter and
   loss runs 249/session against an uncapped 2,690-2,896. Still open from
   this step: the `host_link` field and B1/B3 when authorized (**`B2` is
   done, INDETERMINATE**).
5. Step 4 (audio) jointly with Step 2; Step 5 as pre-registered.

Step 1 stays withdrawn.

## Step 1 — stall-tail regression. WITHDRAWN 2026-09-20 (premise falsified).

As written: revert only the `C3.L2b` hot-path instrumentation and compare
the tail across five sessions.

Group A's A2 re-score (`../evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`,
A2.5) ran the epoch split on all 128 qualifying sessions instead of the
newest 50 files. Pre-flatten stalls of 2,035, 1,832 and 1,350 ms exist; the
338 ms ceiling was a window artifact. Every stall over 1,000 ms in every
epoch carries an outage-class sequence jump (`largest_resync_jump_packets`
vs `max_output_gap_ms`: rho 0.66) and an IDR wait, with `max_codec_ms`
equal to the gap because the last frame is held inside the codec until the
next input arrives. A vs C: spikes, fps and stale drops identical
(p = 0.33 / 0.99 / 0.80); tail shift modest (max gap p = 0.045, > 1,000 ms
share p = 0.27).

Do not run the revert. The `C3.L2b` retention defect — the worst
ordinary-play event is evicted from the 64-entry tail — is real and stays
open on its own (`docs/KNOWN_ISSUES.md`).

Reopen only with a stall over 1,000 ms whose own session report shows no
sequence jump and no IDR wait.

## Step 2 — decoder path

The dominant fault by the target table. What the raw slow events say
(A2.4, A2.6): the decoder holds **2-3 frames** during slow events and 2
during 300 ms+ stalls; 11-13 is a transient session maximum. Steady-state
receive-to-output latency is 20-60 ms on ~66 % of frames (rendered) and
> 60 ms on ~5.5 % (dropped by the client's own stale threshold, which is
most of the fps deficit). `latest_feed_delay_ms` is 0 — the client feeds
promptly. Each long stall is an arrival gap plus one frame held in the
codec until its successor arrives; `C3.L2c` removed the hold, which is why
its output gap exposed the arrival gap (A2.7).

Work:

- ~~reopen `C3.L2c`~~ **done 2026-09-20**, judged on `spike_20_ms/min`,
  `stale_output_drops` and fps across three sessions: the 20-60 ms body
  collapses from 58.8 % of frames to 2.8-4.8 %, and the client-side fps
  deficit from 3.5 fps to 0.22-0.67. The 2026-09-19 rollback's deciding
  comparison (385 vs 359) put an arrival gap against a codec hold. **Fault
  #1 of this investigation is answered, pending the user's keep/revert
  call.** Record: `evidence/C3_L2C_DISTRIBUTION_2026-09-20.md`;
- A1-live is done (2026-09-20): the SPS on the wire carries
  `bitstream_restriction_flag 1`, `max_num_reorder_frames 0`,
  `max_dec_frame_buffering 1`, `pic_order_cnt_type 2`, and every picture's
  timing SEI says `dpb_output_delay 0`; no B-frames. **The decoder ignores a
  correct VUI; the client-side request is the only lever.** Nothing
  host-side is left to change for the hold;
- then decide the 60 ms stale threshold on evidence: it converts 20-60 ms
  latency into dropped frames, and the target's fps line is mostly that
  policy;
- re-audit the Android receiver's resync and IDR-acceptance policy, which has
  not been looked at since `C3.L0`.

## Step 3 — transport

**Link type — settled 2026-09-21 by `B2`.** History: at 2026-09-15 the
host used a USB RTL8822BU radio and the onn the Opal's other radio, **two
wireless hops**; measured 2026-09-20 the host was **wired** (`eno1`,
`r8169`) but, corrected by the user 2026-09-21, **that cable ran to the
Windows PC**, so the path was host -> PC -> Opal -> onn and every session
on disk to that date carries the PC. **`D-BASE-B2` moved the host onto the
Opal and gate-checked it** (default route's interface, gateway identified
as the Opal by vendor OUI and Dropbear / nginx / local-DNS banners, host
and onn on one subnet, adb reaching the onn, the host's internet through
the same gateway): **host wired -> Opal -> onn wireless, one hop, the
production topology.** Record: `../evidence/B2_HOST_ON_OPAL_2026-09-21.md`.
Still true that nothing *per session* records the link — the `host_link`
field specified in the Group A record is unimplemented — so corpus
sessions before and after each move cannot be separated from the reports
alone. The house-router arm remains unrun.

**Loss is undercounted (A2.2):** `lost_packets` excludes every gap
>= 128 packets (those become sequence resyncs). Over the 50 post-`C3.L2b`
sessions the resync jumps total 53,679 packets against 23,521 counted;
corrected median 252/min vs 120 reported, 1.51 % vs 0.47 %. Loss is bursty
(14 packets per gap event median, 39 per largest gap median, zero
reordering) and moves 10x day to day with no code change. The stall tail
belongs here, not in the client. **Counter fixed in source by `D-BASE-R1`
(2026-09-20)**: resync jumps now count as loss, with
`lost_packets_in_resyncs` alongside; **runtime-confirmed on the onn
2026-09-20** (`../evidence/D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md`).

**`B2` result (2026-09-21) — INDETERMINATE.** Six attract-mode sessions on
the production path against the PC-path arm (`D-BASE-P1` A60/B60/C60,
`P2a` Q1-Q5, `C5a` R1-R3): loss/min median **16.6** against **46.3**
(2.8x, where the pre-registration asked an order of magnitude), packets
per gap **4.46** against **11.17** (still four times uniform loss),
forward-gap events 7 against 11. **The arms overlap** — the PC arm spans
0.0-206.7 loss/min and contains the Opal range 7.0-24.1 — so **no verdict
on the Windows PC**. Every transport column moved together and the Opal
arm is far tighter, but Group A's day-to-day swing is 12.6x. **The
deferred UDP burst/gap pathology is narrowed, not resolved.** Separately,
`B2` **falsified `C5a`'s** "a stalled encoder makes no sequence gap": a 3 s
stall gave a 690-packet `sequence_resync` with 0 restarts and 0 SSRC
changes, off a measured resume burst — the boundary is the burst's size.

**`D-BASE-P3` (2026-09-21) — INDETERMINATE.** The first test of *why* the
loss is bursty rather than *where* it is. A diagnostic sender pacer in the
FEC relay (`PRIVYHUB_FEC_PACING_US`, environment, **default off**, clamped
so a frame is out within 8 ms of its first packet) spread each frame's
packets instead of letting the encoder emit them back to back. Fifteen
120 s sessions, strictly alternating, companion restarted for each, 0
rejected. **Loss/min fell in only 3 of 5 pairs** (bar 4) and the medians
**1.72x** / **1.70x** (bar 2x), while **`spike_20_ms`/min rose in 5 of 5**,
which the pre-registration forbids — so **not implicated**. Packets per gap
did fall in 4 of 5 and the median max forward gap halved, 16 → 8, so **not
ruled out**. At 400 µs achieved spacing reaches only 187.5 µs and loss fell
in 0 of 2 pairs: **it does not scale.** **The null is bounded by its own
budget** — the clamp bites above 53 packets/frame at 150 µs against a mean
frame of 15.85, so the large frames a queue-overflow account blames are the
ones the budget refuses to spread. Record:
`../evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md`. **Adopting pacing is a
product decision; the cost (+41 % spikes) is measured, the benefit is not.**

**`D-BASE-P4` (2026-09-21) — CHARACTERIZED: not the air.** The first
measurement of the radio rather than of symptom counts at the decoder,
host-side over adb with no code change. **The onn is on 5 GHz** — 5180 MHz,
channel 36, 80 MHz, 802.11ac, 866 Mbps ceiling, **never re-associated**
across seven sessions. Loss/min swung **1.4 → 105 (74x)** while RSSI spanned
**5 dB** (median −66 every session) and **no scan of any kind** fell inside
any session; at **n = 597** ticks in a 20-minute session, receive rate vs
RSSI **rho = −0.022**, vs link speed **−0.001**. **But half the
pre-registered test could not be run:** this client exposes **no retry,
failure, airtime or channel-occupancy counter** — all identically 0 or
constant. **Signal strength, association, link rate and scanning are
excluded; interference and airtime are invisible from here.** Record:
`../evidence/D_BASE_P4_AIR_TELEMETRY_2026-09-21.md`.

**And the loss is episodic — which reframes this whole step.** The
20-minute session lost **105/min at 14.89 packets per gap** against 3.0-7.0
in the two-minute ones, same radio. **Short sessions sample the loss column
badly**, which explains `P3`'s 1.8-35.2 control swing and `B2`'s overlapping
arms as sampling variance. **Size future loss measurements in tens of
minutes, not two.** No per-minute loss series is available from the
counters (noise sd 86 packets/window against a 3.0-packet signal); that
needs a per-tick loss counter in the client.

**`D-BASE-R5` (2026-09-21) — RUNTIME VALIDATED: the loss column now has a
per-minute series.** The receiver's cumulative loss counters ride the 2 s
heartbeat (schema `…_heartbeat_v2`), read from the same snapshot it already
took. All seven matched the report exactly at the last heartbeat, and the
series accounts for the report to the packet (2,212 + 6 + 0 = **2,218**).
**Inside one 20-minute session loss ran 0 to 303 per minute** (median 87)
while RSSI held −65 to −67 and link speed 260 in twenty of twenty-one
minutes — **episodic within a session**, which is why the two-minute
sessions this step has leaned on kept disagreeing. **Size loss measurements
in tens of minutes.** Record:
`../evidence/D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`.

**`O1` (2026-09-21) — CHARACTERIZED: not the air, and the loss is
reproducible.** The access block is gone; the Opal was read **read-only**
beside two 20-minute sessions (40 minutes, 269 rounds, 1,196 heartbeats).
Record: `../evidence/O1_OPAL_AIR_VIEW_2026-09-21.md`.

**Airtime is closed on the pre-registration's third branch.** Loss swung
**0-331/min** while every Opal reading stayed flat — channel utilization
rho **−0.434** per minute *on the wrong sign* and **−0.008** at 10 s,
`tx retries` **+0.219**, `rx drop misc` and every `dropped`/`errors`
counter on `wlan1`, `br-lan`, `eth0`, `eth0.1` **constant 0**. The 24 worst
10 s windows read **6.78 %** utilization against **6.94 %** in the 141 that
lost nothing, and **the channel is ~93 % idle while streaming**. Retries
run 10.2-11.3 % at −70 dBm and do not track loss. **`sta0`/`sta1` are
`Not connected`** — the radio is not time-shared.

**This step's question has changed.** The per-minute loss series of the two
sessions agree at **Pearson 0.964**, so **the loss is reproducible from
stream position, not environmental**; and **video loses 2.9-7.4x what audio
loses on the same radio in the same second**, so the bursty stream is
selected over the paced one. The remaining suspects are **the AP's
per-station queue and the onn's receive path** — the Opal reports no drop
on any interface, but this driver's **`tx failed` copies `tx retries`**, so
retry exhaustion is unreadable and the two cannot be separated from the
Opal's side. **The next measurement is client-side**: the onn's
`/proc/net/udp` `drops` for the stream socket, per minute, beside the
heartbeat series.

**`D-BASE-P5` (2026-09-21) — CHARACTERIZED: not the client, and the loss
tracks the frame-size tail.** Three instruments on one clock across two
20-minute sessions — frame size from the relay, the onn's `/proc/net/udp6`
receive-queue `drops`, and the `R5` heartbeat counters. Record:
`../evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`.

**The onn's receive path is excluded.** Its UDP socket discarded **0
datagrams in 40 minutes** — 0 of 4,349 lost packets, 0 of 240 windows,
video and audio both; `rx_queue` peaked at **480 KB of a 2 MiB buffer**;
below it every `wlan0` error counter is **+0** and device-wide UDP
`RcvbufErrors` **+1**. **A larger client receive buffer is not a fix.**

**Loss tracks the size of the largest frames**: max packets per frame rho
**0.583** (10 s, n=240) and **0.780** (per minute, n=40); `frames >= 80`
**0.569**/**0.779**. Frame *rate* and *mean* are flat, so only the tail
moves. Distribution per session: **p50 11, p90 29, p99 82/78, max
207/208**, with **4.0 %** of frames >= 40 packets and **1.0 %** >= 80.
Frame size reproduces across sessions at Pearson **0.996**, more tightly
than the loss (**0.890**, just under the pre-registered 0.9 bar).

**So Step 3's remaining question is no longer where the loss is — it is
which cost to pay to flatten the p99.** Encoder VBV (quality on scene
changes), a smaller IDR spike or intra-refresh (compression efficiency),
or a larger pacing budget (latency; `P3` measured +41 % spikes at 8 ms).
**That choice is the user's, not a measurement.**

**`D-BASE-P6` (2026-09-21) — CHARACTERIZED: the tail is controllable, and
controlling it removes the loss.** Seven 20-minute arms with baseline
bookends. Record:
`../evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`.

**`h264_vaapi -max_frame_size 90000` takes the ≥ 80-packet population
718 → 0 and the loss 2,696 → 311**, and on a second pair 2,896 → 408 —
**8.7x and 7.1x**, against a pre-registered bar of 2x. Forward gaps
306 → 105; maximum forward gap 61 → 13-27 packets; spikes 61.6 → 33-35 per
minute; fps 59.58 → 59.88. **Achieved bitrate does not move**
(6,928.9 → 6,929.7 kbps) and encoder CPU does not either (26.6-26.9 %
across every arm).

**The causal pattern:** the ≥ 80-packet bucket carries **93-95 % of
baseline loss at ~14x the loss/window** of any bucket below, capping
deletes it, and the `< 40` bucket is **not raised**. The knee was measured
first — a **step at 100 KB**, 46.3 loss/window above against 1.2-4.2
below — and the caps chosen from it.

**Two bounds.** The benefit **saturates** (a 60 KB cap ties at 299 vs
311), so the looser cap is the better setting; and **conventional VBV is a
different lever** — `-bufsize` at the one-frame budget flattens hardest
but loses **3x more** and is the only arm that *raised* loss in
small-frame windows. **Drift was flagged** (baselines ±15 %) and the
result survives against either bookend.

**So Step 3 is answered.** What remains is not a measurement: it is
**whether the picture cost of the cap is acceptable**, which this
instrumentation cannot see (`h264_vaapi` exposes no achieved QP, and
`slices`/intra-refresh do not exist on it). **That check is the user's,
and nothing is adopted until they make it** — the default is in force.

**`D-BASE-P6a` (2026-09-22) — RUNTIME VALIDATED: adopted. Step 3 closes.**
The user checked the capped picture themselves, decided to adopt, and the
cap became a declared profile parameter (`max_frame_size_bytes = 90,000`).
Validated with nothing set in the environment: **loss 249** against an
uncapped 2,690-2,896, **zero ≥ 80-packet frames**, max frame 89,874 B,
bitrate 6,929.6 kbps, fps 59.90, zero resyncs, zero socket drops, encoder
CPU 26.6 %. `PRIVYHUB_ENC_MAX_FRAME_SIZE=0` still runs uncapped for
comparison. Record:
`../evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`; decision:
`../decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

**Step 3 is closed by adoption, and `D-BASE-S3` confirms it over three
hours** (2026-09-22, SOAK VALIDATED): **5.4 losses/min** — lower than any
20-minute capped session and ~25x below uncapped — 0 resyncs, 0 onn socket
drops, fps 59.96, thermals plateau, and **both bounded logs rotated twice
with zero lost rows**. **The residual tracks nothing** (every Spearman
under 0.08 across 1,080 and 180 windows; the bucketed table flat at
0.80/1.05/0.85), so **a tighter cap is not a lever and the loss column is
closed at this level**. One finding: the driver's cap is a **target, not a
hard ceiling** — two frames came 9-11 bytes over, harmless at ~76 packets,
but a check must allow a tolerance. Record:
`../evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md`.

**What Step 3 does not close, and nobody should read it as closing:**

- **`prolonged_starvation_events`** — 35.8-40.7/min on the Opal path,
  75.9/min on the PC path, unmoved by everything tried and still with no
  account of itself. The only stream metric in that position.
- **`D-BASE-R3b`** — the nftables loss injection, blocked on the session
  classifier rather than on root; `GIVE_UP_MS`, `END_MS` and the recovery
  save stay unexercised.
- **Thermal thresholds** — wanted once, nothing acts on them.
- **`max output gap`** still misses its target row, and the Windows-era
  UDP pathology stays deferred and unclaimed.

Owns: the deferred UDP burst/gap pathology (`DEFERRED.md`, Linux half now
resolved), the counter fix, the pacing knob, the heartbeat loss series, the
Opal read, the frame-size counters, the encoder knobs and the adopted cap,
and B1/B3 when authorized.

## Step 4 — audio

Underruns are a **per-session burst of ~180-320 plus ~17/min steady state**
in sessions >= 300 s (A2.1); the 155/min figure was a session-length
artifact. The variable part co-varies with decode pressure (rho 0.35-0.43),
not with packet loss (rho 0.04). Joint with Step 2, not separate. The
missing instrument is a per-event audio timeline in the session report.

## Step 5 — client viability. PRE-REGISTERED.

If after steps 1-3 a healthy decode path on the production-representative
link — **host wired to the Opal, onn wireless to the Opal, one wireless
hop** — still cannot reach `spike_20_ms/min < 200` and fps `>= 59.5`, **the
onn is the ceiling and the client changes.** (Restated from "on a wired
link" per the battery; the onn is permanently wireless, so the old wording
could never be satisfied. `D-BASE` still carries the old wording and needs
the same amendment.)

Even the low-latency session had a 107 ms worst frame and a 385 ms arrival
gap. The project description calls the onn "the first client", so a second
client is consistent with the architecture.

This criterion is written down now so the conclusion is reached by measurement
rather than by attrition.

## Suspended, not failed

- `C3.L4` automatic controller — suspended. Its gate (`C3.L3a` Part 2) is not
  the blocker; the premise is.
- `C3.L3a` Part 2 — suspended. The probe is installed and carries three known
  defects from its first run: the mark-association window anchors on sequence
  start so ramps close their window before finishing; the telemetry field
  paths were taken from a probe's output artifact rather than the endpoint, so
  settling was never measured; and the picture rating used an unanchored 1-5
  scale that silently rescaled 1-10 answers. Fix these before any rerun. The
  2026-09-20 session's raw marks and per-cycle timings are retained in
  `logs/streaming/c3_l3a_gameplay_acceptance_state.json` and can be re-scored
  without replaying.
- Phase C's completed items stand. The Linux actuator is real and correct.

## Privacy

No network addresses appear in this record. "Link type" means wired versus
wireless.
