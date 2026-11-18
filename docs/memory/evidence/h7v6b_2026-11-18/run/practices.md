# H7-V6b — the practices (by time; the driver's answers and the rows)

| practice | its go | `minigame_practice_end` | answers while it ran | scores while it ran | back to `ready` | `practices` | the way back's frame advance / `minigame_ready` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T88 practice 1 (the kept end P1 loaded during it) | 02:18:28.259Z | 02:19:58.342Z {"by": "time", "practice_s": 90.01} | 83: [('playing', None), ('starting', 'preparing')] | ['None'] | ready | 1 | {"batches": 4, "changed": true, "frames": 14, "moved": 0.0322, "mute_ms": 1136.1, "paused": true} / {"after_practice": true, "prepare_s": 1.186} |
| T88 practice 2 | 02:20:01.471Z | 02:21:31.552Z {"by": "time", "practice_s": 90.003} | 91: [('playing', None), ('starting', 'preparing')] | ['None'] | ready | 2 | {"batches": 4, "changed": true, "frames": 14, "moved": 0.0348, "mute_ms": 1154.4, "paused": true} / {"after_practice": true, "prepare_s": 1.199} |
| T89 practice 1 | 02:22:02.326Z | 02:23:32.418Z {"by": "time", "practice_s": 90.001} | 91: [('playing', None), ('starting', 'preparing')] | ['None'] | ready | 1 | {"batches": 4, "changed": true, "frames": 14, "moved": 0.0, "mute_ms": 1154.3, "paused": true} / {"after_practice": true, "prepare_s": 1.203} |

During T88's first practice the kept end P1 was loaded by hand (02:18:31Z): the answer 5 s later still `playing`, `scores` null, `practices` 0; no `minigame_ended` row between any practice's go and its end.
