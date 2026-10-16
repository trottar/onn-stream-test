---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G4-P1 (overnight, session B): everything the first off-site session needs except the off-site itself. The suite learns a `--remote` mode (a PS1-STREAM row against a client reached over the overlay, through G3's signed setup and declared endpoints); the G4-S1 pre-registration is drafted with bars taken from existing records; the user's runbook for a phone-hotspot first test is written step by step. No stream tonight, no restart
---

# G4-P1 — the first off-site session, prepared

Read first: ROADMAP §G2 (the travel-router model — tonight's test
substitutes a phone hotspot and the Tailscale app on the onn, stated as
the substitution), §G4 (the minimum validation list and the ~10-11 Mbps
planning figure), §G5; `C5_M3_LOW_RUNG_SCREENING_…` (the low rungs: 720p/4000
passed transport at 5.0 Mbit/s wire; 720p/3000 and 540p/3500 did not);
`C5_CLOSE_…` §1 (wire rates); `tools/e1_suite.py` (the PS1-STREAM row,
the client's role in it, the sampler); `G3_S1_…` / `G3_S2_…` (declared
endpoints over the overlay: `endpoint-class-mismatch`, the overlay host
class); `G1_S2_…` (the provider's path state, `no-peer` until a second
device joins); `docs/REMOTE_TRUST.md`.

## 1. `tools/e1_suite.py --remote` (a patch; inert without the flag)

- The PS1-STREAM row, with: the client reached at its **declared overlay
  endpoint** (from the session setup, G3 — never typed into the suite,
  never written to a record: the suite logs "overlay" and the endpoint
  hash only); the host flag `PRIVYHUB_SESSION_IDENTITY=v2` and
  `PRIVYHUB_OVERLAY_PROVIDER=tailscale` required and read back; the
  provider's path (direct / relayed) sampled every 10 s into the run;
  G5-S1's `wan` object sampled with it if `PRIVYHUB_WAN_TELEMETRY=1`
  is set (optional: the row runs without it).
- The adb side: the sampler's device readings (RSSI, link, thermal,
  pauses) over **adb over the overlay** if adb is reachable that way;
  else the row runs without device readings and says so (`client:
  not harvested`) — the row must not fail for lack of adb.
- The window default 10 min for the first test; the E2 warm-up kept.
- Unit test: the argument parsing, the endpoint-hash logging, the row's
  preflight with the two flags absent → refuses with a clear line.

## 2. `handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md` (for Cowork to finalize)

- **The setting:** the onn on a phone hotspot (a different uplink from
  the home), the Tailscale app installed and logged into the same
  tailnet on the onn (the user's hand step; the ROADMAP's travel router
  comes later as G2 — stated), paired already (CL-B2), `identity_v2` on.
- **Pre-registration draft:** runs — PS1-STREAM `--remote` ×3 at 10 min
  (idle gap 5 min); the §G4 minimum list checked per run (authenticated
  setup, discovery/launch, video, audio, controller, pause/resume,
  save/load, end/teardown, reconnect once by toggling the hotspot for 10
  s, local behaviour unchanged when the overlay is absent — a LAN
  PS1-STREAM ×1 after, with the overlay down on the onn); **reported,
  not gated (the first look):** goodput, loss/min, resyncs, rendered,
  the path (direct / relayed), RTT if measured, the `wan` classes; the
  **only gates:** session setup succeeds through G3 over the overlay,
  the stream reaches PLAYING, the host side clean (RetroArch ≥ 59.9,
  capture 60 ± 0.1, dup+drop ≤ 0.2/min). The planning figure (10-11
  Mbps outbound) compared with the measured wire rate.
- **The record shape** and what G4-S2 would then gate.

## 3. The user's runbook (`docs/memory/handoffs/G4_RUNBOOK_HOTSPOT.md`)

Numbered, one action each, what the screen must show: install the
Tailscale app on the onn from the Play Store and sign in (same account
as the hub); confirm on the hub with `tailscale status` that a second
device is listed (don't paste it); put the onn on the phone's hotspot;
open PrivyHub; in its settings point it at the hub's **tailnet name**
(the app's host field — say exactly which screen; if the app has no
host field yet, say so: that is a G3-S3 client item and the draft lists
it as the blocker); start a PS1 game; then the suite's `--remote` row
from the hub. Each step's reply/screen stated; nothing identifying in
the runbook (placeholders).

## 4. The record

`evidence/G4_P1_OFFSITE_TEST_PREP_2026-10-16.md` + `g4_p1_2026-10-16/`
(the diff, the test output, `redact_check.txt`, `manifest.sha256`);
`patches/G4-P1_…md`; ROADMAP §G4 status; `logs/g4_p1_git_status.txt`.
Blockers found (an app host field, adb over the overlay, anything else)
listed first in the record. Then `SESSION_B_DONE_2026-10-16B.md`.
