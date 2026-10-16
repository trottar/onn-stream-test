---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (plus the uncommitted G1-S1 / G3-S1 / G3-S2 / G5-S1 work and session A's CL-B2 work)
---

# G4-P1 — the first off-site session, prepared

**Classification: PREPARED; nothing run off-site.**

- `tools/e1_suite.py run --remote` is built: a new module, `tools/e1_remote.py`,
  reached through one guarded import. Its unit test passes 13 / 13.
- The G4-S1 pre-registration is drafted
  (`handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md`, not hashed).
- The user's runbook is written (`handoffs/G4_RUNBOOK_HOTSPOT.md`).
- No stream, no restart, no adb; nothing adopted.

## 0. Blockers, first

| # | blocker | status | where it was found |
| --- | --- | --- | --- |
| 1 | **CL-B2 not closed**: the onn is not yet paired. Over the overlay an unpaired client is refused (`legacy-overlay`) | **blocks G4-S1** until the user pairs by hand in the morning | the queue's status; G3-S1 §1.6 |
| 2 | **The companion's flags**: `--remote` needs `PRIVYHUB_SESSION_IDENTITY=v2` **and** `PRIVYHUB_OVERLAY_PROVIDER=tailscale`, read back. Tonight only the first is set (`e3_flag.conf`) | **blocks** until session A adds the overlay flag, through a drop-in and a restart. The preflight refuses with one line until then | `tools/e1_remote.py` preflight; the queue |
| 3 | **The Tailscale app on the onn**: whether the Play Store offers it on this device, whether inbound UDP to the onn's tailnet address reaches the PrivyHub app, whether MagicDNS resolves the hub's name | **unverified from the hub**; the runbook's steps 1-4 and 6 check it; if the app is missing, G4-S1 stops | runbook §A |
| 4 | **The hub's firewall on the tailnet interface** (8765/TCP; the controller's UDP input) | **unverified**: no `nft` in these sessions. The first suspect if setup times out | — |
| 5 | **adb over the overlay** | **not set up**; optional: the row runs without device readings and says `client: not harvested` | `tools/e1_remote.py` |
| 6 | **The app's host field** | **not a blocker**: the main screen's **SETTINGS** opens "PrivyHub Settings", whose field takes "an IP address or hostname" (`MainActivity.showCompanionSettings` / `normalizeHost`) | client source |
| 7 | **Calls not carrying the session header** (G3-S2's scope): `TvStateSyncClient`, `TvEpgRepository`, `DiagnosticsActivity` | **not a G4-S1 blocker** (TV and diagnostics are not on §G4's list). They are refused over the overlay; G3-S3 | G3-S2 record §1 |
| 8 | **The range server (port 8000: artwork, VOD) is not gated by G3** and answers whoever reaches it, the overlay included | **a trust finding, not a blocker**: artwork will load. G3-S3 should gate it or bind it to the LAN | `MainActivity` artwork URL; G3-S1 §1.5 ("vod has no companion route") |
| 9 | **The LAN check with the identity flags**: the suite's home row refuses any environ other than the adopted one, and `--remote` refuses a LAN client | the draft makes "local unchanged when the overlay is absent" **a hand check** (audit `token_issued` / `lan`) | `e1_suite.preflight` |

## 1. `tools/e1_suite.py run --remote` (a patch; inert without `--remote`)

- **`tools/e1_suite.py`**: predecessor `602d7696…`, which carries session
  A's CL-B2 `EXPECT_APK` line, untouched. After: `3def90ce…`. **One
  edit:** the first statement of `main()` is
  `if "--remote" in argv: from e1_remote import main_remote; return main_remote(argv, sys.modules[__name__])`.
  Without `--remote`, every path is today's (`g4_p1.diff`).
