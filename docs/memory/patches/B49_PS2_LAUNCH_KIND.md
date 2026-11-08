---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: f3f912c5
---

# B49 — the PS2 launch kind (PCSX2) behind `PRIVYHUB_PS2=1`

**Result: SETTLED + BUILT, host only; `tests/ps2_session` 35 (×3); 4 mutations caught; absent = today PROVEN; NOT
ADOPTED (no drop-in); PCSX2 not started by B; no live run.** Record: `evidence/B49_PS2_LAUNCH_KIND_2026-11-08.md`.
Applied to the tree, uncommitted.

- **Built:**
  - a `ps2` system on the onn's list, read-only from the configured games folder;
  - PCSX2 launched by `EmulatorManager` (`-datapath data/games/ps2/config -nogui -fullscreen -- <title>`), its ini merged
    per launch (Vulkan 1x on the AMD adapter, overlay off, no update check, Discord off, hub memcards / sstates / BIOS
    copy, PINE on, the multitap and the four virtual pads in the DualShock 2 layout via `SDL_GAMECONTROLLERCONFIG`);
  - pause / resume by the hotkey confirmed by PINE, else SIGSTOP / SIGCONT; exit SIGTERM, then SIGKILL after 5 s;
  - the hold rewind, the slot-9 save, the stall-resume load and the link give-up save off for a PS2 session
    (`ps2_mode` rows);
  - `tools/ps2_p2_frames.py` (P2 with the black / static seconds and the beat accounted for).
- **Files:**
  - `companion/ps2_session.py` (new), `companion/games/emulator_manager.py`, `companion/plugins/games.py`;
  - `companion/hold_rewind.py`, `companion/rewind_cores.py`, `companion/games/link_drop_recovery.py`;
  - `companion/games/native_stream_heartbeat.py`, `companion/players_session.py`;
  - `tools/ps2_p2_frames.py` (new), `tests/ps2_session/` (new).
- **Apply:** `git apply evidence/b49_2026-11-08/b49.diff` from the repo root (already applied, uncommitted).
- **On:** a drop-in `Environment=PRIVYHUB_PS2=1`, `daemon-reload`, restart (A's H3-P2, a bench drop-in).
- **Rollback:** remove the drop-in and restart (nothing PS2 reachable); or reverse `b49.diff`. `data/games/ps2/` is left
  as it is (gitignored).
