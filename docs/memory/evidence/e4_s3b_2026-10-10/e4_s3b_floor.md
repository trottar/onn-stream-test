# E4-S3B — the memory floor, closed (four rows, swap off)

**MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, pulseaudio, the desktop and the OS are outside it.**

| row | memory floor, swap off (CPU quota) | steps | at the floor: max / peak MB; anon / file MB at the peak; events high / max; PSI some / full ms/s | from |
| --- | --- | --- | --- | --- |
| PS1-STREAM | **<= 384M (384M passed)** (200 %) | 768M INCONCLUSIVE (link, repeated), 512M INCONCLUSIVE (link, repeated), 384M PASS (E4-S3) | 226.1 / 227.9; 191.1 / 21.4; — / 0; 0.00 / 0.00 | E4-S3 |
| SNES-STREAM | **<= 384M (384M passed)** (150 %) | 768M PASS, 512M PASS, 384M PASS (E4-S3) | 196.3 / 197.4; 165.3 / 19.4; — / 0; 0.00 / 0.00 | E4-S3 |
| CONC | **1536M (ADDENDUM reading: 1G OOM-killed before the window x2; 768M failed)** (CPU unset) | 768M FAIL (E4-S3); 1G INCONCLUSIVE x2 as judged -- OOM-killed before the window in both (run-span kills 3, 3); 1536M PASS, run-span kills 0 (addendum) | 1,147.4 / 1,165.8; 1,087.9 / 20.9; 0 / 0; 0.00 / 0.00 | E4-S3 + E4-S3B addendum |
| META | **1G (768M failed)** (150 %) | 768M FAIL (E4-S3); 1G PASS | 969.5 / 975.9; 940.4 / 0.2; 0 / 0; 0.00 / 0.00 | E4-S3 + E4-S3B |

**The stack's swap-off memory floor** (the maximum over the four rows): 1536M -- resting on the addendum reading for CONC (e4_s3b_addendum.txt).
