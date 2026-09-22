---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P2 — where the audio underruns are

## Classification

**CHARACTERIZED.** Five probe sessions, none rejected, plus a 177-session
corpus read. The question is answered and the answer is narrow:

**`audio.underruns` is almost entirely a startup artifact. A median 98.7 %
of a session's underruns occur in the first 3 seconds, before the
stabilization gate releases gameplay, and they stop the moment real PCM
starts arriving.** The "113 / min" in the target table is a fixed
per-session burst divided by a short session; the steady-state rate is
close to zero, not 17 / min.

Diagnostic instrumentation only. Product audio behaviour is unchanged.

## Step 1 — the corpus, no runtime

177 sessions >= 15 s since 2026-09-16
(`d_base_p2_2026-09-20/p2_audio_corpus.py`, table in
`p2_audio_corpus.csv`, LF line endings). Totals: `underruns` p50 **129**,
p90 255, max 12,020 (one outlier); per minute p50 **121.6**, which
reproduces Group A's 113.

**The per-minute figure falls as sessions get longer, and the total does
not rise with them.** Medians by duration bucket, the 12,020 outlier
excluded:

| duration | n | `underruns` | per min | `prolonged_starvation_events` | `concealed_underruns` |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0-40 s | 42 | **116** | 262.1 | 36 | 378 |
| 40-80 s | 48 | **126** | 124.0 | 74 | 644 |
| 80-150 s | 58 | **158** | 99.8 | 109 | 918 |
| 150-300 s | 16 | **126** | 37.0 | 203 | 1,454 |
| 300 s+ | 7 | **162** | 12.6 | 749 | 5,382 |

`underruns` is flat at 116-162 across a fourteen-fold change in duration
while starvation and concealment scale with it, roughly twentyfold.
Spearman `underruns_pm` against duration is **rho -0.725** (n = 177) — the
signature of a fixed cost divided by a growing denominator. An OLS fit of
`underruns = burst + rate x minutes` gives burst **148.2** and rate
**2.91 / min** with r² 0.006 (n = 171, outlier excluded): the intercept is
the number that matters and the slope is nearly noise, which is exactly
what a burst-plus-nothing looks like.

Spearman against the neighbours (n = 177):

| pair | rho |
| --- | ---: |
| `underruns` vs `concealed_underruns` | **0.502** |
| `underruns` vs `avg_queue_residence_ms` | **-0.414** |
| `underruns` vs `prolonged_starvation_events` | **0.195** |
| `underruns` vs `stale_drops` | 0.186 |
| `underruns` vs `smooth_latency_trims` | 0.186 |
| `underruns` vs `crossfaded_packets` | 0.171 |
| `underruns` vs `packets` | 0.145 |
| `underruns` vs `lost_packets` | **0.113** |

Two readings worth keeping. **Audio packet loss does not drive underruns**
(rho 0.113). And the negative correlation with average queue residence
(-0.414) says underruns happen when the queue is *shallow* — starvation,
not lateness. `stale_drops` and `smooth_latency_trims` are identical
because they are incremented together
(`NativeAudioReceiver.kt` 703-704).

## Step 2 — the probe build

Client-side, diagnostic only, product behaviour unchanged. Added:

- `audio.tick_series` — one row per existing 500 ms tick, capped at
  **400 rows = 200 s**, with `audio.tick_series_columns`
  `[elapsed_ms, underruns_delta, starvation_delta, concealed_delta,
  queue_depth, buffered_ms]`. Deltas, not totals, because the question is
  *when*.
- `audio.first_write_elapsed_ms` — when the first **real** PCM packet
  reached `AudioTrack.write` (`NativeAudioReceiver.firstWriteAtNs`).
- `audio.first_video_output_elapsed_ms` — when the first frame left the
  decoder (`AvcLowLatencyDecoder.firstOutputAtNs`).

APK `466cfb01da00d3e2a9ef8131707dcdf37927b7788651ca56011145511cd7de2f`.

## Step 3 — five sessions

Attract mode, PS1 reference title, 120 s held, zero input, BACK to end.
**None rejected** — all five had **zero** stream discontinuities, so no
session had a resync jump >= 128 packets in the first 30 s or anywhere else.

