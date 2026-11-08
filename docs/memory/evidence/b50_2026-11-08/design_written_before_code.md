# B50 — the PS2 fixes from H3-P2 (design, written and hashed before any B50 code)

Queue: `handoffs/QUEUE_2026-11-08Q.md` §B50. Baseline `85c51c91` (A's audio-wait diff committed with H3-P2's
record). Built in `/tmp/b_q09q_b50`. **Every runtime change is inside `PRIVYHUB_PS2=1`; absent = today byte for byte.**
The two tool changes (§5, §6) add output only for PS2 sessions; a log with no PS2 session reads as today.

## 0. Settled (read from the hub's files; PCSX2 not started)

**S1. PCSX2's startup order** (its own log of H3-P2's last run, seconds since PCSX2's start, read in place):
- 1.41 the Vulkan device and swap chain (the window);
- **1.45 `Opening SPU2` / `Creating Cubeb audio stream`** (the PulseAudio stream; Cubeb's init returns once the stream
  is ready, so the sink-input exists from here);
- 1.54 `VM subsystems initialized`, then the first PINE client answered (our status poll);
- 1.56 the four virtual pads opened.
- The game logs agree:
  - the working launches saw the sink-input 0.1-0.3 s after the window, and a hotkey pause about 0.14 s after that;
  - **the failed launch paused 1.6 s after its launch with PINE not answering → SIGSTOP before the audio stream →
    no sink-input for the session's audio match → no release.**
- **The earliest signal that guarantees the audio stream is the sink-input itself.** PINE's first answer comes later
  (after the VM's init, which follows the audio stream), so it guarantees the audio too, but never earlier.
- **Decision: keep A's wait** (the PID's sink-input, ≤ 45 s, then the paused handoff), **narrowed:**
  - it runs on the session's own injectable `run` / `sleep` / `clock` (the tests fake it; A's version called the real
    `pactl` from the tests, so `tests/ps2_session` took 91 s), and polls every 0.1 s;
  - the first pause after it waits ≤ 1.0 s for PINE's first answer before choosing SIGSTOP (PINE late → the hotkey).
    So SIGSTOP comes only after the audio exists, or after the 45-s bound (logged `PS2 audio: none`).

**S2. The memory cards.**
- The hub's two cards are 8,650,752 bytes (16,384 pages × (512 + 16)) and **all `0xFF`**: PCSX2's unformatted image
  (its log: `[8 MB, UNFORMATTED]`).
- PCSX2 2.8.2 has no CLI or ini path that creates a formatted card (its binary: only the Qt "Create Memory Card"
  dialog strings).
- **So the companion formats the card**, at a PS2 launch, when a slot's card is absent or all `0xFF`. A card holding
  any other byte is never touched.
