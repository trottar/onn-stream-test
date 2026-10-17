# G8-S1 — all cells (22; valid 18)

## Table 1: host side

| cell | validity | suite attempts (failed) | PLAYING (attempt, s) | code version (counted run) | RetroArch | capture | dup+drop /min | gates | host CPU % | companion % core |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | valid | 1 (0) | 2, 3.0 | pre-registered | 59.999 | 59.988 | 0.1 | all met | 12.847 | 29.545 |
| 02_none_on | valid | 1 (0) | 1, 3.1 | pre-registered | 59.999 | 60.038 | 0.1 | all met | 12.611 | 30.173 |
| 03_loss-1_off | valid | 1 (0) | 1, 5.1 | pre-registered | 59.999 | 59.987 | 0.1 | all met | 11.893 | 28.48 |
| 04_loss-1_on | valid | 1 (0) | 1, 3.1 | pre-registered | 59.999 | 59.989 | 0.1 | all met | 12.149 | 29.166 |
| 05_loss-5_off | valid | 1 (0) | 1, 3.1 | pre-registered | 59.999 | 60.039 | 0.1 | all met | 11.874 | 29.192 |
| 06_loss-5_on | valid | 3 (2) | 1, 10.1 | G5-S3 edits | 59.999 | 59.987 | 0.1 | all met | 13.749 | 26.645 |
| 07_burst-50x20_off | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 60.04 | 0.1 | all met | 11.853 | 27.46 |
| 08_burst-50x20_on | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 59.987 | 0.1 | all met | 13.541 | 29.737 |
| 09_delay-50_off | valid | 1 (0) | 1, 8.1 | G5-S3 + G5-S4 edits | 59.999 | 59.987 | 0.1 | all met | 11.975 | 28.869 |
| 10_delay-50_on | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 60.038 | 0.1 | all met | 12.037 | 28.833 |
| 11_delay-150_off | valid | 1 (0) | 1, 3.0 | G5-S3 + G5-S4 edits | 59.999 | 60.037 | 0.1 | all met | 13.056 | 28.532 |
| 12_delay-150_on | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.998 | 59.989 | 0.1 | all met | 12.757 | 29.023 |
| 13_jitter-30_off | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 59.988 | 0.1 | all met | 12.145 | 29.5 |
| 14_jitter-30_on | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 59.988 | 0.1 | all met | 11.902 | 28.702 |
| 15_reorder-5_off | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 59.987 | 0.1 | all met | 13.129 | 29.05 |
| 16_reorder-5_on | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 59.986 | 0.1 | all met | 13.239 | 29.353 |
| 17_cap-6000_off | no_play (FAILED) | 3 (2) | None, None | G5-S3 + G5-S4 edits | None | None | None | not read (no window) | None | None |
| 18_cap-6000_on | no_play (FAILED) | 3 (2) | None, None | G5-S3 + G5-S4 edits | None | None | None | not read (no window) | None | None |
| 19_cap-4500_off | no_play (FAILED) | 3 (2) | None, None | G5-S3 + G5-S4 edits | None | None | None | not read (no window) | None | None |
| 20_cap-4500_on | no_play (FAILED) | 3 (2) | None, None | G5-S3 + G5-S4 edits | None | None | None | not read (no window) | None | None |
| 21_delay-50+loss-1_off | valid | 1 (0) | 1, 5.1 | G5-S3 + G5-S4 edits | 59.999 | 59.987 | 0.1 | all met | 13.379 | 29.535 |
| 22_delay-50+loss-1_on | valid | 1 (0) | 1, 3.1 | G5-S3 + G5-S4 edits | 59.999 | 59.988 | 0.1 | all met | 13.974 | 30.688 |

## Table 2: the link

