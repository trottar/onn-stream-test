---
memory_schema: 1
as_of: 2026-09-16
patch: D-085_LINUX_UDEV_HAT_MAPPING
durable_memory_updated: true
---

# D-085 Linux udev hat mapping

Purpose: correct the Linux ABS_HAT D-pad translation at the RetroArch udev
frontend.

Predecessor:
- Git HEAD `728fdbadd6f7f610d551487bc645cd4642860729`
- successful installed D-084R1 receipt required
- exact D-084R1 post-state SHA-256 values required
- exact original Git blobs required for all four D-076 autoconfig files

Production changes:
- `companion/games/emulator_manager.py`
- four `data/games/retroarch/autoconfig/udev/PrivyHub Virtual Gamepad P*.cfg`

Diagnostic update:
- `tools/probe_a8_2_input_adapter.py`

Intentionally unchanged:
- Android
- PHI1
- Linux uinput generation
- Windows controller backend
- analog axis indexes
- controller mode selection
- emulator lifecycle
- audio/video/networking

Runtime status at packaging: development patch; onn gameplay validation pending.
