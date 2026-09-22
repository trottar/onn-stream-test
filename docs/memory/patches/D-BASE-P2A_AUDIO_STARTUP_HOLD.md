---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P2a — hold audio playback until real PCM arrives

## Purpose

`D-BASE-P2` located the audio underrun burst: a median 98.7 % of a
session's `audio.underruns` occur in the first three seconds, ending the
tick the audio queue first fills, with `queue_depth` **0** throughout.
The mechanism it identified: `playbackLoop` gives up on its prefill after
`STARTUP_PREFILL_TIMEOUT_MS` = 100 ms while the first real PCM packet
arrives a median **1,800 ms** into the session — the host spawns the
encoder first and the audio sender after — so the AudioTrack plays
concealment into an empty queue for ~1.7 s and `AudioTrack.underrunCount`
counts every buffer it missed.

This is that record's candidate fix, implemented.

## Expected predecessor

- `PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`:
  `71daabf541f5c93db55bb5c18e144b45daca280d3b6772ee4da3d529943fb437`
- `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`:
  `98bb8fa863e4d2a9bac1b171170ce45c074b4d71e445f18f0032f32664a1547b`

## Changed scope

**`NativeAudioReceiver.kt`**
-> `76fe6401fb02da3897794b1aff7fe5f9e06815c5d03eb73447306a4a00877131`.
`STARTUP_REAL_PCM_TIMEOUT_MS` = 3,000. `enqueueLatest` sets
`firstRealPacketQueuedNs` on the first real packet — the same event
`firstWriteAtNs` marks, one step earlier. `playbackLoop` waits for it
before the existing prefill and before `AudioTrack.play()`, bounded by that
timeout, then runs the original startup path unchanged. Records
`startupWaitMs` and `startupWaitTimedOut` with accessors.

**`NativeStreamActivity.kt`**
-> `51dab63f996fd8dd85e72f137e59553ad58aa9366fc5cb0c48d0704ff637f551`.
The audio block gains `startup_wait_ms` and `startup_wait_timed_out`.

APK: `95b44b2ace97cdc87ef043cb415e5d1ba679cacbe66de22cf924e043b99c945d`.

**Unchanged:** `TARGET_QUEUE_PACKETS`, `QUEUE_PACKETS`,
`STARTUP_PREFILL_TIMEOUT_MS`, concealment, trim, crossfade and every
steady-state path; every streaming constant; the decoder; the companion.

## Validation performed

- `git diff --check` clean; real `sh ./gradlew :app:assembleDebug
  --no-daemon`; `adb install -r`; companion restarted with 8765 checked
  free (D-068);
- five 120 s attract sessions, zero input, driven per `TOOLS.md`; **none
  rejected** (zero discontinuities in every one);
- teardown per `TOOLS.md`.

## Result

**DEVELOPMENT — not reverted.** Record:
`evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md`.

**The fix works on the thing it targets.** `audio.underruns` per session
**0 / 6 / 21 / 20 / 3, median 6**, against P2's **315 / 205 / 207 / 201 /
399, median 207** — a 34x reduction. Underruns in the first three seconds
are **0 / 1 / 2 / 3 / 0** against ~204. The opening ticks are flat where
P2's climbed. `startup_wait_ms` is 1,640-2,234 and tracks
`first_write_elapsed_ms` to within ~60 ms: the hold lasts exactly as long
as the stream takes to arrive.

**Six of eight accepting checks pass**, including the one that guards
against the obvious failure mode: `first_write_elapsed_ms` median **1,793**
against P2's 1,800 — **7 ms** — so the fix delays the track's start, not
the audio. No session timed out on the 3,000 ms bound.

**Two checks miss.**

- **`prolonged_starvation_events` median 151 against P2's 134-146.**
  Per-session 137 / 143 / 151 / 157 / 163, monotonic in run order where
  P2's was flat. **It does not track link quality** — video loss across the
  five runs is 8.8 / 63.9 / 206.7 / 110.4 / 179.1 per minute, not
  monotonic, and the P2 control saw the same spread with starvation flat.
  So: a +9 % change coinciding with the fix, with a shape the fix cannot
  itself produce. Drift through the run and a real side effect are both
  open; five more sessions in the opposite order would separate them.
- **Rendered fps median 59.38 against a >= 59.4 bar** — missed by 0.02,
  **but the P2 control measured 59.16 on the same build without the fix.**
  Video was not degraded; the client-side deficit fell from 0.38 to 0.27
  fps. The bar was above what this link delivered in either arm.

**Not reverted**, because the fix is not wrong: it removes ~201 underruns
per session, leaves `first_write_elapsed_ms` where it was, and neither
failing check is evidence against the mechanism. The starvation question is
carried forward as the open item.

**Untested:** the 3,000 ms bound never fired, so the absent-audio path is
unexercised; and there was no perceptual check — the fix removes silence
that was already silent.
