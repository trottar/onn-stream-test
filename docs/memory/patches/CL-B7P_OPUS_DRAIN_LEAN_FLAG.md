---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: 7a1ab60
---

# CL-B7P — the Opus drain's `lean` mode behind `debug.privyhub.opus_decode` (client; APK built, NOT installed)

**Result: BUILT, NOT INSTALLED.** Applied in the working tree by session B, 2026-10-19
(`handoffs/CL-B7P_OPUS_CLIENT_COST_TASK.md`). Record: `evidence/CL_B7P_OPUS_CLIENT_COST_2026-10-19.md`. Nothing is
committed or adopted. The install and the A/B are CL-B7, session A.

- **The flag:** system property `debug.privyhub.opus_decode`. `lean` turns the change on. Absent, empty or any other
  value means today, byte for byte in the call sequence and the report.
- **The change:** `OpusAudioDecoder.drain` returns after an output once nothing is pending. That drops a trailing
  `dequeueOutputBuffer(0)`: 4 synchronous MediaCodec calls per frame instead of 5. In lean mode only, the report's
  `opus` object gains `decode_mode`.
- **The files** (`evidence/cl_b7p_2026-10-19/client.diff`; `predecessors/`):

  | file | predecessor sha256 (16) | after (16) |
  | --- | --- | --- |
  | `streaming/OpusAudioDecoder.kt` | `7abe2ee3acf8e57d` | `6d6c7521b7e30f0a` |
  | `streaming/NativeAudioReceiver.kt` | `4baa3aedd940c2d5` | `0ef32e912b1d7821` |
  | `streaming/NativeStreamActivity.kt` | `c0b0432d03dbd808` | `f95ff188ead009b1` |
  | `streaming/OpusDecodeMode.kt` | (new) | `0713908272948ef0` |
  | `src/test/java/streaming/OpusDecodeModeTest.kt` | (new) | `9394a0c0d5d04214` |

- **Validation:**
  - `./gradlew --offline :app:testDebugUnitTest --rerun :app:assembleDebug` in a `/tmp` copy: **72 / 72**;
  - the existing tests unchanged;
  - `git diff --check` clean.
- **The APK:** `93d29b4a38d224fddbcf261dab72b40f1290f009b7dc506d60eb3104071e1624` (9,600,146 B), with the same signer
  as the CONFIRMED `043891e1…1607`. **Not pinned** in `tools/` (`EXPECT_APK` / `ADOPTED_APK_SHA256` are unchanged).
  That pin belongs to CL-B7, if it is adopted.
- **Rollback (written, not applied):** copy the three predecessors back from `evidence/cl_b7p_2026-10-19/predecessors/`
  and remove the two new files. The onn needs nothing: the candidate was never installed.
