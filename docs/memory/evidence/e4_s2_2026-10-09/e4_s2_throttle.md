# E4-S2 — the cgroup per run (how much the quota bit)

**CPUQuota= is CFS bandwidth: the stack gets at most N % of one core's time per period, on full-speed cores. This is a CPU-TIME floor, not a slow-core floor: a machine with fewer, equally fast cores behaves like this; a machine with slower cores does not, exactly. No lower-tier hardware claim.**

| step | row | constraint | CPU used (cores) | periods | throttled periods | share | throttled s (20 min) | memory.current mean / max MB | memory.peak MB | swap max MB | events high / max / oom / oom_kill |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cpu:400 | PS1-STREAM | CPUQuota=400% | 1.072 | 11952 | 0 | 0.000 | 0.0 | 215.6 / 227.1 | 228.4 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:400 | SNES-STREAM | CPUQuota=400% | 0.610 | 11952 | 0 | 0.000 | 0.0 | 191.4 / 194.7 | 196.4 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:400 | CONC | CPUQuota=400% | 2.181 | 11951 | 183 | 0.015 | 21.0 | 661.6 / 1,115 | 1,172 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:400 | META | CPUQuota=400% | 1.145 | 11276 | 85 | 0.007 | 3.3 | 488.9 / 965.4 | 981.7 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:300 | PS1-STREAM | CPUQuota=300% | 0.947 | 11951 | 0 | 0.000 | 0.0 | 219.5 / 225.2 | 226.9 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:300 | SNES-STREAM | CPUQuota=300% | 0.614 | 11951 | 0 | 0.000 | 0.0 | 191.3 / 195.4 | 196.8 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:300 | CONC | CPUQuota=300% | 2.107 | 11951 | 1762 | 0.147 | 125.3 | 664.8 / 1,141 | 1,163 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:300 | META | CPUQuota=300% | 1.137 | 11348 | 179 | 0.016 | 16.8 | 474.5 / 971.3 | 981.6 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:200 | PS1-STREAM | CPUQuota=200% | 0.975 | 11951 | 0 | 0.000 | 0.0 | 214.8 / 220.8 | 222.8 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:200 | SNES-STREAM | CPUQuota=200% | 0.612 | 11951 | 0 | 0.000 | 0.0 | 192.1 / 195.3 | 197.2 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:200 | META | CPUQuota=200% | 1.074 | 11206 | 1753 | 0.156 | 90.9 | 480.1 / 973.5 | 987.5 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:150 | PS1-STREAM | CPUQuota=150% | 1.121 | 11951 | 2 | 0.000 | 0.0 | 213.5 / 219.0 | 220.2 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:150 | SNES-STREAM | CPUQuota=150% | 0.615 | 11951 | 0 | 0.000 | 0.0 | 191.4 / 194.5 | 196.3 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:150 | META | CPUQuota=150% | 0.936 | 11096 | 4955 | 0.447 | 325.8 | 511.8 / 972.9 | 991.2 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:100 | PS1-STREAM | CPUQuota=100% | 0.944 | 11951 | 487 | 0.041 | 29.1 | 215.7 / 224.8 | 226.9 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:100 | SNES-STREAM | CPUQuota=100% | 0.614 | 11951 | 0 | 0.000 | 0.0 | 191.5 / 197.0 | 198.2 | 0.0 | 0 / 0 / 0 / 0 |
| cpu:100 | META | CPUQuota=100% | 0.708 | 10885 | 7909 | 0.727 | 792.7 | 475.9 / 934.3 | 985.1 | 0.0 | 0 / 0 / 0 / 0 |
| cpu_repeat:150 | SNES-STREAM | CPUQuota=150% | 0.608 | 11951 | 0 | 0.000 | 0.0 | 191.6 / 200.6 | 202.6 | 0.0 | 0 / 0 / 0 / 0 |
| mem:4G | PS1-STREAM | CPUQuota=200%+MemoryMax=4G | 0.959 | 11951 | 0 | 0.000 | 0.0 | 213.2 / 219.6 | 221.6 | 0.0 | 0 / 0 / 0 / 0 |
| mem:4G | SNES-STREAM | CPUQuota=150%+MemoryMax=4G | 0.610 | 11952 | 0 | 0.000 | 0.0 | 193.1 / 200.6 | 202.2 | 0.0 | 0 / 0 / 0 / 0 |
| mem:4G | CONC | MemoryMax=4G | 2.100 | None | None | — | — | 657.7 / 1,131 | 1,168 | 0.0 | 0 / 0 / 0 / 0 |
| mem:4G | META | CPUQuota=150%+MemoryMax=4G | 0.990 | 11392 | 5252 | 0.461 | 345.3 | 494.7 / 955.0 | 976.1 | 0.0 | 0 / 0 / 0 / 0 |
| mem:2G | PS1-STREAM | CPUQuota=200%+MemoryMax=2G | 0.957 | 11952 | 0 | 0.000 | 0.0 | 216.0 / 224.9 | 226.6 | 0.0 | 0 / 0 / 0 / 0 |
| mem:2G | SNES-STREAM | CPUQuota=150%+MemoryMax=2G | 0.604 | 11952 | 0 | 0.000 | 0.0 | 191.1 / 194.2 | 196.2 | 0.0 | 0 / 0 / 0 / 0 |
| mem:2G | CONC | MemoryMax=2G | 2.105 | None | None | — | — | 667.2 / 1,150 | 1,163 | 0.0 | 0 / 0 / 0 / 0 |
| mem:2G | META | CPUQuota=150%+MemoryMax=2G | 0.946 | 11184 | 4966 | 0.444 | 336.5 | 503.7 / 966.4 | 973.3 | 0.0 | 0 / 0 / 0 / 0 |
| mem:1G | PS1-STREAM | CPUQuota=200%+MemoryMax=1G | 0.960 | 11951 | 0 | 0.000 | 0.0 | 214.3 / 219.3 | 221.1 | 0.0 | 0 / 0 / 0 / 0 |
| mem:1G | SNES-STREAM | CPUQuota=150%+MemoryMax=1G | 0.607 | 11951 | 0 | 0.000 | 0.0 | 191.6 / 194.8 | 196.7 | 0.0 | 0 / 0 / 0 / 0 |
| mem:1G | CONC | MemoryMax=1G | 2.112 | None | None | — | — | 544.0 / 1,024 | 1,024 | 127.5 | 0 / 204 / 0 / 0 |
| mem:1G | META | CPUQuota=150%+MemoryMax=1G | 0.936 | 11019 | 4988 | 0.453 | 327.5 | 471.5 / 931.8 | 966.1 | 0.0 | 0 / 0 / 0 / 0 |
