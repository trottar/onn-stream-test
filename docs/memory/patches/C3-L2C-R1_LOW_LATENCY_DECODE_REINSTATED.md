---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# C3.L2c-R1 — unconditional `KEY_LOW_LATENCY` reinstated for a distribution read

## Purpose

`C3.L2c` (`patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`) was installed on
2026-09-19 and rolled back the same day on one `max_output_gap_ms` sample
(359 -> 385 ms), while the same session showed 159 receive-to-output
spikes/min against 1,828-2,723 for every other session that day.

Group A's full-corpus re-score established the rule that decided this
re-run: **a worst-case statistic must not overrule a distribution**, and
A2.7 explained the 385 ms as an arrival gap (`max_rx_to_decode_ms` 111, so
>= 274 ms with no access unit arriving), owner transport. A1-live then showed
the bitstream on the wire is explicit and correct — no B-frames,
`max_num_reorder_frames 0`, `max_dec_frame_buffering 1`, `dpb_output_delay 0`
— leaving the client-side `KEY_LOW_LATENCY` request as the only remaining
lever on the 20-60 ms steady state.

`D-BASE` Step 2 reopened `C3.L2c` on the distribution. The user authorized
this change, including the production-behaviour source change, on the
evening of 2026-09-20.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`:
  `22038e355f85bb8330d900bae64c37db54c902d4affdef12be4810bb03271c07`
  (verified before the write — the same predecessor the 2026-09-19 install
  had, because that install was rolled back to exact bytes)

## Changed scope

Changed: the `init` block in `AvcLowLatencyDecoder.kt` — removes the
`codec.codecInfo.getCapabilitiesForType(...)` /
`isFeatureSupported(FEATURE_LowLatency)` gate and the now-unused
`import android.media.MediaCodecInfo`; requests
`MediaFormat.KEY_LOW_LATENCY` unconditionally on
`Build.VERSION.SDK_INT >= Build.VERSION_CODES.R`. The `try`/`catch` and the
`lowLatencyEnabled` reporting flag are retained unchanged.

Installed result:
`9a4e80703169dcbd285de530b44b5c087a0aeab9772a8be3b9549135efcc5f96`.
APK: `10e99088306e7e8762419b9c9930a52adad3f383a7e16885d8f7a4876054da00`.

**This is not byte-identical to the 2026-09-19 install
(`dd67acfe…906e7`).** No diff, installer or backup of those bytes survives —
`archive/patch_backups/privyhub_c3l2c_low_latency_decode_01_20260919T034939Z/`
holds only the predecessor — so the change was re-derived from the
`C3-L2C` record's own description of it. Three formatting variants were
hashed against `dd67acfe…906e7` and none matched; the difference is layout
in the rewritten block, not behavior. `low_latency_enabled` reads **true**
in all three runtime reports, which is what the recorded hash stood for.

Unchanged: `D-BASE-R1`'s resync loss counter (`RtpH264Receiver.kt`,
`NativeStreamActivity.kt`) is kept in and was not touched; resolution, frame
rate, GOP, B-frames, FEC wire format, RTP payload type, packet size, ports,
process audio, controller transport, emulator lifecycle, the decoder's
input/output loop, metrics collection and slow-event retention.

## Validation performed

- predecessor SHA-256 verified before the write;
- `git diff --check` clean;
- the real `sh ./gradlew :app:assembleDebug --no-daemon` from `PrivyHub/` —
  `BUILD SUCCESSFUL in 8s`;
- `adb install -r` to the onn — `Success`, no force-stop issued;
- **runtime, three sessions**: PS1 reference title, attract-mode demo,
  133.0 / 131.8 / 131.8 s, zero input (`controller.motion_events` 0 in all
  three), opened through the launcher's RESUME PLAYING preview and ended
  with BACK, `low_latency_enabled: true` confirmed in each report before it
  was counted;
- scored with `evidence/group_a_2026-09-20/a2_rescore_decoder_sessions.py`
  against the 128-session non-low-latency corpus and against the same-day,
  same-title, same-procedure `D-BASE-R1` control;
- teardown per `TOOLS.md`: game ended from the client first, "NOW PLAYING"
  banner confirmed gone by `uiautomator dump` (0 occurrences), only then the
  companion stopped; no companion, RetroArch, ffmpeg, FEC relay or
  process-audio process and no listener left behind.

**Not performed:** no perceptual or gameplay judgement. By explicit
instruction every acceptance metric in this work is instrumentation. Three
attract-mode demos with zero input do not speak to how the picture looks.

## Result

**INSTALLED — DECISION PENDING.** The build is on the onn and the source
change is in the working tree. It was **not** auto-reverted; the keep/revert
decision is the user's, on the evidence. Full record:
`evidence/C3_L2C_DISTRIBUTION_2026-09-20.md`.

| metric | corpus median (128) | control (same day) | S1 | S2 | S3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `spike_20_ms`/min | 2,534.7 | 2,258.4 | 203.4 | 106.6 | 118.8 |
| `stale_output_drops`/min | 192.1 | 169.9 | 32.9 | 8.7 | 7.3 |
| rendered fps | 55.5 | 56.27 | 58.30 | 58.65 | 59.13 |
| received-AU fps | 59.2 | 59.19 | 58.97 | 59.07 | 59.35 |
| `max_output_gap_ms` | 288.5 | 639 | 1,352 | 388 | 236 |
| `max_codec_ms` | 299.0 | 647 | 209 | 250 | 91 |
| `sequence_resyncs` | — | 3 | 2 | 3 | 0 |

Frames under 20 ms receive-to-output: 36.4 % (control) -> **94.3-97.0 %**.
The 20-60 ms rendered band: 58.8 % -> 2.8-4.8 %.

**What succeeded.** The decode-path faults improve by a factor of ~20 across
all three sessions, not one. `spike_20_ms/min` meets the `D-BASE` target of
< 200 in two of three (S1 is 1.7 % over, in the session with the worst
transport); `stale_output_drops/min` meets < 20 in two of three. The
client-side fps deficit falls from a corpus median of 3.5 fps to
0.22-0.67 fps.

**What did not.** `max_output_gap_ms` misses its 100 ms target in every
session, and rendered fps misses 59.5 in every session. Lost packets/min
(237-432, target < 10) and audio underruns/min (48-184, target < 5) are
untouched, as expected.

**The 2026-09-19 negative result is confirmed, not overturned:** faster
single-frame decode does not imply a shorter worst-case stall. What this run
adds is the attribution — in all three sessions the worst gap is an arrival
gap. In S2 and S3 the slow-event buffer did not overflow, so every frame
with >= 50 ms receive-to-output latency has a row, and the worst gap is not
among them: the ending frame arrived and was output in under 50 ms, so the
decoder held nothing. S3 had **zero** discontinuities and still gapped
236 ms on a 93-packet loss burst. In S1 the buffer overflowed, so the
attribution is a bound: `max_codec_ms` 209 and `max_rx_to_decode_ms` 230 cap
the decode path, leaving >= 1,122 ms of the 1,352 with no access unit to
output. **`max_output_gap_ms` on this build is a transport metric.**

**What remains unknown.** Why the decoder holds 20-60 ms without the flag —
the flag removes the hold, the mechanism is not established, and A1-live has
already ruled out the bitstream asking for it. Also unmeasured: perceptual
quality, and the variance of the effect (n=3; the S1/S2/S3 spread tracks
transport quality, which is an observation, not a finding).

**Instrumentation defect found by this run.** A slow event is recorded only
when receive-to-output latency >= 50 ms (`SLOW_EVENT_THRESHOLD_MS`). On this
build an arrival gap ends with a fast frame, so the session's worst output
gap now routinely has no per-event row, and
`slow_event_retained_marked` was **0 in all three sessions** despite five
resyncs between them — the `C3.L2b` 2,000 ms cycle window protected nothing
because nothing qualified. Locating a gap directly would need a second
trigger on `outputGapMs`. Registered in `KNOWN_ISSUES.md`; not fixed here.
