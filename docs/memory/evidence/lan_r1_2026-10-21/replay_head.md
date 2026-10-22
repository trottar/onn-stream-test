# LAN-R1 replay: the two evenings through the real controller (inputs/ copies only)

## 1. Flag absent

| evening | client sessions | sample rows | recorded decision / state events | recorded reproduced | controller HEAD vs working tree (rows) |
| --- | ---: | ---: | ---: | --- | --- |
| UX-R1 Sunday (2026-10-20) | 41 | 1709 | 505 | exact | identical (2256) |
| UX-R2 last night (2026-10-21) | 12 | 1180 | 318 | exact | identical (1510) |

-> flag absent: PASS

## PRIVYHUB_WAN_ADAPTATION=1, open loop (later reports are the recorded ones); no claim of improvement

### UX-R1 Sunday (2026-10-20) — LAN (as recorded)

- suggestions 6: R1.2:none 2, R3.1:none 3, R3.1:transition 1
- decisions (1):
    2026-10-20T05:11:01.011Z transition ROUTINE 7000->6000 reason capacity_mild trigger capacity_mild
- per minute: 05:11 R3.1:none×3,R3.1:transition×1,R1.2:none×2

### UX-R2 last night (2026-10-21) — LAN (as recorded)

- suggestions 0: none
- decisions (0):

### UX-R1 Sunday (2026-10-20) — read as remote

- suggestions 6: R1.2:none 2, R3.1:none 3, R3.1:transition 1
- decisions (1):
    2026-10-20T05:11:01.011Z transition ROUTINE 7000->6000 reason capacity_mild trigger capacity_mild
- per minute: 05:11 R3.1:none×3,R3.1:transition×1,R1.2:none×2

### UX-R2 last night (2026-10-21) — read as remote

- suggestions 0: none
- decisions (0):

