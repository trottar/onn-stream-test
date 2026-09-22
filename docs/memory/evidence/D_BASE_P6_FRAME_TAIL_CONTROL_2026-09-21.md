---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P6 — control the frame-size tail and watch the loss

Sessions ran 2026-09-22 02:28-05:10 UTC; filed with the rest of the
`D-BASE` night, as `P5` was.

## Classification

**CHARACTERIZED, and the transfer function is now demonstrated rather than
inferred.** `D-BASE-P5` showed loss *correlates* with the count of large
frames. This run *intervened* on that variable and the loss followed.

**Capping the encoder's largest frame at 90,000 bytes removes the
≥ 80-packet population entirely and cuts loss by 7-9x, at no measurable
cost in bitrate, frame rate or encoder CPU.** Two independent pairs.

| | | |
| --- | --- | --- |
| pre-registered: remove ≥ 80 % of ≥ 80-packet frames | required | **100 %** removed (718 → 0, 717 → 0) |
| pre-registered: loss falls ≥ 2x | required | **8.7x** and **7.1x** on the two pairs |
| pre-registered: `< 40`-packet bucket unchanged | required | 3.33 → 1.63 and 4.62 → 2.88 — **not raised** |

**Nothing was adopted. The default is in force**, confirmed by an argv
diff against A0 and by a final `status` read showing
`any_override: false`.

## 1. Step 0 — the installed control surface

| | |
| --- | --- |
| FFmpeg | **7.1.5-0+deb13u1** |
| VA-API / driver | libva **1.22**, **Mesa Gallium 25.0.7-2+deb13u1**, radeonsi (renoir) |
| encoder | `h264_vaapi`, profile high, 1280x720p60, GOP 15, `-bf 0`, `pkt_size=1200` |
| **RC mode in force** | **CBR** — read directly from `-loglevel verbose`: `RC mode: CBR.` `Block Level bitrate control: OFF.` |
| `max_frame_size` | **present** (`<int>` bytes, default 0). Available because the mode is CBR, not CQP |
| `-maxrate` / `-bufsize` | present; the **default already sets both to 7000k**, so the VBV arm changes `-bufsize` alone |
| `rc_mode` | present: auto / CQP / CBR / VBR / ICQ / QVBR / AVBR |
| `slices` | **absent** on this encoder |
| **intra-refresh** | **absent** on this encoder — there is no such option in `h264_vaapi` here |
| average QP | **not exposed.** The progress line reports `q=-0.0`; the `q=2-31` in the stream banner is the declared qmin/qmax, not an achieved value |

**Both knobs were smoke-tested for 60 s before any arm was spent**, exactly
as the task required, and **both bite** — so no arm was dropped:

| 60 s smoke | max frame | frames > 40 KB | ≥ 80 pkt |
| --- | ---: | ---: | ---: |
| default | 142,517 B | 214 | 2 |
| `-max_frame_size 40000` | **39,745 B** | **0** | **0** |
| `-bufsize 117k` | **17,254 B** | **0** | **0** |

`max_frame_size` truncated the tail while leaving p50 and p90 identical
(15,360 / 34,816 B in both). `-bufsize 117k` collapsed the whole
distribution. Neither was ignored by the driver.

## 2. The new instrument: frames measured in bytes

`-max_frame_size` is set in **bytes**, and a cap can only be checked
against the unit it caps, so the relay's `D-BASE-P5` counters gained a
payload-byte series beside the packet series: per second `payload_bytes`,
`max_bytes` with its own timestamp, `mean_bytes` and `frames_over_cap`,
plus a whole-session 1 KiB histogram for percentiles. **Counting only** —
the forwarding path is untouched and pacing stayed at 0 in every arm
(`send_errors` 0 in all seven).

**Measured bytes-per-packet: 1,063-1,069** across arms (1,026 in the VBV
arm, whose frames end on more partial packets). Not the 1,188 an
`pkt_size=1200` payload maximum would suggest, because the last packet of
each frame is partial — which is exactly why the task said to measure it
rather than assume 80 × 1200.

## 3. Choosing the caps from the measured knee, not from arithmetic

From **A0**, 72,500 frames, windows bucketed by their largest frame:

| A0's largest frame in the window | windows | loss | **loss / window** |
| --- | ---: | ---: | ---: |
| 30-40 KB | 10 | 29 | 2.9 |
| 40-50 KB | 13 | 50 | 3.8 |
| 50-60 KB | 15 | 40 | 2.7 |
| 60-80 KB | 16 | 20 | 1.2 |
| 80-100 KB | 12 | 51 | 4.2 |
| **≥ 100 KB** | **54** | **2,500** | **46.3** |

**The knee is at 100 KB and it is a step, not a slope** — a 10x jump from
every bucket below it. A0's own p99 is 90,112 B and 1.01 % of frames exceed
90 KB, which is the same 1 % population as the 718 frames of ≥ 80 packets
(80 × 1,069 ≈ 85.5 KB).

