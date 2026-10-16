# G8-P1 proof tables

## A. Each profile, 60 s, synthetic 7 Mbit/s RTP (60 fps x 12 x 1200 B)

Baseline loopback delay (no impairment), median: 0.193 ms, subtracted below.

| profile | tolerance | loss % | bursts | added delay mean / p95 ms | spread p95-p5 ms | reordered % | out kbit/s | queue max (bound) | shim CPU % of a core | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `none` | no loss, no reorder (the baseline delay is subtracted from the rest) | 0.0 | 0 | -1.16 / 0.32 | 16.42 | 0.0 | 6913.8 | 12 (—) | 2.09 | **PASS** |
| `loss-1` | loss 0.7-1.3 % | 1.104 | 0 | -1.37 / 0.11 | 16.43 | 0.0 | 6837.5 | 12 (—) | 2.08 | **PASS** |
| `loss-5` | loss 4.5-5.5 % | 5.178 | 0 | -1.43 / 0.11 | 16.45 | 0.0 | 6555.8 | 12 (—) | 2.07 | **PASS** |
| `burst-50x20` | 3 bursts of exactly 50 (at 10 / 30 / 50 s) | 0.347 | 3 | -1.37 / 0.1 | 16.43 | 0.0 | 6889.8 | 12 (—) | 2.05 | **PASS** |
| `delay-50` | mean added delay 45-56 ms, no loss | 0.0 | 0 | 48.69 / 50.21 | 16.43 | 0.0 | 6908.0 | 48 (—) | 2.33 | **PASS** |
| `delay-150` | mean added delay 145-156 ms, no loss | 0.0 | 0 | 148.7 / 150.22 | 16.44 | 0.0 | 6896.5 | 120 (—) | 2.38 | **PASS** |
| `jitter-30` | mean 10-30 ms, p95-p5 spread 18-34 ms, order kept | 0.0 | 0 | 23.6 / 29.81 | 18.44 | 0.0 | 6910.7 | 24 (—) | 3.79 | **PASS** |
| `reorder-5` | reordered 4-6 %, no loss | 0.0 | 0 | -1.29 / 0.12 | 16.45 | 4.991 | 6913.8 | 13 (—) | 2.09 | **PASS** |
| `cap-6000` | out 5700-6300 kbit/s, queue within its bound | 13.072 | 0 | 89.79 / 97.71 | 14.95 | 0.0 | 6000.3 | 63 (64) | 6.97 | **PASS** |
| `cap-4500` | out 4275-4725 kbit/s, queue within its bound | 34.803 | 0 | 89.69 / 97.35 | 14.91 | 0.0 | 4500.3 | 48 (48) | 6.07 | **PASS** |
| `loss-1+delay-50+jitter-30` | loss 0.7-1.3 %, mean added delay 55-80 ms | 1.032 | 0 | 73.52 / 79.81 | 18.48 | 0.0 | 6833.5 | 60 (—) | 3.78 | **PASS** |

Shim CPU, the highest profile: 6.97 % of a core (the bar: <= 1 point) -> OVER THE BAR

## B. The real FEC sender (`NativeVideoFecRelay`) with the shim, 60 s each

| case | groups | recovered | unrecoverable | lost after FEC (per min) | G5-S1 window classes (primary) |
| --- | --- | --- | --- | --- | --- |
| `loss-1@pre-fec` | 6862 | 0 | 0 | 477 (477.0) | lossy 6 |
| `loss-1@post-fec` | 7095 | 415 | 10 | 26 (26.0) | lossy 6 |
| `burst-50x20@pre-fec` | 7176 | 0 | 0 | 150 (150.0) | clean 3, lossy 3 |
| `burst-50x20@post-fec` | 7182 | 0 | 3 | 132 (132.0) | clean 3, lossy 3 |
| `cap-4500@post-fec` | 475 | 297 | 163 | 15217 (15217.0) | capacity-limited 6 |

## C. Flag absent

| check | result |
| --- | --- |
| encoder command, HEAD, flag absent | `b3c78756d3390e39…` (sink `rtp://<loopback>:48110?pkt_size=1200`) |
| encoder command, HEAD, flag set | `b3c78756d3390e39…` (sink `rtp://<loopback>:48110?pkt_size=1200`) |
| encoder command, today, flag absent | `b3c78756d3390e39…` (sink `rtp://<loopback>:48110?pkt_size=1200`) |
| encoder command, today, flag set | `b3c78756d3390e39…` (sink `rtp://<loopback>:48110?pkt_size=1200`) |
| encoder command: one hash across all four | yes |
| FEC sender, HEAD vs edited, 10 s, datagram sequence | identical (8400 / 8400) |
| fresh process, no flag | own port bound 1, target the client 1, impairment imported 0, shim thread 0 |
| encoder command built (ends in the rtp sink) | yes |

-> A PASS; C PASS; B is read, not gated.
