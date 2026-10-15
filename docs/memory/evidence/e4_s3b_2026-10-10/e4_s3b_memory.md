# E4-S3B — the cgroup's memory per run

**MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, pulseaudio, the desktop and the OS are outside it.**

| step | row | memory.current mean / max MB | memory.peak MB | anon / file MB at the peak | anon max MB | swap MB | events high / max / oom / oom_kill | PSI some / full ms/s | major faults | companion PSS MB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control | PS1-STREAM | 217.1 / 227.3 | 229.4 | 193.6 / 21.4 | 193.7 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 39.0 |
| mem:1G | CONC | 491.0 / 970.5 | 975.8 | 941.6 / 0.7 | 941.6 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 33.8 |
| mem:1G | META | 477.5 / 969.5 | 975.9 | 940.4 / 0.2 | 940.4 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 33.0 |
| mem_repeat:1G | CONC | 462.9 / 974.0 | 976.6 | 944.4 / 0.8 | 944.4 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 34.0 |
| addendum:1536M | CONC | 649.4 / 1,147.4 | 1,165.8 | 1,087.9 / 20.9 | 1,087.9 | 0.0 | 0 / 0 / 0 / 0 | 0.00 / 0.00 | 0 | 48.5 |
