---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# PS1 Multitap/Core-Options Audit Evidence

The exact-local audit classified `CORE_OPTIONS_STORAGE_DISCOVERED_METADATA_UNVERIFIED`.

The current post-A8 source hashes are recorded in the raw evidence. `emulator_manager.py` contains no `core_options_path`, `game_specific_options`, `global_core_options`, or `max_players` handling.

RetroArch/Beetle PSX HW currently persists core options under the runtime config directory. Both discovered `Beetle PSX HW.opt` files explicitly set `beetle_psx_hw_enable_multitap_port1 = "disabled"` and port 2 disabled. The latest Crash Bash RetroArch log confirms the active nightly saved its core options to `runtime/emulators/retroarch-nightly-20260907/config/Beetle PSX HW/Beetle PSX HW.opt`.

The live Crash Bash catalog response exposed identity/name but did not expose `max_players`, so metadata was not verified by this probe. This does not contradict the runtime observation that Crash Bash Players 3/4 are greyed out while P1-P4 host routing is healthy.

Next step: inspect exact post-A8 source context around game records, controller overrides, session-config preparation, and launch. Then implement one session/game-specific multitap mechanism without changing global PS1 topology.
