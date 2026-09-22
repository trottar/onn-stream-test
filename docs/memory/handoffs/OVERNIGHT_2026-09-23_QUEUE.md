---
memory_schema: 1
as_of: 2026-09-22
status: OVERNIGHT QUEUE for the night of 2026-09-22/23 — two handoffs in order, unattended; authorized by the user 2026-09-22
---

# Overnight queue, 2026-09-22/23

Run in order, each recorded in `docs/memory/` before the next starts. Ask nothing. Each task carries its own read-first list, classification rule and memory list; this file sets the order and the gates.

| # | handoff | needs | gate | approx. |
| --- | --- | --- | --- | --- |
| 1 | `D-BASE-R3C_TASK.md` | host-only probe, then one companion+client change and five adb-driven checks | none; Part 2 is gated on Part 1 inside the task | 2 h |
| 2 | `D-BASE-P8_TASK.md` | one diagnostic client build, three 20-min sessions | R3c recorded and the host idle; the onn paired | 1 h 30 min |

**Rules across the night.**

- **The adopted profile stays adopted** (`any_override: false` confirmed before every hold). No encoder flag changes tonight.
- **If the host is headless by the time this runs** (H2 done), nothing changes: the companion needs `DISPLAY=:0` and nothing else (H1-VERIFY §3); `x11grab` captures the managed window whether or not a monitor is attached. If H2 is not done, the monitor is still attached and nothing here assumes otherwise.
- **The onn** is reached at its fixed adb port (H1-VERIFY §5). If `adb devices` is empty at the start, try `adb connect` on that port **once**; if it still fails, run R3c Part 1 (host-only), record R3c Part 2 and P8 as NOT RUN — the onn was unreachable, and stop.
- **The N150 recovery state** is the only copy of its kind; R3c copies it under evidence/ before anything touches it and leaves no recovery file in the states directory at the end.
- **If a session dies**, record what the logs show, classify INDETERMINATE for that task, and go to the next. Never retry a failing action more than twice.
- **Nothing is committed to git.**
- **Privacy as always:** no addresses, MACs, SSIDs, ADB endpoints, credentials or device identifiers in any memory or evidence file.
- **At the end**, CURRENT.md lists each task's classification and record in one line, and the Next Action reads: H2 headless cutover if not yet done (user's word), else E30/N05/N15b by hand when the user has the time, then whatever R3c and P8 left open. `python3 tools/check_memory_health.py` healthy.
