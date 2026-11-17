# B129 — the watcher reads the game's own picture: the design (written and hashed before any code)

T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title. No title, serial, game id, character name,
cheat name or path; no picture, crop or reference image in git. Only with `PRIVYHUB_H7=1` (absent: the module is not
imported — today).

**Disclosed, before this design:** read-only measurements on H7-D1's / H7-C2's kept pictures (outside git): one look at
two T89 watcher pictures and one H7-C2 keeper picture beside a cut of a watcher picture; the keeper's logged rectangles;
H7-D1's T89 pictures cut by the keeper's rectangle and read with the rules folder's T89 spec (read in place). Numbers
below; nothing copied.

## Settled (code + logs)

1. **How `WindowPicture` picks its window** (`h7_minigame.py`): `xdotool search --onlyvisible --pid <the manager's
   process>`, the largest by `getwindowgeometry` (≥ 64 × 64), its X, Y, W, H; Pillow's X11 grab of that **screen
   rectangle**. **The rectangle is cached in `self._window` and found again only after a grab fails — and a screen
   grab never fails.** `MiniGame` (and its `WindowPicture`) lives as long as the companion; **the cache is not tied to
   the game's process.**
2. **Why T89's pictures were the desktop:** in H7-V5 and in H7-D1, T88 ran first in the same companion; T88's window
   is the whole screen (the keeper's log: (0, 0, 1920, 1080)), so T89's watches grabbed **T88's rectangle** — the whole
   1920 × 1080 screen with T89's window inside it. Not a 1920 × 1080 window of T89's process: **the stream's own
   finder** (`native_stream._find_linux_retroarch_window`: the same search, `getwindowpid` = the process, the largest)
   **found 960 × 720 for all 20 N64 stream sessions** in its log. (Not observed live: no title is started here.)
3. **Why T89 is windowed and T88 full screen:** RetroArch runs windowed for every core (`video_fullscreen = "false"`,
   `video_windowed_fullscreen = "false"` in the hub's base config; no window code in the launch); the window takes the
   core's picture size × RetroArch's scale — the N64 core 960 × 720 (the keeper: (960, 384, 960, 720)), T88's PS1 core
   the whole 1920 × 1080 screen (the PS1 core's windows in the stream's log: 879 × 720 or 1920 × 1080).
4. **What A's keeper took:** the largest visible window of class `retroarch`, found again when RetroArch's pid
   changed — **T89: (960, 384, 960, 720)**, its bottom 24 rows below the screen (Pillow pads them black); T88:
   (0, 0, 1920, 1080). **H7-D1's T89 desktop pictures cut by (960, 384, 960, 720) equal H7-C2's keeper pictures of
   the same screen (mean difference 0.0 grey levels; 38-40 when moved 24-30 px)** — the spec's area exactly.
5. **What the onn's stream shows for T89 in a mini game:** the mini game's switch is the stream's own start for the
   title's process (`_switch_stream` → `native_stream.start(managed_process_id=<title pid>)`) → `_select_capture_target`
   (fail closed: "Whole-desktop capture is intentionally disabled") → the 960 × 720 window **by its id**
   (`x11grab -window_id`), scaled into 1920 × 1080 with black bars at the sides. **The onn sees the game's window, not
   the desktop**; no fix needed for the stream.

## The design

- **The watcher's picture = the largest visible window owned by the game's own process** — `xdotool search
  --onlyvisible --pid P`, each window's `getwindowpid` = P (the stream's own check), ≥ 64 × 64, the largest by area
  (the stream's rule; for T89 the 960 × 720 window the keeper and the stream took; for T88 the full screen) — its
  `getwindowgeometry` rectangle grabbed as today.
- **Found again whenever the game's process changes** (the cache keyed by the process id), after any failed grab (as
  today), and at most every `REFIND_S` = 10 s (a moved or resized window). **No window owned by the process → the
  grab raises "the game's window was not found" → the watcher's existing `picture_failed` row, no read** — never a
  rectangle of another process, never the desktop.
- T88: its window is found exactly as today (the same window, the same rectangle) → reads unchanged.
- Flag absent: nothing changes (the module is not imported).

## Proof

- **Offline** (`scripts/b129_offline.py`, read only): H7-D1's T89 pictures (both passes) cut by the rule's rectangle
  (960, 384, 960, 720) → the T89 spec: the first `start` read and the least start distance per run; **`other` read as
  the screen 0** on the T89 runs with `other` (H7-C1's, through the same cut rule — its pictures are already the
  window). T88's H7-D1 pictures through the rule's rectangle (0, 0, 1920, 1080) → every read's class and screen distance
  = the watcher's own `index.csv` (today).
- **Tests** (`tests/b129_h7_game_window/`): the real HTTP server, B103's harness with **a fake window list** (the
  `xdotool` calls answered from a table: windows, owners, geometry) and **a fake screen** (Pillow's grab returns a
  1920 × 1080 picture with the game's picture pasted at its window's place, the desktop elsewhere; every grab's
  rectangle kept): a game window inside a larger desktop → its rectangle grabbed, `start` read, `recognised` true; a
  full-screen game → (0, 0, 1920, 1080) as today; **a full-screen game, then a windowed one in the same companion (the
  H7-V5 order) → the second's own rectangle** (today: the first's); no window owned by the process (none, or another
  pid's) → `picture_failed` rows, 0 reads; the flag absent → today's answers through the real routes (HEAD's
  companion against mine).
