# E1-VOD inventory (E2-S1 §1) — written 2026-10-05 ~15:00-15:20Z, before any VOD suite run

The user's answer, 2026-10-05: the VOD drive is attached.

**The path.**
- `data/storage.json` `vod_root` → the external drive's tree (`<media mount>/onn-stream-test/media/vod`).
- The drive: a 1.8 TB USB disk, one exFAT partition, mounted **read-only**
  (`ro,nosuid,nodev,noexec`) through an autofs direct mount (D094/D095's
  arrangement). The identity check is the mount's presence and filesystem; no
  identifier is written here.
- The library: **91 files, all `.mp4`, all H.264** (89 GB), in `movies/` and
  its sub-folders. Typical file: 720×360 (26 files) to 720×480, ~0.92 Mbps
  median, 1.5-3 h. Two outliers: 1920×1080 at 3 Mbps; 1920×802 at 11.4 Mbps.
- **How the onn plays it — direct play, no host transcode** (re-confirmed):
  1. the app's tile → `POST /sources/vod_file_<slug>/start` (the companion
     checks the file and keeps `range_server.py` up);
  2. ExoPlayer in `MainActivity` fetches
     `http://<host>:8000/vod/<path>` with HTTP range requests (206);
  3. `range_server.py` (`python3 companion/range_server.py`, the companion's
     child) reads the file and writes it to the socket.
- **What the host does per second of playback** is the range server's reads
  and socket writes at the file's bitrate, in ExoPlayer's buffering bursts.
  Since no transcode exists, **E1-CONC-VOD is ABSENT** (the task's
  condition: "if the VOD path transcodes on the host").

**The fixed file**: `movies/Edge Of Tomorrow.mp4`.
- 720×360, H.264, 918 kbps, 1:53:29 (≥ 25 min).
- It is the library's typical format at the median bitrate, and it sits on the
  `MOVIES` page without scrolling.

**Unattended start, measured by hand once** (15:05-15:07Z; the runner
repeats it):
1. `MainActivity` → tap `VOD >` → `MOVIES >` → `Edge Of Tomorrow`.
2. It plays in the launcher's NOW PLAYING preview, and the progress text
   `now_playing_progress` reads `M:SS / H:MM:SS`.
3. Tap the preview → `fullscreen_player_host`.
4. BACK returns to the launcher with playback continuing and the progress
   readable. STOP (`button_stop`) ends it and posts `/stop`.
5. The app keeps a per-file resume position (`saveProgress` /
   `clearProgress`), so every run taps **RESTART** first and plays from
   0:00. The teardown taps RESTART then STOP, so the onn keeps ~0 s for the
   file.

**What the client reports**: nothing to the companion for VOD (no
heartbeat, no decoder report). The key figure is therefore **the progress
ratio** — seconds played over wall seconds, from the progress text at the
start (just before fullscreen) and at the end of the window (after BACK),
over warm-up + window — and its stall seconds per minute. The range
server's served bytes/s (`wchar`) is reported.

**Inventory session found afterwards**: a PS1 stream opened straight after
the VOD test without a companion restart rendered ~2 fps and never reached
PLAYING. With a unit restart first (as every suite run does) it played
normally. Recorded; both sessions were torn down (game stopped, banner
cleared, flags absent).
