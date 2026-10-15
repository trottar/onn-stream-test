# E4-S1 — drift from E2 (pre-registered §4)

E1's bands (§5); per-process rows as reported comparisons with the same bands. SNES / CONC: E4's run against E2's two-run range widened by the band. Link rows are not banded.

| row | metric | E4 | E2 | band | banded by E1? | drift | explained by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PS1-1080P | retroarch CPU % of a core | 36.52 | 22.50 | ± 2 | reported | **moved** | nothing does (no adoption touches this row/metric) |
| META | main-process RSS kB | 44,414 | 163,586 | ± 5 % | yes | **moved** | the guide index (E3-S6A): grabs read the cached index, no 25.6 MB parse in the companion |
| META | companion CPU % of a core | 0.22 | 7.65 | ± 2 | reported | **moved** | the guide index (E3-S6A): grabs read the cached index, no 25.6 MB parse in the companion |
| META | epg CPU % of a core | 73.96 | 66.82 | ± 2 | reported | **moved** | nothing does (no adoption touches this row/metric) |
| META | companion PSS kB | 33,913 | 153,118 | ± 5 % | reported | **moved** | the guide index (E3-S6A): grabs read the cached index, no 25.6 MB parse in the companion |
| SNES-STREAM | host CPU mean % | 7.42 | 43.38 / 50.02 | ± 2 | yes | **moved** | Snes9x (E3-A2): the SNES core changed (bsnes -> Snes9x) |
| SNES-STREAM | main-process RSS kB | 147,196 | 281,353 / 281,216 | ± 5 % | yes | **moved** | Snes9x (E3-A2): the SNES core changed (bsnes -> Snes9x) |
| SNES-STREAM | rendered fps | 58.74 | 59.66 / 59.98 | ± 0.5 | yes | **moved** | nothing does (no adoption touches this row/metric) |
| SNES-STREAM | retroarch CPU % of a core | 8.34 | 436.26 / 516.50 | ± 2 | reported | **moved** | Snes9x (E3-A2): the SNES core changed (bsnes -> Snes9x) |
| SNES-STREAM | retroarch PSS kB | 113,208 | 247,209 / 247,138 | ± 5 % | reported | **moved** | Snes9x (E3-A2): the SNES core changed (bsnes -> Snes9x) |
| CONC | rendered fps | 58.46 | 56.53 / 56.57 | ± 0.5 | yes | **moved** | nothing does (no adoption touches this row/metric) |
| CONC | companion CPU % of a core | 26.01 | 33.13 / 33.52 | ± 2 | reported | **moved** | the guide index (E3-S6A): grabs read the cached index, no 25.6 MB parse in the companion |
| CONC | epg CPU % of a core | 75.38 | 79.18 / 81.46 | ± 2 | reported | **moved** | nothing does (no adoption touches this row/metric) |
| CONC | companion PSS kB | 47,874 | 174,059 / 200,026 | ± 5 % | reported | **moved** | the guide index (E3-S6A): grabs read the cached index, no 25.6 MB parse in the companion |

Every compared metric within its band: 75 of 89; moved: 14.
