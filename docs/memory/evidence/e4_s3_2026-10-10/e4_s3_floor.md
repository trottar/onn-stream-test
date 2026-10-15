# E4-S3 — the memory floor

**MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, pulseaudio, the desktop and the OS are outside it.**

| row | memory floor (CPU quota) | INCONCLUSIVE above it | at the floor: max / peak MB, anon / file MB at the peak, max events, PSI some / full | the step below: verdict, failing (value) |
| --- | --- | --- | --- | --- |
| PS1-STREAM | **<= 384M (384M passed)** (200 %) | 768M, 512M | 226.1 / 227.9; 191.1 / 21.4; 0; 0.00 / 0.00 | — |
| SNES-STREAM | **<= 384M (384M passed)** (150 %) | — | 196.3 / 197.4; 165.3 / 19.4; 0; 0.00 / 0.00 | — |
| CONC | **above 768M (failed at 768M; E4-S2 passed 1G with swap)** (CPU unset) | — | — / —; — / —; None; — / — | mem:768M: FAIL, rendered_fps (0.00), grabs_failed (1,489,544), no_journal_kill (574), unit_not_restarted (False) |
| META | **above 768M (failed at 768M; E4-S2 passed 1G with swap)** (150 %) | — | — / —; — / —; None; — / — | mem:768M: FAIL, grabs_failed (1,368,917), grabs_ok_min_per_channel (0), no_journal_kill (546), unit_not_restarted (False) |

**The stack's memory floor** (max over rows, swap off): not determined (a row has no floor in this ladder).
