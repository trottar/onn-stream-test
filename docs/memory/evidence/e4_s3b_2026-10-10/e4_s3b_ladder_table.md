# E4-S3B — the memory ladder at 1G swap off, every run

**MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, pulseaudio, the desktop and the OS are outside it.**

Control (PS1-STREAM, unconstrained) video loss/min: 218.2 -> the link FAILS D-BASE's loss row.

| step | row | constraint | verdict | failing | rendered_fps | retroarch_fps | capture_fps | spikes_20ms_per_min | stale_drops_per_min | encoder_dupdrop_per_min | grabs_failed | grabs_ok_min_per_channel | guide_serves | no_oom_kill | no_journal_kill | unit_not_restarted | loss/min | grab median s | fail streaks / attempts | epg.jsonl KB | run-span kills (addendum reading) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control | PS1-STREAM |  | **INCONCLUSIVE** | rendered_fps | **59.48** | 60.00 | 59.99 | 60.22 | 1.90 | 0.05 |  |  |  | 0 | 0 | True | 218.2 | — | — | — | 0 |
| mem:1G | CONC | MemoryMax=1G+MemorySwapMax=0 | **INCONCLUSIVE** | rendered_fps | **0.00** | **—** | **—** | 2.64 | 0.37 | **—** | 0 |  |  | 0 | 0 | True | 0.0 | 4.76 | 0 / 0 | 60.5 | 3 |
| mem:1G | META | CPUQuota=150%+MemoryMax=1G+MemorySwapMax=0 | **PASS** | — |  |  |  |  |  |  | 0 | 38 | True | 0 | 0 | True | — | 5.51 | 0 / 0 | 53.1 | 0 |
| mem_repeat:1G | CONC | MemoryMax=1G+MemorySwapMax=0 | **INCONCLUSIVE** | rendered_fps | **0.00** | **—** | **—** | 6.77 | 1.98 | **—** | 0 |  |  | 0 | 0 | True | 0.0 | 4.77 | 0 / 0 | 60.1 | 3 |
| addendum:1536M | CONC | MemoryMax=1536M+MemorySwapMax=0 | **PASS** | — | 58.29 | 60.00 | 59.99 | 60.18 | 1.24 | 0.05 | 0 |  |  | 0 | 0 | True | 862.9 | 5.30 | 0 / 0 | 55.6 | 0 |
