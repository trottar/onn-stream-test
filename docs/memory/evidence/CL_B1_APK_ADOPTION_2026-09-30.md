---
memory_schema: 1
as_of: 2026-09-30
baseline_commit: f01c3b2
status: CL-B1 APK DONE — ADOPTED by the pre-registered rule (authorized by the user 2026-09-30). New adopted APK de072762…835e (clean build reproducible; Kotlin 11/11), built from the tree unchanged since f01c3b2; beyond the previous f31b1c18…8ae7 it carries only CL-B1's report body and grown slow-event rings and C4-M1's inert v2 FEC decoder. A3: body form, 0 WARNING, slow_event_capacity 1,280, key set identical. A4: every client row met, FEC counters inside the old APK's range. A5 (paired, the old APK the same block): loss 10.29 vs 11.81/min, max gap 246 vs 205 ms — the link's rows, not gating. The onn carries the new APK, hash confirmed; profile adopted, flags, selector and PRIVYHUB_FEC_SCHEME absent; nothing committed
---

# CL-B1 — the next adopted APK

Task: `handoffs/CL-B1_APK_ADOPTION_TASK.md`. It ran after `C3-L4-N3` on
the same prompt.

- The user's authorization, 2026-09-30: "we can queue it now".
- Decision: `decisions/CL-B1_APK_ADOPTION_2026-09-30.md`.
- Evidence: `cl_b1_apk_2026-09-30/` (manifest).

**Outcome: ADOPTED.** The pre-registration
(`cl_b1_apk_preregistration.txt`, sha256 `6e77aa13…`) was written before
the build, and every row held.

## A1 — the build (`build.log`, `build_incremental.log`, `unit_tests.log`, `junit/`, `client_diff_listing.txt`)

- `sh ./gradlew :app:assembleDebug` gave **`de072762…835e`**.
  - The first build was incremental: the classes were up to date and
    only packaging ran.
  - So a **clean** build followed (`clean :app:assembleDebug`, 35 tasks
    executed, Kotlin recompiled). It gave **the same hash**: the build is
    reproducible from the tree.
- `:app:testDebugUnitTest`: **11/11** (DecoderReportUploadTest 4/4,
  FecRs82Test 6/6, ExampleUnitTest 1/1).
- **The diff listing.**
  - The client tree against `f01c3b2` is **empty**: the `CL-B1` and
    `C4-M1` client files were committed in `f01c3b2`, and nothing has
    changed since.
  - The previous APK `f31b1c18…` was built from `824c9d9` (D-BASE-P10,
    2026-09-23). Against that, seven files differ, each attributed:
    - `CL-B1`: `AvcLowLatencyDecoder.kt`, `DecoderReportUpload.kt` (+
      test), `NativeStreamActivity.kt`;
    - `C4-M1`: `FecRs82.kt` (+ test), `RtpH264Receiver.kt`.
  - Nothing else, so **A1 holds**.

## A2 — the install (`install_new.log`)

- `adb install -r`. The device hash was `de072762…` on the first read,
  matching the build's.
- The app woke and opened. The first `am start` caught the TV mid-wake,
  and the second brought `MainActivity` to the front.
- It resumed a stream in every session below (the harness's RESUME
  PLAYING path).

## A3 — the report path (`runs/`, `a3_check.txt`)

One attract-mode session on the new APK, 14:17:34-14:20:54Z (213 s), then
BACK.

- Journal: `decoder-session-log received as body: report_chars=31155`,
  then the POST 200. No target-form upload, 0 WARNING, 0 traceback.
- The report was stored. `slow_event_capacity` **1,280**. Key set
  **identical** to `cl_b1_2026-09-25/report_arm2_body.json`'s (195
  keys).
- The companion was unchanged: the sha256 of its 42 files was the same
  before and after this task.
- **A3 holds.**

The recent ring retained 324 events in 213 s (~1.5/s), as CL-B1 saw.

## A4 and A5 — the holds (`runs/N1`, `runs_old/O1`, `a4_a5_score.txt`)

**The two holds.**

- **N1** (the new APK): 14:21-14:42Z.
- The adopted APK was then installed (`install_old_for_A5.log`, hash
  `f31b1c18…` on the first read).
- **O1** (the old APK, paired): 14:44-15:05Z, straight after, with no
  cold wait.
