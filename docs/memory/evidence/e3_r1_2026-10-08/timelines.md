# E3-R1 timelines -- summaries (rows +/-60 s per second in timelines.json)

| id | kind | trigger, age ms | fault s; fired after s | then (s, event) | ctrl silent s est (-3..+3); rx pps -3..+4 | hb arrival gap max s; delay max s | client out age max ms (+/-6 s); next hb |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E2-1080P-r1 | false | controller_silence, 1002.5 | None; None | 120.4 gave_up_saved | 1.84; [458.0, 488.0, 256.0, 15.0, 1031.0, 258.0, 707.0, 489.0] | None; None | None; None |
| S1-control | false | client_output_silence, 1149.0 | None; None | 2.8 resumed | 0.27; [462.0, 466.0, 468.0, 356.0, 465.0, 566.0, 446.0, 561.0] | 3; 0.97 | 1669; 0 |
| S1-CONC-r1a | false | client_output_silence, 1011.0 | None; None | 9.5 encoder_restart; 18.3 resumed; 21.0 desync_pause (controller_silence); 141.4 gave_up_saved | 0.08; [532.0, 544.0, 510.0, 556.0, 579.0, 440.0, 468.0, 515.0] | 4; 1.13 | 3198; 636 |
| S1-CONC-r1b | false | controller_silence, 1003.2 | None; None | 120.4 gave_up_saved | 1.17; [457.0, 543.0, 393.0, 18.0, 641.0, 978.0, 985.0, 458.0] | 4; 2.0 | 761; 26 |
| S1-CONC-r2a | false | controller_silence, 1002.1 | None; None | 14.9 encoder_restart; 32.2 resumed; 118.4 desync_pause (client_output_silence); 143.2 resumed | 0.91; [415.0, 404.0, 1117.0, 544.0, 605.0, 797.0, 163.0, 809.0] | 4; 2.19 | 931; 144 |
| S1-CONC-r2b | false | client_output_silence, 1206.0 | None; None | 24.8 resumed | 0.35; [877.0, 978.0, 866.0, 440.0, 413.0, 767.0, 390.0, 752.0] | 3; 1.81 | 703; 149 |
| A2-PS1-r1 | false | controller_silence, 1003.6 | None; None | 120.3 gave_up_saved | 3.15; [266.0, 48.0, 931.0, 71.0, 6.0, 1410.0, 452.0, 451.0] | 5; 3.13 | 174; 174 |
| out-10-05-0401 | false-outside | client_output_silence, 1237.0 | None; None | 1.0 resumed; 77.3 desync_pause (client_output_silence); 80.6 encoder_restart; 93.9 resumed; 167.9 session_ended | None; None | None; None | None; None |
| out-10-05-0402 | false-outside | client_output_silence, 1353.0 | None; None | 3.2 encoder_restart; 16.6 resumed; 90.6 session_ended | None; None | None; None | None; None |
| out-10-05-1514 | false-outside | controller_silence, 1002.6 | None; None | 0.5 session_ended | None; None | None; None | None; None |
| R3b-N3 | real | client_output_silence, 1132.0 | 3.06; 1.27 | 3.6 resumed; 25.8 session_ended | None; None | 3; 0.0 | 2166; 23 |
| R3b-N15 | real | client_output_silence, 1281.0 | 15.06; 1.42 | 4.2 encoder_restart; 17.4 resumed; 49.8 session_ended | None; None | 3; -0.0 | 6417; 4367 |
| R3b-N15b | real | client_output_silence, 1147.0 | 15.07; 1.28 | 4.2 encoder_restart; 17.4 resumed; 83.5 session_ended | None; None | 3; 0.01 | 6271; 4228 |
| R3b-N150 | real | client_output_silence, 1300.0 | 150.07; 1.44 | 3.1 encoder_restart; 15.8 encoder_restart; 38.0 encoder_restart; 70.7 encoder_restart; 103.4 encoder_restart | None; None | 3; 0.01 | 7459; 3358 |
| R3b-E30 | real | client_output_silence, 1235.0 | None; 1.36 | 4.2 encoder_restart; 16.9 encoder_restart; 39.1 encoder_restart; 71.8 encoder_restart; 104.5 encoder_restart | None; None | 3; 0.03 | 6351; 4311 |
| R3b-N05 | real-nofire | None, None | 0.56; None | 24.3 session_ended | None; None | 2; 0.01 | 18; 5 |
| R3-F05 | real-nofire | None, None | 0.75; None | 22.1 session_ended; 75.4 desync_pause (client_output_silence); 78.7 encoder_restart; 80.6 resumed; 103.2 session_ended | None; None | 2; 0.03 | 158; 15 |
| R3-F3 | real | client_output_silence, 1095.0 | 3.09; 1.3 | 3.3 encoder_restart; 5.2 resumed; 27.7 session_ended; 84.4 desync_pause (client_output_silence); 98.0 encoder_restart | None; None | 2; 0.05 | 1614; 0 |
| R3-F15 | real | client_output_silence, 1492.0 | 15.25; 1.73 | 13.6 encoder_restart; 23.6 encoder_restart; 43.6 encoder_restart; 44.4 session_ended; 98.3 desync_pause (client_output_silence) | None; None | 2; 0.02 | 7112; 3030 |
| R3-F150 | real | client_output_silence, 1418.0 | 154.6; 1.62 | 14.2 encoder_restart; 24.2 encoder_restart; 44.2 encoder_restart; 74.2 encoder_restart; 104.2 encoder_restart | None; None | 3; 0.94 | 6511; 2440 |
