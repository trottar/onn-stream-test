---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# B2 — the host wired directly into the Opal

## Classification

**INDETERMINATE on the pre-registered question.** Six attract-mode
sessions on the production topology put loss per minute at a median of
**16.6** against the PC path's **46.3** — a **2.8x** fall, not the order
of magnitude the reading required — and the per-gap burst at **4.46**
packets against **11.17**, lower but nowhere near the ~1 of uniform loss.
Forward-gap events did not vanish (7 per session against 11). **The two
arms overlap heavily**: the PC arm spans 0.0-206.7 loss/min and the whole
Opal range, 7.0-24.1, sits inside it. Three PC-path sessions are *quieter*
than every Opal session. No verdict is claimed on six sessions.

**Two sub-results are CHARACTERIZED.** (1) The `D-BASE-R3a` resume burst
**reproduces with the Windows PC out of the path** — a single 690-packet
`sequence_resync`. That mechanism is not the PC. (2) **`C5a`'s durable
fact is falsified as written**: that jump came from a 3 s encoder stall
with **`restarts` 0 and `ssrc_changes` 0**, so a stalled encoder *can*
produce a sequence resync without tripping a restart. The boundary is the
size of the resume burst, not a restart.

## Gate — topology confirmed before measuring

Checked on the host, not taken on report. Recorded by role only.

- **The default route's interface is the host's onboard wired Ethernet**,
  and it is the only interface carrying traffic. One wired interface, no
  radio, no tunnel up.
- **The gateway is the Opal.** Identified without recording its address:
  the OUI belongs to the Opal vendor's registered block, and it answers
  with a Dropbear SSH banner, an nginx admin listener and a local DNS
  resolver — the OpenWrt-derived firmware of the travel router. A Windows
  PC presents none of those. **Gateway is the Opal**, not the PC.
- **Host and onn are on the same subnet**, one /24. The onn holds its
  address on its wireless interface; the host is wired. **By role: host
  wired -> Opal -> onn wireless, one wireless hop, the production
  topology.**
- **`adb` reaches the onn**, and the onn answers shell commands.
- **The host reaches the internet through the Opal's uplink** — the same
  gateway, over the same single wired interface. There is no second
  interface and no separate route to the internet.

The gate passes: the Windows PC is out of the path. Sessions proceeded.

One incidental observation, recorded because it is unexplained rather than
because it bears on B2: **the onn carries no default route**, only the
on-link route for its own subnet. Local streaming does not need one — the
host is on that subnet — so nothing here is affected.

## Method

No code change. The installed build is unchanged and is the `D-BASE-T1`
APK `1bc95f0a…212f0`, verified by hashing the installed package on the
device before the first session.

Six attract-mode sessions of the PS1 reference title, **120 s of hold
each, zero input**, opened through the launcher's RESUME PLAYING preview
per `TOOLS.md`, ended with BACK, the game stopped and `active: false`
confirmed between every session. A seventh session repeated the shape with
**a single 3 s `SIGSTOP`/`SIGCONT` on the x11grab encoder at 60 s**
(`D-BASE-R3a` G3 method: STOP re-applied every 200 ms across the 3 s, then
CONT). The pulse session is reported separately and is **not** pooled into
the six.

Harness and analysis: `b2_2026-09-21/b2_run.sh`,
`b2_2026-09-21/b2_analyze.py`; raw output `b2_2026-09-21/b2_analysis.txt`;
tables `b2_sessions.csv` and `b2_discontinuities.csv`; SHA-256 of every
file in `b2_2026-09-21/b2_sha256.txt`.

**Reference arm:** `D-BASE-P1` A60/B60/C60, `D-BASE-P2a` Q1-Q5, `C5a`
R1-R3 — eleven sessions, all PC path, all attract mode, the existing
reports, nothing re-run.

## The two arms, per session

Loss is read by the `D-BASE-R1` rule: reports carrying
`lost_packets_in_resyncs` already include the resync jumps; older reports
have the jumps added back. Every session in both arms reports
`lost_packets_in_resyncs` 0 and zero discontinuities, so the two readings
coincide and no correction was needed anywhere except the pulse session.

### Opal path (B2), n=6

