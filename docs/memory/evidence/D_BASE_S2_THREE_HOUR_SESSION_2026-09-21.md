---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-S2 — one uninterrupted 3-hour session on the PC path

## Classification

**CHARACTERIZED**, and it answered more than it was asked. One session,
**10,814,688 ms (3.00 h)**, completed and ended cleanly.

Three results, in order of how much they change:

1. **`D-BASE-S1`'s RetroArch memory growth is not a leak.** It plateaus
   after ~30 minutes and **the growth is file-backed, not anonymous.**
2. **The link degraded in the last 30 minutes and did what no injection
   could.** Five natural `desync_pause` events — **three of them on the
   host-side `controller_silence` trigger that MEMORY.md recorded as
   untestable without stopping the client** — one successful
   `method: "restart"` encoder restart during a live 78-second outage, and
   five clean resumes. This is most of what `D-BASE-R3b` is owed, obtained
   naturally.
3. **The `C5` hypothesis is FALSIFIED** by its own pre-registered rule.

## (1) RetroArch memory plateaus, and the growth is file-backed

Host **MemTotal 15,667,476 kB (14.94 GiB)**, swap untouched (`VmSwap` 0 for
the whole session).

`ra_rss_kb` per 30-minute block, start → end, with the slope:

| block | start | end | slope / 30 min |
| --- | ---: | ---: | ---: |
| 0-30 min | 151,780 | 261,976 | **+111,950 kB** |
| 30-60 min | 262,048 | 263,268 | +1,239 |
| 60-90 min | 263,236 | 270,116 | +6,990 |
| 90-120 min | 270,116 | 270,628 | +520 |
| 120-150 min | 270,628 | 271,652 | +1,040 |
| 150-179 min | 271,652 | 271,656 | **+4** |

**The +108 MB per 30 min that `D-BASE-S1` measured is the first block and
only the first block.** After it the rate falls by two orders of magnitude.
Total growth over 3 hours is **+119.9 MB**, of which **+110.2 MB happened
in the first 30 minutes**.

**And it is file-backed.** Splitting the same series:

| | start | end | total |
| --- | ---: | ---: | ---: |
| `RssFile` | 83,208 | 196,772 | **+113,564 kB** |
| `RssAnon` | 66,448 | 72,672 | **+6,224 kB** |
| `RssShmem` | 2,124 | 2,212 | +88 |
| `VmSwap` | 0 | 0 | 0 |

`RssFile`'s own blocks are +109,520 / +1,239 / +3,771 / +520 / +321 / **0**:
the emulator's mapped ROM, core and assets becoming resident, which
finishes and stops. **`RssAnon` — the part that cannot be reclaimed — grew
6.2 MB in three hours, about 2.1 MB/hour**, and its last block was +4 kB.

**So the S1 reading was right about the number and wrong about the risk.**
Projecting S1's +108 MB/30 min to 3 hours would have predicted ~650 MB;
the actual figure is 272 MB. At the anonymous rate that actually persists
(~2.1 MB/h), and against 14.94 GiB of RAM with ~7.6 GiB available at the
end of this session, **exhausting memory would take on the order of 150
days of continuous play** — which is to say it is not a concern, and the
file-backed part is reclaimable under pressure anyway. `MemAvailable` was
**7,832,556 kB at the start and 7,954,440 kB at the end** — higher, not
lower.

## (2) The companion plateaus too

`comp_rss_kb` 40,960 → **47,724 kB**, in blocks of +6,030 / +146 / +118 /
+211 / +179 / +179 kB per 30 min. The first block is startup; after it the
rate is ~0.18 MB per 30 min and flat, so **+6.8 MB over three hours with no
sign of acceleration**. `RssAnon` tracks it exactly (28,560 → 35,324), and
threads stayed 5-7. The encoder is entirely flat: `enc_rss_kb` 120,060 →
120,524, blocks of +524 / 0 / 0 / 0 / 0 / -73 kB.

(This is the first correct companion series; `D-BASE-S1` sampled a shell
wrapper for its S1 session, the defect that record discloses.)

## (3) Starvation is still linear at ~75/min, and the queue did not move

`prolonged_starvation_events` **13,682 over 180.2 minutes = 75.9/min**,
against `D-BASE-S1`'s 72.4-79.2/min and `D-BASE-P2b`'s 63-79/min on
two-minute sessions. **The rate is unchanged across a 90x range of session
lengths**, and it held through a degraded final half-hour.
`avg_queue_residence_ms` **27.86**, inside S1's 27.66-27.96 and P2b's
27.29-28.21 — **the queue equilibrium does not move**, at any duration.

