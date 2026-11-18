# B144 — a practice banner, on the stream only: design (written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AX.md` §B144; the user: "it's hard to tell if we're in practice since they have the
same screen so maybe a hub side banner at the top (unless that messes with the vision model)". Baseline
`baseline_head.txt`. Behind `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1`): only the party layer arms it. Absent = today.

## Settled

- **Where the onn's picture is made:** `NativeStreamManager._build_linux_ffmpeg_command` — `x11grab -window_id <the
  title's window>` → `-vf scale=W:H:force_original_aspect_ratio=decrease…,pad=W:H:(ow-iw)/2:(oh-ih)/2:black,format=nv12,
  hwupload` → `h264_vaapi`. The filter runs inside the encoder process on frames already grabbed: **a band drawn there is
  in the onn's picture only — the title's own window is never drawn on.** The watcher reads the hub's display (the
  title's window) and never the stream; a practice reads nothing after its start; at the way back the banner's encoder is
  gone before the next preparation's reads (the switch to the board runs first, `_way_back`), so the next begin is read
  from a window that never had a band. Not the vision model's input at any time.
- **What the hub's ffmpeg has (nothing fetched):** the hub's ffmpeg 7.1 (the one `_find_ffmpeg` finds) is built with
  libfreetype, libfontconfig, libharfbuzz: `drawtext`, `drawbox`, `overlay` are there; fontconfig resolves the family
  `Sans` to an installed sans font (DejaVu / Noto are installed). **A text filter and a font are there: no image is
  needed** — the text is drawn by name (`font=Sans`), no font path in the command.
- **The cost, on a made-up source** (`testsrc2` 960 × 720 bgr0 at 60, the stream's own scale / pad / nv12 chain, 1800
  frames to `-f null`, three runs each, `banner_cost.txt`): without 7.39 s user CPU, with **`drawtext` and its own box
  after `format=nv12` 8.07 s → +0.38 ms CPU a frame (~2.3 % of one core at 60 fps; wall +0.05 ms a frame)**. Rejected:
  `drawbox` for the band (+1.15 ms a frame by itself), the band drawn before `format=nv12` on the RGB frame (+3.6 ms).
  The VAAPI encode after `hwupload` is unchanged.

## The design

- **The band:** `drawtext=font=Sans:text='PRACTICE — press Start to go back':fontcolor=white:fontsize=h*30/720:
  x=(w-text_w)/2:y=(h*56/720-text_h)/2:box=1:boxcolor=black@0.72:boxborderw=14|4096|14|4096`, inserted **after
  `format=nv12`, before `hwupload`** (constant `PARTY_BANNER_FILTER`). **Where it sits:** across the top of the 16:9
  frame — the text's box widened past both edges (clipped to the frame), white text 30 px high centred over a black
  band at 72 % (**rows 0-58 of 720 at the 720p profile, ~8 % of the height**; scaled with the frame at the 1080 rung).
  A 4:3 picture fills the frame's height (960 × 720 between two 160-px black pillars): the band covers the top ~8 % of
  the title's picture, translucent, and runs on over the black pillars.
- **Only in a practice:** `NativeStreamManager.party_banner_next(pid)` arms the next start **for that process**;
  `_start_linux_locked` takes it once after `_stop_locked` (`_party_banner_on` = armed for this pid; the arm cleared
  either way) and `_build_linux_ffmpeg_command` inserts the band only while `_party_banner_on` (read with `getattr`,
  default False) — so the encoder's own restarts in that capture session (the recovery's restart, a bitrate level)
  keep it, and **the next start (the way back to the board, a real go, any users' start) takes it off.**
- **The party layer:** `_switch_stream(which, pid, banner=False)`; `_handover` passes `banner=True` only for a
  practice's go; the arm cleared in the switch's `finally`. A real go's switch, the way back's, the end's: no arm →
  **byte for byte today's command.**
- The users' own starts: never armed — today's command with the flags set.

## Tests (`tests/b144_party_practice_banner/`)

- **Through the real HTTP server** (B114's harness): a held start, a practice go, the way back, a real go, the end —
  the stream object builds each start's encoder command with the real `NativeStreamManager` (`_start_linux_locked` on
  G8-S2's stubs, nothing spawned): **the practice's switch carries the band, the way back's does not, the real go's
  does not**, and the real go's / the way back's commands equal a start's command on HEAD's code for the same window.
- **The title's window untouched:** a made-up window on the hub's display showing a known picture, grabbed by its id
  with the stream's own grab arguments while a practice's command is in force (as the watcher would see it): the
  window's own picture (no band rows).
- **The band in the output frame:** the practice command's own `-vf` run on a made-up 4:3 source to one frame: the band
  rows (0-58 of 720) differ from the same chain without it; every other row equal within 2 grey levels (the nv12
  round trip); the text's pixels present.
- **A users' start with the flags set:** today's command byte for byte; **the flags absent → today** (B114's flag test).
- Temp dirs removed.
