| workload | metric | run 1 | run 2 | band | holds |
| --- | --- | --- | --- | --- | --- |
| E1-IDLE | **NOT RUN** | | |  | |
| E1-PS1-LOCAL | **NOT RUN** | | |  | |
| E1-SNES-STREAM | **NOT RUN** | | |  | |
| E1-PS1-STREAM | **NOT RUN** | | |  | |
| E1-PS1-1080P | **NOT RUN** | | |  | |
| E1-META | **NOT RUN** | | |  | |
| E1-CONC | **NOT RUN** | | |  | |
| E1-VOD | host CPU mean % | 0.796 | 0.85 | +/-2 points | yes |
|  | GPU busy mean % | 0 | 0 | +/-3 points | yes |
|  | RSS range_server (kB) | 24600 | 24612 | +/-5 % | yes |
|  | VOD progress ratio (played / wall) | 0.998 | 1.001 | +/-0.01 | yes |
|  | served kB/s (range server) | 0 | 0 | reported, not banded | — |
| | **REPEATABLE** | | |  | |
| E1-LIVETV | **ABSENT** | | | Live TV: no unattended channel start (no intent/extra/deep link; video is upstream -> onn) | |
| E1-BROWSER | **ABSENT** | | | browser source: Windows-only (PowerShell/ddagrab); no Linux implementation | |
| E1-CAMERA | **ABSENT** | | | camera source: Windows-only (dshow); no camera attached (no /dev/video*) | |
| E1-NES | **ABSENT** | | | NES: no fixture (games/nes empty) | |
| E1-GENESIS | **ABSENT** | | | Genesis: no fixture (games/genesis empty) | |
| E1-META-RECONCILE | **ABSENT** | | | metadata reconcile: writes library metadata (outside E1's no-change rule) | |