`underruns` were **11,958** here against 16-69 in S1's 30-minute sessions.
That is not a duration effect: it is the outage. Audio starves while video
is gone, and the last half-hour is where the losses are.

## (4) Stream drift over 3 hours: none until the link broke

Per-minute rendered fps by 30-minute block: **59.528 / 59.714 / 59.619 /
59.710 / 58.779 / 56.828**. The first four blocks are flat and indeed the
fourth is the second-highest. The last two fall, and they are the blocks
that contain the outage. Spearman of per-minute fps against elapsed minute
is **-0.251** over the whole session — driven entirely by the tail.

Split at 150 minutes:

| | ticks | fps | max output age | ticks > 1 s |
| --- | ---: | ---: | ---: | ---: |
| first 150 min | 4,465 | **59.416** | 6,640 ms | 1 |
| last 30 min | 807 | 54.702 | **75,661 ms** | 2 |

**For two and a half hours nothing drifted** — that is the answer to the
question as asked, and it extends `D-BASE-S1`'s 30-minute result five-fold.
Host telemetry agrees: encoder CPU 25.5-27.3 % with Spearman -0.012, GPU
power flat, CPU temperature *falling* slightly over the session (Spearman
-0.534, first 40.6 °C, last 55.8 °C, max 57.6 °C — it ramps to plateau
early and the negative rank correlation is the plateau, not cooling).

Whole-session totals are dominated by the tail and should be read with
that in mind: `max_output_gap_ms` **77,592**, loss **389.5/min** against
S1's 115-129, `spike_20_ms` 119.7/min, stale drops 5.1/min, 1,703
forward-gap events, max forward gap 112 packets, **`late_or_reordered_
packets` 0** — the PC path still never reorders, even while failing.

## (5) Recovery fired five times, naturally — including the host trigger

The event this project has been unable to manufacture happened on its own.
From `recovery_lines.jsonl`:

| at | event | trigger | age_ms | outcome |
| --- | --- | --- | ---: | --- |
| 07:13:04.586Z | desync_pause | **controller_silence** | 1,002.8 | resumed after 9,274 ms |
| 07:55:28.492Z | desync_pause | client_output_silence | 1,364.0 | resumed after 13,652 ms |
| 08:18:50.153Z | desync_pause | **controller_silence** | 1,002.9 | resumed after 11,454 ms |
| 08:21:42.899Z | desync_pause | **controller_silence** | 1,004.0 | resumed after 8,391 ms |
| 08:22:52.548Z | desync_pause | **controller_silence** | 1,002.9 | resumed after 78,355 ms, 1 restart |
| 08:26:47.225Z | desync_pause | client_output_silence | 1,050.0 | resumed after 4,713 ms |
| 08:39:59.163Z | desync_pause | client_output_silence | 1,080.0 | resumed after 9,032 ms |

Seven pauses, seven resumes, `PAUSED_SAVED` never reached, no recovery save
written, `restarts` 1 for the session.

**Four of the seven fired on `controller_silence`** — the **host-side**
trigger. `MEMORY.md` recorded that it "has never fired in a test" and that
"testing it needs the client stopped, not the link". **That is now
corrected**: a bad enough wireless link starves the client→host controller
channel too, and the host trigger fires on its own at `age_ms` 1,002.8-
1,004.0, i.e. within 4 ms of `DESYNC_MS`. The design's claim that the host
can be the authority on a desync is confirmed on real evidence.

**The encoder restart worked while the fault was live**, which is exactly
the `D-BASE-R3b` N15 criterion no substitute could reach:

```
08:24:09.813Z encoder_restart  attempt 1  method: "restart"
  last_output_age_ms 75661   age_pair_ms [72118, 75661]
  cycle: encoder_restarted true, capture_restarted false,
         ffmpeg_spawn_ms 215.473, encoder_down_ms 215.07,
         first_rtp_resume_ms 367.353, rtp_silence_after_spawn_ms 151.88,
         rtp_baseline_residual_packets 168, host_verified_ms 1120.226
```

`method: "restart"` (not the `full_start` fallback), the `D-BASE-R3a`
freshness rule satisfied by two rising heartbeats (72,118 → 75,661 ms), and
the session resumed 1.0 s later. The restart cost ~215 ms of encoder
downtime and 367 ms to first RTP — in line with the `C3.L1` figures.

**Still unexercised:** `GIVE_UP_MS` (no outage lasted 120 s), `END_MS`, the
recovery save and its launcher prompt. The 78-second outage is the longest
this project has recorded and it recovered without reaching give-up.

