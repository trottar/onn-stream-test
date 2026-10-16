---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — G-A1 + CL-B3, session A (the hardware), after session B's G3-S3 record exists. The user's three adoptions (2026-10-16, "yes to all three"): the overlay provider (`overlay.conf`), session identity v2 on the host (`session-identity.conf`), and the client's `identity_v2` on. Then CL-B3: G3-S3's APK installed as the CONFIRMED one, a 10-min LAN PS1-STREAM through the signed path on the SEVEN-line adopted state, a VOD play through the range server, and the G5-S1 WAN-telemetry live smoke behind its flag. Nothing else adopted; nothing committed
---

# G-A1 — the three adoptions; CL-B3 — the hardened APK on the LAN

**Precondition:** `evidence/G3_S3_HARDENING_AND_HUB_HOST_2026-10-16.md`
exists and its APK hash is recorded; else stop and say so. Read it,
`CL_B2_…` (the install and state-tool pattern), `E3_A3B_…` (an adoption
record's shape), `G1_S2_…` (the overlay object), `G5_S1_…` (the `wan`
object), `tools/e3_state.py`.

## 1. The adoptions (G-A1)

- Precondition: five lines, no flag, no game, the device paired
  (`paired_devices` 1), `--check` ok.
- Two drop-ins beside the five: `overlay.conf`
  (`Environment=PRIVYHUB_OVERLAY_PROVIDER=tailscale`) and
  `session-identity.conf` (`Environment=PRIVYHUB_SESSION_IDENTITY=v2`);
  `daemon-reload`, restart; the environment read back as **seven**
  `PRIVYHUB_*` lines; `tools/e3_state.py`'s `ADOPTED` list gains both
  names (a patch); `--check` passes; `/status` shows the `overlay`
  object (connected; path `no-peer` until a second device joins) and the
  session status `mode: v2`, `paired_devices: 1`, `legacy_unpaired_lan`
  true. The reverts written: delete the drop-in(s), `daemon-reload`,
  restart.
- **Adoption record:** `evidence/G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`
  + `g_a1_…/` (the drop-ins' text, env before/after, `--check`,
  `status` excerpts redacted, `redact_check.txt`).

## 2. CL-B3 — the hardened APK

- Install G3-S3's debug APK (`adb install -r`); the device secret and
  pairing must survive (`paired_devices` still 1 and the client still
  paired — if the secret did not survive, say so, re-open the pairing
  window and wait for the user to pair, up to 10 min); the state tools'
  CONFIRMED hash updated (a patch); `--check` passes on the seven-line
  state.
- `identity_v2` **on** in the client, persisted (the user flips it if it
  is a screen — say so and wait; confirm via the read-only `run-as` read
  CL-B2 used).
- **The run:** E1-PS1-STREAM ×1 at 10 min through the normal client
  flow on the seven-line state: the audit shows the signed setup, the
  token, the declared endpoints **and the port binding** (the
  stream-start port equal to the signed one), no legacy setup; host
  gates as CL-B2's (RetroArch ≥ 59.9, capture 60 ± 0.1, dup+drop ≤
  0.2/min; host CPU **reported with the ladder's rung range**, not
  gated — the CL-B2 bar lesson); the link reported.
- **The range server:** one VOD play from the onn for 60 s (the user
  starts it; say so and wait): the audit shows the media token used (or
  the header) on the LAN path, the play reaches the client (the
  suite's VOD row readings if the row is cheap to run, else the
  companion's log), no `legacy` refusal.
- **G5-S1 live smoke:** `e3_flag.conf` = `PRIVYHUB_WAN_TELEMETRY=1`,
  restart; one PS1-STREAM ×10 min; the `wan` object present on `/status`
  while PLAYING and in the session report, its eleven measures filled
  or marked "not carried", its class per window; the provider's cost
  (≤ 0.5 point of a core, ≤ 2 MB); then the flag removed, restart,
  `/status` byte for byte with the seven-line state; `flags_absent`.
- Final state: **seven adopted lines**, no `e3_flag.conf`, no game, the
  APK CONFIRMED (the new hash), the device paired, the client setting
  on.

## 3. The record

`evidence/CL_B3_HARDENED_APK_LAN_2026-10-16.md` + `cl_b3_…/` (the runs,
the audit excerpts with no address or token, the hashes, the `wan`
excerpt, `manifest.sha256`, `--check`, `validity.json`,
`redact_check.txt`); `patches/CL-B3_…md`; `logs/g_a1_git_status.txt`,
`logs/cl_b3_git_status.txt`; `docs/KNOWN_ISSUES.md`,
`CURRENT_HANDOFF.md`, the redactor, **`CURRENT.md` last** — Next Action
1: the user's commit; 2: **G4-S1, the first off-site session** (the
draft in `handoffs/G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md`, the
runbook in `G4_RUNBOOK_HOTSPOT.md`; the user's hand steps: the Tailscale
app on the onn, the Hub host set to the tailnet name, the phone
hotspot); 3: G5-S2.