- Both ran in attract mode on the adopted profile at 7000, with
  `any_override` false, adaptive off, `PRIVYHUB_FEC_SCHEME` unset and T2
  on.
- The harness is C5's with an expected-hash check in place of its
  reinstall (`cl_b1_night.sh`).

| hold | APK | spikes/min | fps | stale/min | underruns/min | FEC recovered/min | unrecoverable groups/min | fec_max_hold ms | **loss/min** | **max gap** | slow cap / recent retained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1 | new `de072762` | 27.9 | 59.92 | 0.69 | 0.40 | 6.43 | 1.58 | 15 | 10.29 | 246 | 1,280 / 1,024 |
| O1 | adopted `f31b1c18` | 28.3 | 59.92 | 1.09 | 0.64 | 5.98 | 1.63 | 14 | 11.81 | 205 | 128 / 64 |

- **The reference** is the adopted APK's eight C5-M3 B holds of
  2026-09-30. FEC recovered 6.17-14.80/min, unrecoverable 0.84-3.12/min,
  max hold 14-19 ms; loss 3.16-32.68/min (spread 29.52).
- **A4 holds.** All four client rows are met, and all three FEC counters
  are inside the reference range.
- **A5 does not gate.** The new APK's loss is 1.51/min *lower* than the
  paired old APK's. Both are over the < 10 target, as the adopted APK has
  been on most holds these evenings.
  - T2: the onn's link was at 195 Mbit/s, with the Opal's retries at 85k
    (N1) and 113k (O1).
  - The receive path did not change except C4-M1's inert v2 branch, and
    the numbers agree.
- **The ring.** The new APK's recent ring was full (1,024) at the end of
  the 20-min hold. It rolls, as CL-B1 predicted: ~12 min of events.
  Raising it is a later, optional follow-up.

## A6 — the end (`install_final.log`)

- The new APK was reinstalled; device hash `de072762…` on the first read.
- The build output on disk is the same APK.
- `MainActivity` in front; 0 NOW PLAYING banners.
- `PRIVYHUB_*`: 0 in the manager and 0 in the companion's environ, so the
  flags, the selector and `PRIVYHUB_FEC_SCHEME` are all absent.
- Profile adopted at 7000, `any_override` false, adaptive off, `xor8_1`;
  no game.

## What changed on adoption

- `tools/c3_l4_nft_night.py`: `ADOPTED_APK_SHA256` is the new hash,
  covered by a new test (`tools/test_c3_l4_nft_night.py` 24/24).
- **Not edited:** the C5 night scripts in `c5_m2_2026-09-29/` and
  `c5_m3_2026-09-29/`. These evidence copies are history, per the
  handoff.
  - **Their teardown still reinstalls `f31b1c18…`**
    (`runtime/c4_m1/adopted_app-debug.apk`) whenever the device hash
    differs.
  - **Before any reuse, point `ADOPTED_SHA` / `ADOPTED_APK` at the new
    APK** (noted in `TOOLS.md`).
- Memory: `CURRENT.md`, `TOOLS.md`, `evidence/RUNTIME_VALIDATION.md`,
  `docs/ROADMAP.md` (the C7 CL-B1 line), `docs/PROJECT_STATUS.md`,
  `investigations/ACTIVE.md`.
  - `MEMORY.md` and `handoffs/CURRENT_HANDOFF.md` do not name the APK
    hash.

## Files (`cl_b1_apk_2026-09-30/`)

- `cl_b1_apk_preregistration.txt` (+ `.sha256`).
- `client_diff_listing.txt`.
- `build.log`, `build_incremental.log`, `apk_sha256.txt`.
- `unit_tests.log`, `junit/`, `harness_tests.txt`.
- `install_new.log`, `install_old_for_A5.log`, `install_final.log`.
- `companion_sha256_before.txt` / `_after.txt`.
- The harness: `cl_b1_night.sh`, `c5_m2_run.sh`, `c5_m2_score.py`,
  `t2_sample.py`, `cl_b1_run1.log`, `cl_b1_run2.log`.
- `runs/` (A3, N1) and `runs_old/` (O1).
- `cl_b1_a3_check.py` → `a3_check.txt` / `.json`.
- `cl_b1_a4_a5_score.py` → `a4_a5_score.txt` / `.json`.
- `sha256_manifest.txt`.

The APKs themselves are outside git: `runtime/cl_b1_apk/`,
`runtime/c4_m1/`.
