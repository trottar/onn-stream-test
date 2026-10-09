| run | fault | t_on → t_off (UTC; s) | recovery events (offset from t_on / t_off) | gap lines > 1 s in the fault window (start offset from t_on; gap ms; burst) |
| --- | --- | --- | --- | --- |
| V2-N3 | host->client 48100,48101, 3 s | 00:12:00.248Z → 00:12:03.317Z; 3.07 | desync_pause client_output_silence (+1.34 / -1.73); resumed (+5.40 / +2.33) | none > 1 s |
| V2-N15 | host->client 48100,48101, 15 s | 00:13:27.868Z → 00:13:42.933Z; 15.07 | desync_pause client_output_silence (+1.36 / -13.71); encoder_restart (+5.54 / -9.52); resumed (+18.78 / +3.71) | none > 1 s |
| V2-C2 | client->host 48102, 2 s | 00:15:20.487Z → 00:15:22.569Z; 2.08 | **none** | -0.03 s; 2064.3; 227 |
| V2-C8 | client->host 48102, 8 s | 00:16:46.914Z → 00:16:54.973Z; 8.06 | desync_pause client_output_silence (-17.50 / -25.56); resumed (-14.50 / -22.56); desync_pause controller_silence (+5.35 / -2.71); resumed via controller_return (+9.68 / +1.62) | -0.00 s; 8038.1; 227 |
