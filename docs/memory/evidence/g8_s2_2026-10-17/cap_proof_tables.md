# G8-S2 cap proof — the start rung against the shim's cap profiles (in process; no claim about PLAYING)

30 s per case; the real FEC sender (default pacing) -> the shim @post-fec -> a capture playing the client. Predictions (design §4, written before): drop ≈ 1 − cap / (1.179 × rung) when above the cap.

| cap | start | source | shim in kbps (steady) | out kbps | predicted drop | tail-dropped (steady / all) | FEC recovered / unrecoverable groups | lost after FEC /min | complete frames | first incomplete at | G5-S1 windows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cap-6000 | 7000 | synthetic | 8252.6 | 6000.0 | 27.3 % | 30.1 % / 29.9 % | 0 / 146 | 12866.0 | 0.7 % | 0.22 | capacity-limited 3 |
| cap-6000 | 7000 | recorded c3_l4_nft_night3_2026-09-30 @ 13:15:23Z | 8321.4 | 6000.3 | 27.3 % | 30.5 % / 30.2 % | 0 / 142 | 12974.7 | 1.9 % | 0.53 | capacity-limited 3 |
| cap-6000 | 7000 | recorded c3_l4_nft_night1_2026-09-29 @ 15:20:34Z | 8317.2 | 6000.0 | 27.3 % | 30.4 % / 29.6 % | 0 / 133 | 12628.9 | 3.1 % | 0.75 | capacity-limited 3 |
| cap-6000 | 5000 | synthetic | 6102.7 | 6000.3 | 0.0 % | 1.8 % / 1.7 % | 1 / 0 | 2.0 | 99.9 % | 19.75 | clean 3 |
| cap-6000 | 5000 | recorded c3_l4_nft_night3_2026-09-30 @ 13:15:23Z | 6137.0 | 6000.3 | 0.0 % | 2.4 % / 2.3 % | 7 / 2 | 327.6 | 95.9 % | 7.27 | clean 1, lossy 2 |
| cap-6000 | 5000 | recorded c3_l4_nft_night1_2026-09-29 @ 15:20:34Z | 6137.0 | 5999.9 | 0.0 % | 2.2 % / 2.1 % | 4 / 1 | 208.7 | 98.5 % | 6.77 | clean 1, lossy 2 |
| cap-6000 | 4000 | synthetic | 4634.8 | 4635.5 | 0.0 % | 0.0 % / 0.0 % | 0 / 0 | 0.0 | 100.0 % | None | clean 3 |
| cap-6000 | 4000 | recorded c3_l4_nft_night3_2026-09-30 @ 13:15:23Z | 4675.5 | 4675.8 | 0.0 % | 0.0 % / 0.0 % | 0 / 0 | 0.0 | 100.0 % | None | clean 3 |
| cap-6000 | 4000 | recorded c3_l4_nft_night1_2026-09-29 @ 15:20:34Z | 4672.4 | 4673.1 | 0.0 % | 0.0 % / 0.0 % | 0 / 0 | 0.0 | 100.0 % | None | clean 3 |
| cap-4500 | 7000 | synthetic | 8252.3 | 4500.2 | 45.5 % | 47.6 % / 47.5 % | 176 / 88 | 18640.0 | 0.3 % | 0.1 | capacity-limited 3 |
| cap-4500 | 7000 | recorded c3_l4_nft_night3_2026-09-30 @ 13:15:23Z | 8318.3 | 4500.4 | 45.5 % | 47.9 % / 47.6 % | 208 / 99 | 18692.2 | 1.4 % | 0.4 | capacity-limited 3 |
| cap-4500 | 7000 | recorded c3_l4_nft_night1_2026-09-29 @ 15:20:34Z | 8316.8 | 4500.4 | 45.5 % | 47.8 % / 47.2 % | 176 / 94 | 18398.9 | 0.7 % | 0.2 | capacity-limited 3 |
| cap-4500 | 5000 | synthetic | 6103.3 | 4500.3 | 23.6 % | 28.9 % / 28.6 % | 230 / 0 | 4238.0 | 1.5 % | 0.23 | capacity-limited 3 |
| cap-4500 | 5000 | recorded c3_l4_nft_night3_2026-09-30 @ 13:15:23Z | 6136.0 | 4500.5 | 23.6 % | 29.9 % / 29.6 % | 221 / 7 | 4783.6 | 2.7 % | 0.55 | capacity-limited 3 |
| cap-4500 | 5000 | recorded c3_l4_nft_night1_2026-09-29 @ 15:20:34Z | 6137.7 | 4500.2 | 23.6 % | 29.4 % / 28.7 % | 208 / 2 | 4488.6 | 4.7 % | 1.25 | capacity-limited 3 |
| cap-4500 | 4000 | synthetic | 4635.2 | 4500.3 | 4.5 % | 5.8 % / 5.4 % | 191 / 0 | 646.0 | 82.1 % | 2.83 | lossy 3 |
| cap-4500 | 4000 | recorded c3_l4_nft_night3_2026-09-30 @ 13:15:23Z | 4675.1 | 4500.4 | 4.5 % | 5.7 % / 5.5 % | 129 / 2 | 731.1 | 85.1 % | 4.27 | lossy 3 |
| cap-4500 | 4000 | recorded c3_l4_nft_night1_2026-09-29 @ 15:20:34Z | 4672.4 | 4499.7 | 4.5 % | 5.5 % / 5.3 % | 140 / 1 | 682.0 | 85.8 % | 3.87 | lossy 3 |
