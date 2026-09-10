---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# PS1 Multitap Exact Source-Context Audit — 2026-09-10

Classification: `EXACT_POST_A8_SOURCE_CONTEXT_CAPTURED`.

Exact authoritative local hashes were re-confirmed for the post-A8 production tree. The current emulator manager has a project-local `controller_overrides.json` store keyed by stable game ID; `controller_profile()` reads only the `controller_profile` member, while `set_controller_profile()` currently replaces the whole per-game entry. Session config is generated per launch and the launch path still applies the selected PS1 libretro device explicitly only to users 1 and 2.

The active Beetle PSX HW core-options file is under the active RetroArch nightly config tree. Both `beetle_psx_hw_enable_multitap_port1` and `beetle_psx_hw_enable_multitap_port2` are explicitly disabled. The current manager has no core-options adapter.

Decision from this evidence: reuse the existing controller override store rather than create a parallel settings system. Add a generic `ps1_multitap` mode to per-game override entries, preserve unrelated entry fields when changing controller profile, and materialize a native RetroArch content-specific `.opt` from the current game/core option set. For a managed multitap launch, set `game_specific_options = "true"` in the generated session input override. Only multitap-enabled sessions expand the explicit PS1 `--device` assignment to users 1-4; ordinary PS1 launches preserve the previous users-1/2 behavior.

Crash Bash is the first validation record and receives `ps1_multitap: "port1"`. This is data/configuration of the generic mechanism, not title-specific emulator logic.