## (6) C5 — FALSIFIED by the pre-registered rule

94 sequence resyncs and 1 SSRC change; the report retains the newest **64**
(its capacity). Session counters:
`idr_aus_rejected_waiting_for_idr` **10**,
`non_idr_aus_dropped_waiting_for_idr` **1,059**,
`packets_dropped_waiting_for_idr` **11,563**. **The `C5a` counters fired
for the first time.**

Of the 63 retained sequence resyncs, **7 exceed 250 ms**:

| elapsed | resync_to_idr_ms | jump_packets | rejected_idr_aus | dropped_non_idr_aus | au_complete |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9,348,909 | 275 | 167 | **0** | 12 | true |
| 9,349,145 | 253 | 284 | **0** | 15 | true |
| 10,143,165 | 801 | 128 | **0** | 40 | true |
| 10,425,826 | 450 | 422 | **0** | 10 | true |
| 10,531,209 | 326 | 673 | **0** | 14 | true |
| 10,550,548 | 493 | 154 | 2 | 67 | true |
| 10,561,978 | **1,340** | 403 | **0** | 54 | true |

**`C5a`'s rule: falsified if discontinuities over 250 ms show 0 rejected
IDRs. Six of the seven do, including the longest at 1,340 ms.** And the
converse half fails too: the only other row with a rejection,
elapsed 10,019,155, took **240 ms — under one GOP — while rejecting 1
IDR**, which the mechanism says is impossible, since a rejected IDR is
supposed to cost a further whole GOP.

**So the completeness gate is not what makes an ordinary resync slow.**
What the data shows instead: resyncs are mostly *fast* — p50
**71 ms**, p90 253 ms over the retained rows — and the long tail is not
explained by rejected IDRs. The rows over 250 ms are distinguished by
`dropped_non_idr_aus` (40, 54, 67 on the three longest) rather than by
rejections: the receiver is waiting through many non-IDR access units, i.e.
**waiting for an IDR to arrive at all**, not discarding damaged ones. On a
link losing 389 packets/min the encoder's next scheduled IDR is itself
often lost, and the wait becomes two or three GOPs. `C5`'s own "one GOP of
unavoidable wait" is the mechanism; its second cost is not.

This supersedes `C5`'s §2 conclusion and retires `C5`'s §5 bounded
fallback as a remedy for a cause that does not exist. Adding these to the
five earlier natural resyncs (`D-BASE-P2b`, `D-BASE-S1`), **69 natural
sequence resyncs have now been observed on the `C5a` build and 66 of them
rejected zero IDRs.**

## (7) Rotation: no, and the size it reached

The heartbeat log finished at **2,961,714 bytes** against its 4 MiB
(4,194,304) threshold — it did not rotate, as the task expected. Growth
over the session was ~1.36 MB, i.e. **~453 KB per hour**, so it would
rotate after about **9 hours** of continuous streaming from empty.
`native_stream_recovery.log` reached 19,002 bytes against 1 MiB.
`stream_log_archive/` held **0 files**. `D-BASE-R4`'s rotation is still
only synthetically tested. FEC reported 1,430,759 groups and **0 send
errors**.

## Method

One attract-mode session of the PS1 reference title, 3 hours, zero input,
opened through RESUME PLAYING per `TOOLS.md`, BACK to end. Host sampled
every 30 s (360 samples) by `s2_sampler.py` — `D-BASE-S1`'s sampler with
the companion matcher already fixed, plus `RssAnon` / `RssFile` /
`RssShmem` / `VmSwap` / `VmSize` per process and `MemTotal` /
`MemAvailable` / `SwapFree`. Session 2026-09-21T05:51:02Z - 08:51:15Z.

Teardown per `TOOLS.md`: game stopped, banner confirmed clear, companion
stopped last, no process in state `T`, no listener on 8765 / 48100-48102 /
48110, no recovery save to discard.

## Artifacts

Under `evidence/d_base_s2_2026-09-21/`, with `s2_sha256.txt`: the decoder
report, `samples.jsonl` (360 rows), `heartbeat_lines.jsonl` (5,272 rows),
`recovery_lines.jsonl`, `status_end.json`, `host_samples.csv`,
`per_minute.csv`, `s2_analysis.txt`, and the harness (`s2_sampler.py`,
`s2_session.sh`, `s2_analyse.py`).

## Privacy

No network addresses, MACs, SSIDs, ADB endpoints or device identifiers
appear here or in the artifacts. The sampler drops address-like keys and
IP-shaped values before writing; the only dotted-quad matches in the
artifacts are the RetroArch core version string `0.9.44.1`.
