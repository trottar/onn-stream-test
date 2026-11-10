## H7 — PrivyHub-native games; first: PrivyParty

**Status: PLANNED (2026-11-10) — the last item of Phase H. No work until the user says so ("I might just do it
next").** Adopted into the roadmap on the user's "Adopt" (2026-11-10); the wording was shown to the user first.

**The idea (the user's):** new games made for PrivyHub at roughly PS2-era host demand. The first is **PrivyParty**,
a Mario Party-like board game whose mini games are selected emulator games plus PrivyHub's own.

**Two pieces:**
- **H7a, the PrivyParty board (Godot):** a native game, launched and captured as PCSX2 and Dolphin are (the started
  process's window and audio; the hub's four virtual pads). The code is a new launch kind.
- **H7b, emulated mini games:** a mini game = a game the house has + a save state + a win rule read from game memory.
  The board loads the state, runs it for a fixed time, reads the memory and names the winner.

**Decided (the user, 2026-11-10):**
- **Engine:** Godot on the hub, streamed as PCSX2 and Dolphin are. A short probe comes first (the virtual pads, pause
  and exit from the onn, host cost), as PS2 and GameCube had.
- **Mini games from every system:** SNES, N64, PS1, PS2 and GameCube. Built in that order: SNES and N64 first (the
  proof is on SNES; N64 gives four players), then PS1, then PS2 and GameCube as far as their switch time (~10-12 s)
  and memory reads allow. GameCube has no control socket, so a GameCube mini game depends on finding a way to read its
  memory.
- **Audience:** the user's house only in the first version. Mini games are made against the user's own library. Other
  houses are a later step.

**Known from this project's records:**
- Switching takes seconds (PS1 relaunch ~4-6 s, HOME-7 C17; PS2 ~12 s, HOME-7 C20; GameCube first picture ~10 s,
  HOME-9 C34), so a transition screen is needed.
- No state may be sent into a running N64 core (B61).
- The PS1 multitap works only on titles that support it (B63); the SNES multitap has never been run on this hub.
- PCSX2 has a control socket (PINE); Dolphin has none, so memory reads there are unproven.
- The capture, the audio and the pads are emulator-agnostic (H3-P1's and H2-P1's parts tables; B49, B69).

**To verify before any design (not checked):** RetroArch's read-memory command on the cores in use; Godot's fit on the
hub (the virtual pads, pause and exit from the onn, host cost); the memory addresses per mini game.

**First step when started (a proof; no board, no graphics):** one SNES game, one save state, one memory-read win rule,
driven by a script: load state → run a fixed time → read memory → print the winner. Met when the script names the
right winner from memory values, repeatably. Nothing perceptual is a gate.

**Carries over:** pads on the onn; hold-to-join for up to four; parity for anything shown on the onn; one flag, absent
= today; no project-supplied game content, so mini games match what the house has.

**Open (the user's):** which games become mini games.
