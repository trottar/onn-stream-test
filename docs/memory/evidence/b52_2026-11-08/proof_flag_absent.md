# B52 — `PRIVYHUB_PS2` absent = today, hunk by hunk

| hunk | without the line |
| --- | --- |
| `ps2_session.settings_for`: `[EmuCore/Speedhacks] vuThread = false` | the module is imported only under the flag (B49's guards) |
| `ps2_session.Session` additions (`grab`, `log_path`, `elf_started`, `wait_elf`, `picture`, `check_picture`), `grab_window` | the same module |
| `EmulatorManager._pcsx2_load_state` (the ELF hold, the picture check, the answer) | reached only for `_launch_kind == "pcsx2"`, set only by `_launch_pcsx2` (the flag); a RetroArch load is untouched (B51's `Ps1Untouched` test, the whole host regression as the baseline) |
| `_launch_pcsx2`'s `Session(..., log_path=…)` | the flag only |
| `tests/ps2_session` | B51's load expectations moved to B52's meaning (disclosed): `verification: "picture"`, the fake PCSX2 stateful |
