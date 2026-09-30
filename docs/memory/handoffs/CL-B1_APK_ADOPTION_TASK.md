---
memory_schema: 1
as_of: 2026-09-30
status: TASK HANDOFF — CL-B1 APK: build the next client APK from the source tree (the decoder report as a POST body and the grown slow-event rings; C4-M1's inert v2 FEC path rides along), install it on the onn, and adopt it by the pre-registered rule below — authorized by the user 2026-09-30 ("we can queue it now"). Runs after C3-L4-N3 on the same prompt. If the rule fails, the adopted f31b1c18…8ae7 is reinstalled and confirmed
---

# CL-B1 — the next adopted APK

**Why.** `CL-B1` (2026-09-25) built and tested the client change — the
decoder report travels as a POST body, the slow-event rings grew to 256
marked + 1,024 recent, `slow_event_capacity` is their sum — and the user
chose on 2026-09-28 to bundle it into the next adopted APK. No C5 arm
needed a client change, so this is that APK. **The user authorized the
build, install and adoption on 2026-09-30.** The companion side has been
in the tree and running since 2026-09-25 (both forms accepted).

Read first: `evidence/CL_B1_DECODER_REPORT_BODY_2026-09-25.md` (§2 the
client, §3 the sessions and the ring observation, the adoption call),
`patches/CL-B1_DECODER_REPORT_BODY.md`, `C4_M1_FEC_ARM_2026-09-25.md`
§"What adoption would mean" (the tree carries `FecRs82.kt` and the
receiver's v2 path; inert while `PRIVYHUB_FEC_SCHEME` is unset — it stays
unset), `TOOLS.md` (build, install, device hash, host-shell operation),
`evidence/D_BASE_CLOSEOUT_2026-09-23.md` (the table).

## 0. Pre-registration, written before the build

`evidence/cl_b1_apk_2026-09-30/cl_b1_apk_preregistration.txt`, hashed.
**ADOPTED** if every row holds; otherwise NOT ADOPTED, the rows recorded,
the old APK reinstalled:

- **A1 build.** `:app:assembleDebug` from the tree as it stands (no
  source change in this task); the Kotlin tests pass
  (`DecoderReportUploadTest` 4/4, `FecRs82Test` 6/6, and the rest of the
  suite); the APK's sha256 recorded; the diff of the client source tree
  against the `f01c3b2` baseline listed file by file (it must be only
  `CL-B1`'s and `C4-M1`'s client files — anything else stops the task).
- **A2 install.** Installed on the onn through the pinned adb port; the
  device hash equals the build's on the first read; the app opens, wakes
  and resumes as `TOOLS.md` says.
- **A3 the report path (one session, attract mode, ≥ 190 s, BACK).**
  The journal shows the body form ("received as body"), the report is
  stored, 0 WARNING, 0 traceback; `slow_event_capacity` 1,280; the key
  set identical to `cl_b1_2026-09-25/report_arm2_body.json`'s; the
  companion's target-form path untouched (no code change).
- **A4 a 20-min hold on the new APK** (attract mode, adopted profile at
  7000, `any_override` false, adaptive off, T2 on) meets the client-side
  close-out rows: spikes ≥ 20 ms/min < 200, rendered fps ≥ 59.5, stale
  drops/min < 20, audio underruns/min < 5; the client's FEC counters
  (recovered, unrecoverable groups, `fec_max_hold_ms`) in the same range
  as the adopted APK's B holds of 2026-09-30 (`c5_m3_2026-09-29/`).
- **A5 the link rows, paired.** Post-FEC video loss/min and max output
  gap are **reported with a paired 20-min hold on the adopted
  `f31b1c18…8ae7` the same evening** (install it back for that hold, hash
  confirmed, then reinstall the new build, hash confirmed — or run the
  adopted hold first; say which). They are the link's rows — the adopted
  APK itself missed them on three of the last four evenings — so they do
  not gate adoption unless the new APK's loss is worse than the paired
  adopted hold's by more than the evening's own spread, in which case
  NOT ADOPTED and say so with the two tables. The client's receive path
  did not change in `CL-B1`; if the numbers say otherwise, that is the
  finding.
- **A6 at the end.** The onn carries the new APK (or the old one if NOT
  ADOPTED), hash confirmed; profile adopted, `any_override` false,
  adaptive off, `PRIVYHUB_FEC_SCHEME` unset and absent, no game, 0
  banners; the build output on disk is the installed APK.

Rules never tightened or loosened after data. Two-retry limit on the
build and the install; a session that fails for a harness reason is
re-run once.

## 1. Do it, in that order

Build → tests → diff listing → install → A3 session → A4 hold → the
paired adopted hold (A5) → final install and hash. Every install and hash
in a log. The companion is not changed and not restarted except as the
harness already does through its unit.

## 2. If ADOPTED

- **`decisions/CL-B1_APK_ADOPTION_2026-09-30.md`**: the user's
  authorization (2026-09-30, "we can queue it now"), the rule, the rows,
  the new hash in full, the old hash in full, what the APK carries
  (`CL-B1`'s two changes; `C4-M1`'s v2 FEC decoder, inert without the
  scheme; nothing else), and how to roll back (reinstall the old APK from
  its recorded path; the companion needs nothing).
- Every place that names the adopted APK: `CURRENT.md` (Verified State:
  Installed), `TOOLS.md`, `MEMORY.md` if it names it,
  `evidence/RUNTIME_VALIDATION.md`, `handoffs/CURRENT_HANDOFF.md`, the C7
  row in `docs/ROADMAP.md` ("CL-B1 … adoption waits for the user" → adopted
  2026-09-30, the hash), `investigations/ACTIVE.md`. The harness
  preflights that check the APK hash (`c3_l4_nft_night.py` and the C5
  night scripts) read the adopted hash from wherever they read it — update
  that one place and its tests (`test_c3_l4_nft_night.py` must pass with
  the new hash; the evidence copies of the old scripts are history, not
  edited).
- The record: `evidence/CL_B1_APK_ADOPTION_2026-09-30.md`; evidence dir
  `cl_b1_apk_2026-09-30/` (pre-registration, build log, test output, the
  diff listing, install logs and hashes, the A3 report, both holds' runs,
  score tables, manifest, `--check`).

## 3. If NOT ADOPTED

The old APK reinstalled and confirmed; the record says which row failed
with its data; nothing else changes; the user decides.

## 4. Then, last on this prompt

Re-run `python3 tools/check_memory_health.py` and
`python3 tools/h2_prep_redact.py --check` over every text file written
by both tasks; rewrite `logs/c7_d8_git_status_2026-09-30.txt` (`git status
--short`, `git diff --stat`) so it reflects the whole prompt; append the
APK line to `evidence/C7_D8_CHECKPOINT_2026-09-30.md`; rewrite `CURRENT.md`
last — Next Action 1: **the user's commit** (Cowork gives the line from
the git status file); 2: the user's call on turning live on by default;
3: what `docs/ROADMAP.md` says follows C7 / D8, one line, not started.
No addresses, MACs, SSIDs, ADB endpoints, serials or credentials
anywhere; `nft` and real `sudo` never. Nothing committed.