- **The format** (the PS2 memory card file system as the BIOS and PCSX2's folder cards write it):
  - **the superblock** (page 0): `Sony PS2 Memory Card Format ` / `1.2.0.0`, page 512, 2 pages per cluster, 16 pages
    per erase block, `0xFF00`, 8192 clusters, allocatable offset 41, allocatable end 8135, root at cluster 0, backup
    blocks 1023 / 1022, the indirect FAT list `[8]`, 32 bad blocks −1, card type 2, flags `0x52`, the rest of the page
    `0xFF`;
  - **the indirect FAT** (cluster 8): FAT clusters 9-40;
  - **the FAT:** cluster 0 (the root) `0xFFFFFFFF`, clusters 1-8134 free `0x7FFFFFFF`, the tail `0xFFFFFFFF`;
  - **the root directory** (absolute cluster 41): `.` (mode `0x8427`, length 2) and `..` (mode `0xA426`), created /
    modified now;
  - **every written page with its ECC:** 4 × 128-byte Hamming codes, 3 bytes each, then 4 zero bytes; unwritten pages
    `0xFF` with `0xFF` spare.
- **The ECC is PCSX2's own:** its binary carries both 256-byte tables (byte parity and the column-parity masks) right
  after its copy of the card magic, and both are equal to the formula used here (`ecc_table_check.txt`).
- The superblock's field values are **recalled** from the format; A's HOME-4+ checks PCSX2's boot line
  (`[8 MB, Formatted]`) and a save in play (C12).
- The ini's `[MemoryCards] Slot1_Enable / Slot1_Filename / Slot2_*` are set (`Mcd001.ps2` / `Mcd002.ps2`).
- A **checker** (`ps2_memcard.check`) reads a card back: the size, the magic, the superblock fields, the indirect
  FAT → FAT chain, the root's two entries, and every page's ECC.

**S3. The tears.**
- The ini has `VsyncEnable = false`, so PCSX2 presents immediately (Vulkan IMMEDIATE).
- The hub's X session runs `xfwm4` with compositing on and `unredirect_overlays` true, so PCSX2's fullscreen window
  is **unredirected**: it presents straight to the scanout. An immediate present then lands mid-scanout (a tear), and
  `x11grab` copies whatever the front buffer holds when it reads.
- RetroArch sessions run with `video_vsync = "true"` and showed no tears.
- **Fix:** `VsyncEnable = true` with `DisableMailboxPresentation = false`. PCSX2 then uses MAILBOX when the driver
  offers it (RADV does on X11): tear-free, and no wait on the display, so no frame-time cost. Else FIFO: tear-free,
  with up to one frame (~17 ms) more latency, and a 59.94-Hz game on a 60-Hz display repeats one frame about every
  17 s.
- **The trade-off for the user:** only if FIFO is what the driver gives. A measures frame-time p95 (H3-P2: 16.7 ms)
  and reads PCSX2's log.
- `xfwm4`'s settings are the user's desktop and are not changed.

**S4. The bindings.**
- PCSX2 2.8.2 is built on SDL3. Its log rejected only `SDL-k/A` / `B` / `X` / `Y`, and accepted `Back`, `Start`,
  `DPad*`, `LeftShoulder`, `+LeftTrigger`, `LeftStick` and the axes. Its binary carries `FaceSouth` / `FaceEast` /
  `FaceWest` / `FaceNorth` beside those names.
- **So Cross = `FaceSouth`, Circle = `FaceEast`, Square = `FaceWest`, Triangle = `FaceNorth`;** the other 20 bindings
  are unchanged.
- The accepted set, recorded and asserted in a test: `FaceSouth FaceEast FaceWest FaceNorth Back Guide Start LeftStick
  RightStick LeftShoulder RightShoulder DPadUp DPadDown DPadLeft DPadRight` and the axes `±LeftX ±LeftY ±RightX ±RightY
  +LeftTrigger +RightTrigger`.
- The log also confirms the open order: the four virtual pads opened as player ids 0-3 in creation order, so SDL-0..3
  = P1-P4.

**S5. The keeper's PS2 label.**
- `diag_read` learns a session's title and core from the game logs' names (`…-game_<system>_<hex>.log`). The PS2 log
  is `…-ps2.log` (no id, by B49's design), so a PS2 session takes the previous launch's PS1 label.
- **Fix:**
  - `…-ps2.log` is a launch with system `ps2`, core `pcsx2`, title tag `PS2`;
  - the recovery log's `ps2_session` row before a `session_started` marks that session `ps2` (it wins over the file
    name);
  - a PS2 session's row carries `system: "ps2"` (other rows unchanged);
  - `ps1_reference(rows)` picks the PS1 sessions for a comparison, PS2 never among them;
  - `diag_check` prints one more line, `last session: ps2 (pcsx2) …`, only when the keeper's newest
    `sessions.jsonl` row is PS2.

**S6. P2's capture time** (`tools/ps2_p2_window.py`, new):
- **The plan:** from the recovery log (`session_started`, `session_ended`) and the PS2 game log (`PS2 pause:` /
  `PS2 resume:`), the earliest second t that is ≥ 60 s after the last `session_started` and has no pause in
  [t − 90 s, t + 60 s + 90 s] among the pauses seen so far. Prefer minute 3 of the session (start + 180 s) when it is
  valid; if no valid t comes before minute 9, the fallback is minute 3, marked `fallback`.
- **`check`:** after the capture, the window is valid only if no pause falls inside that span.

**S7. Not built, named open:** the read-ahead (H3-P1 design §2 option 2) and PS2 save states through PINE (the
user's question).

## 1. Tests (`tests/ps2_session` under 10 s; `tests/diag_read` gains its cases or a new `tests/ps2_diag`)

- **A fake PCSX2 timeline** (window 1.40, audio 1.45 unless frozen before, PINE from 1.54 unless frozen; SIGSTOP
  freezes, SIGCONT thaws):
  - (a) the wait + PINE late → hotkey, audio present;
  - (b) the wait + PINE never → SIGSTOP after the audio exists;
  - (c) no wait (B49) + PINE late → SIGSTOP before the audio: no sink-input — **the defect reproduced**;
  - the launch test faked (no real `pactl`), the suite < 10 s.
- **The card:** a formatted card passes the checker; an all-`0xFF` card is "unformatted"; a corrupt ECC byte or magic
  is caught; `ensure_cards` writes absent / all-`0xFF` cards and never touches a card with data; the ini slot keys.
- **Vsync:** the keys `VsyncEnable = true` and `DisableMailboxPresentation = false`.
- **The bindings:** every DS2 binding name in the accepted set, for 1 / 2 / 4 players; no bare `A` / `B` / `X` / `Y`.
- **The keeper:** a `…-ps2.log` launch and a `ps2_session` row → `system: ps2`, core `pcsx2`; a PS1 session's row
  unchanged; `ps1_reference` excludes PS2; diag_check's extra line only for a PS2 newest row.
- **The window tool:** minute 3 when clear; pushed past a pause; the fallback; `check` invalid with a pause inside.
- **Absent:** nothing new is imported or written without the flag (B49's absent tests still pass).
