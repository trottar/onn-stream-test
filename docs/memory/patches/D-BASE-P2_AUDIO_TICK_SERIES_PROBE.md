---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P2 — audio tick series and first-write/first-output timestamps

## Purpose

`audio.underruns` reads 113 / min median against a target of < 5, and the
report gave one total per session, so nobody could say *when* the underruns
happened — at stream start, during the stabilization gate, at the first
resync, or spread. These fields place them in time. Diagnostic only;
product audio behaviour is unchanged.

The measurement they enabled is
`evidence/D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md`.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`:
  `4c2a460953433a8ca902863278e0bed414411d4a9a2698efb3a522ab37b02610`
  (identical to the committed version; this file had not been touched by any
  patch in this series before now)
- `PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt`:
  `1fcafa837bbcff1210753ffe47477915af9e52717d4a2ce774dda474dc038e81`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `4e312415b0a795398067fe35367a98d6383065f7da0639b2c0cbf4434a90deb1`

## Changed scope

**`NativeAudioReceiver.kt`**
-> `71daabf541f5c93db55bb5c18e144b45daca280d3b6772ee4da3d529943fb437`.
A `@Volatile firstWriteAtNs`, set once when the first **real** PCM packet
reaches `AudioTrack.write`, and `firstWriteAtNs()` to read it. Nothing on
the playback path reads it; the prefill, queue target, capacity,
concealment, trim and crossfade logic are untouched.

**`AvcLowLatencyDecoder.kt`**
-> `ce5f03fa813584c5196b942959a96619abd250fabcd7eefc02ddf0cde6901108`.
A `@Volatile firstOutputAtNs`, set once beside the existing
`lastOutputAtUs` assignment in `drainOutputs`, and `firstOutputAtNs()`.

**`NativeStreamActivity.kt`**
-> `98bb8fa863e4d2a9bac1b171170ce45c074b4d71e445f18f0032f32664a1547b`.
`sampleAudioTick()` on the existing 500 ms tick appends one row to a
bounded list; the report's audio block gains `tick_series`,
`tick_series_columns`, `tick_series_capacity`, `first_write_elapsed_ms`
and `first_video_output_elapsed_ms`. `AUDIO_TICK_SERIES_CAPACITY` is 400
rows = 200 s. Rows are **deltas** since the previous tick
(`underruns_delta`, `starvation_delta`, `concealed_delta`) plus the
instantaneous `queue_depth` and `buffered_ms`, because the question is
*when*, and a total answers only *how many*. Both timestamps read -1 until
the event happens.

APK: `466cfb01da00d3e2a9ef8131707dcdf37927b7788651ca56011145511cd7de2f`.

**Unchanged:** every streaming constant, the audio queue target and
capacity, the 100 ms startup prefill, the decoder configuration and stale
policy, FEC, transport, the emulator, the recovery state machine, and every
existing report field.

## Validation performed

- `git diff --check` clean; real `sh ./gradlew :app:assembleDebug
  --no-daemon`; `adb install -r`; companion restarted with 8765 checked
  free (D-068);
- five 120 s attract sessions, zero input, driven per `TOOLS.md`; all five
  carried the new fields and **none was rejected** (zero stream
  discontinuities in every one);
- teardown per `TOOLS.md`: game ended from the client, banner confirmed
  gone, companion stopped last, no process left in state T, no listener
  left.

## Result

**The fields work and the measurement is decisive.** Full record:
`evidence/D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md`.

**A median 98.7 % of a session's underruns occur in the first 3 seconds**,
80 % by 1,512 ms, and they stop the tick the audio queue first fills.
`queue_depth` is **0** for every tick of the burst. The burst is over
before the stabilization gate releases gameplay (median 5,757 ms) and it
ends at the first real PCM write (median 1,800 ms), which itself lands a
median **1,013 ms after the first video frame**.

**So the 113 / min in the target table is a fixed per-session burst divided
by a short session**, and the corpus confirms it: across 177 sessions
`underruns` is flat at 116-162 from the 0-40 s bucket to the 300 s+ bucket
while `prolonged_starvation_events` and `concealed_underruns` scale roughly
twentyfold with duration. Spearman `underruns_pm` against duration is
**-0.725**.

**`prolonged_starvation_events` is a second phenomenon**, not the same
thing counted differently: essentially absent from the burst, steady at
1-2 per 10 s afterwards, correlated with `underruns` at only rho 0.195.

**Steady-state underruns are negligible and independent**: 2-12 per session
after the first 5 s, and 1 of 8 late ticks fell near a video slow event.

**Hypothesis and candidate fix, neither implemented** (in the record's own
section): the AudioTrack starts ~1.7 s before the audio stream flows
because `STARTUP_PREFILL_TIMEOUT_MS` is 100 ms while the first real packet
arrives at ~1,800 ms, so the playback loop writes concealment into an empty
queue and `AudioTrack.underrunCount` counts every buffer it missed. The
candidate is to hold the prefill until the first real packet, with a
bounded fallback. The record names the evidence that would accept it.

**The probe fields stay in the tree** as diagnostics.
