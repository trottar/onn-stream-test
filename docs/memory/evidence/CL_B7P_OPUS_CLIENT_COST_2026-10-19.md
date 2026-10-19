---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: 7a1ab60 (G4-S3 committed; the tree carried the two user prompts and A's G8-S5 files, not touched)
---

# CL-B7P — the Opus path's cost on the client, located from code, and one candidate built (not installed)

**Classification: software only. §1 a hypothesis from the code, with its on-onn test written (not run). §2 one
change behind a runtime client flag, `debug.privyhub.opus_decode=lean`, absent = today. APK built offline and pinned,
`93d29b4a…1624`, NOT INSTALLED. Not benchable off-device. Nothing adopted; nothing committed.**

Task: `handoffs/CL-B7P_OPUS_CLIENT_COST_TASK.md`, session B, in parallel with A's G8-S5. Design
`cl_b7p_2026-10-19/design_written_before_code.md`, sha256 `5871d67d…8815`, hashed **14:43:55Z, before any code edit**.

## 1. The location, from code (`cl_b7p_2026-10-19/s1_thread_map_count_hypothesis.md`)

- **The thread map:**
  - In a stream the client runs RTP-H264-FEC, MediaCodec (video), Native-Audio-RX, Native-Audio-Opus (Opus only),
    Native-Audio-Playback, Native-Controller, and 2-s and one-shot HTTP threads.
  - **The client sets no thread priority anywhere** (0 hits); all its threads are equal at the default.
  - Each MediaCodec also brings framework looper threads into the process, and work-done callbacks arrive on the
    process's binder pool, which both codecs share.
  - Recalled, not read: `c2.android.opus.decoder` runs in `media.swcodec`, outside PrivyHub.
- **The per-second count with Opus:**
  - 200 datagrams/s; 100 hand-offs to the decode thread.
  - **500 synchronous MediaCodec calls/s** (5 per frame). One of the five is a trailing `dequeueOutputBuffer(0)`
    that almost always returns nothing.
  - ~200 Codec2 binder transactions/s; ~384 KB/s copied in Java.
  - **PCM** does 400 datagrams/s and no codec work, with 192 KB/s copied.
  - **Net, Opus against PCM:** −200 socket reads/s; +100 hand-offs, +500 codec calls and +~200 binder
    transactions/s.
- **The hypothesis:** the ~0.2 core is **the MediaCodec client-side per-buffer machinery**: the looper's
  post-and-wait at 500 calls/s, plus the binder traffic. It is not our decode thread's Java code (no tight loop;
  ~3.2 ms per frame is spent blocked), not the copy (too small) and not the decode itself (out of process).
  - **The count does not by itself reach 0.2 core.** At plausible per-call costs it gives ~0.03-0.05 core. Either
    the onn's per-call cost is several times higher, or CL-B6's single samples overstate the gap, or the owner is
    elsewhere. CL-B7 decides which.
- **The test on the onn: `tools/cl_b7_onn_threads.py`** (adb state reads only; written, parsed, **not run**):
  - `top -H` of PrivyHub over 10 one-second iterations: per thread name, PR, NI, and mean / max %CPU;
  - the same seconds by process: PrivyHub, `media.swcodec`, the codec HALs, audioserver, surfaceflinger;
  - the onn's busy %, and `getprop debug.privyhub.opus_decode`;
  - no PID or TID is written, and digit runs in names are masked.
  - The four readings and what each means are in §3 of the §1 file.
- **Why the spikes would follow (hypothesis):**
  - The spike is measured when the nice-0 video drain thread dequeues an output; it polls every ≤ 2 ms.
  - Opus adds a chain of ~6-8 thread wake-ups every 10 ms (RX → decode → looper → binder → swcodec → binder →
    looper → PCM queue). The video threads compete with that chain as equals, and lose to framework threads at
    raised priority (recalled; CL-B7 reads NI). The two codecs also share the binder pool.
  - So more audio wake-ups make more video outputs late by ≥ 20 ms.

