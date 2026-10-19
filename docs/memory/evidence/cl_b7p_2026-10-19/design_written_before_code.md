# CL-B7P design — written before any code edit, hashed (session B, 2026-10-19)

## The one change: the Opus decoder's drain, `lean` mode, behind a runtime client flag

**The flag.** Android system property `debug.privyhub.opus_decode` (the `debug.` prefix is what `adb shell setprop`
may set; the handoff's `privyhub.opus_decode=<mode>`). Value `lean` = the change. **Absent, empty or any other value
= today.** It is not persistent: a reboot clears it, so CL-B7's onn power-cycle returns the client to today.

- Read once, lazily, when the decode thread makes its first `OpusAudioDecoder` (the pipeline's factory). A PCM
  session never makes a decoder, so it never reads the property: the PCM path is not touched.
- Read through `android.os.SystemProperties.get(String)` by reflection. Any failure (hidden-API refusal, absent
  class) resolves to today.
- **Seen in the session report only when not today:** the `opus` object gains `"decode_mode": "lean"`. With the flag
  absent the report is byte for byte today's (no new key). CL-B7 reads the key to prove which arm ran.

**The change.** Today `OpusAudioDecoder.drain` after each output buffer loops once more: with nothing pending it
calls `dequeueOutputBuffer(info, 0)`, which returns `INFO_TRY_AGAIN_LATER` almost always (the next frame's output is
~3 ms away). That is one synchronous MediaCodec call per frame, 100 per second, that yields nothing. In `lean`
mode the drain returns as soon as the outputs have caught up with the inputs (`inputs - outputs <= 0`) after an
output. Everything else is unchanged: the input wait (10 ms), the 4-ms output wait while a frame is pending, the
format-change handling, the drain-timeout accounting, the copy and the split.

- Per frame: today 5 synchronous calls (`dequeueInputBuffer`, `queueInputBuffer`, `dequeueOutputBuffer` with the
  wait, `releaseOutputBuffer`, `dequeueOutputBuffer(0)`); `lean` 4. Per second at 10-ms frames: 500 → 400.
- **Output order and count are unchanged.** If two outputs are ever ready at once (after a drain timeout), today's
  extra poll would take the second at once; `lean` takes it on the next call, one frame (10 ms) later, and the
  same one-frame lag already occurs today whenever the trailing poll comes back empty (the usual case). Nothing is
  dropped.

**The code (four files + one test):**
1. New `streaming/OpusDecodeMode.kt` (pure Kotlin): `enum class OpusDecodeMode { TODAY, LEAN }`;
   `parse(value: String?)` (`"lean"`, trimmed, case-insensitive → LEAN; anything else → TODAY); `fromSystem()`
   (the reflection read, failure → TODAY); `reportName` (`""` for TODAY, `"lean"`);
   `pollAfterOutput(pending: Long)`: TODAY → true (today's loop), LEAN → `pending > 0`.
2. `OpusAudioDecoder(frameSamples, mode = OpusDecodeMode.TODAY)`: one line after `outputs += 1`:
   `if (!mode.pollAfterOutput(inputs - outputs)) return`. With TODAY it is always true: today's call sequence.
3. `NativeAudioReceiver`: the factory passes `OpusDecodeMode.fromSystem()`; the snapshot gains
   `opusDecodeMode: String = ""` from the live decoder's `mode.reportName`. No hunk in the version-1 receive path,
   `enqueuePacket` or the playback loop.
4. `NativeStreamActivity`: `if (audio.opusDecodeMode.isNotEmpty()) put("decode_mode", audio.opusDecodeMode)` inside
   the existing `opus` object.
5. New test `OpusDecodeModeTest`: the parse table (absent, empty, `lean`, ` LEAN `, `today`, junk); TODAY polls
   after every output whatever is pending; LEAN polls only while pending > 0; `reportName`.

**Not done, and why (§1 reading):**
- Two 10-ms frames per MediaCodec buffer: the host's encoder is hard CBR, CELT only; a CBR packet may carry code-3
  padding, so merging two packets needs an RFC 6716 repacketizer on the client, and it adds 10 ms. Not the cheapest.
- libopus through JNI: **no NDK on the host** (`~/Android/Sdk` has build-tools, cmdline-tools, licenses, platforms,
  platform-tools; no `ndk/`, no `cmake/`). Out.
- The decode thread's priority: the client sets no thread priority anywhere (0 hits for `setThreadPriority`,
  `THREAD_PRIORITY`, `priority =`); the decode thread is not above the video path's, so the handoff's condition for
  that option is not met, and a priority moves who runs, not how much.

**The bench:** the change is inside `OpusAudioDecoder.drain`, which only runs against a real MediaCodec. The JVM unit
tests have no MediaCodec (android.jar stubs), and the project rule forbids mock frameworks. **Not benchable
off-device; left to CL-B7.** No claim about the onn's CPU from the host.

**Gates:** the existing unit tests unchanged (`git diff` empty on `src/test` but the new file) and green; the new
test green; `./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug` in a `/tmp/b_` copy holding the
Android project only; the APK's sha256 pinned beside `043891e1…`; **not installed**.
