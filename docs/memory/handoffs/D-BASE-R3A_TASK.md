---
memory_schema: 1
as_of: 2026-09-20
status: TASK HANDOFF — D-BASE-R3a, the two D-BASE-R3 defects; authorized by the user 2026-09-20 for an unattended run without root; superseded once its evidence record exists
---

# D-BASE-R3a task handoff

Fix the two `D-BASE-R3` defects in /home/privyhub/Projects/onn-stream-test. The user is away; run unattended, ask nothing, and stop with INDETERMINATE rather than guessing. Read first, in this order: docs/memory/CURRENT.md, docs/memory/evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md (the whole record — the defects, the substitute fault injection and its three differences, and the teardown that worked), docs/memory/investigations/LINK_DROP_RECOVERY_DESIGN.md, docs/memory/TOOLS.md, docs/memory/patches/D-BASE-R3_LINK_DROP_SELF_RECOVERY.md, companion/games/link_drop_recovery.py, companion/diagnostics/c3_linux_actuator_probe.py (the restart primitive and its failure path), companion/native_stream.py (the full encoder start path that native-stream-start uses), companion/plugins/games.py.

Scope, exactly two changes, both in the companion, one patch:

1. **Failed-restart recovery.** When `_maybe_restart_encoder` finds the session has no encoder process (the `C3.L1` failure path set `manager._process = None`, or `_running_locked()` is otherwise false), it must not call the restart primitive again. It uses the full encoder start path instead — the same code `native-stream-start` uses to bring the encoder up, with the same client target and profile, without touching capture, the FEC relay, audio, the controller transport or the emulator. Log it as `encoder_restart` with a new field `method: "restart"|"full_start"` so the two are countable. The backoff schedule is unchanged. Do not modify the `C3.L1` primitive's failure path; the fix is in the recovery loop's choice of primitive.
2. **Restart trigger freshness.** Replace the single-heartbeat check with: the two newest heartbeats both have `last_output_age_ms >= DESYNC_MS` and the newer is not lower than the older (still rising), AND the newest heartbeat was received after the restart became eligible (`state_since + RESTART_AFTER_MS`, or `last_restart_at + backoff`, whichever applies). A heartbeat older than that is not evidence. Log the two ages on every `encoder_restart` line as `age_pair_ms: [older, newer]`.

Nothing else changes: not the constants, not the client, not the recovery save, not the launcher prompt. Compile the Python, `git diff --check`, restart the companion (D-068) after checking 8765 is free.

Validation, unattended, no root available. The nftables plan cannot run (no non-interactive root — do not attempt `sudo`, do not ask for a password). Use the SIGSTOP/SIGCONT substitute exactly as `D-BASE-R3`'s record describes it, and state in the record that it is the substitute and what it cannot show. Each run from a fresh attract-mode session of the PS1 reference title, 25 s settled before the fault, zero input, opened through RESUME PLAYING per TOOLS.md, ended with BACK, the client seeing the game end before the companion stops:

| run | N | pass criterion |
| --- | ---: | --- |
| G3 | 3 s | pause within 1.8 s; `restarts` **0**; resume within 2.5 s of the clear (fix 2) |
| G15 | 15 s | pause; restart attempts while stopped fail as before; **after the clear, the next attempt uses `method: full_start` and succeeds, and the client resumes through the gate within one backoff interval of the clear** (fix 1) |
| G15b | 15 s | repeat of G15 |
| G150 | 150 s | pause; give-up at 120 s; `PAUSED_SAVED`; after the clear, RESUME PLAYING from the launcher restores play (the prompt appears; choose Resume from recovery save; confirm video and `state PLAYING`) |

Per run keep: the recovery log lines, the heartbeat lines through the fault, the decoder session report, and for G150 a filtered uiautomator dump of the prompt. Classify each run against its criterion; the patch is RUNTIME VALIDATED ONLY for the substitute fault, and the record must say the nftables runs are still owed. If any run cannot be completed, INDETERMINATE with the exact command that failed; never retry a failing action more than twice. Teardown per TOOLS.md, and per the `D-BASE-R3` record's teardown row: recovery save discarded, no process left stopped, no listener left on 8765 / 48100-48102 / 48110, no banner on the onn.

Record raw numbers first in docs/memory/evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md (or the date it runs), the patch in docs/memory/patches/ and PATCH_INDEX.md; update CURRENT.md (fixed headings; run `python3 tools/check_memory_health.py` and keep it healthy — trim superseded text, the file is near its 10 KB limit), MEMORY.md, handoffs/CURRENT_HANDOFF.md, investigations/ACTIVE.md, the dated memory file, KNOWN_ISSUES.md (the link-drop block and the D-BASE-R3 defects), and the design note's status line. Never write IP addresses, ADB endpoints or device identifiers into any memory or evidence file. Keep ROMs, ISOs, BIOS and save files out of Git.
