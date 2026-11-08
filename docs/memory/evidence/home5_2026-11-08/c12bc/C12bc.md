# C12'b / C12'c — the list and LOAD after Stop and relaunch (2026-11-08 16:16-16:20Z; T1)

The user's lines: "Stage 3"; "Stage 3 done Load is just a black screen".

- Stop 16:16:39Z (`PS2 exit: sigterm 0.5s`); the relaunch 16:16:52Z (the same title, `players=1`).
- **LOAD 1** (as the game came up, before the stream): `POST load-state` slot 1 → **200**; game log `PS2 load: slot 1
  pine 0x0a ok; confirmed` (16:17:02.175Z); PCSX2 `Loaded state from slot 1.`; then on PCSX2's resume (16:17:07.977Z)
  **ten `TLB Miss` lines** at EE hardware-register addresses.
- **LOAD 2** (B's steps: Back → Game State → Load → Slot 1 → Resume): `POST load-state` slot 1 → **200** (16:18:59);
  game log `PS2 load: slot 1 pine 0x0a ok; confirmed` (16:18:59.993Z); PCSX2: `Recompiler Reset`, PCSX2's own warning
  `MTVU speedhack is enabled, saved states may not be stable`, `Loading SPU2`, `Loading GS`, `Loaded state from slot
  1.`; on the resume (16:19:06.517Z) **the same `TLB Miss` lines** (18 in the excerpt over both loads).
- The stream stayed up (heartbeats rendering, output age ~30 ms): the black picture is PCSX2's own output after the
  load, not the link.
- **The user: "Load is just a black screen".** The hub's "confirmed" is PCSX2's `Loaded state` line, not the game
  running from it.
- Beside it (C12'a's launch, not a row): an in-launch LOAD at 16:15:59Z also answered 200 / `confirmed`; that launch's
  PCSX2 log was overwritten by the relaunch, and the user gave no line on its picture.
- **C12'b (Slot 1 listed with the save's date and size):** asked of the user at the close (the hub's index holds slot 1
  at 16:13:57.968Z, 16181232 B).
- **C12'c: NOT MET** — HTTP 200, `Loaded Slot 1`'s row and `pine 0x0a ok` present, but **the game does not continue from
  the save** (the gate row). For B: the guest after a PINE load hits `TLB Miss` on hardware registers (MTVU on — PCSX2's
  own warning; PCSX2's log `pcsx2_log_excerpt.txt`, serial and paths stripped).
- The drive: read at the close.