| run | dur s | lost | loss/min | fwd gaps | pkt/gap | max gap pk | late/reord | disc | max out ms | spk20/min | stale/min | fps | aud lost | aud underruns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| O1 | 126.8 | 40 | 18.9 | 7 | 5.71 | 22 | 0 | 0 | 143 | 48.2 | 5.7 | 59.71 | 27 | 2 |
| O2 | 127.8 | 15 | 7.0 | 3 | 5.00 | 8 | 0 | 0 | 153 | 46.5 | 7.0 | 59.68 | 14 | 2 |
| O3 | 126.9 | 15 | 7.1 | 7 | 2.14 | 3 | 0 | 0 | 193 | 54.4 | 5.2 | 59.66 | 14 | 2 |
| O4 | 126.9 | 51 | 24.1 | 13 | 3.92 | 11 | 0 | 0 | 139 | 47.8 | 7.1 | 59.63 | 12 | 1 |
| O5 | 126.8 | 49 | 23.2 | 6 | 8.17 | 32 | 0 | 0 | 231 | 46.4 | 8.0 | 59.66 | 9 | 3 |
| O6 | 126.9 | 30 | 14.2 | 10 | 3.00 | 8 | 0 | 0 | 153 | 50.1 | 7.1 | 59.68 | 5 | 1 |
| **median** | 126.9 | 35 | **16.6** | 7 | **4.46** | 10 | 0 | 0 | 153 | 48.0 | 7.1 | 59.67 | 13 | 2 |

### PC path (reference), n=11

| run | dur s | lost | loss/min | fwd gaps | pkt/gap | max gap pk | late/reord | disc | max out ms | spk20/min | stale/min | fps | aud lost | aud underruns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A60 | 96.8 | 0 | 0.0 | 0 | — | 0 | 0 | 0 | 268 | 67.5 | 3.7 | 59.73 | 1 | 222 |
| B60 | 96.9 | 6 | 3.7 | 2 | 3.00 | 3 | 0 | 0 | 174 | 62.5 | 10.5 | 59.59 | 3 | 225 |
| C60 | 97.0 | 2 | 1.2 | 1 | 2.00 | 2 | 0 | 0 | 147 | 69.9 | 9.3 | 59.65 | 10 | 254 |
| Q1 | 129.0 | 19 | 8.8 | 5 | 3.80 | 6 | 0 | 0 | 296 | 94.0 | 8.4 | 59.66 | 29 | 0 |
| Q2 | 125.9 | 134 | 63.9 | 11 | 12.18 | 31 | 0 | 0 | 191 | 99.6 | 6.7 | 59.49 | 5 | 6 |
| Q3 | 130.9 | 451 | 206.7 | 28 | 16.11 | 58 | 0 | 0 | 259 | 251.1 | 7.3 | 59.13 | 4 | 21 |
| Q4 | 133.0 | 397 | 179.1 | 22 | 18.05 | 49 | 0 | 0 | 175 | 140.3 | 2.7 | 59.26 | 15 | 3 |
| Q5 | 131.0 | 241 | 110.4 | 18 | 13.39 | 38 | 0 | 0 | 292 | 154.8 | 5.0 | 59.38 | 13 | 20 |
| R1 | 158.1 | 122 | 46.3 | 12 | 10.17 | 27 | 0 | 0 | 331 | 84.2 | 6.8 | 59.62 | 9 | 12 |
| R2 | 158.2 | 51 | 19.3 | 7 | 7.29 | 26 | 0 | 0 | 321 | 87.2 | 5.7 | 59.61 | 12 | 13 |
| R3 | 158.5 | 228 | 86.3 | 14 | 16.29 | 47 | 0 | 0 | 357 | 87.1 | 6.8 | 59.59 | 15 | 5 |
| **median** | 130.9 | 122 | **46.3** | 11 | **11.17** | 27 | 0 | 0 | 268 | 87.2 | 6.8 | 59.59 | 10 | 13 |

A60's `pkt/gap` is undefined, not zero: it recorded no forward-gap event
to divide by. The A60/B60/C60 audio underruns (222-254) are the pre-`P2a`
startup burst and are not comparable to the later rows; they are left in
because the task named those three sessions.

### C5a counters, every session

`sequence_resyncs`, `ssrc_changes`, `largest_resync_jump_packets`,
`packets_dropped_waiting_for_idr`, `resync_to_idr_ms` and
`max_resync_to_idr_ms` are **0 in all six Opal sessions and in all eleven
reference sessions.** `first_clean_idr_ms` Opal 573-613 (median 588)
against PC 576-735 (median 634). `sequence_gap_au_drops` Opal 3-13, PC
0-28. `fec_unrecoverable_groups` Opal 3-8, PC 0-5.

