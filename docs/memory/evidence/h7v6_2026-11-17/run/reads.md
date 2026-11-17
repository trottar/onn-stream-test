# H7-V6 — the paused reads (from `h7_results`; numbers only)

The watcher in this order keeps no pictures (`"keep": null`) and `h7_results` writes one `recognised` row per watch —
its last read's class and distances and the count of reads; the reads in between are not in the rows (no
`unknown_screen` row was written, so none of them was `unknown`). That is everything the rows hold.

| preparation | `watching` | `recognise_s` | `label_mask` | the begin | reads | `recognised` | the last read (15.0 s) | its line | the first `start` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **T88**, seats 1,2 (step 5) | 23:16:51.479Z, spec 2 | 15.0 | **true** | the setup's, loaded (27.4 ms) | 15 | **false** | `other`, screen **0.1641** | screen 0.082 | **never in 15** |
| **T89**, seats 3,1,4,2 (step 9) | 23:17:29.046Z, spec 3 | 15.0 | **true** | the setup's, loaded (56.0 ms) | 15 | **false** | `other`, start **0.2367**, end 0.2921 | start 0.0932 | **never in 15** |

For comparison (H7-V5b, the same titles and setups, the title running): T88's start read 0.0117 and T89's 0.0257 —
here, paused, the reads are far from the start for both.
