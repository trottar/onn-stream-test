---
memory_schema: 1
as_of: 2026-10-24
status: TASK HANDOFF — G4-S4 (session A, the user at a friend's house with the onn, ~2 h from ~14:30 EDT 2026-10-24): the first off-site FREE PLAY — no suite, no fixed window; the user plays whatever they like over the tailnet for up to 2 h while a detached driver holds the WAN lines and samples. The ten adopted lines (G-A4 just adopted — the stack's first WAN exposure, disclosed) plus the four per-run WAN lines of G4-S3 with the cap raised to 7000 (the friend's broadband, not a hotspot). Part 1 launches (the user types from the friend's house over SSH); Part 2 records (at home, after). Measurement only; nothing adopted; nothing committed
---

# G4-S4 — off-site free play at a friend's house

Read first: `G4_S3_OFFSITE_4000_OPUS_2026-10-19.md` (the last off-site: ~5.3 Mbit/s at 4000 with Opus; the choreography; what failed), `G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md` (7000 over the tailnet), `handoffs/G4-S3_OFFSITE_4000_OPUS_TASK.md` §2 (the detached driver's scaffolding — reuse it, minus the suite), `G4_RUNBOOK_HOTSPOT.md` (the hand steps; the friend's Wi-Fi stands in for the hotspot), `CL_B12_…` §5 (the stack's costs; H 950 was derived on the LAN — on a WAN path a ≥ 950-ms uplink silence that is not a drop would fire a false hold: **count them**), `UX_R3_…` §1 (the hitch reader).

**The stage is the user's message.** "launch" (or the read line alone) = Part 1. "Code is done" after they are home = Part 2. "stop" = touch STOP now.

## Hand steps (the user, at the friend's house, before "launch")

0. Power-cycle the onn (unplug, 10 s, plug); home screen.
1. The onn joins the friend's Wi-Fi — **the 5 GHz network** (the name often ends in 5G / 5GHz; if there is one name for both, the router's 5 GHz must be on; the PrivyHub notice is off, so nothing on screen will say).
2. Tailscale on the onn → Connect ("Connected").
3. PrivyHub → SETTINGS → Hub host = the hub's Tailscale machine name → Save (the catalog reloads).
4. Then the user types the launch line.

## Part 1 — launch (Code)

- Precondition: ten lines, `--check` host fields ok (adb is off-LAN: the client fields read not ok / MISMATCH, disclosed as G4-S1 §1, not a stop), no `e3_flag.conf`, no game, one device paired, no `privyhub-*` unit but the companion and `privyhub-link-n1`, HEAD named; the overlay check (`python3 -m companion.overlay --state --provider tailscale`: `connected` true, the path direct or relayed — stated — two devices by count; else stop and tell the user "steps 2-3 not done; reply 'launch' again").
- **Pre-registration hashed before the launch:** the four lines; the cap 2 h 30 min from the launch; what is reported (below); the reading: **playable or not is the user's word; the numbers are: hitch s / 10 min, silences ≥ 250 ms / 10 min, holds fired outside drops (false holds), state loads, the rung history, RTT, the overlay path and its changes, post-FEC loss, the tailnet tx rate.**
- **The driver** (unit `privyhub-g4-s4`, status `~/privyhub_g4_s4/status.txt`, STOP, the cap): writes `e3_flag.conf` = `PRIVYHUB_REMOTE_LADDER=1 PRIVYHUB_START_RUNG=floor PRIVYHUB_REMOTE_RUNG_CAP=7000 PRIVYHUB_WAN_TELEMETRY=1` (fourteen lines read back), restarts the companion, then **runs no suite**: every 10 s the tailnet interface's tx/rx bytes, every 60 s the overlay state (path, RTT if offered), every 60 s the companion's session state (PLAYING / idle, the title's class only), and copies the rotating logs (LOG_KEEP 3) into its dir every 5 min so nothing is lost; on STOP or the cap it removes the drop-in, restarts, reads `flags_absent`, ten lines. The restart at the end kills a running stream — the user is told to say "stop" only when done.
- `evidence/G4_S4_LAUNCH_2026-10-24.md`, `logs/g4_s4_launch_git_status.txt`, the redactor (the tailnet name, the friend's network, every endpoint as placeholders); **exit, telling the user: "launched — start any game from the onn within 15 min; play as long as you like; Pause/Resume and Save/Load once each at some point; say 'stop' when you are done, before you leave."** The reply must contain: ten lines, fourteen with the drop-in, the overlay path (direct / relayed), the unit, the cap time.

## When the user says "stop"

Touch `~/privyhub_g4_s4/STOP`; confirm the unit closed, `flags_absent`, ten lines; tell the user the session is closed and the onn can go home (runbook D: Tailscale → Disconnect on the onn; home Wi-Fi; Hub host back to the home value).

## Part 2 — the record (at home; "Code is done")

The unit collected; `--check` ok on ten (adb back on the LAN; the band 5 GHz read). `evidence/G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` + `g4_s4_2026-10-24/` in G4-S3's shape, for the whole play (per 10 min and per game session): the rung history and the clamps, goodput and the wire rate, RTT, the overlay path and its changes, post-/pre-FEC loss, rendered, stale, resyncs, pauses — **with the stack's rows: every `input_hold` / `state_saved` / `input_release` / stall pause, each tagged a real drop (the control gap ≥ 3 s or a dark span) or a false hold (the link alive on both sides), the count per 10 min, and what each cost the player** — hitch s and silences per 10 min (UX-R3 / B6), underruns, decoder spikes, the data per hour; the user's words verbatim in their own subsection; what failed and where. ROADMAP §G4 line; `KNOWN_ISSUES.md`; `CURRENT.md` Next Action (the user's commit; the false-hold count as the first WAN question for B — H on a WAN path; the direct / relayed finding; the reconnect-over-overlay test still pending). Nothing adopted; nothing committed.

No sudo, no nft, the Opal read-only, adb for state reads only (none off-LAN), no addresses or identifiers anywhere (the tailnet name, the friend's network and every endpoint as placeholders); nothing fetched, nothing deleted; ten lines and no `e3_flag.conf` after; nothing adopted; nothing committed.
