---
memory_schema: 1
as_of: 2026-09-16
status: runtime-validated
classification: LINUX_PS1_MULTITAP_FOUR_PLAYER_PARITY_CONFIRMED
---

# D-087/D-087R1 Linux PS1 multitap runtime validation

## Runtime acceptance

With PrivyHub Multitap enabled for Crash Bash on the Linux runtime:
- launch succeeded;
- Players 3 and 4 were available;
- four physical remotes/controllers each worked independently.

## Interpretation

The Linux migration now reproduces the previously validated Windows PS1 Port-1
multitap behavior.

Validated portability fixes:
- D-087 correctly resolves Linux RetroArch core-option storage through the
  XDG/user Config tree;
- D-087R1 correctly handles metadata for external Config-tree files without
  assuming they are under the project root.

The accepted end-to-end topology is:
`per-game multitap setting -> content-specific Beetle PSX HW .opt -> Port-1 multitap -> four RetroArch frontend ports -> four independent players`

## Scope

This evidence closes the dedicated Linux multitap regression. It does not by
itself complete every remaining D4 normal-use Games regression item.