| cell | loss/min heartbeat | pre-FEC /min | post-FEC /min | FEC recovered pkts | unrecoverable groups | rendered | stale /min | spikes≥20 ms /min | resyncs window | resyncs session | client pauses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | 6.03 | 31.54 | 17.85 | 158 | 23 | 59.959 | 1.033 | 43.28 | 0 | 1 | 0 |
| 02_none_on | 3.82 | 8.02 | 4.14 | 45 | 16 | 59.97 | 0.861 | 36.41 | 0 | 0 | 0 |
| 03_loss-1_off | 45.64 | 504.44 | 46.14 | 5334 | 201 | 59.515 | 3.003 | 45.04 | 0 | 0 | 0 |
| 04_loss-1_on | 68.47 | 524.8 | 65.09 | 5332 | 212 | 59.44 | 1.549 | 49.49 | 0 | 0 | 0 |
| 05_loss-5_off | 809.49 | 2511.62 | 809.29 | 19760 | 3570 | 52.616 | 1.635 | 39.49 | 0 | 0 | 0 |
| 06_loss-5_on | 700.64 | 4547.61 | 3305.42 | 14476 | 2669 | 53.802 | 4.676 | 124.38 | 2 | 36 | 0 |
| 07_burst-50x20_off | 940.66 | 843.21 | 829.14 | 163 | 214 | 57.518 | 16.693 | 210.47 | 12 | 11 | 1 |
| 08_burst-50x20_on | 146.24 | 152.2 | 147.88 | 50 | 53 | 59.692 | 1.807 | 90.26 | 0 | 0 | 0 |
| 09_delay-50_off | 18.83 | 29.81 | 19.28 | 123 | 44 | 59.806 | 3.503 | 95.53 | 0 | 0 | 0 |
| 10_delay-50_on | 14.38 | 24.39 | 14.83 | 111 | 39 | 59.908 | 1.291 | 78.15 | 0 | 0 | 0 |
| 11_delay-150_off | 724.8 | 657.04 | 627.85 | 338 | 238 | 58.252 | 7.137 | 186.33 | 10 | 10 | 0 |
| 12_delay-150_on | 356.35 | 331.09 | 308.39 | 263 | 157 | 58.728 | 15.914 | 149.07 | 4 | 3 | 0 |
| 13_jitter-30_off | 337.03 | 356.34 | 286.93 | 804 | 405 | 58.292 | 13.597 | 189.93 | 3 | 3 | 0 |
| 14_jitter-30_on | 91.59 | 148.03 | 95.78 | 606 | 315 | 59.404 | 1.463 | 103.79 | 0 | 0 | 0 |
| 15_reorder-5_off | 19.6 | 393.58 | 18.45 | 4352 | 28 | 59.77 | 1.118 | 68.81 | 0 | 0 | 0 |
| 16_reorder-5_on | 23.0 | 411.32 | 24.2 | 4496 | 37 | 59.78 | 2.064 | 74.84 | 0 | 0 | 0 |
| 17_cap-6000_off | None | 13880.39 | 13845.89 | 20 | 212 | None | 9.648 | 14.47 | None | 1 | 0 |
| 18_cap-6000_on | None | 11953.93 | 11909.02 | 23 | 160 | None | 10.901 | 15.75 | None | 1 | 0 |
| 19_cap-4500_off | None | 17621.82 | 17466.49 | 101 | 152 | None | 10.928 | 14.57 | None | 1 | 0 |
| 20_cap-4500_on | None | 17979.38 | 17828.88 | 119 | 192 | None | 19.41 | 20.62 | None | 0 | 0 |
| 21_delay-50+loss-1_off | 96.82 | 595.68 | 116.66 | 5572 | 318 | 59.241 | 1.974 | 62.82 | 0 | 1 | 0 |
| 22_delay-50+loss-1_on | 85.52 | 634.33 | 161.58 | 5486 | 277 | 59.308 | 1.635 | 64.55 | 0 | 2 | 0 |

## Table 3: the ladder, the rules, the classifier, the shim

