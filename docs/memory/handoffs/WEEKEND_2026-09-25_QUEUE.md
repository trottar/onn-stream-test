---
memory_schema: 1
as_of: 2026-09-25
status: WEEKEND QUEUE 2, 2026-09-25 onward — three handoffs in order, unattended (the user is away); authorized by the user 2026-09-25 ("Proceed")
---

# Weekend queue 2, 2026-09-25

Run in order, each recorded in `docs/memory/` before the next starts. Ask nothing. Each task carries its own read-first list, pre-registered rules and memory list; this file sets the order and the gates. Nobody will answer and nobody will play.

| # | handoff | needs | gate | approx. |
| --- | --- | --- | --- | --- |
| 1 | `C6-D1_SOURCE_ABSTRACTION_DESIGN_TASK.md` | files on disk | none; no host contention | 2 h |
| 2 | `C4-M1_FEC_MEASURED_ARM_TASK.md` | companion + client change on a comparison path, Android build, adb, six holds | step 0's simulation passes its bar; the codec unit tests pass before any build; the arm smoke passes before the night; the first hold ≥ 40 min after the last `session_ended` | 6 h |
| 3 | `D7-R1_LINUX_REGRESSION_TASK.md` | adb, the companion unit, existing probes | task 2's teardown complete: adopted APK reinstalled and its hash confirmed, override absent, profile adopted | 2 h |

**Rules across the queue.**

- **The adopted profile stays adopted.** No encoder flag, cap, cushion or redundancy change. Task 2's FEC scheme runs **only** under `PRIVYHUB_FEC_SCHEME` for its A holds and its smoke; the override is unset and confirmed absent in the manager and the companion's environ before task 3 and at the end. `any_override` is recorded at every PLAYING.
- **The adopted APK (`f31b1c18…8ae7`) is reinstalled at the end of task 2** and its hash confirmed before task 3 runs; if the reinstall fails, task 3 is NOT RUN and the record says the onn carries the arm APK.
- **Nothing acts on the stream**: no transitions, no controller in any mode but off (the shadow flag stays unset all queue long).
- Headless host, everything in tmux; companion through its unit only; MainPID owns 8765 before each session.
- **The onn** at its pinned adb port; `adb connect` once if `adb devices` is empty; if it still fails, tasks 2 and 3 are NOT RUN, task 1 still runs.
- **One thing on the host at a time.** Holds and passes never overlap.
- **Opal read-only. No `nft`.** Task 3's recovery row is cited, not re-run.
- **Stop rules are in the tasks** (task 2's step 0 and the header-gating check; task 3's two-retry limit). A failed step records and moves on; never more than two retries of a failing action.
- **Pre-registered rules are not tightened or loosened after seeing data.**
- **ROMs, saves, savestates, keys, logs stay out of git.** Task 3's scratch slot is removed at the end; the user's slots are hashed before and after.
- **Nothing is committed to git.**
- **Privacy as always**: no addresses, MACs, SSIDs, ADB endpoints, credentials or device identifiers in any memory or evidence file; journals redacted; `h2_prep_redact.py --check` on every text file written.
- **At the end**, `CURRENT.md` lists each task's classification and record in one line; Next Action reads: the user's `C3.L3a` session 4 and their reading of the pooled table; the user's adoption call on the FEC arm (if RECOVERS THE RESIDUAL); `C3.L4` live decision; C5 (needs a profile — the user's yes); D7's NEEDS USER rows; then C7/D8 checkpoint. `python3 tools/check_memory_health.py` healthy. Companion under systemd, profile adopted, adopted APK installed, stream at 7000, no game active, banner cleared, samplers stopped, TV as it is.
