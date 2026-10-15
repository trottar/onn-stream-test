# E4-S5C — the SNES capture fix on bad probes: the bench, the sink in cfr mode

| arm | sessions | bad probes (tbr ≠ 60) | tbr counts | output fps counts | drops at a 60 probe | output -r in the built command |
| --- | --- | --- | --- | --- | --- | --- |
| A (no flag) | 24 | 5 (0.208) | {'59': 1, '59.94': 4, '60': 19} | {'59': 1, '59.94': 4, '60': 19} | max 0 | [False] |
| B (flag) | 24 | 4 (0.167) | {'59': 2, '59.94': 2, '60': 20} | {'60': 24} | max 0 | [True] |

Bad-probe sessions:

| arm | index | tbr | output fps | drops | expected (A) | holds |
| --- | --- | --- | --- | --- | --- | --- |
| A | 10 | 59.94 | 59.94 | 2 | 3.6 | False |
| A | 14 | 59 | 59 | 58 | 60.0 | True |
| A | 18 | 59.94 | 59.94 | 2 | 3.6 | False |
| A | 22 | 59.94 | 59.94 | 2 | 3.6 | False |
| A | 24 | 59.94 | 59.94 | 2 | 3.6 | False |
| B | 7 | 59.94 | 60 | 0 | — | True |
| B | 9 | 59 | 60 | 0 | — | True |
| B | 15 | 59.94 | 60 | 0 | — | True |
| B | 33 | 59 | 60 | 0 | — | True |

Live session(s) (no flag for the companion):

| run | RetroArch | host CPU | bench cost (ffmpeg + Xorg extra) | host − bench | capture / dup+drop per min (companion, no flag) | rendered | loss/min |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runs_bench/E1-SNES-STREAM/run1 | 59.999 | 10.44 | 1.541 (1.393 + 0.148) | 8.898 | 59.97 / 1.669 | 58.912 | 339.73 |

Reading: mechanism reproduces in A: False; the fix works in B: True; sampled enough: True; host-clean: True.

**Verdict: INCONCLUSIVE (the mechanism did not reproduce in arm A)**