| cell | rung min-max (polls) | rung path (decisions.jsonl) | rules suggestions by rule (driver's line count) | wan class | wan windows (primary) | shim in / out | dropped loss / burst / queue | delayed | reordered | queue max | applied |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 27, 'clean': 41} | 665785 / 665785 | 0 / 0 / 0 | 0 | 0 | 48 | True |
| 02_none_on | 7000-7000 {'7000': 69} | none | 0  (0) | clean | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 15, 'clean': 53} | 665626 / 665626 | 0 / 0 / 0 | 0 | 0 | 41 | True |
| 03_loss-1_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 0, 'lossy': 63, 'clean': 2} | 667286 / 660672 | 6614 / 0 / 0 | 0 | 0 | 39 | True |
| 04_loss-1_on | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 64, 'clean': 3} | 665602 / 658996 | 6606 / 0 / 0 | 0 | 0 | 42 | True |
| 05_loss-5_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 68, 'clean': 0} | 665619 / 632441 | 33178 / 0 / 0 | 0 | 0 | 37 | True |
| 06_loss-5_on | 5000-7000 {'5000': 59, '7000': 10} | 7000→5000 recovery_escalation (FALLBACK, 00:33:38Z, in window) | 296 {'R3.1': 2, 'R1.1': 2, 'R1.2': 86, 'R5.1': 206} (297) | path-changed | {'path-changed': 1, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 3, 'lossy': 59, 'clean': 0} | 634606 / 602889 | 31717 / 0 / 0 | 0 | 0 | 52 | True |
| 07_burst-50x20_off | 6000-7000 {'6000': 50, '7000': 19} | 7000→6000 capacity_mild (ROUTINE, 00:49:35Z, in window) | 0  (0) | path-changed | {'path-changed': 1, 'latency-limited': 0, 'starved': 8, 'capacity-limited': 0, 'lossy': 39, 'clean': 18} | 605715 / 603965 | 0 / 1750 / 0 | 0 | 0 | 42 | True |
| 08_burst-50x20_on | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 49, 'clean': 18} | 665747 / 663997 | 0 / 1750 / 0 | 0 | 0 | 42 | True |
| 09_delay-50_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 3, 'capacity-limited': 0, 'lossy': 34, 'clean': 32} | 668991 / 668974 | 0 / 0 / 0 | 668991 | 0 | 237 | True |
| 10_delay-50_on | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 30, 'clean': 38} | 665622 / 665616 | 0 / 0 / 0 | 665622 | 0 | 245 | True |
| 11_delay-150_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 8, 'capacity-limited': 0, 'lossy': 43, 'clean': 11} | 669637 / 669483 | 0 / 0 / 0 | 669637 | 0 | 582 | True |
| 12_delay-150_on | 6000-7000 {'6000': 23, '7000': 46} | 7000→6000 wan_rules (ROUTINE, 02:06:05Z, in window) | 112 {'R2.1': 23, 'R5.1': 89} (133) | path-changed | {'path-changed': 1, 'latency-limited': 0, 'starved': 7, 'capacity-limited': 0, 'lossy': 34, 'clean': 24} | 637818 / 637609 | 0 / 0 / 0 | 637818 | 0 | 588 | True |
| 13_jitter-30_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 9, 'capacity-limited': 0, 'lossy': 53, 'clean': 4} | 664638 / 664637 | 0 / 0 / 0 | 664638 | 0 | 171 | True |
| 14_jitter-30_on | 7000-7000 {'7000': 69} | none | 0  (0) | latency-limited | {'path-changed': 0, 'latency-limited': 1, 'starved': 2, 'capacity-limited': 0, 'lossy': 64, 'clean': 2} | 665472 / 665471 | 0 / 0 / 0 | 665472 | 0 | 148 | True |
| 15_reorder-5_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 45, 'clean': 23} | 666281 / 666281 | 0 / 0 / 0 | 0 | 31657 | 44 | True |
| 16_reorder-5_on | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 47, 'clean': 21} | 666228 / 666228 | 0 / 0 / 0 | 0 | 31654 | 41 | True |
| 17_cap-6000_off | None-None {} | none | 0  (0) | capacity-limited | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 2, 'lossy': 0, 'clean': 0} | 304866 / 219609 | 0 / 0 / 84913 | 0 | 0 | 73 | True |
| 18_cap-6000_on | None-None {} | none | 0  (0) | capacity-limited | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 2, 'lossy': 0, 'clean': 0} | 292555 / 213949 | 0 / 0 / 78378 | 0 | 0 | 69 | True |
| 19_cap-4500_off | None-None {} | none | 0  (0) | capacity-limited | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 3, 'lossy': 0, 'clean': 0} | 296996 / 165208 | 0 / 0 / 131524 | 0 | 0 | 56 | True |
| 20_cap-4500_on | None-None {} | none | 0  (0) | starved | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 3, 'lossy': 0, 'clean': 0} | 244806 / 136074 | 0 / 0 / 108547 | 0 | 0 | 56 | True |
| 21_delay-50+loss-1_off | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 66, 'clean': 1} | 666954 / 660338 | 6612 / 0 / 0 | 660342 | 0 | 239 | True |
| 22_delay-50+loss-1_on | 7000-7000 {'7000': 69} | none | 0  (0) | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 67, 'clean': 1} | 664715 / 658108 | 6599 / 0 / 0 | 658116 | 0 | 240 | True |

