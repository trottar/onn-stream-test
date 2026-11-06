---
memory_schema: 1
as_of: 2026-11-06
status: DRAFT (session B, queue N B44) — the G9 checkpoint against ROADMAP §G9's acceptance list. Nothing applied to ROADMAP, README or CURRENT (A applies it at the checkpoint, after HOME-3). Docs only; no code; nothing committed
---

# G9 — the remote foundation checkpoint, drafted

**Count: 9 MET · 3 DEFERRED (with reason and contract) · 2 OPEN** (local operation with the hub's overlay down never
scored; the clean checkpoint itself).

Every record cited was opened for this draft. Paths are under `docs/memory/evidence/` unless they say otherwise.

## 1. The acceptance list (ROADMAP §G9, verbatim) and where each stands

> Acceptance:
>
> - corrected trust topology documented;
> - overlay provider abstraction established;
> - first provider path validated;
> - travel-router trusted-LAN baseline validated;
> - source address separated from durable client/session identity;
> - application authentication/authorization validated;
> - real off-site onn PS1-and-below session validated;
> - Phase C telemetry/adaptation reused under WAN conditions;
> - adverse-network envelope documented;
> - handheld validated if representative hardware is available, otherwise
>   explicitly pending;
> - Steam/external-compute provider integrated or explicitly deferred with a
>   preserved provider contract;
> - ordinary household LAN remains outside the PrivyHub trust domain;
> - local operation remains functional without remote connectivity;
> - clean checkpoint/push.

