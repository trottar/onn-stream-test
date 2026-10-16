# CL-B3 — the PS1-STREAM runs

| run | window (UTC) | capture fps | dup+drop /min | RetroArch | host CPU %† | rung kbps (polls) | ladder acted | companion / RetroArch / encoder % of a core | flags_absent after | rendered* | loss/min* | resyncs* |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 `runs/E1-PS1-STREAM/run1` | 17:30-17:40 | 59.988 | 0.1 | 59.999 | 11.569 | [7000, 7000] {'7000': 69} | 0 | 24.802 / 34.393 / 36.005 | True | 59.674 | 80.05 | 0 |
| W `runs/E1-PS1-STREAM_flag/run1` | 17:48-17:58 | 60.036 | 0.1 | 59.999 | 11.593 | [7000, 7000] {'7000': 69} | 0 | 25.435 / 35.743 / 35.381 | True | 59.795 | 60.32 | 3 |

† reported, not gated (the CL-B2 bar lesson). \* the link: reported, not gated.

W's cost (companion, W − R1): 0.633 point of a core, 0.35 MB PSS (≤ 0.5 / ≤ 2: False / True).

**ALL HOST GATES HOLD**
