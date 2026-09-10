---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Decision Log

| ID | Date | Status | Decision | Evidence / rationale |
| --- | --- | --- | --- | --- |
| D-001 | 2026-08-25 | Active | Keep PrivyHub local-first with IoT clients isolated from the trusted host network. | Core project goal and threat-model direction. |
| D-002 | 2026-08-26 | Active | Separate control and media planes; use live request-derived client endpoint rather than a second hard-coded client address. | Proven prototype architecture and privacy preference. |
| D-003 | 2026-09-07 | Deferred | Do not tune product buffering around the Prototype 1 UDP burst/gap/duplication pathology; replay diagnostics on representative Linux/network hardware. | Bidirectional synthetic and production evidence localized transformation outside normal application pacing. |
| D-004 | 2026-09-09 | Active | A4 audio lifecycle uses normal Games shutdown and crash-safe session-volume recovery; do not create parallel shutdown logic. | Runtime validation of TV audio, PC duplicate suppression, helper restoration. |
| D-005 | 2026-09-09 | Active | A8 gameplay mapping belongs after canonical PHI1/ViGEm semantics and uses session-only RetroArch overrides. | Boundary probes and gameplay validation. |
| D-006 | 2026-09-10 | Active | `25e9a14` is the immutable pre-four-player baseline; four-player extension precedes A9. | Clean checkpoint and user direction. |
| D-007 | 2026-09-10 | Active / transport-enumeration runtime validated | Preserve PHI1 v1/36-byte format for the four-player extension; generalize the canonical player-count/state layer to four before touching A8 P3/P4 mapping. | Exact-local audit found no packet-format blocker; base slots, real Android assignment, and fresh RetroArch ports 1-4 are now runtime validated without XInput fallback. A8/gameplay validation remains. |
| D-008 | 2026-09-10 | Active | `docs/memory` is the durable project memory/communication layer; old docs remain evidence but newer status must carry freshness/provenance. | Documentation audit found stale top-level status mixed with newer runtime evidence. |
| D-009 | 2026-09-10 | Active / development patch | Keep input-profile schema 1 while expanding A8 supported players from P1/P2 to P1-P4; treat missing legacy P3/P4 maps as default autoconfiguration and derive Android editor players from companion capabilities. | Backend normalization/generation already iterates the player tuple, so this is the narrowest backward-compatible extension and avoids resetting existing user profiles. |
| D-010 | 2026-09-10 | Active / development patch | Reuse the existing per-game controller override store for PS1 multitap topology and apply it through RetroArch native content-specific core-option files; do not enable multitap globally. | Four-player host routing is proven, active Beetle options explicitly disable both multitap ports, and native `.opt` overrides isolate accessory topology per game while preserving other core settings. |

### D-008 — Roll back first PS1 multitap patch for causal isolation

**Status:** Active diagnostic decision (2026-09-10)

The first game-specific multitap patch made Crash Bash expose four human players but immediately coincided with loss of physical P2-P4 input/controller connectivity during the active game stream. Controllers are charged. Restore the exact pre-patch `emulator_manager.py` and `controller_overrides.json` from the install backup and remove the generated Crash Bash `.opt`; then repeat the four-controller assignment probe. Do not make another production multitap change until that comparison is known.

### D-009 — Re-enable PS1 multitap; separate controller-connectivity investigation

**Status:** Active (2026-09-10)

The exact rollback removed multitap but P4 still failed at the physical Android assignment boundary while P1-P3 remained clean. This weakens D-008's causal suspicion of the multitap implementation. Reapply the same game-specific Crash Bash Port-1 multitap implementation and continue the controller-connectivity investigation independently, beginning with a different physical controller.

### D-009 — Accept game-specific PS1 multitap and separate controller-specific dropout

**Status:** Accepted (2026-09-10)

The exact rollback did not restore P4, while a replacement controller restored exact P1-P4 assignment with the same multitap implementation re-enabled. Final Crash Bash four-player gameplay then passed. Therefore keep game-specific Port-1 multitap and do not treat the earlier dropout as a software regression. Preserve the dropout as a hardware/pairing/transient observation and reopen only on representative reproduction.

### D-009 — PS1 multitap is a Port-1-only On/Off per-game flag

**Status:** Accepted 2026-09-10.

PrivyHub targets a maximum of four local players. Do not expose Port 2 or Both in the product. `Multitap: On` maps to Beetle PSX HW Port 1 enabled and Port 2 disabled. Metadata/checker output is recommendation-only; unknown or unconfigured games remain Off.

### D-009 — PS1 multitap is manual On/Off, Port 1 only

**Status:** Accepted (2026-09-10)

PrivyHub supports at most four local players. Expose only `Multitap: On/Off` for PS1 games. On maps to Beetle PSX HW Port 1; Port 2 is always disabled and Port 2/Both are rejected as product modes. Do not auto-enable from current `max_players` metadata because the live 80-game PS1 audit identified zero candidates, including CTR and Crash Bash.

### D-010 — Persist wireless ADB recovery in the build/install tool

**Status:** Accepted (2026-09-10)

Wireless-debugging pairing can remain intact while the ONN disappears from both
`adb devices` and ADB mDNS discovery. `build_install_onn.ps1` therefore owns
bounded recovery.

A successful target is cached privately under LocalAppData and never logged.
The final human action, only after automatic recovery is exhausted, is toggling
Wireless debugging Off/On. Pairing is preserved and no address is requested.

### D-010 validation update — wireless ADB recovery

**Runtime status:** Validated (2026-09-10)

The post-patch ADB audit returned `ADB_TARGET_ALREADY_ONLINE` and measured one
online transport plus recovered TLS-connect discovery. The cached-target/mDNS/
reconnect recovery strategy remains accepted and is now runtime validated.

### D-009 validation update — manual PS1 Multitap On/Off

**Runtime status:** Validated (2026-09-10)

CTR joined Crash Bash as a representative four-player PS1 runtime success.
Port 1 was enabled, Port 2 disabled, Players 3/4 exposed, and all four
controllers independent. Manual On/Off remains authoritative; metadata auto
recommendation remains deferred.

### D-011 — A9 is coverage-aware; no-fixture systems are skipped, not faked

**Status:** Accepted (2026-09-10)

A regression prompt is valid only when a real game session exists. If an
emulator family has zero installed game entries, A9 records
`SKIPPED_NO_LOCAL_FIXTURE` and does not ask gameplay questions. This skip may
coexist with a Phase A checkpoint, but the skipped family remains explicitly
not runtime validated until a real fixture is added.

### D-012 — Durable memory in Git; raw runtime evidence local; checkpoint snapshots committed

**Status:** Accepted (2026-09-10)

Keep `docs/memory/` versioned because it is the durable development bridge.
Keep `docs/memory/evidence/raw/` local and ignored. At major checkpoints,
produce one sanitized compressed evidence snapshot with a machine-readable
manifest. The snapshot is immutable checkpoint evidence, not a general runtime
data store.

Do not use Git/Git LFS as PrivyHub user/runtime storage.
