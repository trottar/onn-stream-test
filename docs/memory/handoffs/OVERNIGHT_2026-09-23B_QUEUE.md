---
memory_schema: 1
as_of: 2026-09-22
status: OVERNIGHT QUEUE, second night of 2026-09-22/23 — three handoffs in order, unattended; authorized by the user 2026-09-22
---

# Overnight queue, 2026-09-22/23 (second run)

Run in order, each recorded in `docs/memory/` before the next starts. Ask nothing. Each task carries its own read-first list, classification rule and memory list; this file sets the order and the gates.

| # | handoff | needs | gate | approx. |
| --- | --- | --- | --- | --- |
| 1 | `D-BASE-N05_CLOSE_TASK.md` | reads the user's N05 run directory | `N05/` non-empty; if empty, record NOT RUN and go on | 15 min |
| 2 | `D-BASE-R3C2_TASK.md` | companion + client change, Android build, seven adb-driven checks | the onn paired; the recovery copy's hashes verified before anything | 2 h 30 min |
| 3 | `H3_COMPANION_AUTOSTART_TASK.md` | read-only session facts, a design record | none; **installs nothing, enables nothing, no reboot** | 30 min |

**Rules across the night.**

- **The adopted profile stays adopted** (`any_override: false` confirmed before every hold). No encoder flag changes.
- The host is headless (`H2`): `DISPLAY=:0` for the companion; run everything from inside tmux. If the companion is not listening on 8765 at the start, start it per `TOOLS.md` and say so.
- **The onn** at its pinned adb port. If `adb devices` is empty at the start, `adb connect` on that port **once**; if it still fails, run task 1 and task 3 (neither needs the onn beyond task 1's files), record task 2 as NOT RUN, and stop.
- **`evidence/d_base_r3c_2026-09-22/recovery_copy/` is the only copy of the N150 save.** Hash-check it before and after task 2; never write into it.
- **No `nft`.** Task 1 only reads what the user ran.
- **If a session dies**, record what the logs show, classify INDETERMINATE for that task, and go to the next. Never retry a failing action more than twice.
- **Nothing is committed to git.**
- **Privacy as always:** no addresses, MACs, SSIDs, ADB endpoints, credentials or device identifiers in any memory or evidence file.
- **At the end**, `CURRENT.md` lists each task's classification and record in one line; Next Action reads: the user's H3 install decision, thermal thresholds, the +45 ms audio-cushion decision (`P8`), then the roadmap list. `python3 tools/check_memory_health.py` healthy. Leave the companion running (the user may play) and the TV as it is.
