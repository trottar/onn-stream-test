# ML-R1 importance (k = 2)

## logistic regression: standardized coefficients (top 30 by |coef|)

- `hb_out_age_max30` -1.7636
- `tx_packets` -1.3845
- `tx_frames_sum10` +1.3845
- `has_hb10` +1.2728
- `hb_fps` -1.1815
- `tx_kbytes` +1.1701
- `tx_frames_sum5` +1.0824
- `tx_frames_min10` -1.0479
- `hb_fps_min2` -1.0208
- `hb_underruns_sum10` +0.9325
- `hb_arrivals_sum30` +0.7478
- `ctrl_age_end_max2` +0.7398
- `hb_out_age_max2` +0.6828
- `tx_frames` -0.6643
- `hb_fec_rec_sum30` -0.6470
- `has_lad10` +0.5695
- `hb_a_gap_max` +0.5392
- `ctrl_new_gaps_sum30` +0.4922
- `tx_frames_min30` -0.4770
- `lad_state_PRESSURE` +0.4626
- `ctrl_age_end` -0.4587
- `hb_unrec_sum30` +0.4519
- `hb_out_age` +0.4479
- `has_frames` +0.4457
- `ctrl_max_in_sec_max10` +0.4221
- `lad_state_REFERENCE` +0.4027
- `hb_concealed_sum5` +0.3903
- `hb_underruns_sum2` -0.3794
- `hb_fps_min5` -0.3758
- `ctrl_age_end_max10` -0.3511

## gradient-boosted trees: split gain summed per feature (top 30)

- `hb_fps` 54880.9
- `hb_fps_min5` 35681.3
- `hb_fps_min2` 35313.6
- `ctrl_new_gaps_sum30` 16227.6
- `ctrl_max_in_sec_max10` 10309.2
- `lad_fps` 6684.8
- `hb_fps_min10` 4338.2
- `ctrl_new_gaps_sum10` 4247.1
- `hb_post_fec_sum30` 4166.1
- `lad_loss_sum30` 3295.8
- `ctrl_max_in_sec_max5` 2582.6
- `hb_age` 2242.6
- `tx_kbytes_max30` 2047.1
- `ctrl_new_gaps_sum5` 1903.6
- `hb_post_fec_sum10` 1902.4
- `lad_age` 1769.8
- `hb_a_gap_max_max5` 1634.6
- `hb_out_age` 1283.5
- `tx_kbytes_max10` 1276.1
- `hb_age_max5` 1216.5
- `ctrl_max_in_sec_max30` 1210.0
- `lad_loss_sum2` 1179.0
- `hb_a_gap_max_max30` 1051.3
- `lad_fps_min30` 1031.3
- `hb_unrec_sum30` 1017.0
- `lad_age_max2` 980.8
- `lad_fps_min5` 926.6
- `hb_a_gap_max` 917.1
- `hb_fec_rec_sum2` 910.0
- `hb_a_gap_max_max10` 899.4

## gradient-boosted trees: permutation importance, AUPRC drop, one grouped validation fold (top 30)

- `hb_fps` +0.02293
- `lad_fps` +0.01776
- `ctrl_new_gaps_sum30` +0.01150
- `secs_since_start` +0.00571
- `lad_loss_sum30` +0.00462
- `hb_fps_min5` +0.00394
- `ctrl_max_in_sec_max10` +0.00384
- `hb_age` +0.00322
- `tx_kbytes_max30` +0.00215
- `hb_fps_min2` +0.00204
- `lad_age` +0.00171
- `tx_max_pk` +0.00150
- `ctrl_max_in_sec_max2` +0.00148
- `lad_loss_sum2` +0.00131
- `hb_unrec_sum30` +0.00120
- `ctrl_max_in_sec_max30` +0.00100
- `tx_max_pk_max2` +0.00100
- `lad_age_max2` +0.00095
- `hb_out_age` +0.00091
- `hb_fps_min30` +0.00082
- `lad_fps_min5` +0.00082
- `lad_state_REFERENCE` +0.00080
- `ctrl_age_end` +0.00078
- `hb_a_gap_max_max5` +0.00077
- `tx_max_pk_max10` +0.00077
- `lad_loss_sum10` +0.00074
- `ctrl_max_in_sec_max5` +0.00073
- `tx_kbytes_max10` +0.00055
- `hb_out_age_max2` +0.00041
- `tx_max_pk_max5` +0.00041