## Table 4: session loss and recovery events

| cell | recovery.jsonl rows | key.recovery pauses (controller / client / other) | gaps.jsonl rows | gap ms (max) |
| --- | --- | --- | --- | --- |
| 01_none_off | 0 | 0 / 0 / 0 | 0 | - |
| 02_none_on | 0 | 0 / 0 / 0 | 0 | - |
| 03_loss-1_off | 0 | 0 / 0 / 0 | 1 | 292 |
| 04_loss-1_on | 0 | 0 / 0 / 0 | 7 | 953 |
| 05_loss-5_off | 0 | 0 / 0 / 0 | 0 | - |
| 06_loss-5_on | 1 | 0 / 0 / 0 | 66 | 709 |
| 07_burst-50x20_off | 2 | 0 / 1 / 0 | 134 | 3697 |
| 08_burst-50x20_on | 0 | 0 / 0 / 0 | 8 | 823 |
| 09_delay-50_off | 0 | 0 / 0 / 0 | 21 | 910 |
| 10_delay-50_on | 0 | 0 / 0 / 0 | 7 | 340 |
| 11_delay-150_off | 0 | 0 / 0 / 0 | 204 | 2426 |
| 12_delay-150_on | 0 | 0 / 0 / 0 | 82 | 2485 |
| 13_jitter-30_off | 0 | 0 / 0 / 0 | 127 | 1812 |
| 14_jitter-30_on | 0 | 0 / 0 / 0 | 10 | 749 |
| 15_reorder-5_off | 0 | 0 / 0 / 0 | 14 | 416 |
| 16_reorder-5_on | 0 | 0 / 0 / 0 | 7 | 368 |
| 17_cap-6000_off | 0 | - | 0 | - |
| 18_cap-6000_on | 0 | - | 0 | - |
| 19_cap-4500_off | 0 | - | 0 | - |
| 20_cap-4500_on | 0 | - | 0 | - |
| 21_delay-50+loss-1_off | 0 | 0 / 0 / 0 | 2 | 319 |
| 22_delay-50+loss-1_on | 0 | 0 / 0 / 0 | 11 | 376 |

## Table 5: the shim's cost (sum cpu_s / sum segment seconds)

| cell | segments | shim seconds | shim % of a core | driver's figure |
| --- | --- | --- | --- | --- |
| 01_none_off | 1 | 698.0 | 3.136 | 3.136 |
| 02_none_on | 1 | 698.0 | 3.227 | 3.227 |
| 03_loss-1_off | 1 | 700.0 | 2.886 | 2.886 |
| 04_loss-1_on | 1 | 698.0 | 2.886 | 2.886 |
| 05_loss-5_off | 1 | 698.0 | 2.923 | 2.923 |
| 06_loss-5_on | 3 | 822.0 | 2.611 | 3.027 |
| 07_burst-50x20_off | 1 | 698.0 | 2.713 | 2.713 |
| 08_burst-50x20_on | 1 | 698.0 | 3.151 | 3.151 |
| 09_delay-50_off | 1 | 702.0 | 3.298 | 3.298 |
| 10_delay-50_on | 1 | 698.0 | 3.312 | 3.312 |
| 11_delay-150_off | 1 | 702.0 | 3.344 | 3.344 |
| 12_delay-150_on | 1 | 698.0 | 3.546 | 3.546 |
| 13_jitter-30_off | 1 | 697.0 | 3.836 | 3.836 |
| 14_jitter-30_on | 1 | 698.0 | 3.904 | 3.904 |
| 15_reorder-5_off | 1 | 699.0 | 2.86 | 2.86 |
| 16_reorder-5_on | 1 | 699.0 | 3.09 | 3.089 |
| 17_cap-6000_off | 6 | 326.0 | 5.32 | 27.973 |
| 18_cap-6000_on | 6 | 328.0 | 5.383 | 28.477 |
| 19_cap-4500_off | 6 | 324.0 | 4.452 | 24.042 |
| 20_cap-4500_on | 5 | 266.0 | 4.648 | 19.94 |
| 21_delay-50+loss-1_off | 1 | 699.0 | 3.377 | 3.377 |
| 22_delay-50+loss-1_on | 1 | 697.0 | 3.741 | 3.74 |

