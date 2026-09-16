---
memory_schema: 1
as_of: 2026-09-16
patch: D-087_LINUX_PS1_MULTITAP_CONFIG_PATH
durable_memory_updated: true
---

# D-087 Linux PS1 multitap Config path

Purpose: remove the Windows portable Config-directory assumption from Linux PS1
multitap core-options materialization.

Predecessor checkpoint: `e0a898bee2d9b6bf3bb3b4ca497f564324d11c95`

Production: `companion/games/emulator_manager.py`
Diagnostic: `tools/probe_ps1_multitap_config_path.py`

Intentionally unchanged: Android, PHI1, uinput, udev autoconfig, A8 mappings,
PS1 controller-profile selection, Port-1-only multitap semantics, A/V/network,
save/load/lifecycle.

Runtime status: development patch pending four-player acceptance.
