# The encoder's and Godot's CPU and the graphics device's busy share (`status_watch.tsv`, once a second; no bar)

Over the play only (the game active, the stream up, not paused). The encoder = the stream's two `ffmpeg` processes
(video and the audio helper), % of one core; Godot = the board's process; the graphics device's `gpu_busy_percent`.

| run | seconds | encoder CPU (median) | Godot CPU (median) | graphics busy (median / max) | VRAM max | load max |
| --- | --- | --- | --- | --- | --- | --- |
| Compatibility (OpenGL), run 1 before Home | 146 | 38 % | 22 % | 21 % / 39 % | 397 MB | 2.66 |
| Compatibility (OpenGL), run 1 after RESUME | 88 | 38 % | 22 % | 23 % / 38 % | 402 MB | 3.25 |
| Mobile (Vulkan), run 2 | 77 | 38 % | 19 % | 27 % / 44 % | 433 MB | 1.90 |

The board's busy textures in motion did not move the encoder's cost between renderers (38 % each); Mobile drew with a
little less CPU and a little more graphics time, as in PP-H1. (The capture and encode run at the stream's 1280 × 720,
60 fps, 7,000 kbit/s.)
