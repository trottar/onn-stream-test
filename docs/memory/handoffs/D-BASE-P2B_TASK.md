---
memory_schema: 1
as_of: 2026-09-21
status: TASK HANDOFF — D-BASE-P2b, the separating experiment from D-BASE-P2a (starvation: drift or side effect); runs after D-BASE-R3b; authorized 2026-09-21 for an unattended run
---

# D-BASE-P2b task handoff — is the +9 % starvation the fix or the night?

No dependency on other tasks; run whenever the host is idle (no game session, no listener on 8765). Unattended, ask nothing. Read first: docs/memory/evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md (including the correction at the end: run order was 137, 143, 151, 163, 157), docs/memory/TOOLS.md, PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt.

**Question.** `prolonged_starvation_events` per 120 s session read 134-146 without the startup hold and 137-163 with it. Either the host drifts over a run or the fix shifts the queue equilibrium. Separate them.

**Method.** Two builds: the current one (hold on) and the same source with `STARTUP_REAL_PCM_TIMEOUT_MS` set to **0** (hold effectively off; everything else identical — do not revert the patch, flip the constant, and record `audio.startup_wait_ms` so each report proves which arm it is). Ten attract-mode sessions of the PS1 reference title, 120 s each, zero input, per TOOLS.md, **strictly alternating** hold-on / hold-off starting with hold-off, reinstalling the APK between arms (the harness already force-stops the app before each launch). Reject and re-run any session with a discontinuity in the first 30 s; say how many.

**Per session:** `prolonged_starvation_events`, `underruns`, `concealed_underruns`, `avg_queue_residence_ms`, `max_queue_residence_ms`, `startup_wait_ms`, `first_write_elapsed_ms`, video loss per minute, rendered fps, host time. **Reading, pre-registered:** if both arms rise together with run order (Spearman of starvation against run index, pooled), it is drift and the fix is clear; if the hold-on arm sits above the hold-off arm at every pair (5 of 5 pairs, sign test) with no shared trend, it is the fix and the record must say what `avg_queue_residence_ms` did (the mechanism the P2a record proposed is a shifted queue equilibrium — that column either shows it or does not); mixed, say so. Then, if the fix is clear, reclassify `D-BASE-P2a` **RUNTIME VALIDATED** (its other miss, 59.38 vs 59.4 fps, was a bar above what the link delivered in either arm, as its record shows) and update the target table's audio row; if the fix is implicated, leave it DEVELOPMENT and state the trade (a ~200-underrun startup burst removed against ~+13 starvation events per 2 min).

End with the **hold-on** build installed. Record raw numbers first in docs/memory/evidence/D_BASE_P2B_STARVATION_SEPARATION_<date>.md with reports under evidence/d_base_p2b_<date>/ and SHA-256s; update CURRENT.md (fixed headings, `python3 tools/check_memory_health.py` healthy — trim, it is at its limit), MEMORY.md, handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, KNOWN_ISSUES.md, evidence/RUNTIME_VALIDATION.md, and the P2a record's classification line. Teardown per TOOLS.md. Never retry a failing action more than twice. No addresses or device identifiers in any memory or evidence file.
