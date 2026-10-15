# E4-S5 — the sessions and the flagged runs

| run | class | capture fps / dup+drop per min | input tbr → output fps (-r) | window distinct fps (min-max) | rendered | RetroArch | host CPU | loss/min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| runs_sessions/E1-SNES-STREAM/run1 | **CLEAN** | 59.933 / 3.611 | 59.94 → 59.94 (None) | [49.105] [(4, 60)] | 58.351 | 59.999 | 8.16 | 607.12 |
| runs_sessions/E1-SNES-STREAM/run2 | **CLEAN** | 59.992 / 0.1 | 60 → 60 (None) | [49.86] [(2, 60)] | 59.226 | 59.999 | 9.06 | 174.07 |
| runs_sessions/E1-SNES-STREAM/run3 | **CLEAN** | 59.892 / 3.019 | 60 → 60 (None), 59 → 59 (None), 60 → 60 (None), 59.94 → 59.94 (None) | [49.0, 48.947] [(4, 60), (3, 60)] | 55.128 | 59.999 | 8.33 | 2459.04 |
| runs_flag/E1-SNES-STREAM_flag/run1 | **CLEAN** | 59.968 / 0.05 | 60 → 60 (60), 60 → 60 (60), 60 → 60 (60), 60 → 60 (60) | [49.0, 47.842, 49.491, 47.31] [(8, 60), (2, 60), (1, 60), (3, 60)] | 57.987 | 59.999 | 9.38 | 955.55 |
| runs_flag/E1-SNES-STREAM_flag/run2 | **CLEAN** | 59.993 / 0.1 | 60 → 60 (60) | [49.0] [(7, 60)] | 59.205 | 59.999 | 8.75 | 315.82 |

Statement (i), the fault iff the probe reads 59: False; (ii), the window at ~60 distinct frames/s: False.
Faulty sessions in §2: 0 of 3.

**§3 verdict: REJECTED (rendered_ge_59.5)**

RetroArch's verbose log (first session), timing-related lines:

```
lines 216, [DEBUG] lines 89
[INFO] [Core] Geometry: 256x224, Aspect: 1.3333, FPS: 60.0988, Sample rate: 32040 Hz.
[INFO] [GLX] GLX_EXT_swap_control_tear supported.
[INFO] [GLX] Found swap function: glXSwapIntervalEXT.
[INFO] [Audio] Set audio input rate to: 31987.32 Hz.
[INFO] [Audio] Driver "pulse" reports a 18432-byte buffer: 48.0 ms of float at 48000 Hz against a 64 ms latency setting; rate control holds it near 24.0 ms.
[INFO] [XINERAMA] Saved monitor #0.
[DEBUG] [Video] Average monitor Hz: 60.002400 Hz. (2.969 % frame time deviation, based on 2048 last samples).
```
