# PP-H3c (second try) — every preparation: the rows, the paused proof, the frame-advance row, the go

| preparation | watch row | frame advance (`frames`, `batches`, `moved`, `changed`, `mute_ms`, `paused`) | `prepare_s` | `recognised` (first read) | `PAUSED` / words, watch → go | the go | `held_s` | reload | pictures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| part 1 (e) — the bench start | 03:36:04.601Z | 2, 2, 0.5241, True, 338.8, True | 1.268 | True at 1.0 s (start 0.0118) | **4 / 4** | 03:36:08.670Z real | 2.961 | none | `p1e_001`-`004` (4) |
| the streamed self-proof | 03:37:42.692Z | 2, 2, 0.5973, True, 370.1, True | 1.304 | True at 1.0 s (start 0.0118) | **3 / 3** | 03:37:45.318Z real | 1.517 | none | `selfproof_001`-`003` (3) |
| load screen 1 (after round 1) | 03:39:33.911Z | 2, 2, 0.5947, True, 374.1, True | 1.316 | True at 1.0 s (start 0.0118) | **6 / 6** | 03:39:40.676Z real | 5.654 | none | `load1_001`-`006` (6) |
| load screen 2 (after round 2) | 03:45:03.316Z | 2, 2, 0.5954, True, 378.6, True | 1.317 | True at 1.0 s (start 0.0118) | **6 / 6** | 03:45:09.300Z practice | 4.873 | none | `load2_001`-`006` (6) |
| load screen 3 (the way back after the practice left by Start) | 03:46:34.473Z | 2, 2, 0.4723, True, 373.3, True | 1.223 (after a practice) | True at 1.0 s (start 0.0118) | **78 / 78** | 03:47:52.201Z practice | 76.618 | none | `load3_001`-`074` (74) |
| load screen 4 (the way back after the practice left by time) | 03:49:26.088Z | 2, 2, 0.4997, True, 358.1, True | 1.21 (after a practice) | True at 1.0 s (start 0.0118) | **20 / 20** | 03:49:46.036Z real | 18.837 | none | `load4_001`-`020` (20) |

No `minigame_reloaded` row anywhere; no `label_mask` on any `watching` row; no `minigame_route` / `minigame_stream` between any watch row and its go. Every word with its second: `proof.tsv`. The pictures are in the git-ignored `runtime/pph3c_frames/` (`DISPLAY` set; the first file of the self-proof checked before the user was asked to play); nobody looked at them — no preparation missed.
