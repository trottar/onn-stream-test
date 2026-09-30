---
memory_schema: 1
as_of: 2026-09-30
status: DECISION 2026-09-30 — the CL-B1 client APK ADOPTED by its pre-registered rule (authorized by the user 2026-09-30, "we can queue it now"). New adopted APK de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e; previous f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7
---

# CL-B1 — the next adopted APK

**The user's authorization**, 2026-09-30: **"we can queue it now"**
(`../handoffs/CL-B1_APK_ADOPTION_TASK.md`). It follows the user's
2026-09-28 call to bundle `CL-B1` into the next adopted APK.

**The rule** is
`../evidence/cl_b1_apk_2026-09-30/cl_b1_apk_preregistration.txt`, sha256
`6e77aa13…`, written before the build. It was ADOPTED because every row
held.

| row | result |
| --- | --- |
| A1 build | HOLDS. A clean `:app:assembleDebug` gives the same hash as the incremental build. Kotlin 11/11 (DecoderReportUploadTest 4/4, FecRs82Test 6/6, ExampleUnitTest 1/1). The client source is unchanged since `f01c3b2`. Against the old APK's source (`824c9d9`), only CL-B1's and C4-M1's seven client files differ. |
| A2 install | HOLDS. The device hash equals the build's on the first read; the app opens and wakes, and resumes in every session. |
| A3 report path | HOLDS. A 213 s session: the journal shows "received as body" (31,155 chars), the report is stored, 0 WARNING, 0 traceback, `slow_event_capacity` 1,280, the key set identical (195 keys). |
| A4 20-min hold | HOLDS. Spikes 27.9/min, fps 59.92, stale 0.69/min, underruns 0.40/min. The FEC counters are inside the adopted APK's reference range. |
| A5 paired link rows | Do not gate. Loss 10.29/min (new) against 11.81 (adopted, paired), inside the 29.52 spread. Max gap 246 against 205 ms, reported. |
| A6 end | HOLDS. The onn carries the new APK, hash confirmed. Profile adopted, `any_override` false, adaptive off, `PRIVYHUB_FEC_SCHEME` absent, no game, 0 banners; the build output is the installed APK. |

**The hashes, in full.**

- **New adopted APK:**
  `de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e`,
  kept at `runtime/cl_b1_apk/cl_b1_app-debug.apk` (and the build output
  `PrivyHub/app/build/outputs/apk/debug/app-debug.apk`).
- **Previous adopted APK:**
  `f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7`,
  kept at `runtime/c4_m1/adopted_app-debug.apk`.

**What the APK carries** beyond the previous one. Its source is `f01c3b2`
against the previous `824c9d9`, seven client files:

- **`CL-B1`:**
  - the decoder report as a POST body (`DecoderReportUpload.kt`,
    `NativeStreamActivity.kt`'s `httpPostBody`);
  - the slow-event rings grown to 256 marked + 1,024 recent
    (`AvcLowLatencyDecoder.kt`), with `slow_event_capacity` their sum;
  - the test (`DecoderReportUploadTest.kt`).
- **`C4-M1`:** the RS(8+2) v2 FEC decoder (`FecRs82.kt`,
  `RtpH264Receiver.kt`'s v2 path, `FecRs82Test.kt`). It is **inert
  while `PRIVYHUB_FEC_SCHEME` is unset** (it stays unset): a v1 stream
  takes the old branch every time.
- **Nothing else.**

**Rollback.** Reinstall the previous APK and confirm its hash:

- `adb install -r runtime/c4_m1/adopted_app-debug.apk`;
- then `adb shell sha256sum $(adb shell pm path com.safeiot.privyhub | sed 's/package://')`
  must read `f31b1c18…`;
- then set `tools/c3_l4_nft_night.py`'s `ADOPTED_APK_SHA256` back.

The companion needs nothing: it accepts both report forms, and it was not
changed by this task.

Record: `../evidence/CL_B1_APK_ADOPTION_2026-09-30.md`.