## Comparison (i): CL-B3 (no shim) beside the `none` cells

| run | host CPU % | companion % core | rendered | loss/min | resyncs | rung |
| --- | --- | --- | --- | --- | --- | --- |
| CL-B3 R1 | 11.569 | 24.802 | 59.674 | 80.05 | 0 | [7000, 7000] |
| CL-B3 W | 11.593 | 25.435 | 59.795 | 60.32 | 3 | [7000, 7000] |
| G8-S1 01_none_off | 12.847 | 29.545 | 59.959 | 6.03 | 0 | 7000-7000 |
| G8-S1 02_none_on | 12.611 | 30.173 | 59.97 | 3.82 | 0 | 7000-7000 |

## Comparison (ii): off vs on per profile

| profile | arm | rules suggestions: rule suggestion -> ladder result | rung path | rendered | stale /min | loss/min heartbeat | post-FEC /min (wan) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| none | off | 0 | none | 59.959 | 1.033 | 6.03 | 17.85 |
| none | on | 0 | none | 59.97 | 0.861 | 3.82 | 4.14 |
| loss-1 | off | 0 | none | 59.515 | 3.003 | 45.64 | 46.14 |
| loss-1 | on | 0 | none | 59.44 | 1.549 | 68.47 | 65.09 |
| loss-5 | off | 0 | none | 52.616 | 1.635 | 809.49 | 809.29 |
| loss-5 | on | {'R3.1 step_down -> refused:guard': 1, 'R3.1 step_down -> transition': 1, 'R1.1 hold -> none': 2, 'R1.2 no_step_up -> none': 86, 'R5.1 no_step_up -> none': 206} | 7000→5000 recovery_escalation (FALLBACK, 00:33:38Z, in window) | 53.802 | 4.676 | 700.64 | 3305.42 |
| burst-50x20 | off | 0 | 7000→6000 capacity_mild (ROUTINE, 00:49:35Z, in window) | 57.518 | 16.693 | 940.66 | 829.14 |
| burst-50x20 | on | 0 | none | 59.692 | 1.807 | 146.24 | 147.88 |
| delay-50 | off | 0 | none | 59.806 | 3.503 | 18.83 | 19.28 |
| delay-50 | on | 0 | none | 59.908 | 1.291 | 14.38 | 14.83 |
| delay-150 | off | 0 | none | 58.252 | 7.137 | 724.8 | 627.85 |
| delay-150 | on | {'R2.1 step_down -> transition': 1, 'R2.1 step_down -> none': 3, 'R2.1 step_down -> refused:hold_down': 19, 'R5.1 no_step_up -> none': 89} | 7000→6000 wan_rules (ROUTINE, 02:06:05Z, in window) | 58.728 | 15.914 | 356.35 | 308.39 |
| jitter-30 | off | 0 | none | 58.292 | 13.597 | 337.03 | 286.93 |
| jitter-30 | on | 0 | none | 59.404 | 1.463 | 91.59 | 95.78 |
| reorder-5 | off | 0 | none | 59.77 | 1.118 | 19.6 | 18.45 |
| reorder-5 | on | 0 | none | 59.78 | 2.064 | 23.0 | 24.2 |
| cap-6000 | off | no window | none | None | 9.648 | None | 13845.89 |
| cap-6000 | on | no window | none | None | 10.901 | None | 11909.02 |
| cap-4500 | off | no window | none | None | 10.928 | None | 17466.49 |
| cap-4500 | on | no window | none | None | 19.41 | None | 17828.88 |
| delay-50+loss-1 | off | 0 | none | 59.241 | 1.974 | 96.82 | 116.66 |
| delay-50+loss-1 | on | 0 | none | 59.308 | 1.635 | 85.52 | 161.58 |

## Comparison (iii): class vs intent

