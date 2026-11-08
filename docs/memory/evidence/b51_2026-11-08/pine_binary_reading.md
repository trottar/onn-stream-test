# PCSX2 2.8.2's PINE, read from the AppImage's binary (B51 S1; nothing run, nothing fetched)

Method: the AppImage's squashfs (it starts at the end of its ELF runtime, offset 944,632) opened read-only with `7z`;
`usr/bin/pcsx2-qt` extracted into `/tmp` (gitignored scratch); its `.symtab` read with `nm -C`, and
`PINEServer::MainLoop` (0x543890-0x544340) and the two state lambdas disassembled with `objdump -d`.

- **The dispatch:** `movzbl 0x4(%rbx,%rax,1)` (the byte after the 4-byte size), `cmp $0xf` / `ja` → the failure path,
  then a 16-entry relative jump table at 0x17ead0 (`pine_opcodes.txt`).
- **0x09 → 0x543d29:**
  - `s_state − 2 ≤ 2` (the VM in states 2-4) else the failure path;
  - `movzbl` of the next byte (the slot);
  - `lea` of `ParseCommand::$_0::_M_invoke`;
  - `QMetaObject::invokeMethodImpl(g_emu_thread, …, ConnectionType 2 = Qt::QueuedConnection, …)`.
  - `$_0` = `VMManager::SaveStateToSlot(slot, esi = 1 (zip on a thread), <SaveState_ReportSaveErrorOSD>)`.
- **0x0A → 0x543e12:** the same checks and slot byte, `$_1` = `VMManager::LoadStateFromSlot(slot, …)` with
  `SaveState_ReportLoadErrorOSD` on error.
- **The reply** (`s_ret_buffer`): OK = `movl $0x5` size, `movb $0x0`; failure (0x5441db) = size 5, `movb $0xff`.
- **The file name strings:** `{} ({:08X}).{:02d}.p2s`, `….p2s.backup`, `Creating save state backup {}...`,
  `Saving state to slot {}...`, `Saved state to slot {}.`, `Loaded state from slot {}.`.