**A build correction, recorded as an absence rather than a zero:**
`idr_aus_rejected_waiting_for_idr` and
`non_idr_aus_dropped_waiting_for_idr` **do not exist in the A60/B60/C60 or
Q1-Q5 reports** — those predate the counters. They are present and 0 in
R1-R3 and in all seven Opal sessions. So the reference arm is **not one
build**, contrary to the task's premise, and the Opal arm is on a build
newer than all eleven (`D-BASE-T1` added the thermal sampler after `C5a`).
This is a confound between the arms and is stated, not smoothed over.

## Medians side by side

| metric | PC path | Opal path | ratio |
| --- | ---: | ---: | ---: |
| lost packets | 122 | 35 | 3.49x |
| **loss / min** | **46.3** | **16.6** | **2.80x** |
| forward-gap events | 11 | 7 | 1.57x |
| **packets per gap event** | **11.17** | **4.46** | **2.50x** |
| max forward gap, packets | 27 | 10 | 2.84x |
| late or reordered | 0 | 0 | — |
| discontinuities | 0 | 0 | — |
| max output gap, ms | 268 | 153 | 1.75x |
| spikes >= 20 ms / min | 87.2 | 48.0 | 1.82x |
| stale drops / min | 6.8 | 7.1 | 0.96x |
| rendered fps | 59.59 | 59.67 | 1.00x |
| audio lost packets | 10 | 13 | 0.77x |
| audio underruns | 13 | 2 | 6.50x |

Full per-session lists, because the day-to-day swing is larger than most
effects:

- **loss per minute** — PC: 0.0, 1.2, 3.7, 8.8, 19.3, 46.3, 63.9, 86.3,
  110.4, 179.1, 206.7 · **Opal: 7.0, 7.1, 14.2, 18.9, 23.2, 24.1**
- **packets per gap event** — PC: 2.00, 3.00, 3.80, 7.29, 10.17, 12.18,
  13.39, 16.11, 16.29, 18.05 · **Opal: 2.14, 3.00, 3.92, 5.00, 5.71, 8.17**

## Reading, against the pre-registration