| cell | intent | class | windows (primary) | window counts (any class) | reports | goodput kbps | rtt ms p50/p95 | jitter ms p50/p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01_none_off | clean | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 27, 'clean': 41} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 27, 'clean': 41} | 345 | 7099.3 | 44.0/302.0 | 0.74/1.612 |
| 02_none_on | clean | clean | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 15, 'clean': 53} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 15, 'clean': 53} | 347 | 7098.0 | 43.0/306.4 | 0.712/1.871 |
| 03_loss-1_off | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 0, 'lossy': 63, 'clean': 2} | {'path-changed': 0, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 0, 'lossy': 67, 'clean': 2} | 348 | 7061.8 | 44.5/305.0 | 0.683/1.581 |
| 04_loss-1_on | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 64, 'clean': 3} | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 66, 'clean': 3} | 347 | 7049.3 | 45.0/307.0 | 0.804/1.913 |
| 05_loss-5_off | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 68, 'clean': 0} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 69, 'clean': 0} | 347 | 6782.4 | 43.0/302.8 | 0.74/1.667 |
| 06_loss-5_on | lossy | path-changed | {'path-changed': 1, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 3, 'lossy': 59, 'clean': 0} | {'path-changed': 1, 'latency-limited': 0, 'starved': 4, 'capacity-limited': 4, 'lossy': 67, 'clean': 0} | 335 | 5193.7 | 86.0/895.4 | 1.412/4.118 |
| 07_burst-50x20_off | lossy | path-changed | {'path-changed': 1, 'latency-limited': 0, 'starved': 8, 'capacity-limited': 0, 'lossy': 39, 'clean': 18} | {'path-changed': 1, 'latency-limited': 0, 'starved': 9, 'capacity-limited': 1, 'lossy': 48, 'clean': 18} | 331 | 6556.5 | 76.0/931.4 | 1.213/3.232 |
| 08_burst-50x20_on | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 49, 'clean': 18} | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 51, 'clean': 18} | 346 | 7369.4 | 72.5/308.25 | 1.066/2.639 |
| 09_delay-50_off | - | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 3, 'capacity-limited': 0, 'lossy': 34, 'clean': 32} | {'path-changed': 0, 'latency-limited': 0, 'starved': 3, 'capacity-limited': 0, 'lossy': 37, 'clean': 32} | 348 | 7351.2 | 73.0/334.75 | 1.043/2.52 |
| 10_delay-50_on | - | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 30, 'clean': 38} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 31, 'clean': 38} | 347 | 7312.2 | 66.0/313.8 | 1.006/2.586 |
| 11_delay-150_off | latency-limited | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 8, 'capacity-limited': 0, 'lossy': 43, 'clean': 11} | {'path-changed': 0, 'latency-limited': 0, 'starved': 8, 'capacity-limited': 0, 'lossy': 51, 'clean': 11} | 312 | 7450.9 | 97.0/1328.4 | 1.247/2.812 |
| 12_delay-150_on | latency-limited | path-changed | {'path-changed': 1, 'latency-limited': 0, 'starved': 7, 'capacity-limited': 0, 'lossy': 34, 'clean': 24} | {'path-changed': 1, 'latency-limited': 0, 'starved': 8, 'capacity-limited': 0, 'lossy': 42, 'clean': 24} | 334 | 6947.3 | 74.0/436.5 | 1.04/3.051 |
| 13_jitter-30_off | - | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 9, 'capacity-limited': 0, 'lossy': 53, 'clean': 4} | {'path-changed': 0, 'latency-limited': 0, 'starved': 9, 'capacity-limited': 0, 'lossy': 61, 'clean': 4} | 334 | 7336.0 | 79.5/810.8 | 1.84/3.826 |
| 14_jitter-30_on | - | latency-limited | {'path-changed': 0, 'latency-limited': 1, 'starved': 2, 'capacity-limited': 0, 'lossy': 64, 'clean': 2} | {'path-changed': 0, 'latency-limited': 1, 'starved': 2, 'capacity-limited': 0, 'lossy': 67, 'clean': 2} | 347 | 7324.3 | 69.0/336.8 | 1.846/3.61 |
| 15_reorder-5_off | - | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 45, 'clean': 23} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 45, 'clean': 23} | 347 | 7245.7 | 74.0/319.4 | 1.022/2.919 |
| 16_reorder-5_on | - | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 47, 'clean': 21} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 48, 'clean': 21} | 347 | 7258.3 | 71.0/321.8 | 1.01/2.627 |
| 17_cap-6000_off | capacity-limited | capacity-limited | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 2, 'lossy': 0, 'clean': 0} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 3, 'lossy': 3, 'clean': 0} | 18 | 5169.5 | 91.0/436.6 | 3.012/4.366 |
| 18_cap-6000_on | capacity-limited | capacity-limited | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 2, 'lossy': 0, 'clean': 0} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 3, 'lossy': 3, 'clean': 0} | 16 | 5448.0 | 96.0/120.6 | 2.689/2.979 |
| 19_cap-4500_off | capacity-limited | capacity-limited | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 3, 'lossy': 0, 'clean': 0} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 4, 'lossy': 4, 'clean': 0} | 20 | 4186.9 | 69.0/119.9 | 3.469/5.061 |
| 20_cap-4500_on | capacity-limited | starved | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 3, 'lossy': 0, 'clean': 0} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 4, 'lossy': 4, 'clean': 0} | 24 | 4207.9 | 101.0/392.8 | 3.237/5.862 |
| 21_delay-50+loss-1_off | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 66, 'clean': 1} | {'path-changed': 0, 'latency-limited': 0, 'starved': 2, 'capacity-limited': 0, 'lossy': 68, 'clean': 1} | 348 | 7242.0 | 70.0/310.75 | 0.98/2.344 |
| 22_delay-50+loss-1_on | lossy | lossy | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 67, 'clean': 1} | {'path-changed': 0, 'latency-limited': 0, 'starved': 1, 'capacity-limited': 0, 'lossy': 68, 'clean': 1} | 347 | 7296.9 | 73.0/343.4 | 0.988/2.511 |

