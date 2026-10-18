---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: f314126
---

# CL-B4 — the Opus-decode APK, sig_v 3, and the CONFIRMED APK hash

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-10-18, as CL-B2 / CL-B3 did;
`handoffs/CL-B4_APK_OPUS_DECODE_TASK.md`; record `evidence/CL_B4_APK_OPUS_DECODE_2026-10-18.md`).

- **The client (debug APK)** declares and decodes Opus. It signs `sig_v` 3 with `audio_codecs: ["opus"]` (one v2
  fallback for a host without v3), accepts PHA1 v2, and decodes with MediaCodec `audio/opus` in sequence order. It
  conceals a lost frame with today's slots, splits each frame into 5-ms queue packets, counts loss in Opus frames, and
  reports `codec` / `opus` in the session report and `audio_codec` in the heartbeat.
  - Edited: `identity/SessionProtocol.kt`, `identity/IdentitySession.kt`, `streaming/NativeAudioReceiver.kt`,
    `streaming/NativeStreamActivity.kt`.
  - New: `streaming/OpusFraming.kt`, `streaming/OpusAudioDecoder.kt`.
  - Diff: `evidence/cl_b4_2026-10-18/client.diff`.
- **The host:** `companion/session_identity.py` gets `sig_v` 3. It signs v2's fields plus `audio_codecs` (required
  under v3), and `token_issued` records them. v1 / v2 are byte for byte as HEAD's (`v2_compare.json`). Diff:
  `host_sig_v3.diff`. Effective from the companion's next restart: it is live since 22:00Z, through CL-B4's run and
  its teardown restart.
- **The APK:** **`8e10497ef43850d54165593a680f68a41b89114536a806f0788b9a04945fd84e`** (`adb install -r` at
  21:59Z, `Success`; the device read back the same hash; the pairing survived). It replaces CL-B3's `59f736d2…f65f`,
  kept at `PrivyHub/app/build/cl_b4_preserved/app-debug.apk` (gitignored; sha256 re-read).
- **The state tools' pinned hash, three edits** (`cl_b4_hash.diff`, `predecessors/`):

  | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- |
  | `tools/e1_suite.py` | `3dcc355d740a9f4a` | `e023c601f5ea170b` | `EXPECT_APK` (+ comment lines) |
  | `tools/c3_l4_nft_night.py` | `4ef6005b8c9a08a9` | `71d4c459120bf049` | `ADOPTED_APK_SHA256` (+ two comment lines) |
  | `tools/test_c3_l4_nft_night.py` | `f69e1f5280012800` | `2a23f9ed6ebc836c` | `AdoptedApk` expects the new hash |

- **Validation:**
  - APK unit tests 62 / 62 and an offline `assembleDebug`;
  - host suites: overlay 17, session_identity 88, audio_codec 19, nft_night 33;
  - `git diff --check` clean;
  - `--check` ok, CONFIRMED, before and after the run;
  - the LAN smoke valid, every host gate held.
- **Rollback (written, not applied):**
  - `adb install -r PrivyHub/app/build/cl_b4_preserved/app-debug.apk` (`59f736d2…`);
  - copy the three predecessors back from `evidence/cl_b4_2026-10-18/predecessors/`;
  - for the host: `predecessors/session_identity.py` over `companion/session_identity.py`, then restart the
    companion. A v3 client then falls back to v2 by itself.
