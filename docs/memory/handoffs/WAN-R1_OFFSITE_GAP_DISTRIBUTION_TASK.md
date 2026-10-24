---
memory_schema: 1
as_of: 2026-10-24
status: TASK HANDOFF — WAN-R1 (session A, read-only, unattended, after G4-S4's record, the user away 17:00-21:30 EDT): across the four off-site sessions (G4-S1, G4-S2, G4-S3, G4-S4) the uplink-silence and output-gap distributions over the tailnet, per overlay path (direct / relayed), against the LAN's — the input for the stack's thresholds on a WAN path (H 950 and the 400-ms stall were derived on the LAN). Copies only; no run, no restart, no adb beyond `--check`. Nothing adopted; nothing committed
---

# WAN-R1 — what a WAN link's gaps look like

Read first: `G4_S4_OFFSITE_FREE_PLAY_2026-10-24.md` (just written: the false-hold count, the path), `G4_S1_…`, `G4_S2_…`, `G4_S3_…` (their dirs hold the control-gap logs, heartbeats, reports), `B6_INPUT_HOLD_TRIGGER_2026-10-22.md` (`gap_distribution.py`; how H 950 was derived from the LAN's distribution), `B9_…` (the 400-ms stall), `UX_R3_…` §1 (the hitch reader), `LINK_R1_…` and `G_A3_…` (the 5-GHz LAN baselines: 0 silences / 10 min).

- **Per off-site session and per overlay path class** (direct / relayed, from each session's overlay samples), from the copies in their evidence dirs: the uplink silences ≥ 250 ms per 10 min and B6's full distribution (the percentiles, the longest), the output gaps (the client's report spikes ≥ 50 / ≥ 80 / ≥ 200 ms per min), RTT per minute, the rung history beside them. The same for the LAN's 5-GHz windows (LINK-R1, G-A3, CL-B10 cell 1, CL-B11 cell 1, CL-B12 cell 1) as the other column.
- **Then, written plainly:** where a WAN path's silences sit against H 950 and the 400-ms stall — how many per 10 min would fire the hold, how many the stall signal, on each path class; G4-S4's actual false holds beside the prediction; and the H and stall values that would give ≤ 1 false fire per 10 min on each class (from the distribution, as B6 did), stated as numbers for B's design, **not changed here**.
- `evidence/WAN_R1_OFFSITE_GAP_DISTRIBUTION_2026-10-24.md` + `wan_r1_2026-10-24/` (the per-session tables, the scripts, `redact_check.txt`, `manifest.sha256`); `logs/wan_r1_git_status.txt`; `CURRENT.md` Next Action (the user's commit; B's WAN-threshold design as the next B item with these numbers). Exit.

No sudo, no nft, the Opal read-only, no adb beyond `--check`, no run, no restart, no addresses or identifiers (the tailnet and every endpoint as placeholders); nothing fetched, deleted or moved; nothing adopted; nothing committed.