## The cap cells: the suite's attempts and the client's reports

| cell | attempt file | started | code version | launch | client: duration ms / rendered frames / lost packets / max output gap ms / resyncs / audio underruns | flags absent after |
| --- | --- | --- | --- | --- | --- | --- |
| 17_cap-6000_off | summary_failed_attempt1.json | 03:07:45Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49480 / 23 / 10688 / 47521 / 1 / 5422 | True |
| 17_cap-6000_off | summary_failed_attempt2.json | 03:12:18Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49640 / 25 / 9194 / 47790 / 1 / 3970 | True |
| 17_cap-6000_off | summary.json | 03:16:51Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49751 / 20 / 10754 / 45988 / 1 / 4520 | True |
| 18_cap-6000_on | summary_failed_attempt1.json | 03:21:26Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49505 / 20 / 9529 / 47397 / 1 / 4968 | True |
| 18_cap-6000_on | summary_failed_attempt2.json | 03:26:01Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49377 / 16 / 9222 / 45577 / 1 / 5915 | True |
| 18_cap-6000_on | summary.json | 03:30:36Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49535 / 22 / 9219 / 45620 / 1 / 5279 | True |
| 19_cap-4500_off | summary_failed_attempt1.json | 03:35:12Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49534 / 11 / 16922 / 47753 / 1 / 5903 | True |
| 19_cap-4500_off | summary_failed_attempt2.json | 03:39:44Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49459 / 14 / 14378 / 47699 / 1 / 6091 | True |
| 19_cap-4500_off | summary.json | 03:44:17Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49416 / 14 / 14339 / 47234 / 1 / 4582 | True |
| 20_cap-4500_on | summary_failed_attempt1.json | 03:48:53Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49392 / 14 / 16878 / 47656 / 1 / 6112 | True |
| 20_cap-4500_on | summary_failed_attempt2.json | 03:53:25Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49285 / 15 / 14204 / 45702 / 1 / 5932 | True |
| 20_cap-4500_on | summary.json | 03:58:00Z | G5-S3 + G5-S4 edits | {'ok': False, 'recovery': 'ENDED'} | 49458 / 9 / 14499 / 47988 / 0 / 1 | True |

## The cap cells: the shim per stream start (segment)

