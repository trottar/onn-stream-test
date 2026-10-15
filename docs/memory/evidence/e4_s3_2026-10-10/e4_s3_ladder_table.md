# E4-S3 — the memory ladder, every run

**MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, pulseaudio, the desktop and the OS are outside it.**

Control (the first PS1-STREAM, at 768M) video loss/min: 184.9 -> the link FAILS D-BASE's loss row.

| step | row | constraint | verdict | failing | rendered_fps | retroarch_fps | capture_fps | spikes_20ms_per_min | stale_drops_per_min | encoder_dupdrop_per_min | grabs_failed | grabs_ok_min_per_channel | guide_serves | no_oom_kill | no_journal_kill | unit_not_restarted | loss/min | grab median s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mem:768M | PS1-STREAM | CPUQuota=200%+MemoryMax=768M+MemorySwapMax=0 | **INCONCLUSIVE** | rendered_fps | **59.35** | 60.00 | 60.02 | 88.73 | 6.05 | 0.10 |  |  |  | 0 | 0 | True | 184.9 | — |
| mem:768M | SNES-STREAM | CPUQuota=150%+MemoryMax=768M+MemorySwapMax=0 | **PASS** | — | 58.64 | 60.00 | 59.97 | 166.26 | 7.03 | 0.05 |  |  |  | 0 | 0 | True | 405.5 | — |
| mem:768M | CONC | MemoryMax=768M+MemorySwapMax=0 | **FAIL** | rendered_fps, grabs_failed, no_journal_kill, unit_not_restarted | **0.00** | **—** | **—** | 2.22 | 0.28 | **—** | **1,489,544** |  |  | 0 | **574** | **False** | 0.0 | 4.83 |
| mem:768M | META | CPUQuota=150%+MemoryMax=768M+MemorySwapMax=0 | **FAIL** | grabs_failed, grabs_ok_min_per_channel, no_journal_kill, unit_not_restarted |  |  |  |  |  |  | **1,368,917** | **0** | True | 0 | **546** | **False** | — | 5.52 |
| mem:512M | PS1-STREAM | CPUQuota=200%+MemoryMax=512M+MemorySwapMax=0 | **INCONCLUSIVE** | rendered_fps | **59.39** | 60.00 | 59.99 | 92.42 | 3.01 | 0.10 |  |  |  | 0 | 0 | True | 181.9 | — |
| mem:512M | SNES-STREAM | CPUQuota=150%+MemoryMax=512M+MemorySwapMax=0 | **PASS** | — | 58.45 | 60.00 | 58.99 | 114.45 | 2.77 | 59.93 |  |  |  | 0 | 0 | True | 126.2 | — |
| mem:384M | PS1-STREAM | CPUQuota=200%+MemoryMax=384M+MemorySwapMax=0 | **PASS** | — | 59.56 | 60.00 | 59.99 | 89.53 | 3.60 | 0.10 |  |  |  | 0 | 0 | True | 92.1 | — |
| mem:384M | SNES-STREAM | CPUQuota=150%+MemoryMax=384M+MemorySwapMax=0 | **PASS** | — | 58.70 | 60.00 | 58.99 | 98.34 | 1.67 | 59.93 |  |  |  | 0 | 0 | True | 68.3 | — |
| mem_repeat:768M | PS1-STREAM | CPUQuota=200%+MemoryMax=768M+MemorySwapMax=0 | **INCONCLUSIVE** | rendered_fps | **59.34** | 60.00 | 60.02 | 78.04 | 2.22 | 0.10 |  |  |  | 0 | 0 | True | 217.6 | — |
| mem_repeat:512M | PS1-STREAM | CPUQuota=200%+MemoryMax=512M+MemorySwapMax=0 | **INCONCLUSIVE** | rendered_fps | **58.77** | 60.00 | 59.99 | 121.25 | 7.12 | 0.05 |  |  |  | 0 | 0 | True | 352.7 | — |