```
run     dur_s  underr  starv  conceal  firstWr firstVid    gate  80% by  last dU  burst%
P2A     127.1     315    138     1213     2180     1091    5209    1992     6615   99.4%
P2B     125.9     205    146     1210     1712      727    4200    1512     6642   96.6%
P2C     130.9     207    138     1181     1679      787    9260    1476   124447   94.2%
P2D     134.0     201    145     1211     1800      766   12378    1478    21874   99.0%
P2E     127.1     399    134     1304     2762     1757    5757    2499    81202   98.7%
```

Medians: `underruns` **207**, `prolonged_starvation_events` **138**,
`concealed_underruns` **1,211**; `first_write_elapsed_ms` **1,800**,
`first_video_output_elapsed_ms` **787**, so **audio's first real packet
lands 1,013 ms after the first video frame**; `native-stream-ready` (the
gate release, from the companion recovery log) at **5,757 ms**; 80 % of
underruns by **1,512 ms**; **98.7 % of underruns inside the first 3 s**.

The first ticks of P2A, which is the whole phenomenon in six rows
(`[elapsed_ms, dU, dStarv, dConceal, queue_depth, buffered_ms]`):

```
[  19,  0, 0,  0, 0,  0]
[ 448, 45, 1, 47, 0,  0]
[ 666, 34, 0, 38, 0,  5]
[ 963, 42, 0, 53, 0,  5]
[1476, 76, 0, 88, 0,  0]
[1992, 81, 0, 92, 0,  4]
[2409, 35, 0, 38, 5, 19]   <- real PCM arrives; queue fills; underruns stop
[2505,  0, 0,  0, 5, 18]
```

`queue_depth` is **0** for every tick of the burst and `buffered_ms` is
0-5. At 2,409 ms the queue reaches 5 packets and 19 ms buffered, and the
underrun count never moves again in any meaningful way.

## The four questions

**(1) When does the burst happen?** In the window **0 to ~2.5 s**, holding
a median **98.7 %** of the session's underruns (80 % by 1,512 ms). It is
**over before the stabilization gate releases gameplay** — the gate fired
at a median 5,757 ms, and in the latest case 12,378 ms, two to eight times
later than the burst. It **starts before and ends at** the first real audio
write (median 1,800 ms), and it **starts after the first video output**
(median 787 ms). So the ordering is: video output at ~0.8 s, underruns from
~0.4 s to ~2.4 s, first real audio at ~1.8 s, gate release at ~5.8 s.

**(2) One event or many?** One. After 5 s each session has **1 to 3
isolated ticks** carrying **2 to 12 underruns in total** — between 0.6 %
and 5.8 % of the session. There is no second burst and no drift.

**(3) Do the steady-state underruns coincide with video slow events?**
**No.** Across the five sessions there were 8 late underrun ticks in all,
and **1 of 8** fell within 750 ms of a `slow_events_ge_50_ms` row — against
64 slow events per session, so a randomly placed tick would often land near
one anyway. They run independently, and there are too few of them to carry
any conclusion in either direction.