| cell | cap kbps | segment | seconds | in / out packets | dropped_queue | queue max | steady in kbps | steady out kbps (max) | steady drop fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 17_cap-6000_off | 6000 | 1 | 60.0 | 57261 / 40934 | 16269 | 73 | 8258.1 | 6000.1 (6011.5) | 0.2856 |
| 17_cap-6000_off | 6000 | 2 | 48.0 | 45741 / 32697 | 12986 | 72 | 8259.4 | 6000.1 (6011.1) | 0.2855 |
| 17_cap-6000_off | 6000 | 3 | 60.0 | 53922 / 39452 | 14414 | 68 | 8251.6 | 6000.0 (6008.1) | 0.2688 |
| 17_cap-6000_off | 6000 | 4 | 49.0 | 43978 / 32176 | 11746 | 68 | 8253.0 | 6000.0 (6007.6) | 0.2688 |
| 17_cap-6000_off | 6000 | 5 | 62.0 | 59181 / 42304 | 16820 | 72 | 8259.4 | 6000.2 (6008.2) | 0.2855 |
| 17_cap-6000_off | 6000 | 6 | 47.0 | 44783 / 32046 | 12678 | 72 | 8257.0 | 6000.0 (6010.1) | 0.2847 |
| 18_cap-6000_on | 6000 | 1 | 60.0 | 53922 / 39455 | 14411 | 68 | 8252.6 | 6000.0 (6008.0) | 0.2686 |
| 18_cap-6000_on | 6000 | 2 | 50.0 | 43782 / 32100 | 11682 | 67 | 8043.8 | 5859.4 (6008.1) | 0.2685 |
| 18_cap-6000_on | 6000 | 3 | 62.0 | 55730 / 40644 | 15029 | 68 | 8253.0 | 6000.0 (6007.9) | 0.2709 |
| 18_cap-6000_on | 6000 | 4 | 48.0 | 42125 / 30794 | 11331 | 67 | 8064.6 | 5876.1 (6009.1) | 0.2708 |
| 18_cap-6000_on | 6000 | 5 | 62.0 | 55730 / 40764 | 14909 | 69 | 8253.0 | 5999.9 (6009.7) | 0.2688 |
| 18_cap-6000_on | 6000 | 6 | 46.0 | 41266 / 30192 | 11016 | 68 | 8253.0 | 6000.0 (6007.5) | 0.2688 |
| 19_cap-4500_off | 4500 | 1 | 60.0 | 57261 / 31564 | 25652 | 56 | 8259.4 | 4500.1 (4509.6) | 0.449 |
| 19_cap-4500_off | 4500 | 2 | 48.0 | 45742 / 25214 | 20482 | 56 | 8259.2 | 4499.9 (4508.1) | 0.4491 |
| 19_cap-4500_off | 4500 | 3 | 60.0 | 53923 / 30122 | 23758 | 52 | 8251.9 | 4500.0 (4509.3) | 0.4417 |
| 19_cap-4500_off | 4500 | 4 | 48.0 | 43074 / 24067 | 18962 | 52 | 8253.0 | 4500.0 (4507.6) | 0.4418 |
| 19_cap-4500_off | 4500 | 5 | 60.0 | 53922 / 30150 | 23730 | 52 | 8253.0 | 4500.1 (4510.7) | 0.4413 |
| 19_cap-4500_off | 4500 | 6 | 48.0 | 43074 / 24091 | 18940 | 52 | 8253.0 | 4500.2 (4509.5) | 0.4413 |
| 20_cap-4500_on | 4500 | 1 | 60.0 | 57261 / 31546 | 25668 | 56 | 8259.4 | 4499.9 (4509.3) | 0.4489 |
| 20_cap-4500_on | 4500 | 2 | 48.0 | 45742 / 25220 | 20477 | 55 | 8259.2 | 4500.0 (4509.4) | 0.4489 |
| 20_cap-4500_on | 4500 | 3 | 62.0 | 55730 / 31159 | 24525 | 52 | 8253.0 | 4500.0 (4507.8) | 0.4412 |
| 20_cap-4500_on | 4500 | 4 | 46.0 | 41266 / 23084 | 18140 | 52 | 8252.7 | 4500.3 (4508.8) | 0.4413 |
| 20_cap-4500_on | 4500 | 5 | 50.0 | 44807 / 25065 | 19737 | 52 | 8237.6 | 4500.2 (4509.6) | 0.442 |

## Reference: a valid cell's shim input (the stream at 7000 with FEC and audio)

| cell | segments | steady in kbps | steady out kbps |
| --- | --- | --- | --- |
| 01_none_off | 1 | 8296.5 | 8296.5 |
| 02_none_on | 1 | 8298.2 | 8298.2 |
| 09_delay-50_off | 1 | 8295.4 | 8295.8 |
| 10_delay-50_on | 1 | 8298.1 | 8298.7 |
| 15_reorder-5_off | 1 | 8294.9 | 8294.9 |
| 16_reorder-5_on | 1 | 8292.4 | 8292.4 |

PRIVYHUB_REMOTE* flags in any restart environ: none