| # | item | state | the evidence |
| --- | --- | --- | --- |
| 1 | corrected trust topology documented | **MET** | `docs/REMOTE_TRUST.md` §1-§3: the two topologies, the threat model, the fail-closed rules. Written in G1-S1 (`G1_S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_2026-10-15.md` §1), kept current by each adoption (§8a-§15). Decision D-059 (`decisions/DECISION_LOG.md`) is the source |
| 2 | overlay provider abstraction established | **MET** | `companion/overlay/`: the contract, `none`, `tailscale` (G1-S1, 17 tests). **Adopted** as line 6, `PRIVYHUB_OVERLAY_PROVIDER=tailscale` (`G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`). Tailscale is the first provider, not the contract (REMOTE_TRUST §4) |
| 3 | first provider path validated | **MET** | **Live smoke:** `G1_S2_OVERLAY_PROVIDER_LIVE_SMOKE_2026-10-16.md` (PASSED: `/status` `overlay`, +0.28 point of a core). **First play:** `G4_S1_OFFSITE_FIRST_SESSION_2026-10-16.md` (2 of 3 runs valid, PLAYING over the overlay; gates 1-2 met). **The path in use:** G4-S2..S4 and the trip (`TRIP_R2_FRIDAY_GAMEPLAY_2026-10-31.md`: every game session `direct`). |
| 4 | travel-router trusted-LAN baseline validated | **DEFERRED** (reason below; the contract preserved) | **Reason:** no travel router was bought or needed. The onn's own Tailscale app stood in for the router's overlay off-site, on a phone hotspot (`G4_S1_…` §1: "a phone hotspot standing in for §G2's travel router, with the Tailscale app on the onn") and on a friend's 5-GHz Wi-Fi (`G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md`; the trip). D-059: "Do not choose a permanent travel-router model yet." **The contract preserved:** ROADMAP §G2's required behaviours and REMOTE_TRUST §1 / §2's visited-network row stand unchanged. A router would take the overlay's place under the same provider contract (item 2). **The cost of the substitute:** the onn joins each visited network itself (the trip runbook's step B), which is what §G2 wanted to avoid |
| 5 | source address separated from durable client/session identity | **MET** | **The audit:** `g1_s1_2026-10-15/source_address_audit.md` (80 lines, each categorized). **The host:** `G3_S1_SESSION_IDENTITY_HOST_SIDE_2026-10-15.md` (declared endpoints, not the source; `legacy-lan` accepted only on the LAN, overlay / unknown refused). **The client:** `G3_S2_…`, and `G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md` (stream-start ports bound to the signed ones). **Adopted:** line 7 `PRIVYHUB_SESSION_IDENTITY=v2` (G-A1); the client's `identity_v2` on (CL-B3). **Live:** G4-S1's `token_issued` with `routing_evidence: overlay` and no `legacy_setup` all evening |
| 6 | application authentication/authorization validated | **MET** | **Built:** G3-S3 (per-session media token, the range server gated over the overlay, the permission set, failing closed). **Adopted:** G-A1 + CL-B3. **Live:** `CL_B3_HARDENED_APK_LAN_2026-10-16.md` (on the LAN), G4-S1 (overlay: `session_refused token-unknown` after a restart, then one retry and `token_issued`), and every off-site session since. sig_v 3 since CL-B4 |
| 7 | real off-site onn PS1-and-below session validated | **MET** | **The first fully valid run:** `G4_S3_OFFSITE_4000_OPUS_2026-10-19.md` (VALID 1 / 1, every host gate met, RetroArch's counter read). **Free play:** `G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` (100 min, 13 sessions). **The trip:** `TRIP_R2_FRIDAY_GAMEPLAY_2026-10-31.md` (36 sessions, ~3 h, 9 titles, 59.7-60.1 fps median; "overall ran very well, but a few massive issues"). **The fixes since, through HOME-2:** B32-B35 / B38-B39 (`HOME_1_…`, `HOME_2_HOLD_PADS_VOD_2026-11-03.md`: C1' / C2 / C3 / C4' met; G-A10). |
| 8 | Phase C telemetry/adaptation reused under WAN conditions | **MET** | **G5-S1** WAN telemetry (`G5_S1_WAN_TELEMETRY_CLASSIFICATION_2026-10-16.md`). **G5-S3** the remote ladder (`G5_S3_REMOTE_LADDER_2026-10-17.md`). **G5-S4** the cap (`G5_S4_REMOTE_RUNG_CAP_2026-10-17.md`). **G8-S2** the start rung. **All four adopted together** as line 13, `PRIVYHUB_REMOTE=1` (G-A9, `TRIP_PREP_2026-10-29.md`; B28's umbrella, acting only on a remote-class session; CL-B16 cell 2 at home over the overlay). In use on G4-S4 and the trip. **The step in place** adopted, line 14 (`G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`). **Not adopted:** G5-S2's rules, whose live smoke G5-S2-L never ran (§2) |
| 9 | adverse-network envelope documented | **MET** (two questions open, §2) | **The envelope:** `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` (18 / 22 cells valid; the four rate-cap cells never reached PLAYING). **The cap cells, G8-S2 / S3:** a 5000 start plays under cap-6000; cap-4500 stays `no_play`, as predicted (`G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md`). **The encoder's rate control:** G8-S4 / S5 (`G8_S5_CAP_CELL_ENCODER_RC_TIGHT_2026-10-19.md`). **The off-site gap distribution:** `WAN_R1_OFFSITE_GAP_DISTRIBUTION_2026-10-24.md`. **The remote RTT budget:** `B37_CONTROL_ECHO_BUDGET_2026-10-31.md`. The capability rows are in `docs/CAPABILITY_MODEL.md` §7 |
| 10 | handheld validated if representative hardware is available, otherwise explicitly pending | **DEFERRED — explicitly pending** | **No representative handheld exists in the project** (no record of one; CURRENT's open list: "the handheld (pending)"). ROADMAP §G6: "Absence of handheld hardware must not block the onn-based Phase G remote foundation." **The contract it would test:** the same Android client, the identity model (REMOTE_TRUST §5-§6), the lost-device row of the threat model (§2) |
| 11 | Steam/external-compute provider integrated or explicitly deferred with a preserved provider contract | **DEFERRED — with the contract** | **Not built;** no record touches it. CURRENT lists it "deferred". **The preserved contract:** ROADMAP §G7: PrivyHub owns discovery, readiness, library, permissions and session UX, with a direct provider-to-client media path allowed under "the same PrivyHub authorization/session boundary". G3's identity and permission set (REMOTE_TRUST §5, §8) is that boundary; a provider is one more permission-gated target. |
| 12 | ordinary household LAN remains outside the PrivyHub trust domain | **MET by design; not probed** | **The decision:** D-059 ("The home Opal is the PrivyHub network/trust domain. The ordinary household router/Wi-Fi is upstream connectivity only"). **The documents:** REMOTE_TRUST §1 / §2 (the household row: upstream only, never a PrivyHub service or a route into the overlay). **The production topology:** the hub wired into the Opal (`B2_HOST_ON_OPAL_2026-09-21.md`). **The overlay:** terminates on the hub (G1), not on the household router. **No record probes it from the household side;** A states this at the checkpoint (the Opal is read-only to B) |
| 13 | local operation remains functional without remote connectivity | **OPEN** (half shown) | **Shown:** LAN play with the onn off the overlay works with every remote line adopted. CL-B16 cell 3 (`CL_B16_REMOTE_UMBRELLA_AND_QUIET_GUARD_2026-10-29.md`: overlay path `no-peer`, the newest `token_issued` lan, valid) and HOME-1 / HOME-2's LAN cells. **Not scored:** the hub's own overlay absent. `handoffs/G4_RUNBOOK_HOTSPOT.md` step 18 ("local behaviour unchanged when the overlay is absent") has never been run (KNOWN_ISSUES' open index). One LAN session with the hub's Tailscale down closes it; that is the user's to do (no sudo for B) |
| 14 | clean checkpoint/push | **OPEN** — A / the user | **A must check:** `git status --short` prints nothing; queue N's work and HOME-3 committed by the user; ROADMAP §G9's status line and this draft applied; `tools/check_memory_health.py` passing; the push done by the user (the ZIP / commit boundary in AGENTS.md); `--check` ok on the adopted lines with the CONFIRMED APK |

## 2. What the G track leaves open for later (none blocks items 1-12)

- **The loss guard's return.** G-A8 (`PRIVYHUB_LOSS_GUARD=1`) is PREPARED and never applied. The guard has been out
  since TRIP-PREP; B27 / B29 are not in the confirmed APK. The guard / stall interaction is unsolved
  (`CL_B16_…` S1; KNOWN_ISSUES).
- **G-A6, shelved.** B23's WAN thresholds are built and off. Reopen only with a remote-path signal that today's
  thresholds misfire (`CL_B13_RESTART_FAST_AND_WAN_CLASS_2026-10-25.md`).
- **The WAN thresholds on a relayed path.** Every measured off-site play was `direct`; `relayed` appeared only around
  idle spans and departures (G4-S4 §5; TRIP-R2 §0 and §4). A relayed session's ladder, cap and recovery are
  unmeasured.
- **The adverse envelope's two questions:**
  - G8-S6, whether `tight` keeps a capped stream from going silent: QUEUED, never run;
  - G5-S2-L, the WAN rules' first live smoke: never run (`handoffs/QUEUE_2026-10-19N.md`).
- **Reconnect over the overlay.** There is candidate evidence (G-A4, G4-S4, the trip), but it needs a read
  (`DOCS_AUDIT_2026-11-02.md` §2.7).
- **The CONC row.** The guide grabs under a live stream (`docs/CAPABILITY_MODEL.md` §6, E4-S2's 400 %) were measured
  on the LAN only, never under a remote stream.
- **E5-S2 / E6, the user's calls.** The capability probe on a second machine, and the Prototype-2 / friend-alpha
  hardware (ROADMAP §E5 / §E6).
- **Queue N's own open cells.** They are not G9 acceptance items: VOD retry and the player prompt are product
  behaviour, not the remote foundation.
  - **The cells:** C5'' (the movie retry under `drop 45` and a companion restart), C6 (the player prompt), and the
    user's G-A13 and the prompt's default.
  - **Order:** HOME-3 runs them before the checkpoint, by the queue's order; they do not gate it. If C5'' is not met,
    G9 can still close with the VOD retry listed here.

## 3. For the README — what away-from-home play is today

PrivyHub can be played away from home. Take the onn, its remote and your controllers. Join the place's Wi-Fi (5 GHz if
it has it) and turn on Tailscale on the onn. Then set PrivyHub's Hub host to the hub's name. Your hub at home does all
the work and streams to the onn over an encrypted link that only your devices can join, and the onn still has to pair
with the hub before it gets anything. Away from home the stream starts a little softer and sharpens over the first few
minutes. The hub turns down the picture before it lets the game lag. A brief drop pauses the game and picks it up again
by itself. Two more protections are coming on by default once the next app version is confirmed at home: the screen-loss hold,
which keeps the session through a Home press, and stable player slots, which keep each pad on its player number. On Friday's trip three hours of PS1 and SNES play ran at a
full 60 frames per second. Expect a press to reach the game a little later than at home: about 15-25 ms on that trip.
There is no travel router yet, so the onn joins each place's Wi-Fi itself. At home nothing changes: the remote
features stay out of the way on the home network.
