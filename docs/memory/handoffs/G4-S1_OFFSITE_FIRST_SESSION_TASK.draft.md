---
memory_schema: 1
as_of: 2026-10-16
status: DRAFT (G4-P1, session B, overnight) — for Cowork to finalize with the user. G4-S1, the first off-site session: the onn on a phone hotspot, reached over the overlay, through G3's paired identity. The pre-registration below is a draft; it is hashed only when finalized, before any run. Nothing here has run
---

# G4-S1 — the first off-site session (DRAFT)

**Blockers first** (the record `G4_P1_OFFSITE_TEST_PREP_2026-10-16.md`
§0 lists them with their sources):

1. **CL-B2 must be closed:** the onn paired by hand on the LAN, with
   `identity_v2` on. Over the overlay an unpaired client is refused:
   `legacy-overlay` (G3-S1).
2. **The companion must run with both flags,** `PRIVYHUB_SESSION_IDENTITY=v2`
   and `PRIVYHUB_OVERLAY_PROVIDER=tailscale`. Optionally also
   `PRIVYHUB_WAN_TELEMETRY=1`. Each goes through a drop-in and a restart
   (session A's step). The suite's `--remote` preflight refuses otherwise.
3. **The Tailscale app on the onn,** signed into the same tailnet: the
   user's hand step. **Not verified from the hub:** that the app exists for
   this onn, that inbound UDP to the onn's tailnet address reaches the
   PrivyHub app, and that MagicDNS resolves the hub's name on the onn.
4. **The hub's firewall on the tailnet interface** (control port 8765 TCP;
   the controller's UDP input) is **not read** (no `nft` in these
   sessions). If the first run's setup times out, this is the first
   suspect.

## The setting (stated as a substitution)

- **The ROADMAP's model** (§G2): a travel router with a portable trusted
  LAN, and the overlay on the router.
- **This first test substitutes:**
  - **a phone hotspot** for the travel router (a different uplink from
    the home Opal);
  - **the Tailscale app on the onn** for the router's overlay.

  G2 (the router) comes later.
- The hub stays at home on the Opal, wired, with the companion as adopted
  plus the two flags. The onn is paired (CL-B2), with `identity_v2` on,
  and its host field set to the hub's tailnet name.

## Pre-registration (draft; hash before the first run)

**Runs.**

- `python3 tools/e1_suite.py run --remote --out <dir> --prereg <this file> --runs 3 --window 600 --gap 300`:
  three PS1-STREAM `--remote` runs at 10 min, 5-min idle gaps, the E2
  warm-up (90 s from PLAYING). **The user starts the PS1 game on the onn**
  when the suite says "waiting".
- **After them, one LAN check, overlay absent:** the Tailscale app off on
  the onn, the onn back on the home Wi-Fi, one PS1 session of ≥ 2 min by
  hand.

**§G4's minimum list, checked per run:**

| item | how it is checked | source of the reading |
| --- | --- | --- |
| authenticated control / session setup | a `token_issued` line in `logs/session_audit.jsonl` with `routing_evidence: overlay` at the run's start; no `legacy_setup` for it | G3-S1 audit |
| Games discovery / launch | the games list loads on the onn; the launch succeeds | the user's observation + `games_status` |
| video | PLAYING; rendered fps reported | telemetry |
| process audio | heard on the onn; audio counters in the heartbeat | the user + heartbeat |
| controller input | the game responds; no controller-silence pause | the user + recovery log |
| Pause / Resume | the user pauses and resumes once | recovery / games status |
| Save / Load | one save-state and one load, by hand | games plugin |
| End / teardown | BACK ends the session; no RetroArch or encoder left | the suite's teardown |
| reconnect / recovery | **run 2 only:** the hotspot toggled off for 10 s at ~5 min, then on; the session resumes (a recovery pause, then a resume) | recovery log, `path.jsonl` |
| local behaviour unchanged when the overlay is absent | the LAN check: setup over the LAN (`token_issued` with `routing_evidence: lan`), PLAYING, the same game playable | audit + the user |

**The only gates** (the first look; everything else is reported):

1. **The session is set up through G3 over the overlay:** `token_issued`,
   overlay; the suite's endpoint class is `overlay`.
2. **The stream reaches PLAYING** within the suite's `--wait`.
3. **The host side is clean:** RetroArch ≥ 59.9 fps, capture 60 ± 0.1,
   encoder dup+drop ≤ 0.2 / min (the host-side clauses E4-S4 / E4-S5 used;
   E4-S1's reference).

**Reported, not gated:**

- delivered goodput (kbit/s);
- post-FEC loss / min (and pre-FEC, from the heartbeat);
- resyncs;
- rendered fps;
- the overlay path (direct / relayed, `path.jsonl`) and its changes;
- RTT (`latency.control_round_trip_ms`, the client's echo);
- G5-S1's `wan` classes per window, if the flag is set;
- the client's device readings, **only if adb reaches the onn over the
  overlay** (else `client: not harvested`);
- **the measured wire rate** against ROADMAP §G4's planning figure of
  10-11 Mbps outbound:
  - the hub's tailnet-interface tx rate in the sampler;
  - at home, 720p/7000 measured 1.45 MB/s ≈ 11.6 Mbit/s on the wire
    (E2-S1 §6);
  - C5-M3's 720p/4000 passed transport at 5.0 Mbit/s on the wire.

  **Not turned into a requirement** (§G4: "Measure the real envelope").

**Validity.**

- A run is valid if it reached PLAYING over the overlay.
- A run whose client turns out to be on the LAN (endpoint class not
  `overlay`) is **void**, not failed.
- No run is replaced except for a void, at most once.

## The record (shape)

`evidence/G4_S1_OFFSITE_FIRST_SESSION_<date>.md`:

1. the setting and the substitution;
2. per run, the §G4 list and the three gates;
3. the reported table (goodput, loss, pre-FEC, resyncs, rendered, path,
   RTT, wan classes, wire rate vs the planning figure);
4. the reconnect (run 2): the pause length and how the path behaved;
5. the LAN check;
6. what failed and where.

No addresses: the endpoint as "overlay" plus its hash; the hotspot and the
tailnet as placeholders.

## What G4-S2 would gate (after this first look)

- **The D-BASE table on the remote path**, at the remote ladder's level.
  `docs/WAN_ADAPTATION_RULES.md` R3.2: 720p/4000 is the lowest screened
  rung.
- The reconnect gated: a hotspot toggle resumes within the recovery bound.
- The §G4 list gated item by item, for NES / SNES / Genesis / PS1.
