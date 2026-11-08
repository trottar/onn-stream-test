# C11 attempt 1 (2026-11-08 07:34-07:41Z; T1, a two-player PS2 title, the user's pick)

The user's lines: "Stage 5"; then "Save failed." / "It ran very well besides that. No issues I could notice".

- Hub reads at the start: all met (`hub_reads_start.txt`): the four PS2 log lines, PCSX2's log (0 `Invalid binding`, 4
  `Opened gamepad`, `McdSlot 0 … [8 MB, Formatted]`), the ini keys (`MultitapPort1 = false`, `[Pad2] Cross =
  SDL-1/FaceSouth`, `VsyncEnable = true`), the `ps2_session` row, `ps2_mode` on every heartbeat.
- Two sessions (Back + Resume at 07:37:48 → 07:38:03); each: the chooser, P1 (`padA`) then P2 (`padB`) claimed,
  `players_chosen` 2 (07:35:21 / 07:35:29; 07:38:11 / 07:38:13). Exit 07:40:55, then Stop: `PS2 exit: sigterm 0.6s`
  07:41:06.
- Exit report (07:40:55): `players` 2, `players_chosen` 2, `pad_claims` slots 0 / 1 `prompt`, `ports_set` `players` 2,
  `multitap` false, `source` `metadata` — met.
- **Two pads driving two players: not shown.** `updates_by_player` (state changes per slot) at the last heartbeat:
  slot 0 **685**, slot 1 **14** (the claim presses and a few more), slots 2 / 3 0. The user's line says it ran well,
  not that both pads drove their players in a two-player mode. **C11 incomplete on its gate row → re-run asked.**
- Tearing: "No issues I could notice" (none noticed).
- **The save (ahead of stage 6): "Save failed."** `Mcd001.ps2` and `Mcd002.ps2` sha256 unchanged from the post-format
  value `69358f81…74e1` (the files' mtime touched at the exit, 07:41:06Z, the content not); `ps2_memcard.check` still
  `formatted` True, 8134 free clusters. PCSX2's log: no memory-card error line; the cards opened `[8 MB, Formatted]`;
  one `Read Abort` (t = 260 s, a disc read). The BIOS PCSX2 reported in the session: a Japanese v1.00 (2000) image.
  Read-only; the cause is B's to find (B50's format as the real card manager reads it; the BIOS's region / version).
- The drive's folders: equal to stage 1 (listing + mtimes).
- **Corrected 08:01Z:** the "Save failed" was PrivyHub's save-state button (503 by design for PS2), not the game's card save — `../c12/save_state_presses.md`.
