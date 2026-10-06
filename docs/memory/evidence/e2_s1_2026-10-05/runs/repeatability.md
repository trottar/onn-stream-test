| workload | metric | run 1 | run 2 | band | holds |
| --- | --- | --- | --- | --- | --- |
| E1-IDLE | **NOT RUN** | | |  | |
| E1-PS1-LOCAL | **NOT RUN** | | |  | |
| E1-SNES-STREAM | host CPU mean % | 43.378 | 50.018 | +/-2 points | **no** |
|  | GPU busy mean % | 7.988 | 7.018 | +/-3 points | yes |
|  | RSS retroarch (kB) | 281353.007 | 281215.613 | +/-5 % | yes |
|  | RetroArch frames/s | 59.993 | 59.999 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 59.659 | 59.978 | +/-0.5 | yes |
|  | video loss/min | 49.11 | 2.46 | reported, not banded | — |
|  | audio underruns | 7 | 15 | reported, not banded | — |
|  | max output gap ms (C2) | 74 | 65 | reported, not banded | — |
| | **NOT YET REPEATABLE** | | | host CPU mean % | |
| E1-PS1-STREAM | **NOT RUN** | | |  | |
| E1-PS1-1080P | **NOT RUN** | | |  | |
| E1-META | **NOT RUN** | | |  | |
| E1-CONC | host CPU mean % | 20.546 | 21.898 | +/-2 points | yes |
|  | GPU busy mean % | 23.587 | 21.708 | +/-3 points | yes |
|  | RSS retroarch (kB) | 270941.367 | 271696.5 | +/-5 % | yes |
|  | RetroArch frames/s | 59.999 | 59.999 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 56.532 | 56.571 | +/-0.5 | yes |
|  | video loss/min | 1622.33 | 1601.54 | reported, not banded | — |
|  | audio underruns | 448 | 312 | reported, not banded | — |
|  | max output gap ms (C2) | 473 | 421 | reported, not banded | — |
|  | median grab s | 5.88 | 5.816 | +/-30 % | yes |
|  | grabs ok / failed | 208/0 | 214/0 | reported | — |
| | **REPEATABLE** | | |  | |
| E1-VOD | **NOT RUN** | | |  | |
| E1-LIVETV | **ABSENT** | | | Live TV: no unattended channel start (no intent/extra/deep link; video is upstream -> onn) | |
| E1-BROWSER | **ABSENT** | | | browser source: Windows-only (PowerShell/ddagrab); no Linux implementation | |
| E1-CAMERA | **ABSENT** | | | camera source: Windows-only (dshow); no camera attached (no /dev/video*) | |
| E1-NES | **ABSENT** | | | NES: no fixture (games/nes empty) | |
| E1-GENESIS | **ABSENT** | | | Genesis: no fixture (games/genesis empty) | |
| E1-META-RECONCILE | **ABSENT** | | | metadata reconcile: writes library metadata (outside E1's no-change rule) | |
