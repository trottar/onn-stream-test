---
memory_schema: 1
as_of: 2026-09-16
patch: D-087R1_LINUX_PS1_MULTITAP_METADATA_PATH
durable_memory_updated: true
---

# D-087R1 Linux PS1 multitap metadata path

Purpose: remove the remaining project-root assumption from Linux multitap
`options_file` metadata after D-087 correctly moved core options to the external
RetroArch Config tree.

Requires successful D-087 receipt and exact D-087 post-state hashes.

Production change:
- `companion/games/emulator_manager.py`

Diagnostic update:
- `tools/probe_ps1_multitap_config_path.py`

No core-option content, controller, A/V, network, or lifecycle changes.
