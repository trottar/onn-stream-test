# S — the sound after every planned switch (B150's wording)

N_HB 2028; the switches of the sitting (after the self-proof), T and the read as `scell.py` (A's, off the repo) computes them:

```
switch 1 (minigame, 1.901 s, 19:29:10Z): READ — sound 0.2 s after T (depth 6); 9 rows to 16.5 s, underrun rises max 0; lost 0; max arrival gap 1702 ms → met
switch 2 (board, 3.584 s, 19:29:30Z): READ — sound 0.3 s after T (depth 4); 3 rows to 5.8 s, underrun rises max 2; lost 0; max arrival gap 3393 ms → met
switch 3 (minigame, 1.711 s, 19:29:37Z): READ — sound 0.9 s after T (depth 5); 15 rows to 30.0 s, underrun rises max 0; lost 0; max arrival gap 1516 ms → met
switch 4 (board, 1.978 s, 19:30:21Z): READ — sound 1.1 s after T (depth 9); 15 rows to 30.0 s, underrun rises max 1; lost 0; max arrival gap 1759 ms → met
switch 5 (minigame, 3.605 s, 19:32:52Z): READ — sound 0.0 s after T (depth 2); 11 rows to 21.4 s, underrun rises max 1; lost 10; max arrival gap 3410 ms → met
switch 6 (board, 3.598 s, 19:33:17Z): READ — sound 1.2 s after T (depth 8); 4 rows to 7.5 s, underrun rises max 1; lost 0; max arrival gap 3399 ms → met
switch 7 (minigame, 3.572 s, 19:33:28Z): READ — sound 0.2 s after T (depth 1); 15 rows to 30.0 s, underrun rises max 6; lost 0; max arrival gap 3374 ms → met
switch 8 (board, 1.834 s, 19:34:12Z): READ — sound 2.0 s after T (depth 9); 7 rows to 30.0 s, underrun rises max 0; lost 0; max arrival gap 1637 ms → met
switch 9 (minigame, 1.779 s, 19:36:47Z): READ — sound 0.2 s after T (depth 1); 14 rows to 27.0 s, underrun rises max 2; lost 0; max arrival gap 1584 ms → met
switch 10 (board, 3.496 s, 19:37:18Z): READ — sound 1.8 s after T (depth 3); 14 rows to 30.0 s, underrun rises max 2; lost 0; max arrival gap 3300 ms → met
switch 11 (minigame, 1.693 s, 19:37:56Z): READ — sound 0.1 s after T (depth 5); 12 rows to 22.9 s, underrun rises max 0; lost 0; max arrival gap 1499 ms → met
switch 12 (board, 1.655 s, 19:38:21Z): READ — sound 1.7 s after T (depth 4); 7 rows to 13.8 s, underrun rises max 2; lost 0; max arrival gap 1459 ms → met
switch 13 (minigame, 1.692 s, 19:38:36Z): READ — sound 0.3 s after T (depth 8); 15 rows to 30.0 s, underrun rises max 2; lost 0; max arrival gap 1500 ms → met
switch 14 (board, 3.587 s, 19:40:00Z): READ — sound 0.8 s after T (depth 2); 15 rows to 30.0 s, underrun rises max 2; lost 0; max arrival gap 3381 ms → met
switch 15 (minigame, 1.852 s, 19:41:15Z): READ — sound 0.2 s after T (depth 2); 7 rows to 13.1 s, underrun rises max 5; lost 0; max arrival gap 1654 ms → met
switch 16 (board, 3.48 s, 19:41:32Z): READ — sound 1.8 s after T (depth 5); 2 rows to 4.1 s, underrun rises max 0; lost 0; max arrival gap 3284 ms → met
switch 17 (minigame, 1.913 s, 19:41:38Z): READ — sound 1.8 s after T (depth 12); 14 rows to 30.0 s, underrun rises max 2; lost 0; max arrival gap 1678 ms → met
switch 18 (board, 1.91 s, 19:43:25Z): READ — sound 0.7 s after T (depth 9); 15 rows to 30.0 s, underrun rises max 2; lost 0; max arrival gap 1721 ms → met
S: MET (18 switches)
```

**Read 18, listed 0** (every next switch began ≥ 4 s after). Sound within 0.0-2.0 s of every switch; underrun rises ≤ 6 a row; `audio_lost_packets` 10 once (switch 5), else 0; `audio_max_arrival_gap_ms` 1459-3410 at the switches. The Home → RESUME gap (19:34:42-19:35:12Z) is not a switch. The users: "Sound worked very nicely, a little jarring during transitions"; after Home "audio lingered 15 seconds" (no `native-stream-stop` from the onn at Home).
