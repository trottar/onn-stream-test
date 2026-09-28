---
memory_schema: 1
as_of: 2026-09-25
status: CL-B1 DONE — the decoder report can travel as a POST body; companion backward-compatible (target form unchanged) with MAX_REPORT_CHARS 128,000 as the only limit and the 414-path logger crash fixed; client posts the body, slow-event rings 256 marked + 1,024 recent; companion 4/4, Kotlin 4/4 (+6 FEC) tests; arm APK 71d8c3d7…cd4c (a first build 0220a294…2dd4 reported a stale total capacity and was rebuilt); body form stored (29,834 chars, 0 WARNING), target form on the adopted APK stored (0 WARNING), key sets identical to R3's; the adopted APK f31b1c18…8ae7 is installed at the end; nothing adopted
---

# CL-B1 — the decoder report as a POST body

Task: `handoffs/PHASE_C_PRECONDITIONS_2026-09-25_TASK.md` §3 (authorized
by the user 2026-09-25). Patch: `../patches/CL-B1_DECODER_REPORT_BODY.md`.
Evidence: `cl_b1_2026-09-25/` (manifest `sha256_manifest.txt`).
Predecessor: `C3_L3A_R2B_REPORT_CAP_2026-09-24.md`.

## 1. The companion, backward-compatible

**The two forms, one route** (`POST /plugins/games/decoder-session-log`):

- **Body form (new).** With a non-empty `Content-Length`, the report is
  read from the body:
  - JSON as-is (`application/json`), or a form's `report` field
    (`application/x-www-form-urlencoded`);
  - handled by the plugin's new `handle_decoder_session_log`, the **same
    `write_decoder_session_log` call** as before;
  - the journal gets `decoder-session-log received as body:
    report_chars=<n>`.
- **Target form (`?report=`, no body)** falls through to the plugin
  exactly as before. The adopted APK keeps working byte for byte.

**The limit.** `MAX_REPORT_CHARS` went 48,000 → **128,000**, and it is now
the only limit.

- The body bound is 4 bytes per character, so it never refuses a report
  within the cap.
- **Justification:** the largest report seen was 32,435 characters
  (rerun session 3, 24 SSRC changes). The ring growth below adds up to
  1,152 rows × ~23.3 characters ≈ 26.8K when both rings fill. A
  24-transition session with full rings is therefore ~59K, and 128,000 is
  ~2.2× that.

**The WARNING line** is kept on both forms. For a refused body it reads
`WARNING decoder-session-log rejected (400): <reason>; report_chars=<n>`
(or `body_bytes=` when the body was never read), and the connection is
closed.

**The 414-path logger crash is fixed in the companion's own override.**

- `http.server` logs a 414 before it sets `path`. The companion's
  `log_message` read `self.path`, so it raised `AttributeError`, and **no
  414 was ever sent** (R2B).
- It now reads the path through `games.decoder_report_http.access_log_path`,
  which never raises.

**Unit tests** (`tools/test_cl_b1_decoder_report_body.py`, 4/4,
`python_tests.txt`):

- The same report through the target form, a JSON body and a form body
  yields identical text, and the two stored files carry identical
  `report`s.
- The cap is 128,000: 60,000 is accepted and 128,100 refused "too large",
  and the body bound is exact at 4 × 128,000.
- The body branch keeps the WARNING line and the "received as body" line.
- **A 70,000-byte request line** against a throwaway `http.server` using
  the companion's guard gets its **414**, with no `AttributeError`. The
  pre-CL-B1 logger shape on the same server sends no 414, which is the
  defect reproduced.
- The tests import the helpers, not the companion: importing
  `privyhub_service` starts its metadata-reconcile thread and writes logs.

## 2. The client

- **The sender.** At BACK, the stop thread now calls `httpPostBody(…,
  DecoderReportUpload.encode(report), "application/json; charset=utf-8")`
  on `/plugins/games/decoder-session-log`, instead of URL-encoding the
  report into `?report=`. The timeouts and error handling are
  `httpPost`'s.
- **The rings** (`AvcLowLatencyDecoder`): **MARKED 64 → 256, RECENT 64 →
  1,024.** The split and the eviction are unchanged.
  - Marked: a transition's 2 s cycle window logs ~5 events (session 3
    filled 64 in 12 of 24 transitions), so 256 holds 24 transitions twice
    over.
  - Recent: sized from session 3's ~0.63 events/s (see the observation
    in §3).
