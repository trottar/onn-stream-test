---
memory_schema: 1
as_of: 2026-09-24
status: WEEKEND QUEUE, 2026-09-24 onward — five handoffs in order, unattended (the user is away); authorized by the user 2026-09-24
---

# Weekend queue, 2026-09-24/25

Run in order, each recorded in `docs/memory/` before the next starts. Ask nothing. Each task carries its own read-first list, pre-registered rules and memory list; this file sets the order and the gates. The user is away for the weekend: no one will answer, and no one will play.

| # | handoff | needs | gate | approx. |
| --- | --- | --- | --- | --- |
| 1 | `C3-L3A-R3_TASK.md` | files on disk only | none | 30 min |
| 2 | `C4-D1_ADAPTIVE_FEC_EVIDENCE_TASK.md` | files on disk only | none | 1 h 30 min |
| 3 | `CTRL-L1_CONTROLLER_LOSS_LOCATION_TASK.md` | the onn paired, companion under systemd, `tcpdump` on the host, `t2_sample.py` | the first hold starts ≥ 40 min after the last `session_ended` (cold) | 2 h |
| 4 | `C3-L4-S1_SHADOW_CONTROLLER_TASK.md` | a companion change (flag default off), unit tests, then four holds | unit tests all pass before the companion is restarted with the flag; the cold hold starts ≥ 40 min after task 3's last `session_ended` | 4 h |
| 5 | `D6-R1_UDP_SUITE_REPLAY_TASK.md` | the preserved suite, the onn, Opal read-only | stream inactive; the `B2` topology gate passes | 1 h 30 min |

**Rules across the queue.**

- **The adopted profile stays adopted** (`any_override: false`, cap 90,000, cushion 12/17, redundancy 2/4, no `PRIVYHUB_*` except task 4's `PRIVYHUB_ADAPTIVE_BITRATE_MODE=shadow` during its holds, **unset at its end** and confirmed absent in the companion's environ). No encoder flag changes. No client change. No probe change.
- **Nothing acts on the stream.** Task 4's controller is shadow only; the word `live` is not an accepted mode. No transitions fire in any task (task 3 and 4 holds are plain; task 5 runs with the stream inactive).
- The host is headless (`H2`), everything from inside tmux; the companion is the systemd user unit — `systemctl --user restart`, never `kill` + `nohup`; MainPID owns 8765 before each hold.
- **The onn** at its pinned adb port; if `adb devices` is empty at the start of a task, `adb connect` once; if it still fails, record that task NOT RUN and go on (tasks 1 and 2 need no onn).
- **One thing on the host at a time.** Holds never overlap; task 5 starts only after task 4's teardown.
- **The Opal is read-only.** **No `nft`.** `tcpdump` in task 3 is on the host only, headers only, the pcap deleted after the sequence extract.
- **If a hold dies**, record what the logs show, mark it INDETERMINATE, continue; never retry a failing action more than twice. If task 4's unit tests fail, do not restart the companion with the flag: record the failures, leave the flag off, and go to task 5.
- **Pre-registered rules are in the tasks; do not tighten or loosen them after seeing data.**
- **Nothing is committed to git.**
- **Privacy as always:** no addresses, MACs, SSIDs, ADB endpoints, credentials or device identifiers in any memory or evidence file; journals and suite outputs redacted; `h2_prep_redact.py --check` on every text file written.
- **At the end**, `CURRENT.md` lists each task's classification and record in one line; Next Action reads: the user's `C3.L3a` session 4 and their reading of the pooled table; then `C3.L4` live-mode decision (gated on that reading); C4 per its decision record; D6 per its classification; open and not blocking: max output gap, `host_link`, the thermal flag proposal, the controller item as task 3 left it, the client body-POST follow-up. `python3 tools/check_memory_health.py` healthy. Leave the companion running under systemd with the flag unset, the stream at 7000, no game active, the banner cleared, the samplers stopped, and the TV as it is.
