# E4-S5B — the SNES capture fix on bad probes: the bench

| arm | sessions | bad probes (tbr ≠ 60) | tbr counts | output fps counts | drops at a 60 probe | output -r in the built command |
| --- | --- | --- | --- | --- | --- | --- |
| A (no flag) | 24 | 1 (0.042) | {'59.94': 1, '60': 23} | {'59.94': 1, '60': 23} | max 0 | [False] |
| B (flag) | 24 | 4 (0.167) | {'59': 1, '59.94': 3, '60': 20} | {'60': 24} | max 0 | [True] |

Bad-probe sessions:

| arm | index | tbr | output fps | drops | expected (A) | holds |
| --- | --- | --- | --- | --- | --- | --- |
| A | 42 | 59.94 | 59.94 | 0 | 3.6 | False |
| B | 21 | 59 | 60 | 0 | — | True |
| B | 27 | 59.94 | 60 | 0 | — | True |
| B | 31 | 59.94 | 60 | 0 | — | True |
| B | 33 | 59.94 | 60 | 0 | — | True |

Live session(s) (no flag for the companion):

| run | RetroArch | host CPU | bench cost (ffmpeg + Xorg extra) | host − bench | capture / dup+drop per min (companion, no flag) | rendered | loss/min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runs_bench/E1-SNES-STREAM/run1 | 59.999 | 10.11 | 1.516 (1.375 + 0.141) | 8.595 | 59.944 / 2.246 | 58.344 | 538.99 |

PS1-STREAM with the flag:

`{"status": "OK", "capture_fps": 59.991, "dupdrop_per_min": 0.1, "retroarch_fps": 59.999, "host_cpu": 12.109, "rendered_fps": 59.846, "loss_per_min": 39.39, "resyncs": 0}`
clauses: {'capture_60_pm_0.1': True, 'dupdrop_le_0.2': True, 'retroarch_ge_59.9': True, 'host_cpu_pm_2': True}; the companion's last 1920x1080 probes (tbr, output fps): [('1000k', '60')]

Reading: mechanism reproduces in A: False; the fix works in B: True; sampled enough: True; host-clean: True; PS1: True.

**Verdict: INCONCLUSIVE (the mechanism did not reproduce in arm A)**
