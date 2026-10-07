| workload | metric | run 1 | run 2 | band | holds |
| --- | --- | --- | --- | --- | --- |
| E1-IDLE | **NOT RUN** | | |  | |
| E1-PS1-LOCAL | **NOT RUN** | | |  | |
| E1-SNES-STREAM | host CPU mean % | 7.444 | 7.857 | +/-2 points | yes |
|  | GPU busy mean % | 7.366 | 8.039 | +/-3 points | yes |
|  | RSS retroarch (kB) | 147351.85 | 147187.75 | +/-5 % | yes |
|  | RetroArch frames/s | 59.999 | 59.999 | +/-0.5 | yes |
|  | rendered fps (heartbeat) | 59.986 | 59.968 | +/-0.5 | yes |
|  | video loss/min | 1.85 | 5.41 | reported, not banded | — |
|  | audio underruns | 7 | 11 | reported, not banded | — |
|  | max output gap ms (C2) | 64 | 64 | reported, not banded | — |
| | **REPEATABLE** | | |  | |
| E1-PS1-STREAM | **NOT RUN** | | |  | |
| E1-PS1-1080P | **NOT RUN** | | |  | |
| E1-META | **NOT RUN** | | |  | |
| E1-CONC | **NOT RUN** | | |  | |
| E1-VOD | **NOT RUN** | | |  | |
| E1-LIVETV | **ABSENT** | | | Live TV: no unattended channel start (no intent/extra/deep link; video is upstream -> onn) | |
| E1-BROWSER | **ABSENT** | | | browser source: Windows-only (PowerShell/ddagrab); no Linux implementation | |
| E1-CAMERA | **ABSENT** | | | camera source: Windows-only (dshow); no camera attached (no /dev/video*) | |
| E1-NES | **ABSENT** | | | NES: no fixture (games/nes empty) | |
| E1-GENESIS | **ABSENT** | | | Genesis: no fixture (games/genesis empty) | |
| E1-META-RECONCILE | **ABSENT** | | | metadata reconcile: writes library metadata (outside E1's no-change rule) | |