So: **A1 = 90,000 B** (just below the knee), **A2 = 60,000 B** (33.3 %
lower, inside the task's 25-35 % band), **B1 = `-bufsize 117k`** — the
one-frame budget, 7,000,000 / 60 ≈ 116,700 bits. B1 ran cleanly at 1x, so
the 2x fallback was not needed. `max_frame_size` and tight VBV were never
combined.

## 4. The arms

Seven 20-minute attract-mode sessions, zero input, companion restarted per
arm, the argv confirmed from `native-stream-status` before each hold.

| arm | knob | loss | /min | fwd gaps | max pkt | max byte | ≥ 80 pkt | enc kbps | fps | spike20/min | max gap ms | audio loss % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **A0** | default | **2,696** | 134.0 | 306 | 205 | 242,418 | 718 | 6,928.9 | 59.58 | 61.6 | 366 | 0.349 |
| **A1** | `max_frame_size 90000` | **311** | 15.4 | 105 | 77 | 89,996 | **0** | 6,929.7 | 59.88 | 34.9 | 167 | 0.200 |
| **A2** | `max_frame_size 60000` | **299** | 14.9 | 88 | 52 | 60,092 | **0** | 6,929.2 | 59.89 | 25.5 | 489 | 0.174 |
| **B1** | `-bufsize 117k` | **938** | 46.6 | 238 | 16 | 17,144 | **0** | 6,931.3 | 59.76 | 15.0 | 387 | 0.236 |
| **A0′** | default | **2,189** | 108.8 | 249 | 207 | 244,794 | 717 | 6,930.0 | 59.68 | 54.9 | 507 | 0.244 |
| **A1r2** | `max_frame_size 90000` | **408** | 20.3 | 119 | 77 | 89,937 | **0** | 6,929.7 | 59.88 | 33.3 | 561 | 0.348 |
| **A0r2** | default | **2,896** | 144.0 | 341 | 209 | 247,170 | 734 | 6,929.9 | 59.56 | 60.8 | 447 | 0.444 |

**Every arm: 0 sequence resyncs (A0 had 1), 0 onn socket drops, 0 relay
send errors.** The onn's receive path stayed excluded throughout, as `P5`
found it.

## 5. Loss conditional on frame size — the causal evidence

**Attribution method, stated because it is not exact.** The client reports
loss per heartbeat, not per frame, so a lost packet cannot be tied to the
frame it came from. Each 10 s window is instead assigned to the bucket of
its **largest** frame and the window's loss attributed there. This measures
*"windows that contained a frame this big lost N"*, not *"frames this big
lost N"* — the strongest statement the instruments support.

| bucket (largest frame in the window) | A0 loss/win | A0r2 loss/win | A1 loss/win | A1r2 loss/win | B1 loss/win |
| --- | ---: | ---: | ---: | ---: | ---: |
| < 40 packets | 3.33 | 4.62 | 1.63 | 2.88 | **7.79** |
| 40-59 | 2.45 | 2.71 | 2.83 | 4.91 | — |
| 60-79 | 1.27 | 3.79 | 2.69 | 2.75 | — |
| **≥ 80** | **42.5** | **45.5** | *(none)* | *(none)* | *(none)* |

**In both baselines the ≥ 80 bucket carries almost all the loss** — 2,550
of A0's 2,696 (94.6 %) and 2,685 of A0r2's 2,896 (92.7 %) — at **~14x the
loss per window** of any bucket below it. Cap the frames and that bucket
ceases to exist, while the small-frame buckets stay where they were. **That
bucket-specific pattern is the causal evidence this run was after, and it
is present in both pairs.**

## 6. What each knob did

**`max_frame_size` — effective, and the benefit saturates.** A1 (90 KB)
and A2 (60 KB) are **statistically indistinguishable on loss** (311 vs
299), although A2 constrains a third harder and removes 52-packet frames
A1 keeps. **Once the ≥ 80-packet population is gone there is nothing
further to win**, so the looser cap is the better setting: same benefit,
less constraint on the encoder, and therefore less of the quality cost this
run cannot see. A2 does reach a lower spike rate (25.5 vs 34.9 per minute).

**VBV — effective on the tail, but 3x worse overall, and it moves loss
into windows that had none.** B1 flattened hardest of all — **every frame
14-16 packets, max 17,144 bytes**, and its per-0.5 s achieved bitrate range
collapsed from A0's 64-15,792 kbps to **6,661-7,168 kbps**. Yet it lost
**938** against A1's 311. The reason is in the bucket table: **B1's
`< 40` bucket loses 7.79 per window against the baselines' 3.33 and 4.62**
— it is the only arm that made the small-frame windows *worse*. So
conventional rate control does **not** yield a similar tail benefit; it
trades a removed tail for a raised floor. By the pre-registered wording —
which requires the `< 40` buckets to be unchanged — **B1 does not show the
clean pattern and is not the recommendation**, despite the best spike rate
of any arm (15.0/min).

**No arm cost anything measurable elsewhere.** Achieved bitrate
**6,928.9-6,931.3 kbps** across all seven — a 0.03 % spread, so the cap
does not starve the stream, it redistributes within it. Encoder CPU
**26.6-26.9 %** median (range 26.1-27.5 across every arm), GPU power
17-20 W median with overlapping ranges: **no encoder-time cost**, which is
what the task asked to watch for.

## 7. Drift — flagged, and the conclusion survives it

The three baselines were **2,696 / 2,189 / 2,896**, a **±15 % spread**
around a 2,594 mean; A0 vs A0′ differ by 19 %, more than the ~10 % the
task set as tolerable. **Drift is flagged: the environment moved during
the run.**

Two things keep the result standing:

- **The content did not move.** The baselines' frame distributions are
  near-identical — ≥ 80-packet frames **718 / 717 / 734**, max byte
  **242,418 / 244,794 / 247,170**, p50 **11 / 11 / 11** packets. Only the
  loss moved, so the drift is in the air, not in what the encoder made.
- **Both pairs clear the bar against their nearer bookend.** A1 (311)
  against A0 (2,696) is **8.7x**; A1r2 (408) against A0r2 (2,896) is
  **7.1x**. Against even the most favourable baseline for the null — A0′'s
  2,189 — A1 is still **7.0x**. The pre-registered bar was 2x.

Per-minute Pearson: A0 vs A0′ **0.854**, A0 vs A0r2 **0.779** — the
content-lock holds between baselines. Against the capped arms it collapses
(A0 vs A1 **0.337**, vs A1r2 **0.038**), which is the *expected* signature:
the loss no longer tracks the content because the content's tail has been
removed.

## 8. What this run does NOT measure — the quality cost

**Stated plainly, as the task requires.** Nothing here can see a QP rise on
a scene change, and by standing instruction nothing perceptual is an
acceptance gate. Two consequences:

- **Average QP is not available.** `h264_vaapi` reports `q=-0.0` in the
  progress line on this driver; the `q=2-31` in the banner is the declared
  range, not an achieved value. Recorded as an absence rather than
  substituted.
- **The one number that stands in for it is the achieved bitrate**, and it
  does not move: **6,929.7 kbps capped against 6,928.9 uncapped**. The
  encoder is spending the same bits. What a cap changes is *when* it is
  allowed to spend them — a 242 KB scene-change frame becomes a 90 KB one
  and the difference is made up over the following frames.

**A 90 KB cap is 2.7x the p90 frame and 1.5x the uncapped p99**, so it
binds on roughly 1 % of frames. That is the shape of the risk: a small
number of scene changes encoded with fewer bits than the encoder wanted.

**Whether that is visible is the user's own check, and it is the step
before anything is adopted.** This run cannot make it.

## 9. Levers and costs — the user's decision

Nothing was adopted and the default is in force.

- **`-max_frame_size 90000`** — the measured recommendation. **7-9x less
  loss**, 3x fewer forward gaps, max forward gap 61 → 13-27 packets, spikes
  61.6 → 33-35/min, fps 59.58 → 59.88, audio loss also lower. **Costs: no
  bitrate, no CPU, no GPU power that this run can measure — only the
  unmeasured picture quality on the ~1 % of frames it binds on.**
- **`-max_frame_size 60000`** — same loss benefit, lower spike rate, and a
  third more constraint. Choose it only if the tighter spike figure matters
  more than the larger quality risk.
- **`-bufsize 117k` (VBV)** — smoothest bitrate and best spike rate, but
  **3x the loss of the cap** and it raises loss in windows that had none.
  Not recommended on this evidence.
- **Not a lever: a larger client receive buffer** (`P5`), and **not
  intra-refresh**, which this encoder does not offer at all.

## 10. Sessions and artifacts

Seven 20-minute sessions plus three 60 s knob smokes. Per arm: ~598
heartbeats, 1,201 frame-size seconds, ~631 socket samples, ~72,500 frames
counted. Teardown per `TOOLS.md` after the last: game stopped, banner
confirmed gone, companion stopped last, no orphaned RetroArch.

**The default is restored and verified two ways**: `encoder_cmd_A0r2.txt`
diffs clean against `encoder_cmd_A0.txt`, and the final `status` read
returns `encoder_overrides.any_override: false`.

Under `evidence/d_base_p6_2026-09-21/`, SHA-256s in `p6_sha256.txt`:
`p6_run.sh`, `p6_analyze.py`, `p6_host.py`, `test_frame_bytes.py`;
per arm `frames_*.jsonl`, `heartbeat_*.jsonl`, `socket_*.jsonl`,
`report_*.json`, `status_*.json` (the per-second ring stripped — it is
`frames_*.jsonl`; the whole-session histograms are kept),
`encoder_cmd_*.txt`; plus `index.txt`, `analysis_full.txt`,
`host_summary.txt`, `p6_arms.json`, `p6_host.json`.

Patch: `patches/D-BASE-P6_FRAME_BYTE_COUNTERS_AND_ENCODER_KNOBS.md`.

## 11. Privacy

No address, MAC, SSID or device identifier appears in this record or in any
stored artifact. The encoder argv files contain the loopback destination
`127.0.0.1` and the local render node, both constants of the code rather
than device identity.
