# E4-S5D — the confirmation runs on the five-line adopted state

| run | capture fps | dup+drop /min | encoder starts: input tbr → output fps (-r) | RetroArch | host CPU % | rendered* | loss/min* | resyncs* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1-SNES-STREAM | 59.964 | 0.05 | 60 → 60 (-r 60); 60 → 60 (-r 60) | 59.999 | 7.807 | 57.727 | 1006.14 | 54 |
| E1-PS1-STREAM | 59.942 | 0.101 | 1000k → 60 (-r 60) | 59.999 | 12.379 | 53.325 | 3349.47 | 108 |

\* the link: reported, not gated.

## Gates

- **E1-SNES-STREAM**: argv_r60_every_start ✓, capture_60_pm_0.1 ✓, dupdrop_le_0.2 ✓, retroarch_ge_59.9 ✓, host_cpu_pm_2_of_7.4 ✓
- **E1-PS1-STREAM**: capture_60_pm_0.1 ✓, dupdrop_le_0.2 ✓

**CONFIRMED**
