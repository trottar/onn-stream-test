---
memory_schema: 1
as_of: 2026-11-03
---

# Active investigations — index

Active work is tracked in `docs/memory/CURRENT.md` and `docs/KNOWN_ISSUES.md`'s open index. This file is only an
index; it holds no live state. It stays at this path because an old September probe
(`tools/probe_b5_native_only_regression.py`) reads it.

The previous content of this file (Phase E as of 2026-10-10, Phase C and the D-BASE work, the 2026-09-18 open state)
is kept verbatim in `../history/ACTIVE_INVESTIGATIONS_THROUGH_2026-10-15.md`.

## Files still in `docs/memory/investigations/` (2026-11-03)

- `ACTIVE.md` — this index.
- `BASELINE_STREAM_HEALTH.md` — D-BASE baseline stream health: CLOSED 2026-09-23, MET.
- `C5_RESYNC_IDR_ACCEPTANCE_READ_2026-09-20.md` — C5 receiver resync / IDR-acceptance read: COMPLETE; its §2 second
  cost FALSIFIED (D-BASE-S2, 2026-09-21); §5's bounded fallback retired.
- `CLOSED.md` — the closed-investigations ledger (D4 controller parity, multiplayer, the D083 branch and others).
- `DEFERRED.md` — deferred / paused items; its Linux + Opal + onn UDP root-cause section is CLOSED for the old
  signature (D6-R1, 2026-09-24: not reproduced on the production path).
- `D_LINUX_UDP_EGRESS_2026-09-15.md` — Linux → onn UDP egress: PAUSED (its own status); see `DEFERRED.md` for the
  D6-R1 close of the old signature.
- `EXPRESSVPN_WINDOWS_BRIDGE_2026-09-16.md` — temporary Windows router / VPN forwarding: DEFERRED.
- `LINK_DROP_RECOVERY_DESIGN.md` — link-drop self-recovery design (D-BASE-R3 / R3a): IMPLEMENTED; its own front matter
  (2026-09-22) still reads "NOT yet RUNTIME VALIDATED"; `docs/ROADMAP.md` §0 records link-drop recovery validated on
  real loss (R3-R3d). Today's link-recovery stack is adopted line 10 (G-A4, `docs/REMOTE_TRUST.md` §11).
- `SEAMLESS_LOCAL_PLAY_TEST_BATTERY.md` — seamless local play battery: Group A run 2026-09-20; B2 INDETERMINATE
  (2026-09-21); B1, B3-B5 and Group C not authorized.

## Archived 2026-11-03

The 39 investigations archived on 2026-11-03 (the D5 EPG / guide / TV-state family, the C3 actuator family,
`ADB_STALE_CACHE_NATIVE_ERROR_2026-09-14`, `B1_DIAGNOSTICS_INVENTORY`, `D4_PS1_MULTITAP_LINUX_2026-09-16`) are listed
in `docs/memory/archive/INDEX.md`; the files are under `docs/memory/archive/memory/investigations/`.