- **`slow_event_capacity`** is now the sum of the two segments. It was a
  literal 128, which the first arm build reported beside 1,280 rows (§3).
  Its meaning, the total capacity, is unchanged. No other field changed.
- **Kotlin tests** (`DecoderReportUploadTest`, 4/4, beside `FecRs82Test`
  6/6):
  - the body is the report's exact UTF-8;
  - the rings hold the sizing;
  - a full report stays under 128,000;
  - `slow_event_capacity` is the sum.
- **Builds.** The arm APK is
  **`71d8c3d7e9cf287fc79ec16cfe8e514842d005278e3c7f25a90b3ac1393bcd4c`**.
  - A first build, `0220a29421499ae8159cabbd88dcedb481b95f93a09988e5c6be30c31a652dd4`,
    ran one session and reported `slow_event_capacity` 128. It was fixed
    and rebuilt.
  - Both arm APKs also carry `C4-M1`'s v2 FEC decoder from the source
    tree. It is inert without `PRIVYHUB_FEC_SCHEME`, which stayed unset.

## 3. The sessions (`cl_b1_sessions.py`, `cl_b1_rerun.py`; `sessions_first.json`, `sessions.json`)

The companion was restarted through its unit to load the change (MainPID
owned 8765, profile adopted, `xor8_1`, 0 `PRIVYHUB_*`). Each session was
attract mode at 7000, with `any_override` false at PLAYING and BACK after
≥ 190 s.

| session | APK | form in the journal | report chars | stored | WARNING | traceback | key set vs R3's report |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| arm (first build) | `0220a294…` | body (`POST … decoder-session-log HTTP/1.1`, "received as body") | 29,508 | 1 | 0 | 0 | identical (195 keys) |
| adopted | `f31b1c18…` | target (`?report=`) | 24,893 | 1 | 0 | 0 | identical |
| **arm (rebuilt)** | **`71d8c3d7…`** | **body** | **29,834** | 1 | 0 | 0 | identical; `slow_event_capacity` 1,280 (256 + 1,024) |

- Every install was confirmed by device hash on the first try.
- **The adopted APK was reinstalled after each arm session**, and its hash
  confirmed (`f31b1c18…`).
- The first arm session and the adopted session ran in one driver pass
  (07:03-07:12Z). The rebuilt arm session is the re-run (07:13-07:17Z).
  The target-form session was not repeated, because the companion had not
  changed since.

**Observation: the recent ring fills faster on this hold than it was
sized for.** The rebuilt-arm session retained 288 recent events in 197 s
(~1.46/s), against the ~0.63/s the sizing used from session 3. At that rate
1,024 covers ~12 min, not ~27.

- A 20-min hold would still roll the recent ring.
- The marked ring (transitions) is unaffected.
- The size stays at 1,024 here. Whether to raise it is a follow-up; the
  cost is ~23 characters a row under a cap with ~69K of room.

## 4. Nothing adopted

- **The onn carries the adopted APK `f31b1c18…8ae7` at the end**, hash
  confirmed. The build output was also restored to it.
- The client change waits for the user's next APK adoption.
- The companion change accepts both forms, and it stays in the working
  tree.

## Files (`cl_b1_2026-09-25/`)

- **Drivers and logs**: `cl_b1_sessions.py`, `cl_b1_rerun.py`,
  `cl_b1_sessions_first.log`, `cl_b1_rerun.log`, `sessions_first.json` and
  `sessions.json`.
- **Reports**: `report_arm_body.json`, `report_adopted_target.json` and
  `report_arm2_body.json`.
- **Journal**: `companion_journal_redacted.txt` (the decoder-report lines
  of the window).
- **Code copies**: `decoder_report_http.py`, `DecoderReportUpload.kt`,
  `DecoderReportUploadTest.kt` and `test_cl_b1_decoder_report_body.py`.
- **Test output**: `python_tests.txt` and the two JUnit XML files.
- **Patch**: `cl_b1_patch.diff`, `pre_patch_sha256.txt` and
  `post_patch_sha256.txt`.

`h2_prep_redact.py --check` reports 0 residual matches on every file
except the decoder-report byte copies, which carry the known core-version
false positive. The journal's client address is written `<ipv4>`.
