# The picture keeper (`picture_keeper.py`, off the repo; this copy with paths replaced)

- **The run folder:** `runtime/h7_frames/t89_c1_20261117T003035Z/` (git-ignored: `git check-ignore` →
  `.gitignore:5:runtime/` before the first file); `index.csv` (seconds, UTC, file, grab ms, save ms), `keeper_log.txt`;
  **794 pictures, 960 × 720 JPEG q90, 122 MB** — the game's whole window: the visible window of class `retroarch` was
  960 × 720 at (960, 384) on the 1920 × 1080 screen, **the same window the stream captured** (the client's decoder log:
  "Capture: RetroArch window 960x720"). No picture in git.
- **From the launch to the END:** the first picture 00:33:45.270Z (the window found at the launch), the last
  00:46:58.245Z (the END 00:46:53Z); **one a second, the largest step 1.01 s — no gap**.
- **Per stretch (by the users' line times):** the launch → "ready" (the join, VS Mode, the rules, the select screen,
  SAVE 1) 113 pictures (`f000001`-`f000113`); **M1** 216 (`f000114`-`f000329`, its results screen and SAVE 2 at
  00:38:31Z inside); **M2** 133 (`f000330`-`f000462`); **M3** 136 (`f000463`-`f000598`); **M4** 96
  (`f000599`-`f000694`); **M5** 71 (`f000695`-`f000765`); the END 29 (`f000766`-`f000794`). Each match's results screen
  before its line, inside the run.
- **Its cost:** a grab 11.0 ms median (worst 15.7), a JPEG save 3.4 ms median (worst 6.8); niced 10; **its CPU not
  read** (the keeper was stopped before its CPU time was read). It wrote only into its run folder and sent nothing to
  the game.
