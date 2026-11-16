# The picture keeper (`picture_keeper.py`, off the repo; this copy with paths replaced)

- **The run folder:** `runtime/h7_frames/h7v2_20261116_run/` (git-ignored: `git check-ignore` → `.gitignore:5:runtime/`
  before the first file); `index.csv` (seconds, UTC, file, grab ms, save ms), `keeper_log.txt`; **508 pictures,
  1920 × 1080 JPEG q90, 165 MB**. No picture in git.
- **Per match:** M1 264 pictures (03:32:59-03:37:22Z; the first 34 s after the start not kept — see below); the relaunch
  19; M2 219 (03:37:56-03:41:34Z). Seconds covered: M1 ~264 s, M2 ~219 s.
- **Disclosed:** started at stage 1 with the window looked up by RetroArch's own process; **the live window belongs to
  the AppImage's launcher process, not RetroArch's**, so it found none from 03:32:24Z. Fixed at 03:32:59Z (the
  launcher's parent tried, then the visible window of class `retroarch`); the keeper restarted twice; no picture lost
  after that (one a second to the end).
- **Its cost:** a grab 10.8 ms median (worst 15.9), a JPEG save 7.5 ms (worst 12.4); its CPU 12.6 s over 720 s alive
  (~25 ms a picture, niced 10). It writes only into its run folder and sends nothing to the game.
