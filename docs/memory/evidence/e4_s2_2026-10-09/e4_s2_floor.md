# E4-S2 — the floor

**CPUQuota= is CFS bandwidth: the stack gets at most N % of one core's time per period, on full-speed cores. This is a CPU-TIME floor, not a slow-core floor: a machine with fewer, equally fast cores behaves like this; a machine with slower cores does not, exactly. No lower-tier hardware claim.**

| row | CPU floor | INCONCLUSIVE above it | CPU used / throttled s / share at the floor | the step below: verdict, first failing metric (value) | memory floor (at CPUQuota) | memory at the floor (max MB, swap MB) | the memory step below |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PS1-STREAM | **150 %** | — | 1.12 cores / 0.0 s / 0.000 | cpu:100: FAIL, rendered_fps (55.1), encoder_dupdrop_per_min (0.653) | **<= 1G (1G passed)** (CPUQuota 200) | 219.3, 0.0 | — |
| SNES-STREAM | **<= 100 % (100 % passed)** | — | 0.61 cores / 0.0 s / 0.000 | — | **<= 1G (1G passed)** (CPUQuota 150) | 194.8, 0.0 | — |
| CONC | **400 %** | — | 2.18 cores / 21.0 s / 0.015 | cpu:300: FAIL, retroarch_fps (59.9), encoder_dupdrop_per_min (7.5) | **<= 1G (1G passed)** (CPUQuota unset) | 1,024, 127.5 | — |
| META | **<= 100 % (100 % passed)** | — | 0.71 cores / 792.7 s / 0.727 | — | **<= 1G (1G passed)** (CPUQuota 150) | 931.8, 0.0 | — |

**The stack's CPU-time floor** (max over rows): 400 %; **memory floor** (max over rows): 1G.
