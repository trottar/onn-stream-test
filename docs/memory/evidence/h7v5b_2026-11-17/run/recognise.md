# H7-V5b — recognition per mini game (the `h7_results` rows; change 4)

| mini game | `watching` | `recognise_s` | `recognised` | `after_s` | `picture_failed` | the read |
| --- | --- | --- | --- | --- | --- | --- |
| T88, seats 1,2 (step 12) | 06:58:35.508Z, `"begin": "setup"`, loaded, spec 2 | **15.0** | **true** | **10.0 s** (10 reads) | none | `start`: start 0.0117, screen 0.0038 (`s12.txt`) |
| T88, seats 2,1 (step 14) | 06:59:18.083Z, setup | 15.0 | true | 9.0 s | none | — |
| T88, seats 1,2 (step 15) | 06:59:34.843Z, setup | 15.0 | true | 9.0 s | none | — |
| T89, seats 1,2,3,4 (step 16) | 07:00:49.532Z, `"begin": "setup"`, loaded, spec 3 | **15.0** | **true** | **2.0 s** (2 reads) | **none** | `h7-result` `last`: start **0.0257** (line 0.0932), end 0.3273 |
| T89, seats 3,1,4,2 (step 18) | 07:00:57.049Z, setup | 15.0 | true | 2.0 s | none | start 0.0257 |

T88 at 9-10 s — RetroArch's notices as H7-D1 measured (9.00 s), now inside B130's 15.0 s. T89 at the second read —
B129's own window, not the desktop (H7-D1: never in 45). The watcher's rectangle is not carried in the rows.
