---
memory_schema: 1
as_of: 2026-09-20
status: TASK HANDOFF — D-BASE-R4, session-report visibility; authorized by the user 2026-09-20 for an unattended run after D-BASE-R3a; superseded once its evidence record exists
---

# D-BASE-R4 task handoff

Close the four open diagnostic-visibility items in /home/privyhub/Projects/onn-stream-test. Run only after `D-BASE-R3a` has finished and its memory is written (check docs/memory/CURRENT.md first; if R3a is not recorded there, stop and say so). The user is away; run unattended, ask nothing. Read first: docs/memory/CURRENT.md, docs/memory/TOOLS.md, docs/KNOWN_ISSUES.md (the items named below, verbatim), docs/memory/evidence/D_BASE_R2_STALL_VISIBILITY_2026-09-20.md, docs/memory/evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md (the F15 note: `max_output_gap_ms` 135 for a 46 s terminal stall), PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt and NativeStreamActivity.kt (report assembly), companion/games/native_stream_heartbeat.py, tools/diagnostic_retention.py.

Scope, four items, diagnostic and report-only, one patch (client + companion). No streaming constant, decoder configuration, stale-drop policy, FEC, transport, emulator, or recovery behaviour changes.

1. **A terminal stall gets recorded.** On every 500 ms tick and at report assembly, if `last_output_age_ms` exceeds the current `max_output_gap_ms`, the report's `max_output_gap_ms` is raised to it and a row is written for it with the existing slow-event columns, flagged `terminal: true` (or an equivalent explicit marker) so a gap that never ended is distinguishable from one that did. The report also gains `output_age_at_end_ms`.
2. **Per-session top-N slow-event retention.** Alongside the 64-entry recent ring and the 64 marked, keep two top-16 lists for the session: by `output_gap_ms` and by `rx_to_decode_ms`, each with the same row shape, so the worst events of a long session survive the ring. Keep every existing retention counter; add `slow_event_retained_top_gap` and `slow_event_retained_top_latency` and their capacities. Do not shrink or reshape the existing lists.
3. **`slow_events_marked` serialization.** KNOWN_ISSUES (2026-09-18 C3.L2b reporting defect) says the marked window is counted but emitted as an empty array. Check whether that is still true on the current code; if it is, fix the serialization; if it is already fixed, say so in the record with the report that proves it and mark the KNOWN_ISSUES item closed.
4. **Heartbeat log rotation.** `logs/games/native_stream_heartbeat.log` rotates at 4 MB, keeping 3 rotated files, and `tools/diagnostic_retention.py` covers it. Same for `logs/games/native_stream_recovery.log` at 1 MB. Rotation must never lose the line being written.

Build the APK with the real toolchain and install it per TOOLS.md; restart the companion (D-068) after checking 8765 is free; compile the Python; `git diff --check`.

Validation, unattended, host shell, per TOOLS.md driving rules:

- Three attract-mode sessions of the PS1 reference title, 90 s each, zero input, ended with BACK: every report must carry the new fields; for each report show that its `max_output_gap_ms` has a row and that the top-16 lists hold the session's true worst events (cross-check by comparing the top-gap list's maximum against `max_output_gap_ms` and the top-latency list's maximum against `max_rx_to_decode_ms` or the closest existing field).
- One terminal-stall session: settle 25 s, then apply the SIGSTOP substitute from the `D-BASE-R3` record for 20 s **without** clearing it, end the session with BACK while still stopped, then SIGCONT and tear down. The report must show `max_output_gap_ms` >= 20,000 with a `terminal: true` row and `output_age_at_end_ms` >= 20,000. (Recovery will pause the game and try restarts during this; that is expected and is not what is being measured.)
- Rotation: append synthetic lines to a copy of the heartbeat log until it crosses 4 MB through the real rotation code path, and show the rotated file set; then confirm `tools/diagnostic_retention.py --dry-run` (or its equivalent) lists both logs.

Keep every report and the recovery/heartbeat lines for the terminal-stall session under docs/memory/evidence/d_base_r4_<date>/ with SHA-256s. Record raw numbers first in docs/memory/evidence/D_BASE_R4_REPORT_VISIBILITY_<date>.md; classify RUNTIME VALIDATED only if every check above passes, else DEVELOPMENT with the failing check named. Patch record in docs/memory/patches/ and PATCH_INDEX.md; update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy), MEMORY.md, handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, and KNOWN_ISSUES.md (mark the four items fixed or state why not). Teardown per TOOLS.md: no stopped process left, no listener left on 8765 / 48100-48102 / 48110, no banner on the onn. If a step cannot be completed, INDETERMINATE with the exact command; never retry a failing action more than twice. No IP addresses, ADB endpoints or device identifiers in any memory or evidence file.
