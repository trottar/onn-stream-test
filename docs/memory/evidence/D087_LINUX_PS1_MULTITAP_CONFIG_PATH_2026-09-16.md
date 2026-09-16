---
memory_schema: 1
as_of: 2026-09-16
status: diagnosed
classification: LINUX_PS1_MULTITAP_CONFIG_PATH_MISMATCH
---

# D-087 Linux PS1 multitap Config-path evidence

## Runtime symptom

Multitap-enabled game launch stopped before RetroArch:
`Beetle PSX HW core-options file is unavailable for multitap launch`

## Targeted Linux audit

Managed Config grep: no explicit `rgui_config_directory`.

Discovered active seed:
`~/.config/retroarch/config/Beetle PSX HW/Beetle PSX HW.opt`

Keys:
- `beetle_psx_hw_enable_multitap_port1 = "disabled"`
- `beetle_psx_hw_enable_multitap_port2 = "disabled"`

## Source mismatch

Current manager resolved:
`runtime["executable"].parent / "config" / "Beetle PSX HW"`
and required that path below the project root.

That is the historical Windows portable layout, not Linux AppImage's active
Config tree.

## Fix boundary

Host-aware Config-root resolution only. Preserve seed-copy semantics, atomic
per-game `.opt` install, Port-1 product ceiling, `game_specific_options`, users
1-4 device assignment, controller stack, A/V, and lifecycle.