- **The PC is not implicated.** The criterion was loss per minute falling
  by an order of magnitude *and* the burst collapsing toward ~1 or the
  forward-gap events largely vanishing. Loss fell **2.8x**, the burst fell
  to **4.46** (still four times a uniform-loss signature, still bursty by
  A2.2's own 1.5 threshold), and gaps persist at 7 per session. **Not
  met.**
- **The PC is not exonerated either.** Every transport column moved the
  same way at once — loss 2.8x, burst 2.5x, max gap 2.84x, max output gap
  1.75x, spikes 1.82x — and the Opal arm is far *tighter* (7.0-24.1, a
  3.4x spread) than any PC-path night. That is the shape a real
  improvement would have.
- **The arms overlap, so no verdict is claimed.** A60, C60 and B60 — all
  PC path — are quieter than all six Opal sessions. The Group A day-to-day
  medians swing 31-392/min, a 12.6x range; a 2.8x median shift sits inside
  it. Six sessions in one 17-minute window cannot separate "the Opal path
  is better" from "this quarter of an hour was quiet".

**This is the in-between case the task named, and it is reported as such.**

## The resume burst reproduces without the PC

The pulse session, 126.9 s, a single 3 s encoder stall at 60 s:

| field | value |
| --- | ---: |
| discontinuity | **1**, `sequence_resync` at elapsed **69,968 ms** |
| **jump_packets** | **690** |
| first IDR after it | elapsed 70,029 ms, `resync_to_idr_ms` **60** |
| `au_complete` / fec recovered / fec unrecoverable group | true / false / false |
| `rejected_idr_aus` / `dropped_non_idr_aus` | 0 / **13** |
| `packets_dropped_waiting_for_idr` | **109** |
| `lost_packets` / of which in resyncs | 740 / **690** |
| loss / min | 349.9 |
| `max_output_gap_ms` | **3,048** |
| rendered fps | 58.78 |
| spike 20/50/80/250/500 | 116.3/min, 43, 8, 0, 0 |

Recovery log for the run: `desync_pause` on `client_output_silence`
1.2 s after the STOP, `resumed` 3.2 s after the CONT (`recovering_ms`
5,222), **0 restarts** — the encoder was never replaced, so the jump is
not a restart artifact.

**The burst-then-drop mechanism suspected of living in a receive buffer
does not need the Windows PC.** It reproduces on the one-hop production
path with the same shape `D-BASE-R3a` recorded: one outage-class sequence
jump, a short wait for the next IDR, and a multi-second output gap. The
690-packet jump is far larger than the 128-packet resync threshold, so it
is counted as loss under the `D-BASE-R1` rule and not as a forward gap —
which is why this session's `pkt/gap` (5.00) is ordinary while its
loss/min is twenty times the arm's median.

## The stall produced the jump with no restart — `C5a` needs amending

`C5a`'s durable fact reads: *"SIGSTOP of the encoder cannot produce a
sequence resync at the receiver, at any pulse length short of tripping a
restart."* **This session contradicts it.** The 3 s stall produced a
**690-packet `sequence_resync` with `restarts` 0 and `ssrc_changes` 0** —
no restart, no new SSRC, no `ssrc_change` fast path. The recovery log
shows only `desync_pause` -> `resumed`, `recovering_ms` 5,222,
**`restarts` 0**.

The heartbeat log shows the mechanism. `rx_packets` per 2 s tick, steady
state **1,566-1,873** (mean ~1,650):

| tick | time | d rx_packets | `last_output_age_ms` |
| ---: | --- | ---: | ---: |
| 33 | 15:59:48.0 | 1,654 | 1 |
| **34** | 15:59:50.0 | **393** | **1,544** |
| **35** | 15:59:52.1 | **1,161** | 2 |
| **36** | 15:59:54.2 | **2,587** | 27 |
| 37 | 15:59:56.2 | 1,633 | 58 |

STOP landed at 15:59:48.4 and CONT at 15:59:51.5. Ticks 34-35 run a
**deficit of ~1,746 packets** against the steady rate; tick 36 is a
**resume burst ~937 packets above** it; and the sequence jumped **690**.
Deficit minus burst minus jump is ~119 packets — closing to within the
2 s bucket boundaries and the ±150 tick-to-tick variance.

**So the packets were minted and then lost, not never sent.** A stopped
encoder burns no sequence numbers, which is what `C5a` measured at 0.3 s;
but a 3 s stall ends in a resume burst large enough that ~690 packets are
dropped somewhere between the encoder and the decoder, and *that* is the
sequence jump. `C5a`'s boundary — "short of tripping a restart" — is the
wrong one. **The boundary is the size of the resume burst.**

This is one observation of one 3 s stall and it is reported as that. It is
enough to falsify the claim as written, because the claim is universal and
this session has `restarts` 0 and `ssrc_changes` 0 on the record. It is
**not** enough to re-attribute `D-BASE-R3a`'s 720 / 984 / 480-packet jumps,
which `C5a` assigned to restart-plus-new-SSRC; those sessions are not
re-read here.

## Target table on the Opal path

Six sessions, against `BASELINE_STREAM_HEALTH.md`:

| metric | target | Opal arm | verdict |
| --- | --- | ---: | --- |
| spikes >= 20 ms / min | < 200 | 46.4-54.4 | **PASS**, all six |
| rendered fps | >= 59.5 | 59.63-59.71 | **PASS**, all six |
| max output gap | <= 100 ms | 139-231 | **FAIL**, all six |
| stale drops / min | < 20 | 5.2-8.0 | **PASS** |
| lost packets / min | < 10 | 7.0-24.1, median 16.6 | **FAIL** on the median; 2 of 6 pass |
| audio underruns / session | ~<= 10 | 1-3 | **PASS** |

Four of six rows meet target and the two that do not are both transport.
**`max output gap` remains the one row no topology change has moved** —
it failed on the PC path and it fails here.

## Host thermals, incidental

The `D-BASE-T1` sampler ran unattended with every session, as designed: 38
samples across the window, hottest sensor **44.85 -> 58.38 °C**, the same
ramp-to-plateau `S1`/`T1` recorded. Nothing acts on it.

## What this does not establish

- Six sessions in one window against eleven across two nights, with the
  arms overlapping and the builds not matched. **Not a verdict on the
  Windows PC.**
- The deferred UDP burst/gap pathology is **not** resolved. The burst
  shape fell but did not go away, and same-stamp duplication was not
  measured here at all (`duplicate_highest_packets` is 0 in every session
  of both arms, which is the client's view, not the wire's).
- Nothing about the house-router arm of Group B, which was not run.
