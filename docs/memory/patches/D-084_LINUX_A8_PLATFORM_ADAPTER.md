---
memory_schema: 1
as_of: 2026-09-16
patch: D-084_LINUX_A8_PLATFORM_ADAPTER
durable_memory_updated: true
---

# D-084 Linux A8 platform adapter

Purpose: make the existing A8 named gameplay-profile runtime adapter portable
across Windows XInput and Linux PrivyHub uinput/udev without changing profile
storage or controller transport.

Predecessor checkpoint:
`728fdbadd6f7f610d551487bc645cd4642860729`

Production source changed:
- `companion/games/emulator_manager.py`

Diagnostic changed:
- `tools/probe_a8_2_input_adapter.py`

Documentation/memory changed:
- `docs/A8_INPUT_PROFILES.md`
- `docs/memory/CURRENT.md`
- `docs/memory/MEMORY.md`
- `docs/memory/handoffs/CURRENT_HANDOFF.md`
- `docs/memory/2026-09-16.md`
- D-084 evidence/patch records

Intentionally unchanged:
- Android source
- PHI1/XUSB transport
- `companion/native_session_io.py`
- Linux uinput capabilities/event generation
- project udev autoconfig
- Windows A8 numeric behavior
- emulator lifecycle
- video/audio/networking

Runtime status at packaging: development patch; onn gameplay validation pending.

## D-084R1 installer preflight correction

The first D-084 installer correctly failed before modification, but for the wrong
reason: its clean-tree gate used `git status --porcelain` and therefore treated
the intentionally untracked patch ZIP and `_patches/` extraction directory as
source changes.

R1 narrows that preflight exactly as intended:
- HEAD and expected predecessor blobs must still match;
- tracked working-tree changes still reject installation;
- staged changes still reject installation;
- unrelated untracked delivery/extraction artifacts do not block installation.

No production source transformation changed between D-084 and D-084R1.
