# B23 — the recorded silences through the real hold detector at H 950 and H 450

Whole logs (no 10-s edge exclusion: stricter than WAN-R1); a hold on a gap ≥ 3 s is real, else false. `replay_holds.py`, read only.

H 450 + guard (addendum 1): the session starts at 450 and reverts to 950 at its first non-drop hold.

| log | class | silences ≥ 250 | drops ≥ 3 s | H 950: real / false | H 450: real / false | H 450 + guard: real / false | false gaps at 450 (ms) |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| G4-S4 (friend's broadband) | direct | 3 | 3 | 3 / **0** | 3 / **0** | 3 / **0** | — |
| G4-S1 run 1 (hotspot) | direct | 2 | 1 | 1 / **0** | 1 / **0** | 1 / **0** | — |
| G4-S1 run 2 (hotspot; incl. the no-peer span after the toggle) | direct + no-peer | 54 | 0 | 0 / **1** | 0 / **18** | 0 / **2** | 516, 484, 525, 794, 1894, 632, 548, 780, 553, 486, 640, 467 |
| G4-S2 run 1 (hotspot) | direct | 2 | 2 | 2 / **0** | 2 / **0** | 2 / **0** | — |
| G4-S3 (hotspot) | direct | 1 | 1 | 1 / **0** | 1 / **0** | 1 / **0** | — |
| LINK-R1 (5 GHz) | lan | 0 | 0 | 0 / **0** | 0 / **0** | 0 / **0** | — |
| G-A3 (5 GHz) | lan | 0 | 0 | 0 / **0** | 0 / **0** | 0 / **0** | — |
| CL-B10 cell 1 (5 GHz) | lan | 2 | 2 | 2 / **0** | 2 / **0** | 2 / **0** | — |
| CL-B11 cell 1 (5 GHz) | lan | 7 | 1 | 1 / **0** | 1 / **2** | 1 / **1** | 540, 564 |
| CL-B12 cell 1 (5 GHz) | lan | 2 | 2 | 2 / **0** | 2 / **0** | 2 / **0** | — |
| CL-B10 cell 4 (2.4 GHz; reference, not a WAN-R1 window) | lan 2.4 | 221 | 2 | 2 / **10** | 2 / **59** | 2 / **10** | 1536, 612, 478, 513, 499, 1054, 711, 927, 540, 952, 787, 1162 |
