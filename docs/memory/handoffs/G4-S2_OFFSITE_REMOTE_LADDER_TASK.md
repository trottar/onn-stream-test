---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G4-S2 (session A, the user at the TV with a phone): the second off-site session — the first with the remote ladder (G5-S3), the start rung (G8-S2) and the cap (G5-S4) live on a real remote path. Two 10-min PS1-STREAM `--remote` runs on the phone hotspot: run 1 capped at 4000 (the data-saver picture, the user's judgement), run 2 uncapped from a 4000 start (the climb and the ladder on the real path, rules on). No hotspot toggle this time. Part 1 launches, Part 2 records. Measurement only; nothing adopted; nothing committed
---

# G4-S2 — off-site with the remote ladder

Read first: `G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md` (the setting, the §G4 list, gate 3 not evaluable, run 1's 2,259 loss/min at 7000, the audit's `routing_evidence`, §9 the data arithmetic), `G4_P2_REMOTE_ROW_GATE3_2026-10-17.md` (gate 3 now recorded by the remote row), `G5_S3_…` (`path_class` remote → the 4000 rung), `G5_S4_…` (the cap), `G8_S2_…` (`START_RUNG=floor` → 4000 on a remote path; the climb: ~12 min to 7000 from 4000 on a clean link), `G8_S3_…` §3 (the encoder's per-second burstiness vs a cap), `G4-S1_OFFSITE_FIRST_SESSION_TASK.md` §2 (Part 1's steps and the user's cues — the same choreography), `G5_S3_LAN_SMOKE_…` (the three flags read back as ten lines).

**Why no toggle:** at home the onn falls back to the home Wi-Fi when the hotspot drops (G4-S1 §4), so the reconnect-over-overlay test cannot be run from the house. It stays open for a true off-site day.

## 1. Pre-registration (Code writes it to `evidence/g4_s2_2026-10-17/g4_s2_preregistration.txt`, hashes it before the first run)

- **Runs:** two E1-PS1-STREAM `--remote` runs, `--window 600 --gap 300 --wait 900`, E2's warm-up, no `--adb`. The companion's `e3_flag.conf` per run, written before the run, read back, removed at teardown with `flags_absent` true:
  - **run 1 (capped):** `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_REMOTE_RUNG_CAP=4000`, `PRIVYHUB_WAN_TELEMETRY=1` → the session starts and stays at 720p/4000 (the first decisions row: start rung 4000, source `floor`, `path_class` remote; every clamp row `source: remote_cap`);
  - **run 2 (uncapped, rules on):** `PRIVYHUB_REMOTE_LADDER=1`, `PRIVYHUB_START_RUNG=floor`, `PRIVYHUB_WAN_TELEMETRY=1`, `PRIVYHUB_WAN_ADAPTATION=1` → starts at 4000; the ladder's own increase rule and G5-S2's R5 (K = 36 clean windows on a remote path) decide the climb; R2/R3 may step it down.
  - The remote row's preflight (`tools/e1_remote.py`) allows the two adopted flags plus `WAN_TELEMETRY`; **if it refuses the G5-S3 / G5-S4 / G8-S2 / G5-S2 flags, Code patches the allow-list by one line (a patch, disclosed in the launch record, the row otherwise unchanged) — not a reason to stop.**
- **Validity:** PLAYING over the overlay (endpoint class `overlay`); a LAN-class run is void, replaced at most once.
- **Gates (host, now readable — G4-P2):** RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤ 0.2/min, `flags_absent` after. **Everything link-side reported:** the start rung and its source, the rung path and every acted transition with its reason, the clamps (run 1), the rules' suggestions by rule id (run 2), goodput, post-/pre-FEC loss/min, FEC recovered / unrecoverable, rendered, stale, resyncs, pauses, RTT, the overlay path (direct / relayed) and its changes, the `wan` class and windows, the hub's tailnet-interface tx rate (the wire rate at 4000, measured — the number G8-S3 §3 needs for the remote floor), the data per run from that rate.
- **Expected, written beforehand (reported as met / not met, not gated):** run 1 holds 4000 for the window with no clamp violated; run 2 starts at 4000 and, if the windows read clean, climbs one rung at a time (the first step at ~report 90); the wire rate at 4000 is near 4.65 Mbit/s (G8-S2's bench) — the measured value is the result.
- **The user's report, recorded as such:** the picture at 4000 in run 1 against what they remember of 7000 (G4-S1), and anything seen in run 2 as it climbed; Pause/Resume and Save/Load once per run. **Nothing perceptual is a gate.**
- **Comparisons:** run 1 and run 2 against G4-S1's run 1 and run 2 (7000 start, no remote ladder): loss, rendered, stale, the wire rate, the data per 10 min.

## 2. Part 1 — launch (Code), the user's hand steps first

**Hand steps (the user, before launching Code), as G4-S1's:** Tailscale on the onn → Connect; PrivyHub → SETTINGS → **Hub host** = the hub's Tailscale machine name → Save (catalog reloads); hotspot on; the onn joined to the hotspot; Tailscale still "Connected".

Code: precondition (seven lines, `--check` ok, no `e3_flag.conf`, no game, one device paired, no G8 units; HEAD named); the overlay check (`connected: true`, path direct or relayed, two devices — count only; else stop and tell the user "runbook steps 1–2 not done; reply 'resume'"); the pre-registration written and hashed with the hashes of `remote_ladder.py`, `remote_cap.py`, `start_rung.py`, `wan_adaptation.py`, `adaptive_bitrate_live.py`, `native_stream.py`, `tools/e1_remote.py` beside it; **the two runs as a detached driver** (the G8-S3 scaffolding: unit `privyhub-g4-s2`, status file `~/privyhub_g4_s2/status.txt`, STOP, cap 2026-10-18T02:00:00Z) that writes each run's drop-in, restarts, runs `e1_suite.py run --remote … --runs 1` with that run's `--out`, removes the drop-in, restarts, then waits the gap and repeats — **the user starts the game on the onn when the TV shows nothing; the game ends by itself**; confirm the first run's preflight passed (the idle gap in its console, not a refusal); `evidence/G4_S2_LAUNCH_2026-10-17.md`, `logs/g4_s2_launch_git_status.txt`, the redactor; **exit**, telling the user "launched — start the PS1 game within 15 min; when it ends by itself wait 5 min and start it again for run 2".

**The user's cues, by the TV:** run 1 — start the game within 15 min; play; Pause/Resume once; Save/Load once; it ends by itself after ~11 min. Wait 5 min. Run 2 — start the game again; play until it ends by itself. Then runbook D: Tailscale → Disconnect on the onn; home Wi-Fi; clear Hub host; hotspot off. Then "Code is done" → Part 2.

## 3. Part 2 — the record (Code, after the user's "Code is done")

The unit collected; `--check` ok on the seven lines; `evidence/G4_S2_OFFSITE_REMOTE_LADDER_2026-10-17.md` in G4-S1's shape plus: the start rung and the rung path per run; the clamps; the rules' rows; the measured wire rate at 4000 and the data per run; gate 3 read for the first time off-site; the comparison with G4-S1; the user's report in its own subsection; what failed and where. `manifest.sha256`, `validity.json`, the redactor (the endpoint as class + hash only; the hotspot and tailnet as placeholders); `logs/g4_s2_git_status.txt`; ROADMAP §G4/§G5 lines; `KNOWN_ISSUES.md` for anything that failed; `CURRENT.md`: Next Action (the user's commit; G8-S4 — the encoder's rate-control headroom from session B — pending on the stream; the reconnect test pending a true off-site day). Nothing adopted; nothing committed.

No sudo (systemd --user is not sudo), no nft, the Opal read-only, no adb beyond reading state, no addresses or identifiers anywhere; nothing fetched, nothing deleted; nothing adopted; nothing committed.
