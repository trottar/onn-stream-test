# E3-R2 replay (fixed model)

| id | kind | recorded | today first fire (R1 model) | today first fire (fixed) | v2 controller fires (fixed) | carried state |
| --- | --- | --- | --- | --- | --- | --- |
| E2-1080P-r1 | false | (0.0, 'controller_silence') | (0.56, 'controller_silence') | (0.56, 'controller_silence') | [] | - |
| S1-control | false | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| S1-CONC-r1a | false | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| S1-CONC-r1b | false | (0.0, 'controller_silence') | (-5.24, 'controller_silence') | (0.83, 'controller_silence') | [] | [(-22, 'PAUSED'), (-3, 'PLAYING')] |
| S1-CONC-r2a | false | (0.0, 'controller_silence') | (24.86, 'controller_silence') | (24.86, 'controller_silence') | [] | - |
| S1-CONC-r2b | false | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| A2-PS1-r1 | false | (0.0, 'controller_silence') | (-1.42, 'controller_silence') | (-1.42, 'controller_silence') | [] | - |
| out-10-05-0401 | false-outside | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | no data | - |
| out-10-05-0402 | false-outside | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | no data | - |
| out-10-05-1514 | false-outside | (0.0, 'controller_silence') | None | None | no data | - |
| R3b-N3 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| R3b-N15 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| R3b-N15b | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| R3b-N150 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| R3b-E30 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | - |
| R3b-N05 | real-nofire | None | None | None | [] | - |
| R3-F05 | real-nofire | None | None | None | [] | - |
| R3-F3 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | [(-54, 'ENDED')] |
| R3-F15 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | [] | [(-57, 'ENDED')] |
| R3-F150 | real | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | (0.0, 'client_output_silence') | no data | [(-54, 'ENDED')] |

## r4, the exit

| controller pause | basis | firing run (start s, len s) | packets back (s) | (a) by (s) | resume (s) | via | resume - back (s) | r4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E2-1080P-r1 | the firing run | [-0.44, 1.41] | 0.97 | 2.0 | 4.0 | telemetry out_gap_ms 45 at t=3 (substitute) | 3.03 | holds |
| S1-CONC-r1b | the firing run | [-0.17, 1.13] | 0.96 | 2.0 | 4.0 | heartbeat out_age_ms 4 at t=3 | 3.04 | holds |
| S1-CONC-r2a | overlapping run (not resolvable at 1 s) | [-1.14, 0.14] | -1.0 | 0.0 | 2.0 | heartbeat out_age_ms 144 at t=1 | 3.0 | holds |
| A2-PS1-r1 | the firing run | [0.16, 1.83] | 1.99 | 3.0 | 5.0 | heartbeat out_age_ms 6 at t=4 | 3.01 | holds |

```
{
 "r1_today_faithful": {
  "E2-1080P-r1": true,
  "S1-control": true,
  "S1-CONC-r1a": true,
  "S1-CONC-r1b": true,
  "S1-CONC-r2b": true,
  "A2-PS1-r1": true,
  "R3b-N3": true,
  "R3b-N15": true,
  "R3b-N15b": true,
  "R3b-N150": true,
  "R3b-E30": true,
  "R3b-N05": true,
  "R3-F05": true,
  "R3-F3": true,
  "R3-F15": true,
  "R3-F150": true
 },
 "r1_excluded_by_name": {
  "S1-CONC-r2a": "resolution limit of the 1-s records (R1 \u00a73): a ~1.0-s silence across two sampler seconds whose catch-up burst lands in the same seconds; not reproducible from them"
 },
 "r1_outside_suite_reported": {
  "out-10-05-0401": true,
  "out-10-05-0402": true,
  "out-10-05-1514": false
 },
 "r1_S1-CONC-r2a_reported": {
  "today_first_fire": [
   24.86,
   "controller_silence"
  ]
 },
 "r1": true,
 "r2_v2_within_2s_of_today": {
  "R3b-N3": true,
  "R3b-N15": true,
  "R3b-N15b": true,
  "R3b-N150": true,
  "R3b-E30": true,
  "R3-F3": true,
  "R3-F15": true,
  "R3-F150": true
 },
 "r2_reported_v2_on_N05_F05": {
  "R3b-N05": null,
  "R3-F05": null
 },
 "r2": true,
 "r3_v2_controller_fires_in_window": {
  "E2-1080P-r1": [],
  "S1-CONC-r1b": [],
  "S1-CONC-r2a": [],
  "A2-PS1-r1": []
 },
 "r3": true,
 "r3_client_pauses_reported": {
  "S1-control": [
   0.0,
   "client_output_silence"
  ],
  "S1-CONC-r1a": [
   0.0,
   "client_output_silence"
  ],
  "S1-CONC-r2b": [
   0.0,
   "client_output_silence"
  ]
 },
 "r4": true,
 "replay_bar_holds": true
}
```
