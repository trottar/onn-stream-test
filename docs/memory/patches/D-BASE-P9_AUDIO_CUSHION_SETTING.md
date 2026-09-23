---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 3e6cde5
durable_memory_updated: true
---

# D-BASE-P9 — the audio cushion as a declared profile setting

## Purpose

The user decided on 2026-09-23 to spend `P7`'s +45 ms of audio latency on
a deeper client cushion (`P7`/`P8`: the audio holes are the path's, p90
≈ 60 ms). This makes the client's audio queue **target** and **capacity**
a declared field pair of the stream profile, passed to the client at
stream start, with the old 3 / 8 kept as the client default and reachable
per session from the environment. Built and installed directly under the
task authorization (`handoffs/D-BASE-P9_TASK.md`), not as a ZIP.

**What the code says each number does (read before the change):** the
target is **only the startup prefill** (the playback loop waits for
`queue.size >= target`, 100 ms bound, once). The running depth sits near
the **capacity**: every arrival hole is concealed on the track's timeline,
and the late burst that follows refills the queue until the capacity trims
it (`P8` arm A: residence 30.9 ms against a 40 ms ceiling;
`smooth_latency_trims` 4,622 = `concealed_underruns` 4,637). **So the
capacity sets the steady latency**, and the handoff's 12 / 24 would have
cost ≈ +80 ms, not +45. The user chose to run both: **12 / 17** (+9
packets = +45 ms) as the profile default and **12 / 24** as a comparison.

## Changed scope

**`companion/native_stream_profiles.py`**
-> `11287c52c571d590aa697788599d632a89259e5b1924d5777af9e6555aecc06f`
after the revert (12 / 17 build `e981585f0ea0a56a42dcf499c32604471ee360ba8ace619d086539dfaa5e003d`)
(was `cd8b95cd9ded9a7b1a257ccaef372b7cf7a54a150775018c5510a68e8de8ddc5`).

- `NativeStreamProfile.audio_queue_target_packets` (default 3) and
  `audio_queue_capacity_packets` (default 8), validated
  `1 <= target <= capacity <= 32`, in `to_dict()` beside
  `max_frame_size_bytes`. `AUDIO_QUEUE_MAX_PACKETS = 32`,
  `AUDIO_PACKET_MS = 5`.
- `native_game_720p60_reference`: **12 / 17** for the run, **reverted to
  3 / 8** after it by the pre-registered rule (see Status).

**`companion/native_stream.py`**
-> `417af4c87b5308f17a7a416db8b356f279b7d80c5ad4658ad21665ba9d8496a5`
(was `84e08aac9c2514a01aba5ad61e63829385cf41b27333590efd61a10f43eda28f`).

- `PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS` / `..._CAPACITY_PACKETS`: a
  per-session override, read at each stream start; **both** must be set
  and valid or both are ignored (`env_ignored: true`).
- `audio_cushion()` → `native-stream-status.audio_cushion`
  {queue_target_packets, queue_capacity_packets, packet_ms, target_ms,
  capacity_ms, source `profile`|`environment`, env_ignored, defaults}.
  The stream-start response is `status()`, so the client gets it there.
  **Kept out of `encoder_overrides`: `any_override` stays about the
  encoder.**

**`PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`**
-> `1e2ef717679294d9ee2511439064cda873810f5931dee235dce1a9ee7a0a82e9`
(was `3537b26102c33180f0c63a25388e3a4fbd0f1a6a08bb47bca6b1c98c261edf81`).

- `QUEUE_PACKETS` / `TARGET_QUEUE_PACKETS` → `DEFAULT_QUEUE_PACKETS` (8)
  / `DEFAULT_TARGET_QUEUE_PACKETS` (3), used when the response carries no
  `audio_cushion`. The queue is allocated once at `MAX_QUEUE_PACKETS` = 32;
  the capacity in force (`@Volatile`) is enforced in `enqueuePacket`
  (`queue.size >= capacity || !offer` → the same trim path). One producer,
  so at 8 this is exactly the old offer-fails test.
- `configureCushion(target, capacity)`: values ≤ 0 ignored; capacity
  clamped 1-32, target 1-capacity; records `cushionSource` "host" and
  whether it landed before the first real PCM packet was queued.
- The prefill loop reads the target in force. **Nothing else changed**:
  the `P2a` startup hold, concealment, trims/crossfade, the starvation
  counter, `P8`'s ring.

**`PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`**
-> `cc8c3faa50a716c2aa4711b08e52f9531f039cf38f8012f210893657d70c6efc`
(was `b640e2bedc6c1c5e36acfcd111cad31a94ebcc4c70433a5df135b683ed9dfe60`).

- After `heartbeat_interval_ms`, reads the response's `audio_cushion`
  and calls `configureCushion`.
- Report: `audio.queue_cushion_source`,
  `audio.cushion_applied_before_first_pcm` beside the existing
  `queue_target_packets` / `queue_capacity_packets` (which now report the
  values in force). Additive; schema stays `_v2`.

## Validation performed

- `py_compile` of both companion files; `git diff --check` clean.
- `sh ./gradlew :app:assembleDebug --no-daemon` — BUILD SUCCESSFUL, first
  attempt. APK
  `a9355bb0030b617a292aaa2909982214d9bccb1a3e92e00da3b15b6e1bb44a72`;
  installed, the device's package hash equal.
- Companion restarted with `systemctl --user restart privyhub-companion`;
  8765 owned by the unit's MainPID; `audio_cushion` 12 / 17 `profile`;
  `any_override: false`.
- 60 s smoke on the profile: report `queue_target_packets` 12,
  `queue_capacity_packets` 17, `queue_cushion_source` "host",
  `max_queue_depth` 17, avg residence 60.7 ms. **`cushion_applied_before_first_pcm`
  false** — see below.
- The three 20-minute sessions:
  `evidence/D_BASE_P9_AUDIO_CUSHION_2026-09-23.md`.

## Known limitation — the target does not reach the startup prefill

The client's audio receiver is started before it posts
`native-stream-start`, and the companion starts the audio sender at the
end of that same request, so **the first real PCM is queued before the
response is parsed** (`startup_wait_ms` ≈ 2.1 s). The prefill therefore
still runs at the client default 3 and the host's capacity takes over
immediately after. Consequence: the target field is inert on this path,
the `P2a` hold and `first_write_elapsed_ms` do not move, and the cushion
under test is the running one (the capacity). Reordering the startup to
change that was not done: it would touch `P2a`.

## Status

**INSTALLED; setting in force, default 3 / 8.** The sessions
(`evidence/D_BASE_P9_AUDIO_CUSHION_2026-09-23.md`): 12 / 17 cut
`prolonged_starvation_events`/min 42.4 → 0.8 at +36.0 ms of residence,
but underruns rose 20 → 25, so the pre-registered reading is FALSIFIED
and the profile default went back to 3 / 8 (companion restarted through
systemd, `audio_cushion` 3 / 8 `profile`). The APK needs no change to
re-adopt — the default lives in the companion
(`decisions/D-BASE-P9_AUDIO_CUSHION.md`).
