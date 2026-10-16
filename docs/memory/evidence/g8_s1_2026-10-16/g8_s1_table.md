# G8-S1 — the completed cells (partial)

| cell | validity | PLAYING (attempt, s) | RetroArch | capture | dup+drop /min | gates | host CPU % | companion % core | shim % core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | valid | 2, 3.0 | 59.999 | 59.988 | 0.1 | all met | 12.847 | 29.545 | 3.136 |
| 02_none_on | valid | 1, 3.1 | 59.999 | 60.038 | 0.1 | all met | 12.611 | 30.173 | 3.227 |
| 03_loss-1_off | valid | 1, 5.1 | 59.999 | 59.987 | 0.1 | all met | 11.893 | 28.48 | 2.886 |
| 04_loss-1_on | valid | 1, 3.1 | 59.999 | 59.989 | 0.1 | all met | 12.149 | 29.166 | 2.886 |
| 05_loss-5_off | valid | 1, 3.1 | 59.999 | 60.039 | 0.1 | all met | 11.874 | 29.192 | 2.923 |

| cell | loss/min heartbeat | pre-FEC /min | post-FEC /min | FEC recovered pkts | unrecoverable groups | rendered | stale /min | spikes≥20 ms /min | resyncs window | resyncs session | client pauses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | 6.03 | 31.54 | 17.85 | 158 | 23 | 59.959 | 1.033 | 43.28 | 0 | 1 | 0 |
| 02_none_on | 3.82 | 8.02 | 4.14 | 45 | 16 | 59.97 | 0.861 | 36.41 | 0 | 0 | 0 |
| 03_loss-1_off | 45.64 | 504.44 | 46.14 | 5334 | 201 | 59.515 | 3.003 | 45.04 | 0 | 0 | 0 |
| 04_loss-1_on | 68.47 | 524.8 | 65.09 | 5332 | 212 | 59.44 | 1.549 | 49.49 | 0 | 0 | 0 |
| 05_loss-5_off | 809.49 | 2511.62 | 809.29 | 19760 | 3570 | 52.616 | 1.635 | 39.49 | 0 | 0 | 0 |

| cell | rung min-max (polls) | ladder acted | rules suggestions (by rule) | wan class | wan windows (primary) | shim in / out | dropped loss / burst / queue | delayed | reordered | queue max | applied |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | 7000-7000 {'7000': 69} | 0 | 0  | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 27, 'clean': 41} | 665785 / 665785 | 0 / 0 / 0 | 0 | 0 | 48 | True |
| 02_none_on | 7000-7000 {'7000': 69} | 0 | 0  | clean | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 15, 'clean': 53} | 665626 / 665626 | 0 / 0 / 0 | 0 | 0 | 41 | True |
| 03_loss-1_off | 7000-7000 {'7000': 69} | 0 | 0  | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 0, 'lossy': 63, 'clean': 2} | 667286 / 660672 | 6614 / 0 / 0 | 0 | 0 | 39 | True |
| 04_loss-1_on | 7000-7000 {'7000': 69} | 0 | 0  | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 64, 'clean': 3} | 665602 / 658996 | 6606 / 0 / 0 | 0 | 0 | 42 | True |
| 05_loss-5_off | 7000-7000 {'7000': 69} | 0 | 0  | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 68, 'clean': 0} | 665619 / 632441 | 33178 / 0 / 0 | 0 | 0 | 37 | True |

Comparison (i): CL-B3 (no shim) beside the `none` cells.

| run | host CPU % | companion % core | RetroArch / encoder % core | rendered | loss/min | resyncs | rung |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CL-B3 R1 | 11.569 | 24.802 | 34.393 / 36.005 | 59.674 | 80.05 | 0 | [7000, 7000] |
| CL-B3 W | 11.593 | 25.435 | 35.743 / 35.381 | 59.795 | 60.32 | 3 | [7000, 7000] |
| G8-S1 01_none_off | 12.847 | 29.545 | (cells.jsonl keeps the companion only) | 59.959 | 6.03 | 0 | 7000-7000 |
| G8-S1 02_none_on | 12.611 | 30.173 | (cells.jsonl keeps the companion only) | 59.97 | 3.82 | 0 | 7000-7000 |

Comparison (iii): class vs intent.

| cell | intent | class | windows |
| --- | --- | --- | --- |
| 01_none_off | clean | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 27, 'clean': 41} |
| 02_none_on | clean | clean | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 15, 'clean': 53} |
| 03_loss-1_off | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 0, 'lossy': 63, 'clean': 2} |
| 04_loss-1_on | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 64, 'clean': 3} |
| 05_loss-5_off | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 68, 'clean': 0} |
