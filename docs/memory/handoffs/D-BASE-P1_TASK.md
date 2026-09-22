---
memory_schema: 1
as_of: 2026-09-20
status: TASK HANDOFF — D-BASE-P1, stale-drop threshold characterization probe; diagnostic only, product default unchanged at the end; authorized 2026-09-20 for an unattended run
---

# D-BASE-P1 task handoff — stale-drop threshold characterization

A measurement, not a product change. In /home/privyhub/Projects/onn-stream-test the client drops any decoded frame whose receive-to-output latency exceeds 60 ms (`AvcLowLatencyDecoder.kt`, `if (latencyMs > 60L)`, "v0.7 stale-presentation policy"). Group A measured that rule as the cause of the 3.5 fps gap between received-AU fps (59.2) and rendered fps (55.5) — 5.5 % of frames sit above 60 ms and are thrown away. Nobody has measured what the threshold buys or costs. This probe does. The user is away; run unattended, ask nothing.

Read first: docs/memory/CURRENT.md, docs/memory/TOOLS.md, docs/memory/evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md (the A2 re-score, the latency distribution), docs/memory/investigations/BASELINE_STREAM_HEALTH.md (the target table), docs/memory/evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md (the report fields you will read), PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt.

**The probe build.** Replace the literal `60L` with a constant `STALE_OUTPUT_MS` read once at decoder construction from an Intent extra `privyhub.stale_output_ms` that `NativeStreamActivity` accepts, default **60** so the product path is byte-for-byte the same behaviour when the extra is absent. Record the value in force in the session report as `decoder.stale_output_ms`. Add nothing else. This is the only code change and it stays in the tree (it is a diagnostic knob with the product default; document it as such).

Build with the real toolchain, install per TOOLS.md, companion restarted with 8765 checked free. Since NativeStreamActivity is not exported, the extra must reach it through the path TOOLS.md records (MainActivity + tap) — if the launch path cannot carry an extra, use a companion-served value instead (`native-stream-start` response carrying `stale_output_ms`, default 60, settable only through a `?stale_output_ms=` query on that action for this probe) and say which mechanism was used.

**Sessions.** Attract mode, PS1 reference title, 90 s each, zero input, per TOOLS.md driving rules, BACK to end, teardown between:

| threshold | sessions |
| ---: | ---: |
| 60 (product default, control) | 3 |
| 90 | 3 |
| 120 | 3 |
| 200 | 3 |

Twelve sessions, interleaved (60, 90, 120, 200, 60, 90, …) so drift in the link does not load one arm. Reject and re-run any session whose report shows a sequence resync jump ≥ 128 packets or `max_output_gap_ms` ≥ 1,000 (an outage, not the thing being measured) — say how many were rejected.

**Per session, from the report:** `rendered_frames` / duration → rendered fps; `stale_output_drops`; `spike_20_ms`, `spike_50_ms`, `spike_80_ms`; `max_output_gap_ms`; `max_rx_to_decode_ms`; the receive-to-output latency distribution of the rows in `slow_events_ge_50_ms` and the top lists (p50 / p90 / max of `rx_to_decode_ms` over the retained rows — say that it is the retained-row distribution, not all frames); `audio.underruns`. If the client can cheaply add a 10-bucket histogram of receive-to-output latency for all rendered frames (0-20, 20-40, … , >180 ms) to the report in the same probe build, do it — it is the number this probe is really after — and name it `decoder.rx_to_output_histogram_ms`.

**Answer these, with the arms' medians side by side:** (1) how much rendered fps each threshold recovers; (2) what it costs in latency — does the p90 of rendered-frame latency move, or do the recovered frames simply land at 60-90 ms while the bulk stays where it was; (3) whether `max_output_gap_ms` changes at all (it should not; the gap tail is transport); (4) whether the 20 ms spike count changes (it should not; it is measured before the drop decision). State plainly which threshold, if any, meets both `rendered fps ≥ 59.5` and a p90 latency you consider acceptable — and that the decision is the user's.

**At the end the product default is 60 and unchanged**: the last build installed on the onn must carry no extra, and one final 60 s control session must report `stale_output_ms` 60. `git diff --stat` must show only the decoder, the activity, and (if used) games.py.

Record raw numbers first in docs/memory/evidence/D_BASE_P1_STALE_THRESHOLD_<date>.md with all reports under evidence/d_base_p1_<date>/ and SHA-256s; classify as CHARACTERIZED / INDETERMINATE (no keep/revert, nothing is being accepted). Patch record for the knob in docs/memory/patches/ and PATCH_INDEX.md; update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy — trim, it is near 10 KB), MEMORY.md, handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, KNOWN_ISSUES.md (the "60 ms stale threshold" item points at the record). Teardown per TOOLS.md. Never retry a failing action more than twice; INDETERMINATE with the exact command otherwise. No IP addresses, ADB endpoints or device identifiers in any memory or evidence file.
