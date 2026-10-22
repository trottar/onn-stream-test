# B6 correction: the CL-B5/6/7 clean windows added (their control gaps are in the live logs)

| window (600 s) | gaps >= 250 | >= 500 | >= 900 | >= 950 | longest ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| CL-B5 A pcm | 59 | 12 | 0 | 0 | 694 |
| CL-B5 B opus | 74 | 13 | 2 | 1 | 981 |
| CL-B5 L opus | 78 | 10 | 1 | 1 | 1007 |
| CL-B6 1 opus | 81 | 12 | 0 | 0 | 688 |
| CL-B6 2 pcm | 17 | 4 | 0 | 0 | 553 |
| CL-B7 pcm | 38 | 12 | 1 | 1 | 1172 |
| CL-B7 opus today | 5 | 1 | 0 | 0 | 550 |
| CL-B7 opus lean | 3 | 0 | 0 | 0 | 382 |

**H by B6's rule with these added: 950 ms** (B6's own: 950 ms). The idle room of 10-18/19 made 59-81 uplink silences >= 250 ms per 10 min in CL-B5/B6 -- more than cell 8's 16 -- and 0-1 >= 950.
