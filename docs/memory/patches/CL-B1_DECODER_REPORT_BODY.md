---
memory_schema: 1
as_of: 2026-09-25
baseline_commit: 05aac43
durable_memory_updated: true
---

# CL-B1: the decoder report as a POST body (companion backward-compatible)

## Purpose

This lifts the request-line ceiling (~41K decoded characters) on the
end-of-session decoder report. Task:
`handoffs/PHASE_C_PRECONDITIONS_2026-09-25_TASK.md` §3. Record:
`evidence/CL_B1_DECODER_REPORT_BODY_2026-09-25.md`. **Nothing adopted.**

## Change

**Companion:**

- `games/decoder_report_http.py` is new: pure helpers for the body length,
  the report from a body, and the access log's path guard.
- `games/decoder_session_log.py`: `MAX_REPORT_CHARS` goes 48,000 →
  128,000.
- `plugins/games.py`: `handle_decoder_session_log` (the body form). The
  target form is unchanged.
- `privyhub_service.py`:
  - the body branch for `decoder-session-log`, with the WARNING line
    kept and a "received as body" line added;
  - `log_message` goes through `access_log_path`, so the 414 path no
    longer crashes.

**Client:**

- `DecoderReportUpload.kt` is new.
- `NativeStreamActivity.kt`: `httpPostBody`; the report is sent as the
  body; `slow_event_capacity` is now the sum of the segments.
- `AvcLowLatencyDecoder.kt`: MARKED 256, RECENT 1,024.

**Tests (new):** `tools/test_cl_b1_decoder_report_body.py` (4) and
`DecoderReportUploadTest.kt` (4).

**APKs:**

- arm: `71d8c3d7e9cf287fc79ec16cfe8e514842d005278e3c7f25a90b3ac1393bcd4c`
  (a first build, `0220a294…2dd4`, was superseded);
- adopted: `f31b1c18…8ae7`, installed at the end, hash confirmed.

## Files (SHA-256 after)

```
d45711d8337d211edfa7c63502281eb30c05e5f360715eec7771e48cfaecfc52  companion/games/decoder_report_http.py
5da008c79e44741ce4f43016b80ee7a678a6143a932770ff6be3b423fc265d6d  companion/games/decoder_session_log.py
3eda8c9211e641a619cd54f3ac65e93ff79384e26ee7a61e436ccae09f3a90d6  companion/privyhub_service.py
72ffe692d24f3c392ef82c6ea23d5a014f2e774b65026e6546be2efdcd90c86b  companion/plugins/games.py
e76c234b9adbbe569eb5f90d56d410d2b0b7d10742446b09ccd1a0716ca3c409  PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt
6cf4e189642c4989c80dc8e23c90ba271cda57e38b06838954bdd57d522b2905  PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt
6aa853d813174e49a1b0006b37991620d8faf860f95d028e098571bd36a266a4  PrivyHub/app/src/main/java/streaming/DecoderReportUpload.kt
9d008133e574b91b51800ed1513dbd8cf0ddba297f78b46dda2d6d1675c6fca4  PrivyHub/app/src/test/java/streaming/DecoderReportUploadTest.kt
6f8fff5e4294d2cc9df8961a2040dbba10563254836093ac240fb1dce3d1b44d  tools/test_cl_b1_decoder_report_body.py
```

Before: `evidence/cl_b1_2026-09-25/pre_patch_sha256.txt`. The diff is
`cl_b1_patch.diff`.

## Rollback

1. Delete the new files.
2. Revert the hunks (`cl_b1_patch.diff`).
3. Restart the companion through its unit.

The adopted APK needs nothing: it uses the target form throughout.