## 2. The one change (`cl_b7p_2026-10-19/client.diff`, `diffstat.txt`)

- **The flag:** Android system property `debug.privyhub.opus_decode`. With `lean` the change runs; absent, empty or
  any other value runs today's drain.
  - It is read once, by reflection, when the decode thread makes its first Opus decoder. A PCM session never reads
    it, and a failed read means today.
  - It does not survive a reboot.
- **The change, `lean`:** `OpusAudioDecoder.drain` returns once the outputs have caught up with the inputs. It drops
  the trailing `dequeueOutputBuffer(0)`: 5 → 4 synchronous calls per frame, 500 → 400 per second.
  - Output order and count are unchanged. A second ready output is taken one call later, the lag today's empty
    poll already has.
- **Absent = today:** `TODAY.pollAfterOutput` is always true, so the call sequence is today's.
  - The report's `opus` object gains `"decode_mode": "lean"` **only in lean mode**. With the flag absent the report
    has no new key.
  - The PCM path has no hunk: the version-1 receive path, `enqueuePacket` and the playback loop are untouched.
    `NativeAudioReceiver` has 3 hunks: the data class field, the Opus factory and the snapshot field.
- **Files:**
  - new `streaming/OpusDecodeMode.kt` (39 lines);
  - `OpusAudioDecoder.kt` (+6 / −1: a constructor param, defaulting to TODAY, and one line in the drain);
  - `NativeAudioReceiver.kt` (+7 / −3);
  - `NativeStreamActivity.kt` (+4);
  - new test `OpusDecodeModeTest.kt` (5 tests).
- **Not chosen:**
  - **two frames per buffer:** the host's encoder is hard CBR, CELT only, and may pad with code-3 packets, so it
    needs a client repacketizer and adds 10 ms;
  - **libopus via JNI: there is no NDK on the host** (`sdk_listing.txt`: no `ndk/`, no `cmake/`);
  - **priority:** no client thread sits above the video path, and a priority moves who runs, not how much.

## 3. Tests, build, the APK (`tests_apk.txt`, `build_console.txt`, `apk_sha256.txt`)

- **Session A's unit:** it was active at 14:46Z (started 14:42Z), and **the build waited**. A background poll every
  60 s read it inactive at 15:15:31Z (31 polls). It read inactive again just before the build (15:15Z) and before the
  baseline build.
- **Command:** `sh ./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug`, run in `/tmp/b_cl_b7p`,
  a copy of `PrivyHub/` only, with its source hashes checked equal to the tree's. Result: **BUILD SUCCESSFUL in 39 s.**
- **Unit tests: 72 / 72** (67 existing + 5 new, 0 failures).
  - The existing tests are unchanged: `git diff` on `src/test` is empty, apart from the new file.
  - OpusDecodePipeline 5, OpusFraming 12, FecRs82 6, DecoderReportUpload 4 and the identity suites are all green.
- **Warnings:** one compiler warning, pre-existing (`onBackPressed` deprecated). None in the changed lines.
- **The APK, pinned beside the CONFIRMED one:**

  | APK | sha256 | bytes | state |
  | --- | --- | ---: | --- |
  | **CL-B7P candidate** | **`93d29b4a38d224fddbcf261dab72b40f1290f009b7dc506d60eb3104071e1624`** | 9,600,146 | built offline, **NOT installed** |
  | CONFIRMED (CL-B5) | `043891e1cc7d643dc496eb6f6dcef50472418e9444300f667ac6abb7d0201607` | 9,810,323 | on the onn; the tree's build output untouched |
  | scratch baseline (predecessors, no change) | `6a4b74a0d35bb8903ebc01914ee70ee36b204e45320755d9afe4649edf90f4c2` | 9,598,274 | `/tmp/b_cl_b7p_base`, for size only |

  - The build is not reproducible across build directories: the unchanged predecessors, built the same way, give
    `6a4b74a0…`, not `043891e1…`. **The candidate against that baseline is +1,872 B.** The 210-KB gap to the
    CONFIRMED APK comes from the build environment, not the change.
  - **Signer:** the candidate has the CONFIRMED APK's certificate (apksigner; digests compared, not printed), so
    `adb install -r` keeps the data and the pairing.
