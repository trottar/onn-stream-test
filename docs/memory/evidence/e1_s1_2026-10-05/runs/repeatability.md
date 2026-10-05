| workload | metric | run 1 | run 2 | band | holds |
| --- | --- | --- | --- | --- | --- |
| E1-IDLE | host CPU mean % | 0.834 | 0.809 | +/-2 points | yes |
|  | GPU busy mean % | 0 | 0 | +/-3 points | yes |
|  | RSS companion (kB) | 37515.68 | 37224 | +/-5 % | yes |
| | **REPEATABLE** | | |  | |
| E1-PS1-LOCAL | host CPU mean % | 4.948 | 4.962 | +/-2 points | yes |
|  | GPU busy mean % | 18.653 | 18.693 | +/-3 points | yes |
|  | RSS retroarch (kB) | 235018.28 | 234687.067 | +/-5 % | yes |
|  | RetroArch frames/s | 59.999 | 59.999 | +/-0.5 | yes |
| | **REPEATABLE** | | |  | |
| E1-SNES-STREAM | host CPU mean % | 42.333 | 40.973 | +/-2 points | yes |
|  | GPU busy mean % | 8.01 | 8.99 | +/-3 points | yes |
|  | RSS retroarch (kB) | 281291.76 | 281371.813 | +/-5 % | yes |
|  | RetroArch frames/s | 59.992 | 59.999 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 58.471 | 58.913 | +/-0.5 | yes |
|  | video loss/min | 75.43 | 12.3 | reported, not banded | — |
|  | audio underruns | 0 | 3 | reported, not banded | — |
|  | max output gap ms (C2) | 79 | 46 | reported, not banded | — |
| | **REPEATABLE** | | |  | |
| E1-PS1-STREAM | host CPU mean % | 11.215 | 10.578 | +/-2 points | yes |
|  | GPU busy mean % | 23.063 | 21.423 | +/-3 points | yes |
|  | RSS retroarch (kB) | 242033.36 | 242296.947 | +/-5 % | yes |
|  | RetroArch frames/s | 59.999 | 59.998 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 59.96 | 59.884 | +/-0.5 | yes |
|  | video loss/min | 8.47 | 54.05 | reported, not banded | — |
|  | audio underruns | 9 | 8 | reported, not banded | — |
|  | max output gap ms (C2) | 26 | 71 | reported, not banded | — |
| | **REPEATABLE** | | |  | |
| E1-PS1-1080P | host CPU mean % | 15.76 | 15.046 | +/-2 points | yes |
|  | GPU busy mean % | 23.967 | 24.157 | +/-3 points | yes |
|  | RSS retroarch (kB) | 255174.573 | 253874.467 | +/-5 % | yes |
|  | RetroArch frames/s | 59.999 | 59.999 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 59.894 | 59.931 | +/-0.5 | yes |
|  | video loss/min | 8.27 | 11.42 | reported, not banded | — |
|  | audio underruns | 10 | 4 | reported, not banded | — |
|  | max output gap ms (C2) | 60 | 56 | reported, not banded | — |
|  | precondition: share of window at 1920x1080 | 1 | 1 | >= 0.95 each | yes |
| | **REPEATABLE** | | |  | |
| E1-META | host CPU mean % | 10.027 | 10.403 | +/-2 points | yes |
|  | GPU busy mean % | 0 | 0 | +/-3 points | yes |
|  | RSS companion (kB) | 172165.92 | 173249.76 | +/-5 % | yes |
|  | median grab s | 5.187 | 5.125 | +/-30 % | yes |
|  | grabs ok / failed | 58/0 | 61/0 | reported | — |
| | **REPEATABLE** | | |  | |
| E1-CONC | host CPU mean % | 21.975 | 22.441 | +/-2 points | yes |
|  | GPU busy mean % | 23.917 | 24.587 | +/-3 points | yes |
|  | RSS retroarch (kB) | 242934.24 | 242022.307 | +/-5 % | yes |
|  | RetroArch frames/s | 60 | 59.999 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 53.912 | 54.946 | +/-0.5 | **no** |
|  | video loss/min | 2826.61 | 2311.36 | reported, not banded | — |
|  | audio underruns | 141 | 144 | reported, not banded | — |
|  | max output gap ms (C2) | 170 | 376 | reported, not banded | — |
|  | median grab s | 5.926 | 5.907 | +/-30 % | yes |
|  | grabs ok / failed | 53/0 | 53/0 | reported | — |
| | **NOT YET REPEATABLE** | | | rendered fps (heartbeat) | |
| E1-LIVETV | **ABSENT** | | | Live TV: no unattended channel start (no intent/extra/deep link; video is upstream -> onn) | |
| E1-VOD | **ABSENT** | | | VOD: the configured media drive is not attached (vod_root: No such device) | |
| E1-BROWSER | **ABSENT** | | | browser source: Windows-only (PowerShell/ddagrab); no Linux implementation | |
| E1-CAMERA | **ABSENT** | | | camera source: Windows-only (dshow); no camera attached (no /dev/video*) | |
| E1-NES | **ABSENT** | | | NES: no fixture (games/nes empty) | |
| E1-GENESIS | **ABSENT** | | | Genesis: no fixture (games/genesis empty) | |
| E1-META-RECONCILE | **ABSENT** | | | metadata reconcile: writes library metadata (outside E1's no-change rule) | |
