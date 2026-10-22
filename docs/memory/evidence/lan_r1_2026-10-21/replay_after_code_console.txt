# LAN-R1 replay: the two evenings through the real controller (inputs/ copies only)

## 1. Flag absent

| evening | client sessions | sample rows | recorded decision / state events | recorded reproduced | controller HEAD vs working tree (rows) |
| --- | ---: | ---: | ---: | --- | --- |
| UX-R1 Sunday (2026-10-20) | 41 | 1709 | 505 | exact | identical (2256) |
| UX-R2 last night (2026-10-21) | 12 | 1180 | 318 | exact | identical (1510) |

-> flag absent: PASS

## PRIVYHUB_LAN_LOSS_RULE=1 (T 4 unrecoverable groups per 10-s window on K 2 windows; one rung; floor 5000)

| span | client sessions | asks | taken (rung path) | refused (by reason) | the ladder's own transitions |
| --- | ---: | ---: | --- | --- | --- |
| UX-R1 Sunday (2026-10-20) | 41 | 7 | 05:03:05 7000->6000; 05:06:07 6000->5500; 05:10:48 5500->5000; 05:20:52 7000->6000 | refused:hold_down 3 | — |
| UX-R2 last night (2026-10-21) | 12 | 2 | — | refused:guard 2 | — |
| CL-B5 A pcm | 1 | 0 | — | — | — |
| CL-B5 B opus | 1 | 0 | — | — | — |
| CL-B5 L opus | 1 | 0 | — | — | — |
| CL-B6 1 opus | 1 | 0 | — | — | — |
| CL-B6 2 pcm | 1 | 0 | — | — | — |
| CL-B7 pcm | 1 | 0 | — | — | — |
| CL-B7 opus today | 1 | 0 | — | — | — |
| CL-B7 opus lean | 1 | 0 | — | — | — |
| G4-S3 (remote, 4000; no LAN part) | 5 | 0 | — | — | — |
| G8-S1 03 loss-1 off | 2 | 6 | 20:46:14 7000->6000; 20:49:21 6000->5500; 20:51:40 5500->5000 | refused:hold_down 3 | — |
| G8-S1 04 loss-1 on | 2 | 7 | 21:01:28 7000->6000; 21:05:45 6000->5500; 21:08:02 5500->5000 | refused:guard 1, refused:hold_down 3 | — |
| G8-S1 05 loss-5 off | 2 | 15 | 21:14:58 7000->6000; 21:17:04 6000->5500; 21:19:11 5500->5000 | refused:guard 2, refused:hold_down 10 | — |
| G8-S1 06 loss-5 on | 2 | 2 | — | refused:guard 2 | 00:33:38 7000->5000 recovery_escalation |
| G8-S1 07 burst-50x20 off | 2 | 5 | 00:49:33 7000->6000; 00:52:44 6000->5500 | refused:guard 1, refused:hold_down 2 | — |
| G8-S1 08 burst-50x20 on | 2 | 0 | — | — | — |
| G8-S1 21 delay-50+loss-1 off | 2 | 13 | 04:05:38 7000->6000; 04:07:43 6000->5500; 04:09:49 5500->5000 | refused:guard 2, refused:hold_down 8 | — |
| G8-S1 22 delay-50+loss-1 on | 2 | 10 | 04:19:56 7000->6000; 04:22:49 6000->5500; 04:25:22 5500->5000 | refused:guard 2, refused:hold_down 5 | — |

