---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — C3.L3a R2B: raise the companion's decoder-report size cap so a 24-transition rerun session's report is stored (companion change, one constant + one warning line, restart through the systemd unit), then finalize rerun session 2 against the report rebuilt from the journal and append its decoder-axis check to the R2 record; no client, profile, encoder or route-shape change; no session; authorized by the user 2026-09-24 ("Go")
---

# C3-L3A-R2B — store the report; finish session 2

**Why.** `C3_L3A_R2_SESSION2_2026-09-24.md`: the client posted its
decoder report at BACK and the companion returned 400 because the report
(32,057 chars) exceeded `MAX_REPORT_CHARS = 32_000`
(`companion/games/decoder_session_log.py`); the client swallows non-2xx
(`NativeStreamActivity.kt`, stop thread). A one-client-session rerun
(24 SSRC changes) is expected to exceed the cap every time; the S1 soak's
20-transition sessions had 39-426 chars of headroom. Sessions 3 and 4
must not lose their reports. The user authorized the companion change.

Read first: `C3_L3A_R2_SESSION2_2026-09-24.md` §"Why there is no decoder
session" and §"Open", `c3_l3a_r2_2026-09-24/report_check.txt`,
`companion/games/decoder_session_log.py`, the `decoder-session-log` route
in `companion/plugins/games.py`, `privyhub_service.py` (the `ValueError`
→ 400 path and the HTTP server's request-line limit),
`evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`, `TOOLS.md` (the
systemd companion).

**Scope.** Companion: `decoder_session_log.py` (the constant) and the
one place the 400 is produced (a warning log line). Nothing else in the
companion; **no client change** (the APK stays `f31b1c18…8ae7`); no
profile, encoder, route-shape or environment change; no session. The
adopted profile stays adopted — confirm `any_override: false`, cap
90,000, cushion 12/17, redundancy 2/4 after the restart.

## 1. The cap

- The report travels URL-encoded in the request target (50,759 chars for
  the 32,057-char report, ratio ~1.58). Python's `http.server` refuses a
  request line over 65,536 bytes with 414 before any handler runs, so the
  transport's own ceiling is ~41K decoded chars. Set
  `MAX_REPORT_CHARS = 48_000`: above every plausible one-session report
  (32K at 24 changes; ~300 chars per additional change), below nothing
  the transport can carry. Write the transport ceiling and the arithmetic
  in the constant's comment. **The proper fix — the client posting the
  report as a request body — is a client change and is registered as a
  follow-up in `docs/KNOWN_ISSUES.md`, not done here.**
- Where the `ValueError` becomes the 400: log one WARNING line with the
  reason and the report length (no report content), so a rejection is
  visible in the journal. Nothing else changes; the response stays 400.
- `py_compile`; a direct call of `write_decoder_session_log` from a
  scratch script with (a) the rebuilt 32,057-char report and (b) a
  synthetic 47,000-char JSON object, both written to a **scratch
  directory** (if the function's output directory is not a parameter,
  monkeypatch the module constant in the scratch script) — accepted; (c)
  49,000 chars — refused with the length reason. Never write a synthetic
  file into `logs/games/decoder_sessions/`.
- `systemctl --user restart privyhub-companion`; the unit's MainPID owns
  8765; `native-stream-status` shows the profile as adopted; journal shows
  the clean start. Record the restart time.

## 2. Session 2's decoder axis

- Wrap `c3_l3a_r2_2026-09-24/rejected_report_20260924_171642_from_journal.json`
  as a decoder-session file in the stored shape (`schema`,
  `received_at_utc` = the journal's POST time 2026-09-24T17:16:42.799Z,
  `report`), saved as
  `c3_l3a_r2_2026-09-24/native_decoder_20260924_171642_rebuilt.json` —
  in the evidence directory, **not** in `logs/games/decoder_sessions/`
  (it was never stored by the companion, and the probe's auto-selection
  must not find it).
- `--finalize --state logs/streaming/c3_l3a_runs/states/20260924_130016_state.json
  --decoder <that file>`; the run files in `c3_l3a_runs/` are regenerated
  (the marks-only versions are already in `c3_l3a_r2_2026-09-24/runs/`).
  Confirm expected 24 = 24 SSRC changes, alignment spread ≤ 1 s, the
  per-transition table, and — as in `C3-L3A-R1` — every mark's largest
  slow event in the 5 s before it (`mark_check.py` from `c3_l3a_r1_…`).
- **Append** to `C3_L3A_R2_SESSION2_2026-09-24.md` (do not rewrite it) a
  section "Decoder axis — DONE 2026-09-24 (R2B)" with: alignment, the
  per-transition cost distribution beside R1's and S1's, the per-mark table
  (how many of the 11 transition-window marks sit behind a measured
  restart gap; how many of the 15 unattributed marks have any slow event
  in the 5 s before them), and the close-out rows for the session beside
  the close-out C / W. Update the frontmatter status line to say the
  decoder axis is done from the rebuilt report. `--aggregate` afterwards:
  still 2 pooled (the detection table does not change).

## Record and memory

`evidence/C3_L3A_R2B_REPORT_CAP_2026-09-24.md` (the change, the
validation, the restart, what remains — the body-POST follow-up), with
outputs and a `sha256sum` manifest under `evidence/c3_l3a_r2b_2026-09-24/`;
`patches/C3-L3A-R2B_*.md` with per-file SHA-256 before and after (the
companion file too); regenerate `patches/PATCH_INDEX.md`.
`docs/KNOWN_ISSUES.md`: the cap item → mitigated (48,000) with the
transport ceiling stated and the body-POST follow-up open.
`evidence/RUNTIME_VALIDATION.md` (the cap: RUNTIME VALIDATED only once a
real 24-change session is stored — say PENDING until session 3).
`CURRENT.md` (companion restarted, cap raised; sessions 3-4 awaiting the
user; `python3 tools/check_memory_health.py` healthy); `TOOLS.md` one line
(the cap and the warning line); `2026-09-24.md`;
`handoffs/CURRENT_HANDOFF.md` one line. No addresses or device
identifiers in any file. Nothing committed.