- **The bench:** **not benchable off-device.** The change lives inside `OpusAudioDecoder.drain`, which runs only
  against a real MediaCodec. The JVM has android.jar stubs, and the project rule forbids mock frameworks. A host
  timing of the pipeline's queue and copy would be the same in both modes, because the mode does not touch them.
  **No claim about the onn's CPU from the host.** Left to CL-B7.

## 4. For CL-B7 (session A, later; sketched, not pre-registered)

1. Power-cycle the onn and preserve the CONFIRMED APK. Install `93d29b4a…` (`adb install -r`), read it back and
   check the pairing.
2. Three arms on one evening, same title, ~10-min windows:
   - **PCM**;
   - **Opus today** (property absent);
   - **Opus lean** (`adb shell setprop debug.privyhub.opus_decode lean` before the start; the report must show
     `"decode_mode": "lean"`).
3. Mid-window in each arm, run `tools/cl_b7_onn_threads.py <arm>`, plus CL-B6's `cl_b6_onn_read.py`.
4. Readings:
   - the per-thread delta, Opus-today minus PCM, by category;
   - lean minus today on the framework-codec and binder threads (predicted ~−1/5 of their Opus share, if the
     hypothesis holds);
   - spikes per minute (if they follow the call count, lean sits between the other two arms);
   - underruns.
5. Arm 2 is the predecessor behaviour by construction (flag absent), so if lean shows nothing, the CONFIRMED APK
   can stay.

## 5. Files

**`cl_b7p_2026-10-19/`:**
- `baseline_head.txt`, `git_status_at_start.txt`;
- `predecessors/` with `predecessor_sha256.txt` and `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `s1_thread_map_count_hypothesis.md`;
- `client.diff`, `diffstat.txt`;
- `build_started_at.txt`, `build_console.txt`, `tests_apk.txt`, `apk_sha256.txt`, `sdk_listing.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.
  - `redact_check.py` is CL-B6's check without adb and without reading the device store. Result: **0 FAIL over 28
    files.** The first run flagged 10 files on the host name. The host name equals the project's own name, so it is
    in every class and path; the check now skips it in that case and says so. Its own docstring's sample endpoint
    was reworded.

**Elsewhere:**
- `PrivyHub/app/src/main/java/streaming/OpusDecodeMode.kt` (new); `OpusAudioDecoder.kt`, `NativeAudioReceiver.kt`,
  `NativeStreamActivity.kt` (modified); `PrivyHub/app/src/test/java/streaming/OpusDecodeModeTest.kt` (new);
- `tools/cl_b7_onn_threads.py`;
- `patches/CL-B7P_OPUS_DRAIN_LEAN_FLAG.md`;
- `docs/KNOWN_ISSUES.md` (the spikes item);
- `logs/cl_b7p_git_status.txt`;
- `handoffs/SESSION_B_STATUS.txt`, `handoffs/SESSION_B_DONE_2026-10-19.md`.

**Left in `/tmp` (not the tree):** `/tmp/b_cl_b7p` (the build copy and the candidate APK) and `/tmp/b_cl_b7p_base`
(the baseline copy). In that scratch copy B removed its own two new files before building the baseline. Nothing
else was deleted.

No sudo, no nft, the Opal untouched, **no adb at all**, nothing fetched (`--offline`), nothing installed, nothing
adopted, nothing committed. Not touched: `companion/` (read only, to check the encoder's CBR), `tools/e1_suite.py`,
`e1_remote.py`, `e3_state.py`, the drop-ins, the companion service, the audit log, the onn, the tree's
`PrivyHub/app/build/`. In `logs/`, only `cl_b7p_git_status.txt` was written (by B, as the task asks); nothing was
written there by tests.
