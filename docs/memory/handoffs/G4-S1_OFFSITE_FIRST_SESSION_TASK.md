---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G4-S1 (session A, the user at the TV with a phone): the first off-site session. The onn on a phone hotspot, the Tailscale app on the onn, the hub at home; three PS1-STREAM `--remote` runs through G3's paired identity over the overlay, one reconnect, one LAN check. Finalized from `G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md` (G4-P1) and `G4_RUNBOOK_HOTSPOT.md`. Two parts: Part 1 launches, Part 2 writes the record. Measurement only; nothing adopted; nothing committed
---

# G4-S1 — the first off-site session

Read first: `G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md` (the §G4 list, the gates, the reported set — **this file's §1 is that draft's pre-registration, with the two additions marked**), `G4_RUNBOOK_HOTSPOT.md` (the user's steps), `G4_P1_…` (`tools/e1_remote.py`: arguments, preflight, the endpoint class and hash, `path.jsonl`, `client: not harvested`), `G3_S3_…` ("Hub host"; leave empty at home), `CL_B3_…` §W (the telemetry flag's cost), `G1_S2_…` (`companion.overlay --state`), E4-S2's constraint discipline (a drop-in, read back, removed at teardown).

**The setting, as the draft states it:** a phone hotspot substitutes for the travel router, the Tailscale app on the onn for the router's overlay (§G2 later). The hub at home on the Opal, wired, the companion on the seven adopted lines.

## 1. Pre-registration (Code writes it to `evidence/g4_s1_2026-10-16/g4_s1_preregistration.txt` and hashes it before the first run; the suite's `--prereg` points at it)

The draft's "Pre-registration" section verbatim — runs, the §G4 table, the three gates, the reported set, validity — with these two additions:

- **A1. The telemetry flag is on for the runs:** `e3_flag.conf` carries exactly `PRIVYHUB_WAN_TELEMETRY=1` (the `--remote` preflight allows it; G5-S1's `wan` classes are then reported per run). Written before the runs, read back (eight environ lines), **removed at teardown with `flags_absent` true** before the LAN check. `PRIVYHUB_WAN_ADAPTATION` stays absent (its first off-site run is G4-S2, as G5-S2 recorded).
- **A2. Hand observations are recorded as the user's report, not as readings:** audio heard, the game responding, Pause/Resume, Save/Load — one line each in the record, "the user reported …". Nothing perceptual is a gate (the three gates are the draft's).

Nothing else in the draft's pre-registration changes. The planning figure (10–11 Mbit/s outbound) is reported against, not required.

## 2. Part 1 — launch (Code, with the user at the TV)

Precondition: `tools/e3_state.py --check` ok on the seven lines; no `e3_flag.conf`; no game; one device paired; the G8-S1 unit collected (`systemctl --user status privyhub-g8-s1` → not found); `G4_P1_…`, `G3_S3_…` and `CL_B3_…` exist. Baseline HEAD named.

1. **The overlay sees the onn:** `python3 -m companion.overlay --state --provider tailscale` → `connected: true` and `path` `direct` or `relayed`. `tailscale status` → two devices online: write **only the count and the hub's own state** into the record (never the output). If `path` is `no-peer` or the count is not two: **stop**, tell the user "runbook steps 1–2 (Tailscale on the onn) are not done; reply 'resume' when they are", and exit.
2. **The pre-registration:** written (§1), sha256 beside it, `preregistration_hashed_at.txt`; the hashes of `tools/e1_suite.py`, `tools/e1_remote.py`, `companion/wan_telemetry.py` and `companion/overlay/` into `tools_at_preregistration_sha256.txt`.
3. **The flag:** the drop-in with `PRIVYHUB_WAN_TELEMETRY=1`, restart, environ read back = eight lines (seven + one); `--check` would refuse this environ — that is expected; record the read-back instead.
4. **Launch the remote row detached** (not a child of this session): `systemd-run --user --unit=privyhub-g4-s1 --collect -p WorkingDirectory=<repo> /usr/bin/python3 tools/e1_suite.py run --remote --out docs/memory/evidence/g4_s1_2026-10-16/runs --prereg docs/memory/evidence/g4_s1_2026-10-16/g4_s1_preregistration.txt --runs 3 --window 600 --gap 300 --wait 900`, its console to `g4_s1_2026-10-16/suite_console.log`. No `--adb` (adb over the overlay is not set up; `client: not harvested` is expected).
5. **Confirm the preflight passed:** within 60 s the console shows the idle gap, not a refusal. A refusal: write it to the launch record, remove the drop-in, restart, `flags_absent` true, exit, tell the user the refusal's line.
6. Write `evidence/G4_S1_LAUNCH_2026-10-16.md` (precondition, overlay path class, hash, launch time, the console's first lines, the unit's status) and `logs/g4_s1_launch_git_status.txt`; the redactor over them; **exit** and tell the user: "launched — start the PS1 game on the onn when you're ready (within 15 min)".

**The user's cues, by the TV, no terminal** (also given in chat):

- Run 1: start the PS1 game; play; Pause then Resume once; Save then Load once; the game **ends by itself** when the window closes (the suite tears it down).
- Wait 5 min after it ends, then start the game again for run 2; **at about 5 min in, turn the phone's hotspot off, count 10, turn it on**; the stream pauses, then resumes; play on until it ends by itself.
- Wait 5 min, start again for run 3; play until it ends by itself.
- Then runbook D (steps 15–18): Tailscale off on the onn, back on the home Wi-Fi, Hub host emptied, one PS1 session of ≥ 2 min by hand, BACK.
- Then "Code is done" → Part 2.

If a run's start fails ("not reached over the overlay"), the suite says so in its console; Part 2 reads it. The user needs no terminal during the runs.

## 3. Part 2 — the record (Code, after the user's "Code is done")

1. `systemctl --user status privyhub-g4-s1` → not found (collected); `suite_console.log` ended. Remove the drop-in, restart, `flags_absent` true, `--check` ok on the seven lines, no game, one device paired.
2. **`evidence/G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md`** in the draft's shape: (1) the setting and the substitution; (2) per run: validity (PLAYING over the overlay; void if the endpoint class is not overlay), the §G4 table item by item with its source, the three gates met or not; (3) the reported table: goodput, post-FEC and pre-FEC loss/min, resyncs, rendered, the overlay path (direct / relayed, and every change in `path.jsonl`), RTT, the `wan` classes per window, the measured wire rate against the planning figure (reported); (4) the reconnect in run 2: the pause's length, the path's behaviour, the recovery log's lines; (5) the LAN check: `logs/session_audit.jsonl`'s `token_issued` for it with `routing_evidence: lan`, and the user's report; (6) what failed and where — a run that never reached PLAYING, a refusal, a session loss — stated with the console's and the audit's lines. The hub's firewall on the tailnet interface remains unread (no `nft`): if setup timed out, name it as the first suspect, not as the cause.
3. `manifest.sha256`, `validity.json`, the redactor over `g4_s1_2026-10-16/` (the endpoint as class + hash only; the hotspot and the tailnet as placeholders; no address anywhere); `logs/g4_s1_git_status.txt`; ROADMAP §G4 status line ("first off-site session measured: <n> of 3 valid; see the record"); `KNOWN_ISSUES.md` for anything that failed; `CURRENT.md`'s state line and Next Action (the user's commit; G4-S2 as the draft frames it; the G8-S1 resume). Nothing adopted; nothing committed; exit.
