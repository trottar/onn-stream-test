# E4-S3 — the cgroup's memory per run

**MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, pulseaudio, the desktop and the OS are outside it.**

| step | row | memory.current mean / max MB | memory.peak MB | anon / file MB at the peak | anon max MB | swap MB | events high / max / oom / oom_kill | PSI some / full ms/s | major faults | companion PSS MB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mem:768M | PS1-STREAM | 215.1 / 223.0 | 224.3 | 189.2 / 21.4 | 189.2 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 37.5 |
| mem:768M | SNES-STREAM | 191.0 / 194.5 | 196.4 | 163.5 / 19.3 | 163.6 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 38.8 |
| mem:768M | CONC | 448.2 / 765.5 | — | 742.7 / 0.1 | 742.7 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 32.0 |
| mem:768M | META | 448.5 / 765.3 | 666.1 | 742.1 / 0.2 | 742.1 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 31.5 |
| mem:512M | PS1-STREAM | 214.6 / 219.3 | 220.8 | 183.4 / 21.5 | 185.2 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 38.1 |
| mem:512M | SNES-STREAM | 191.5 / 196.8 | 198.3 | 165.1 / 19.9 | 165.1 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 38.6 |
| mem:384M | PS1-STREAM | 216.9 / 226.1 | 227.9 | 191.1 / 21.4 | 191.1 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 37.6 |
| mem:384M | SNES-STREAM | 191.1 / 196.3 | 197.4 | 165.3 / 19.4 | 165.4 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 38.6 |
| mem_repeat:768M | PS1-STREAM | 214.4 / 224.0 | 225.7 | 190.3 / 21.4 | 190.3 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 37.8 |
| mem_repeat:512M | PS1-STREAM | 214.8 / 223.2 | 224.8 | 189.6 / 21.2 | 189.6 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 38.3 |
