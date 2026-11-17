# H7-D1 — what the reads and the pictures show (measurements for Cowork; not cells; no fix)

- **T88 — RetroArch's notices.** In the board's order (early) the setup's begin loads 0.08 s after the launch answers;
  the window shows the unlocked select screen (00 – 00) from the first reads, but RetroArch's own notices — the cheat
  being applied, the virtual pads configured in ports 1-4, the state loaded — sit in the screen's lower-left corner for
  about 8 s; every read until then is `other` with the screen distance 0.083-0.092 (the spec's line 0.082); **the first
  `start` read at 9.00 s**, one second past the hub's 8-s window, and every read after it `start` (0.0117-0.0118).
  Loaded 15 s after the launch (late), the notices of the launch are gone: **the first `start` at 4.00 s**,
  `recognised` true. (T88's pictures are 1920 × 1080, its window full screen.)
- **T89 — the picture is the desktop, not the game's window.** In both orders the watcher's every picture is the whole
  **1920 × 1080 screen** — the desktop with the game's **960 × 720** window inside it (the window shows the unlocked
  four-player select screen, Stock 1, after its notices clear in a few seconds). T89's spec was learnt from H7-C1's and
  H7-C2's pictures, which the keeper took of the visible window of class `retroarch` (960 × 720). The watcher's
  `WindowPicture` takes **the largest visible window of the game's process** (`xdotool search --onlyvisible --pid`),
  which for T89 is a 1920 × 1080 area. So every read is `other`, start 0.25-0.26 against 0.0932, **never `start` in 45
  reads, early or late** — the load order does not matter for T89.
- **The load line** was present in every counted pass (`.state8` under the setup's own folder; T88 16,777,240 bytes,
  T89 16,793,440), 0.08 s (early) or 15.5 s (late) after the launch's answer, `load_line_ms` 24-57 ms.
