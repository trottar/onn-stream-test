---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: f9a8260
---

# CL-B5 — the Opus decode on its own thread; sig_v 3's overlay capture; the CONFIRMED APK hash

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-10-18; `handoffs/CL-B5_OPUS_DECODE_THREAD_AND_AB_TASK.md`;
record `evidence/CL_B5_OPUS_DECODE_THREAD_AB_2026-10-18.md`).

- **Client (debug APK):** the Opus decode moves off the audio receive thread (new `streaming/OpusDecodePipeline.kt`:
  a bounded queue of 64 items and one decode thread; the receive thread offers in release order and never waits).
  - `OpusAudioDecoder` implements the pipeline's `FrameDecoder`. `NativeAudioReceiver`'s Opus path is wired to it;
    the PCM path is unchanged.
  - The session report's `opus` object gains the decode queue's depth max, wait max, drops and failures.
  - Diff: `evidence/cl_b5_2026-10-18/client.diff`.
- **Host, one line (B's file, disclosed):** `companion/audio_codec.py` `note_setup` records the overlay host for
  `sig_v` in (2, 3). It is effective whenever the flag is on, after a restart. Test `test_overlay_host_with_sig_v3`.
  Diff: `host.diff`.
- **The APK:** **`043891e1cc7d643dc496eb6f6dcef50472418e9444300f667ac6abb7d0201607`** (`adb install -r` at 23:26Z,
  `Success`; read back; the pairing survived). It replaces CL-B4's `8e10497e…d84e`, kept at
  `PrivyHub/app/build/cl_b5_preserved/app-debug.apk` (gitignored).
- **The pinned hash** (`cl_b5_hash.diff`, `predecessors/`):

  | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- |
  | `tools/e1_suite.py` | `e023c601f5ea170b` | `6d0fd284aabe0bf6` | `EXPECT_APK` (+ comment lines) |
  | `tools/c3_l4_nft_night.py` | `71d4c459120bf049` | `c0d102a6ba602153` | `ADOPTED_APK_SHA256` (+ two comment lines) |
  | `tools/test_c3_l4_nft_night.py` | `2a23f9ed6ebc836c` | `2dd049d4b393bc5c` | `AdoptedApk` expects the new hash |

- **Validation:**
  - APK unit tests 67 / 67 and an offline `assembleDebug`;
  - host suites: overlay 17, session_identity 88, audio_codec 20; nft_night OK;
  - `git diff --check` clean;
  - `--check` ok, CONFIRMED, after the install and at the end;
  - the paired A/B both valid, host gates held.
- **Rollback (written, not applied):**
  - `adb install -r PrivyHub/app/build/cl_b5_preserved/app-debug.apk` (`8e10497e…`);
  - copy the predecessors back from `evidence/cl_b5_2026-10-18/predecessors/` (the three tools files;
    `audio_codec.py` and its test for the host line).