- **`tools/e1_remote.py`** (new):
  1. **arguments:** `--out`, `--prereg` (hash-checked as the home row
     does), `--runs` 3, `--window` 600, `--gap` 300, `--wait` 900, `--adb`;
  2. **preflight:** both host flags read back from the companion's environ,
     else `refusing: --remote needs the companion running with
     PRIVYHUB_SESSION_IDENTITY=v2 and PRIVYHUB_OVERLAY_PROVIDER=tailscale;
     not read back: …`; `PRIVYHUB_WAN_TELEMETRY=1` optional. Nothing set,
     nothing restarted;
  3. the host sampler (`--telemetry --title`), the idle gap;
  4. **waiting for the user's launch** on the onn (`--wait`);
  5. **the endpoint** from the client's control connections
     (`/proc/net/tcp`, `tcp6`, port 8765): its class (overlay range → remote)
     and a 12-hex hash. **The address is never written.** Not over the
     overlay → the run fails with "not reached over the overlay";
  6. the status poll and **`path.jsonl`**: `/status`'s `overlay` (connected,
     path, MTU, endpoint present + hash) and `wan` if present, every 10 s;
  7. the warm-up (90 s from PLAYING), then the window;
  8. teardown: the game stopped through the companion; the client's report
     over adb only with `--adb` and a device answering;
  9. the home row's own figures (`heartbeat_figures`, `telemetry_figures`,
     `poll_figures`, the sampler's summary) plus `path_figures`.
- **The endpoint is the observed control peer,** not the declared media
  host itself. G3 forces the declared host into the source's routing class,
  so "overlay" holds for both. The companion exposes no declared address,
  by design (C1's status privacy).

**Verification** (`tests_output.txt`): `python3 -m unittest tools/test_e1_remote.py -v`
→ **13 / 13**:

- the arguments: defaults, values, four refusals;
- the endpoint's classes and hashes from `/proc/net/tcp` text (v4, v6,
  v4-mapped, other ports ignored), with no address string, dotted or hex,
  in the output;
- the preflight: both flags absent, one absent, both present; `main` refusing
  without creating the run directory;
- a whole run against a fake suite: **the log and `summary.json` carry the
  hash and never the address**; a LAN client fails "not reached over the
  overlay" and the game is stopped;
- the suite's dispatch: the import guarded (AST), and `--remote` without
  `--prereg` refusing.

## 2. The G4-S1 draft (`handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md`)

- **Blockers first.**
- **The substitution** (a phone hotspot and the Tailscale app on the onn,
  for §G2's travel router).
- **The pre-registration draft:**
  - runs: `--remote` ×3 at 10 min with 5-min gaps; the hotspot toggled for
    10 s in run 2; the LAN check by hand afterwards;
  - **§G4's list per run**, each with how it is read;
  - **three gates only:**
    1. setup through G3 over the overlay;
    2. PLAYING;
    3. host-side clean (RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop
       ≤ 0.2 / min: E4-S4 / E4-S5's host clauses);
  - everything else **reported**, including the measured wire rate against
    §G4's 10-11 Mbps planning figure (E2-S1: 720p/7000 ≈ 11.6 Mbit/s on
    the wire; C5-M3: 720p/4000 at 5.0 Mbit/s).
- **The record shape**, and what G4-S2 would gate.

## 3. The runbook (`handoffs/G4_RUNBOOK_HOTSPOT.md`)

20 numbered steps, one action each, with the expected screen or terminal
line:

- **A:** the Tailscale app on the onn, signed in; `tailscale status` shows
  two devices; the overlay reads `direct` / `relayed`.
- **B:** SETTINGS → the host field → `<hub-tailnet-name>`; the identity
  line checked.
- **C:** the onn on `<hotspot-name>`; the hub runs `--remote`; the user
  starts PS1 when the terminal says so; Pause / Resume and Save / Load once
  per run; the hotspot toggle in run 2.
- **D:** back home, Tailscale off, the home host value restored, 2 minutes
  of play (the overlay-absent check).

Placeholders only.

## 4. Files; disclosures

- **`g4_p1_2026-10-16/`:** `baseline_commit.txt`,
  `git_status_at_start.txt`, `predecessor_sha256.txt`, `after_sha256.txt`,
  `g4_p1.diff`, `tests_output.txt`, `redact_check.txt`, `manifest.sha256`.
- **Patch:** `patches/G4-P1_E1_SUITE_REMOTE_ROW.md`.
- **ROADMAP:** the §G4 status line.
- **Git status:** `logs/g4_p1_git_status.txt`.
- **No off-site run** happened, nor any live check of the remote row: it
  needs the onn on another uplink and both host flags (blockers 1-2).
- The tests left temporary directories under the system temp directory,
  and `__pycache__/`. Nothing was deleted.
- No sudo, no nft, the Opal untouched; nothing fetched; no stream, no game,
  no adb, no restart. Not touched: `e3_flag.conf`, `paired_devices.json`,
  the session audit log, `cl_b2_2026-10-16/`, `companion/session_identity.py`.
