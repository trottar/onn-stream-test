# H7-V6b — every read of every preparation (`h7-result` polled every 0.2 s, each new read kept; numbers only)

Thresholds (the specs): T88 screen 0.082, start 0.0958, end_P1 0.1044, end_P2 0.0983; T89 start 0.0932, end 0.1011. Every read from the `watching` row to the preparation's go is in `reads.tsv` (second after the watch row, class, distances, margin).

| preparation | `watching` | `label_mask` | reads to the go | classes | the first `start` read (s after the watch row) | its distances | the largest start / screen distance before the go |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T88 step 5 (seats 1,2, held) | 02:14:16.594Z, spec 2, `begin` setup | False | 184 (the row: 1 at `recognised`) | start | 1.0 (`recognised` True) | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} | 0.0118 / 0.0038 |
| T88 step 6 (seats 2,1, go before ready) | 02:18:11.187Z, spec 2, `begin` setup | False | 0 (the row: 1 at `recognised`) |  | 1.0 (`recognised` True) | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} | None / None |
| T88 step 8 (seats 1,2, held) | 02:18:25.719Z, spec 2, `begin` setup | False | 2 (the row: 1 at `recognised`) | start | 1.0 (`recognised` True) | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} | 0.0118 / 0.0038 |
| T88 step 8, the way back after practice 1 | 02:19:58.505Z, spec 2, `begin` setup | False | 2 (the row: 1 at `recognised`) | start | 1.0 (`recognised` True) | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} | 0.0118 / 0.0038 |
| T88 step 8, the way back after practice 2 | 02:21:31.720Z, spec 2, `begin` setup | False | 2 (the row: 1 at `recognised`) | start | 1.0 (`recognised` True) | {"end_P1": 0.2028, "end_P2": 0.1977, "screen": 0.0038, "start": 0.0118} | 0.0118 / 0.0038 |
| T89 step 9 (seats 3,1,4,2, held) | 02:22:00.073Z, spec 3, `begin` setup | False | 1 (the row: 1 at `recognised`) | start | 1.0 (`recognised` True) | {"end": 0.3396, "screen": 0.0067, "start": 0.0067} | 0.0067 / 0.0067 |
| T89 step 9, the way back after its practice | 02:23:32.643Z, spec 3, `begin` setup | False | 2 (the row: 1 at `recognised`) | start | 1.0 (`recognised` True) | {"end": 0.3407, "screen": 0.0045, "start": 0.0045} | 0.0045 / 0.0045 |
