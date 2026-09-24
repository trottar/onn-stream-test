---
memory_schema: 1
as_of: 2026-09-24
status: OVERNIGHT QUEUE, night of 2026-09-24/25 — one handoff, unattended; authorized by the user 2026-09-24
---

# Overnight queue, 2026-09-24/25

Run in order, each recorded in `docs/memory/` before the next starts. Ask nothing. Each task carries its own read-first list, classification rules and memory list; this file sets the order and the gates.

| # | handoff | needs | gate | approx. |
| --- | --- | --- | --- | --- |
| 1 | `C3-L3A-S1_TRANSITION_SOAK_TASK.md` | the onn paired, the companion under systemd, the PS1 reference title, `t2_sample.py` (host + onn + Opal read-only) | T0 smoke passes preflight headless; T1 starts ≥ 40 min after the last `session_ended` | 2 h 30 min including the cold wait |

**Rules across the night.**

- **The adopted profile stays adopted** (`any_override: false`, cap 90,000, cushion 12/17, redundancy 2/4, no `PRIVYHUB_*` set — confirmed in the companion's environ and `native-stream-status` before every session). No encoder flag changes. No companion, client or profile source change.
- **The probe is not a controller and stays that way.** Every transition fires from the probe's seeded schedule; nothing reads a condition and picks a bitrate. The only permitted probe change is a `--headless` flag if `printf '\n' |` fails in T0, recorded as a patch.
- The host is headless (`H2`): `DISPLAY=:0`; run everything from inside tmux. The companion is the systemd user unit `privyhub-companion`: restart with `systemctl --user restart`, never `kill` + `nohup`; the MainPID must own 8765 before each session.
- **The onn** at its pinned adb port. If `adb devices` is empty at the start, `adb connect` on that port **once**; if it still fails, record the task NOT RUN and stop.
- **Two things on the host disturb each other.** No other session, probe or fault injection runs tonight; the user does not play until the queue reports done.
- **The Opal is read-only over `ssh opal`** — `t2_sample.py` reads it; nothing writes to it.
- **No `nft`.**
- **If a session dies**, record what the logs show, mark that session INDETERMINATE, continue with the next; never retry a failing action more than twice. If T0 fails preflight headless and `--headless` does not fix it, run H1-H3 only (the no-transition band is still worth having), record the T arms NOT RUN, and say why.
- **Pre-registered rules are in the task; do not tighten or loosen them after seeing the data.** The band rule compares against five no-transition values on the direction that matters, never a single pair.
- **Nothing is committed to git.**
- **Privacy as always:** no addresses, MACs, SSIDs, ADB endpoints, credentials or device identifiers in any memory or evidence file; companion journals redacted; `h2_prep_redact.py --check` on every text file written.
- **At the end**, `CURRENT.md` lists the task's classification and record in one line; Next Action reads: the user's four `C3.L3a` rerun sessions (their play; nothing runs without them), then `C3.L4` under `C3.L2`'s `video_only_restart` constraint; still open and not blocking: max output gap, `host_link`, the thermal flag proposal, the controller `lost_packets` item. `python3 tools/check_memory_health.py` healthy. Leave the companion running under systemd, the stream at 7000, no game active, the banner cleared, the sampler stopped, and the TV as it is.
