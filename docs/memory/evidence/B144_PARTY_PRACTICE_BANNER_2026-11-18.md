---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AX) — a practice banner on the onn's picture only, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). The encoder's own filter draws "PRACTICE — press Start to go back" across the top of the stream's picture, from a practice's planned switch to the way back's. It is drawn by the hub's ffmpeg drawtext with fontconfig's Sans (no font path, nothing fetched), after format=nv12 and before hwupload, and costs +0.38 ms CPU a frame on a made-up source. The title's window is never drawn on, so the watcher's reads cannot see it. Every other start's command is byte for byte today's. Tests: through the real routes only the two practices' commands carry it, every other command equals HEAD's; a made-up window grabbed by its id is its own picture, and the band is in rows 0-58 of the output only. Nothing adopted; nothing committed
---

# B144 — a practice banner, on the stream only

Queue: `handoffs/QUEUE_2026-11-18AX.md` §B144. The user: "it's hard to tell if we're in practice since they have the
same screen so maybe a hub side banner at the top (unless that messes with the vision model)". The directory is
`b144_2026-11-18/`: the design + `.sha256` (hashed 04:18:47Z, before any code), `banner_cost.txt`, `b144.diff`, the
checks, `manifest.sha256`. The runs are in `b143_2026-11-18/`. Patch: `patches/B144_PARTY_PRACTICE_BANNER.md`. No
picture in git (the probes' pictures were made-up sources, looked at once, then removed).

## Settled

- **Where the onn's picture is made:** `x11grab -window_id <the title's window>` → `-vf scale…,pad…,format=nv12,hwupload`
  → `h264_vaapi`. A filter there runs inside the encoder on frames already grabbed, so **the title's window is never
  drawn on** and the watcher, which reads the window, never sees the band. A practice reads nothing after its start.
  At the way back, the board's switch runs before the next preparation, so the next begin is read from a window that
  never had a band.
- **What the hub has (nothing fetched):** its ffmpeg 7.1 is built with libfreetype, libfontconfig and libharfbuzz, so
  `drawtext`, `drawbox` and `overlay` are there. fontconfig gives `Sans` (DejaVu and Noto are installed). **A text
  filter and a font are there, so no image is needed.**
- **The cost** (`banner_cost.txt`: `testsrc2` 960 × 720 at 60, the stream's own scale / pad / nv12 chain, 1800 frames,
  three runs each): **+0.38 ms user CPU a frame (~2.3 % of one core at 60 fps; wall +0.05 ms a frame).** Rejected:
  `drawbox` for the band (+1.15 ms a frame alone), and the band drawn on the RGB frame before `format=nv12` (+3.6 ms).

## Built (`b144.diff`)

- `companion/native_stream.py`: `PARTY_BANNER_FILTER` = `drawtext=font=Sans:text='PRACTICE — press Start to go
  back':fontcolor=white:fontsize=h*30/720:x=(w-text_w)/2:y=(h*56/720-text_h)/2:box=1:boxcolor=black@0.72:
  boxborderw=14|4096|14|4096`. **`party_banner_next(pid)`** arms the next start for that process; `_start_linux_locked`
  takes it once after `_stop_locked` (`_party_banner_on`); `_build_linux_ffmpeg_command` inserts the band before
  `,hwupload` only while it is on. The encoder's own restarts in that capture session (the recovery's restart, a bitrate
  level, a fast restart) keep it, and the next start takes it off.
- `companion/party_minigame.py`: `_switch_stream(…, banner=False)`; `_handover` passes `banner=True` only for a
  practice's go; the arm is cleared in the switch's `finally`.
- **Where it sits:** across the top of the 16:9 frame, the text's own box widened past both edges. White 30-px text sits
  centred on black at 72 %, in **rows 0-58 of 720 (~8 % of the height)**, scaled with the frame at the 1080 rung. A 4:3
  picture fills the frame's height (960 × 720 between two 160-px black pillars), so the band lies over the picture's top
  ~8 %, translucent, and runs on over the pillars.

## Tests (`tests/b144_party_practice_banner/`, 5)

| test | shown |
| --- | --- |
| the steps | through the real routes (B143's `b143` scenario, mine and HEAD's): the board's own start, a real go and its way back, two practices and their ways back, a real go and the end — 9 starts each |
| only the practices | **the two practices' switches carry the band** (after `format=nv12`, ending `,hwupload`); the real goes', the ways back' and the onn's own start's do not |
| everything else is HEAD's | the 7 other commands **equal HEAD's at the same step**; a practice's command with the band taken out equals the real go's |
| HEAD never draws it | none of HEAD's 9 commands has it |
| the window and the frame | a made-up 960 × 720 window on the hub's display (~6 s; disclosed) showing a known picture, grabbed by its id with the stream's own x11grab arguments: **its own picture within 2 levels (no band)**; the practice command's own `-vf` on that grab (`hwupload` swapped for an RGB frame out): **the rows that differ from the same chain without the band are 0-58 only**, the rest equal within 2 levels, white text pixels inside the band, the band darker |

**Users' starts with the flags set:** the onn's own start (step 0) equals HEAD's. **The flags absent → today:** B114's
flag test (`b143_2026-11-18/tests_others.txt`).
