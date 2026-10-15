# E4-S5 §1 — the offline pass (13 Snes9x windows, 3 PS1 for contrast)

| run | class | capture / drops per s | 1st min | before it | encoder input (x11grab) | discovered | RetroArch: core fps / audio rate / video size / GL res / SET_GEOMETRY | launch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| e3_a2_2026-10-07/SNES-STREAM/run1 | **CLEAN** | 60.019 / 0.0 | 59.99 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 2, 3.0 s |
| e3_s4_2026-10-07/SNES-STREAM_flag/run1 | **CLEAN** | 59.994 / 0.0 | 59.99 | None | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 2, 5.1 s |
| e3_s4_2026-10-07/SNES-STREAM_flag/run2 | **CLEAN** | 59.995 / 0.0 | 60.0 | E1-SNES-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.0 s |
| e4_s1_2026-10-09/SNES-STREAM/run1 | **FAULT (partial, >= 2 min)** | 59.017 / 1.0 | 58.99 | E1-VOD | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 59 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 2, 3.0 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu100/run1 | **CLEAN** | 59.993 / 0.0 | 60.0 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.1 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu150/run1 | **CLEAN** | 59.957 / 0.059 | 59.93 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 59.94 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.1 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu150/run2 | **CLEAN** | 60.019 / 0.0 | 60.0 | E1-META | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 2, 6.1 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu150_mem1G/run1 | **CLEAN** | 59.994 / 0.0 | 59.99 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.0 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu150_mem2G/run1 | **CLEAN** | 59.993 / 0.0 | 59.99 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | None / None / None / None / None | 1, 3.0 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu150_mem4G/run1 | **CLEAN** | 59.932 / 0.059 | 59.93 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 59.94 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.0 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu200/run1 | **CLEAN** | 59.994 / 0.0 | 60.0 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | None / None / None / None / None | 1, 3.0 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu300/run1 | **CLEAN** | 59.994 / 0.0 | 59.99 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.0 s |
| e4_s2_2026-10-09/SNES-STREAM_cpu400/run1 | **FAULT (partial, >= 2 min)** | 58.993 / 0.999 | 58.99 | E1-PS1-STREAM | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 59 tbr, 1000k tbn (1 sess.) | 897x672 | 60.0988 / 31987.32 / 897x672 / 897x672 / 1 | 1, 3.0 s |
| e4_s1_2026-10-09/PS1-STREAM/run1 | **CLEAN** | 59.993 / 0.0 | 59.99 | E1-PS1-LOCAL | rawvideo (BGR[0] / 0x524742), bgr0, 1920x1080, 3981312 kb/s, 60 fps, 1000k tbr, 1000k tbn (1 sess.) | 1920x1080 | 59.9400 / 44144.14 / None / 1920x1080 / 24 | 2, 3.1 s |
| e4_s2_2026-10-09/PS1-STREAM_cpu400/run1 | **CLEAN** | 60.017 / 0.0 | 59.99 | None | rawvideo (BGR[0] / 0x524742), bgr0, 1920x1080, 3981312 kb/s, 60 fps, 1000k tbr, 1000k tbn (1 sess.) | 1920x1080 | 59.9400 / 44144.14 / None / 1920x1080 / 24 | 1, 3.0 s |
| e4_s2_2026-10-09/PS1-STREAM_cpu200/run1 | **CLEAN** | 59.993 / 0.0 | 59.99 | E1-META | rawvideo (BGR[0] / 0x524742), bgr0, 1920x1080, 3981312 kb/s, 60 fps, 1000k tbr, 1000k tbn (1 sess.) | 1920x1080 | 59.9400 / 44144.14 / None / 1920x1080 / 24 | 2, 4.1 s |

Faulty: 2 (E1-SNES-STREAM/run1, E1-SNES-STREAM_cpu400/run1); clean: 11.

**The reading rule** (a value that differs between every faulty window and every clean window names the cause):

| field | faulty values | clean values | separates? |
| --- | --- | --- | --- |
| previous_row | E1-PS1-STREAM, E1-VOD | E1-META, E1-PS1-STREAM, E1-SNES-STREAM, None | no |
| hour_utc | 08, 10 | 07, 08, 11, 13, 14, 15, 16, 17, 18, 20, 23 | no |
| launch_attempt | 1, 2 | 1, 2 | no |
| encoder_sessions | 1 | 1 | no |
| enc_input | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 59 tbr, 1000k tbn | rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 59.94 tbr, 1000k tbn, rawvideo (BGR[0] / 0x524742), bgr0, 897x672, 1157345 kb/s, 60 fps, 60 tbr, 1000k tbn | **yes** |
| enc_discovered | 897x672 | 897x672 | no |
| enc_core | Snes9x | Snes9x | no |
| ra_core_fps | 60.0988 | 60.0988, None | no |
| ra_audio_input_rate | 31987.32 | 31987.32, None | no |
| ra_video_size | 897x672 | 897x672, None | no |
| ra_gl_resolution | 897x672 | 897x672, None | no |
| ra_swap_fn | glXSwapIntervalEXT. | None, glXSwapIntervalEXT. | no |
| ra_set_geometry | 1 | 1, None | no |
| ra_screen | 1920x1080 | 1920x1080, None | no |
| ra_audio_buffer | 18432 | 18432, None | no |

**Separating fields:** enc_input.

## Every Snes9x encoder session in `native_video_alpha.log`: x11grab's probed frame rate (tbr) vs the encoder's output rate

| session start (UTC) | input tbr | output fps | drops at the session's end | frames |
| --- | --- | --- | --- | --- |
| 2026-10-07T07:43:01+00:00 | 60 | 60 | 0 | 11346 |
| 2026-10-07T07:58:02+00:00 | 60 | 60 | 0 | 77993 |
| 2026-10-07T08:22:25+00:00 | 60 | 60 | 0 | 77843 |
| 2026-10-07T22:45:02+00:00 | 59.94 | 59.94 | 1 | 2312 |
| 2026-10-07T23:54:00+00:00 | 60 | 60 | 0 | 77899 |
| 2026-10-09T08:31:16+00:00 | 59 | 59 | 1295 | 76606 |
| 2026-10-09T10:03:00+00:00 | 59 | 59 | 1295 | 76611 |
| 2026-10-09T11:39:04+00:00 | 60 | 60 | 0 | 77913 |
| 2026-10-09T13:15:15+00:00 | 60 | 60 | 0 | 77903 |
| 2026-10-09T14:26:50+00:00 | 59.94 | 59.94 | 75 | 77824 |
| 2026-10-09T15:38:36+00:00 | 60 | 60 | 0 | 77873 |
| 2026-10-09T16:26:21+00:00 | 60 | 60 | 0 | 78053 |
| 2026-10-09T17:14:55+00:00 | 59.94 | 59.94 | 75 | 77824 |
| 2026-10-09T18:51:18+00:00 | 60 | 60 | 0 | 77903 |
| 2026-10-09T20:27:44+00:00 | 60 | 60 | 0 | 77843 |

PS1 (Beetle PSX HW) sessions: 638; input tbr values ['1000k', 'None']; output fps values ['60', 'None'].