**(4) Is `prolonged_starvation_events` the same thing counted
differently?** **No — it is a second, unrelated phenomenon.** It is
essentially absent from the burst (one event in the whole of P2A's burst)
and accrues steadily for the rest of the session at 1-2 per 10 s. It scales
with duration across the corpus (36 → 749 from the shortest to the longest
bucket) where `underruns` does not, and correlates with it at only
rho 0.195. `concealed_underruns` serves both: it tracks underruns closely
during the burst (47/45, 53/42, 92/81) and tracks starvation afterwards.

## One hypothesis and one candidate fix

**Hypothesis.** *The AudioTrack starts playing about 1.7 s before the audio
stream is flowing, and `AudioTrack.underrunCount` counts every buffer it
needed and did not get in between.* `playbackLoop` waits for the queue to
reach `TARGET_QUEUE_PACKETS` (3) but gives up after
`STARTUP_PREFILL_TIMEOUT_MS` = **100 ms**
(`NativeAudioReceiver.kt` 70, 777-799) and starts writing regardless. The
first real packet does not arrive until a median **1,800 ms**, because on
the host the encoder is spawned first and `_session_io.start(...)` —
which starts the audio streamer — runs after it
(`companion/native_stream.py` 1358, 1400). For ~1.7 s the loop therefore
writes concealment into a track with an empty queue, which is precisely
what the tick series shows: `queue_depth` 0, `buffered_ms` 0-5, underruns
accruing at 34-81 per 500 ms, stopping the tick the queue fills.

**Candidate fix, not implemented.** Do not start playback until there is
something to play: hold the prefill until the first **real** PCM packet has
been queued, with a generous bound (say 3 s) after which the current
behaviour resumes so a silent or absent audio stream cannot wedge the loop.
Equivalently, defer `AudioTrack.play()` to the first real packet. This
touches only the startup path; the steady-state queue target, capacity,
concealment, trim and crossfade logic stay as they are.

**Evidence that would accept it**, in order: `audio.underruns` per session
falls from ~207 to single digits with `audio.first_write_elapsed_ms`
unchanged (the fix must not delay audio, only the track's start);
`concealed_underruns` in the first 3 s falls with it;
`prolonged_starvation_events` and the steady-state series are unchanged,
confirming the second phenomenon was untouched; and no new A/V offset — the
first write timestamp is the control for that. Five sessions of the same
shape would settle it. A perceptual check is not required for this one:
nothing audible is being added, only silence that was already silent.

## What this does not show

- **Five sessions on a quiet link**, all with zero discontinuities, all
  attract mode with zero input. A session with real transport trouble may
  have a different steady-state behaviour; there is almost none here to
  measure.
- **The 12,020-underrun outlier in the corpus is unexplained** and was
  excluded from the fit. It is one session; nothing in this probe reaches
  it.
- **`prolonged_starvation_events` is named but not explained.** It accrues
  at 1-2 per 10 s all session long with a full queue, which is odd enough
  to deserve its own question; this probe only established that it is not
  the underrun burst.
- **Why audio starts ~1.0 s after video is not instrumented end to end.**
  The host ordering is visible in the code (encoder spawn, then session
  I/O), but the split between host-side start latency and client-side
  first-packet latency was not measured.
- **The steady-state rate is not zero, only near it.** Two to twelve
  underruns per session after the burst, on five sessions.

## Artifacts

Under `evidence/d_base_p2_2026-09-20/`:

| file | SHA-256 |
| --- | --- |
| `p2_audio_corpus.py` | `2e3b7cce48e12cd21d3ad8f4f1c90629a0f23a0fee826e2831d4496a348758ba` |
| `p2_audio_corpus.csv` (177 rows, LF) | `7e8f44f698cc668921c4e55fe061e0ce9e8be4b3815fbd49fa52b0dd2e461c3a` |
| `p2_audio_corpus_result.json` | `6c5eeb7ac91b761530dc140c25a281483ebbf8bf703a9b7ca862f411f9f42f37` |
| `p2_probe_analysis.txt` | `4f921b3e86dadc3da23b6e1b76f81c63c4397fdab50beea135164ca9a1e75700` |
| `session_index.txt` | `58db304cc01fc03d30370c76ae1dae0a9e55ee0fc9796d8a9bc22e2f42354338` |
| `native_decoder_20260920_235004_228.json` (P2A) | `d23d7e63fdb338d907a950e496c1c06d6b856a161a3010d34fc60d8e1f26b84f` |
| `native_decoder_20260920_235252_984.json` (P2B) | `30a79a84e001b8ec1a676e923de158910d7b765da7bc5406dc48ef570d4b09c0` |
| `native_decoder_20260920_235518_290.json` (P2C) | `b2804f946d740bcfab8b2e350f2b55491d25a50b2e5556d3252951c95e6aa8f2` |
| `native_decoder_20260920_235805_410.json` (P2D) | `7074cf1a3e027357717074c8497b1ac06d8cabad43b09146ff73ca04e099f7aa` |
| `native_decoder_20260921_000028_109.json` (P2E) | `2af64fe2818358db89f6f28a406fd08b2c4539f1a61aa46bce60b3b42897839a` |

## Teardown

Game ended from the client ("Don't Save"), banner confirmed gone (0
occurrences), companion stopped last. No companion, RetroArch or encoder
process left, **no process in state T**, no listener on 8765 or
48100-48102 / 48110.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts.