Every ask:

    UX-R1 Sunday (2026-10-20) 2026-10-20T05:03:05.138Z ask windows [4, 4] at 7000 -> transition
    UX-R1 Sunday (2026-10-20) 2026-10-20T05:06:07.834Z ask windows [6, 4] at 6000 -> transition
    UX-R1 Sunday (2026-10-20) 2026-10-20T05:06:55.010Z ask windows [17, 4] at 5500 -> refused:hold_down
    UX-R1 Sunday (2026-10-20) 2026-10-20T05:10:48.352Z ask windows [8, 5] at 5500 -> transition
    UX-R1 Sunday (2026-10-20) 2026-10-20T05:20:52.728Z ask windows [17, 6] at 7000 -> transition
    UX-R1 Sunday (2026-10-20) 2026-10-20T05:21:19.664Z ask windows [12, 10] at 6000 -> refused:hold_down
    UX-R1 Sunday (2026-10-20) 2026-10-20T05:21:44.911Z ask windows [24, 5] at 6000 -> refused:hold_down
    UX-R2 last night (2026-10-21) 2026-10-21T05:12:50.320Z ask windows [10, 5] at 7000 -> refused:guard
    UX-R2 last night (2026-10-21) 2026-10-21T05:17:32.678Z ask windows [5, 4] at 7000 -> refused:guard
    G8-S1 03 loss-1 off 2026-10-16T20:46:14.770Z ask windows [4, 4] at 7000 -> transition
    G8-S1 03 loss-1 off 2026-10-16T20:46:50.983Z ask windows [4, 4] at 6000 -> refused:hold_down
    G8-S1 03 loss-1 off 2026-10-16T20:47:11.079Z ask windows [4, 4] at 6000 -> refused:hold_down
    G8-S1 03 loss-1 off 2026-10-16T20:49:21.724Z ask windows [5, 4] at 6000 -> transition
    G8-S1 03 loss-1 off 2026-10-16T20:50:38.104Z ask windows [7, 4] at 5500 -> refused:hold_down
    G8-S1 03 loss-1 off 2026-10-16T20:51:40.408Z ask windows [4, 4] at 5500 -> transition
    G8-S1 04 loss-1 on 2026-10-16T20:59:52.280Z ask windows [4, 5] at 7000 -> refused:guard
    G8-S1 04 loss-1 on 2026-10-16T21:01:28.762Z ask windows [4, 4] at 7000 -> transition
    G8-S1 04 loss-1 on 2026-10-16T21:02:21.123Z ask windows [5, 4] at 6000 -> refused:hold_down
    G8-S1 04 loss-1 on 2026-10-16T21:03:13.252Z ask windows [4, 4] at 6000 -> refused:hold_down
    G8-S1 04 loss-1 on 2026-10-16T21:05:45.975Z ask windows [4, 4] at 6000 -> transition
    G8-S1 04 loss-1 on 2026-10-16T21:07:38.495Z ask windows [4, 4] at 5500 -> refused:hold_down
    G8-S1 04 loss-1 on 2026-10-16T21:08:02.597Z ask windows [4, 4] at 5500 -> transition
    G8-S1 05 loss-5 off 2026-10-16T21:14:17.746Z ask windows [45, 63] at 7000 -> refused:guard
    G8-S1 05 loss-5 off 2026-10-16T21:14:37.885Z ask windows [57, 65] at 7000 -> refused:guard
    G8-S1 05 loss-5 off 2026-10-16T21:14:58.035Z ask windows [57, 40] at 7000 -> transition
    G8-S1 05 loss-5 off 2026-10-16T21:15:24.200Z ask windows [35, 47] at 6000 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:15:44.321Z ask windows [56, 39] at 6000 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:16:04.433Z ask windows [49, 54] at 6000 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:16:24.545Z ask windows [57, 46] at 6000 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:16:44.663Z ask windows [52, 42] at 6000 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:17:04.750Z ask windows [49, 42] at 6000 -> transition
    G8-S1 05 loss-5 off 2026-10-16T21:17:30.901Z ask windows [58, 55] at 5500 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:17:51.015Z ask windows [47, 64] at 5500 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:18:11.142Z ask windows [54, 48] at 5500 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:18:31.213Z ask windows [53, 67] at 5500 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:18:51.334Z ask windows [52, 49] at 5500 -> refused:hold_down
    G8-S1 05 loss-5 off 2026-10-16T21:19:11.424Z ask windows [53, 54] at 5500 -> transition
    G8-S1 06 loss-5 on 2026-10-17T00:32:18.849Z ask windows [80, 69] at 7000 -> refused:guard
    G8-S1 06 loss-5 on 2026-10-17T00:32:39.190Z ask windows [47, 66] at 7000 -> refused:guard
    G8-S1 07 burst-50x20 off 2026-10-17T00:48:56.377Z ask windows [22, 9] at 7000 -> refused:guard
    G8-S1 07 burst-50x20 off 2026-10-17T00:49:33.423Z ask windows [14, 5] at 7000 -> transition
    G8-S1 07 burst-50x20 off 2026-10-17T00:50:08.790Z ask windows [10, 8] at 6000 -> refused:hold_down
    G8-S1 07 burst-50x20 off 2026-10-17T00:51:08.170Z ask windows [7, 13] at 6000 -> refused:hold_down
    G8-S1 07 burst-50x20 off 2026-10-17T00:52:44.735Z ask windows [10, 4] at 6000 -> transition
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:04:32.217Z ask windows [7, 10] at 7000 -> refused:guard
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:04:58.331Z ask windows [5, 4] at 7000 -> refused:guard
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:05:38.593Z ask windows [6, 5] at 7000 -> transition
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:06:08.780Z ask windows [6, 5] at 6000 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:06:32.872Z ask windows [12, 5] at 6000 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:06:52.988Z ask windows [8, 10] at 6000 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:07:15.072Z ask windows [7, 4] at 6000 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:07:43.213Z ask windows [4, 5] at 6000 -> transition
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:08:09.341Z ask windows [5, 4] at 5500 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:08:29.465Z ask windows [7, 5] at 5500 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:08:57.646Z ask windows [4, 5] at 5500 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:09:17.695Z ask windows [6, 4] at 5500 -> refused:hold_down
    G8-S1 21 delay-50+loss-1 off 2026-10-17T04:09:49.842Z ask windows [5, 4] at 5500 -> transition
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:18:48.323Z ask windows [7, 8] at 7000 -> refused:guard
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:19:08.490Z ask windows [4, 6] at 7000 -> refused:guard
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:19:56.821Z ask windows [11, 4] at 7000 -> transition
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:20:22.990Z ask windows [6, 4] at 6000 -> refused:hold_down
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:20:57.153Z ask windows [4, 5] at 6000 -> refused:hold_down
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:21:17.281Z ask windows [6, 4] at 6000 -> refused:hold_down
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:21:41.457Z ask windows [5, 5] at 6000 -> refused:hold_down
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:22:49.774Z ask windows [6, 5] at 6000 -> transition
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:24:46.376Z ask windows [4, 4] at 5500 -> refused:hold_down
    G8-S1 22 delay-50+loss-1 on 2026-10-17T04:25:22.583Z ask windows [7, 5] at 5500 -> transition

