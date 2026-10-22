# ML-R1 results (as pre-registered; every metric, every baseline, per set, per k)

Rows 49,785 (43,683 training), 132 inputs. The detector (k = 2, by CV AUPRC): **hgb**.

## The bar (k = 2, held-out evenings pooled)

```
{
 "detector": "hgb",
 "detector_recall": 1.0,
 "best_rule": "silence_250",
 "best_rule_recall": 0.6836363636363636,
 "margin_points": 31.6,
 "fa_train_clean": 0.0,
 "fires_before_sunday_0506": true,
 "fires_before_death": true,
 "met": true
}
```

## k = 1

CV: `{"logreg": {"0.01": 0.54218, "0.1": 0.58077, "1": 0.58951, "10": 0.59043}, "hgb": {"d2_lr0.05": {"rounds": 300, "cv_auprc": 0.66995}, "d2_lr0.1": {"rounds": 300, "cv_auprc": 0.6746}, "d4_lr0.05": {"rounds": 110, "cv_auprc": 0.68268}, "d4_lr0.1": {"rounds": 97, "cv_auprc": 0.68263}}}`
Chosen: `{"logreg_C": "10", "hgb": "d4_lr0.05", "hgb_rounds": 110}`; thresholds `{"logreg": 0.0041842461186743915, "hgb": 0.009060055915641935}`

### train_oof

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.5894 | 99.9 % | 4845 | 99.9 % | 3406 | 218 | 0.0 | — | 597.4 |
| hgb | 0.7011 | 99.8 % | 4845 | 99.8 % | 3406 | 222.0 | 0.0 | — | 561.0 |
| lan_r1_T4_K2 | 0.1894 | 42.8 % | 4845 | 43.3 % | 3406 | 22 | 1.749 | — | 97.7 |
| silence_250 | 0.1827 | 22.5 % | 4845 | 4.7 % | 3406 | 2.0 | 25.364 | — | 35.1 |
| silence_950 | 0.1258 | 2.8 % | 4845 | 1.6 % | 3406 | 1.0 | 0.0 | — | 2.9 |

### heldout_evenings

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.6123 | 100.0 % | 275 | 100.0 % | 109 | 430 | — | 0.544 | 598.1 |
| hgb | 0.6251 | 100.0 % | 275 | 100.0 % | 109 | 411 | — | 0.544 | 599.9 |
| lan_r1_T4_K2 | 0.2278 | 32.4 % | 275 | 18.3 % | 109 | 5.0 | — | 0.816 | 16.7 |
| silence_250 | 0.3807 | 58.2 % | 275 | 15.6 % | 109 | 5 | — | 2.721 | 29.0 |
| silence_950 | 0.1027 | 5.8 % | 275 | 2.8 % | 109 | 1 | — | 0.0 | 1.9 |

### heldout_bench5

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.5855 | 100.0 % | 184 | 100.0 % | 88 | 304.0 | — | — | 600.0 |
| hgb | 0.5571 | 100.0 % | 184 | 100.0 % | 88 | 304.0 | — | — | 600.0 |
| lan_r1_T4_K2 | 0.3139 | 92.9 % | 184 | 93.2 % | 88 | 28.0 | — | — | 474.2 |
| silence_250 | 0.3846 | 46.7 % | 184 | 14.8 % | 88 | 4 | — | — | 146.9 |
| silence_950 | 0.3109 | 10.9 % | 184 | 6.8 % | 88 | 3.0 | — | — | 27.3 |

### heldout_ux_r1

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.6716 | 100.0 % | 241 | 100.0 % | 85 | 452 | — | — | 599.8 |
| hgb | 0.6838 | 100.0 % | 241 | 100.0 % | 85 | 452 | — | — | 600.0 |
| lan_r1_T4_K2 | 0.2868 | 36.9 % | 241 | 23.5 % | 85 | 5.0 | — | — | 26.8 |
| silence_250 | 0.4297 | 62.7 % | 241 | 18.8 % | 85 | 5.5 | — | — | 45.7 |
| silence_950 | 0.1307 | 6.2 % | 241 | 3.5 % | 85 | 1 | — | — | 3.1 |

### heldout_ux_r2

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.2172 | 100.0 % | 34 | 100.0 % | 24 | 226.5 | — | 0.544 | 595.8 |
| hgb | 0.2355 | 100.0 % | 34 | 100.0 % | 24 | 132.0 | — | 0.544 | 599.7 |
| lan_r1_T4_K2 | 0.015 | 0.0 % | 34 | 0.0 % | 24 | None | — | 0.816 | 2.9 |
| silence_250 | 0.1146 | 26.5 % | 34 | 4.2 % | 24 | 4 | — | 2.721 | 6.1 |
| silence_950 | 0.0439 | 2.9 % | 34 | 0.0 % | 24 | None | — | 0.0 | 0.3 |

### the named moments

```
{
 "sunday_0506_burst": {
  "E": "2026-10-20T05:06:00",
  "logreg": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "hgb": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "lan_r1_T4_K2": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  },
  "silence_250": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_at": [
    3,
    2,
    1,
    0
   ]
  },
  "silence_950": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": [
    0
   ]
  }
 },
 "death_045455": {
  "E": "2026-10-21T04:54:55",
  "logreg": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "hgb": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "lan_r1_T4_K2": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  },
  "silence_250": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": [
    0
   ]
  },
  "silence_950": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  }
 }
}
```

## k = 2

CV: `{"logreg": {"0.01": 0.66247, "0.1": 0.68172, "1": 0.70726, "10": 0.70485}, "hgb": {"d2_lr0.05": {"rounds": 300, "cv_auprc": 0.75578}, "d2_lr0.1": {"rounds": 290, "cv_auprc": 0.75717}, "d4_lr0.05": {"rounds": 215, "cv_auprc": 0.76282}, "d4_lr0.1": {"rounds": 117, "cv_auprc": 0.7612}}}`
Chosen: `{"logreg_C": "1", "hgb": "d4_lr0.05", "hgb_rounds": 215}`; thresholds `{"logreg": 0.0025934455915761997, "hgb": 0.008170905366755086}`

### train_oof

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.7011 | 100.0 % | 4845 | 100.0 % | 3406 | 301 | 0.0 | — | 599.3 |
| hgb | 0.7835 | 99.9 % | 4845 | 99.9 % | 3406 | 247.5 | 0.0 | — | 572.1 |
| lan_r1_T4_K2 | 0.3205 | 44.1 % | 4845 | 44.2 % | 3406 | 21 | 1.64 | — | 97.7 |
| silence_250 | 0.2522 | 29.1 % | 4845 | 10.9 % | 3406 | 2.0 | 23.943 | — | 35.1 |
| silence_950 | 0.2005 | 4.4 % | 4845 | 2.1 % | 3406 | 1.0 | 0.0 | — | 2.9 |

### heldout_evenings

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.6491 | 100.0 % | 275 | 100.0 % | 109 | 446 | — | 0.544 | 598.5 |
| hgb | 0.6656 | 100.0 % | 275 | 100.0 % | 109 | 446 | — | 0.544 | 600.0 |
| lan_r1_T4_K2 | 0.2501 | 34.2 % | 275 | 19.3 % | 109 | 5 | — | 0.816 | 16.7 |
| silence_250 | 0.3983 | 68.4 % | 275 | 30.3 % | 109 | 4 | — | 2.449 | 29.0 |
| silence_950 | 0.1124 | 9.8 % | 275 | 2.8 % | 109 | 1 | — | 0.0 | 1.9 |

### heldout_bench5

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.6572 | 100.0 % | 184 | 100.0 % | 88 | 304.0 | — | — | 600.0 |
| hgb | 0.6585 | 100.0 % | 184 | 100.0 % | 88 | 304.0 | — | — | 600.0 |
| lan_r1_T4_K2 | 0.4626 | 94.6 % | 184 | 94.3 % | 88 | 27 | — | — | 474.2 |
| silence_250 | 0.4852 | 57.6 % | 184 | 25.0 % | 88 | 2.5 | — | — | 146.9 |
| silence_950 | 0.4419 | 16.8 % | 184 | 8.0 % | 88 | 3 | — | — | 27.3 |

### heldout_ux_r1

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.7269 | 100.0 % | 241 | 100.0 % | 85 | 452 | — | — | 600.0 |
| hgb | 0.7471 | 100.0 % | 241 | 100.0 % | 85 | 452 | — | — | 600.0 |
| lan_r1_T4_K2 | 0.3232 | 39.0 % | 241 | 24.7 % | 85 | 5 | — | — | 26.8 |
| silence_250 | 0.4631 | 73.9 % | 241 | 36.5 % | 85 | 4 | — | — | 45.7 |
| silence_950 | 0.1484 | 10.4 % | 241 | 3.5 % | 85 | 1 | — | — | 3.1 |

### heldout_ux_r2

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.1994 | 100.0 % | 34 | 100.0 % | 24 | 285.5 | — | 0.544 | 596.3 |
| hgb | 0.2087 | 100.0 % | 34 | 100.0 % | 24 | 285.5 | — | 0.544 | 600.0 |
| lan_r1_T4_K2 | 0.0256 | 0.0 % | 34 | 0.0 % | 24 | None | — | 0.816 | 2.9 |
| silence_250 | 0.1114 | 29.4 % | 34 | 8.3 % | 24 | 3.0 | — | 2.449 | 6.1 |
| silence_950 | 0.0424 | 5.9 % | 34 | 0.0 % | 24 | None | — | 0.0 | 0.3 |

### the named moments

```
{
 "sunday_0506_burst": {
  "E": "2026-10-20T05:06:00",
  "logreg": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "hgb": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "lan_r1_T4_K2": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  },
  "silence_250": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_at": [
    3,
    2,
    1,
    0
   ]
  },
  "silence_950": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": [
    0
   ]
  }
 },
 "death_045455": {
  "E": "2026-10-21T04:54:55",
  "logreg": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "hgb": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "lan_r1_T4_K2": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  },
  "silence_250": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": [
    0
   ]
  },
  "silence_950": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  }
 }
}
```

## k = 3

CV: `{"logreg": {"0.01": 0.68639, "0.1": 0.6941, "1": 0.70839, "10": 0.72571}, "hgb": {"d2_lr0.05": {"rounds": 291, "cv_auprc": 0.76152}, "d2_lr0.1": {"rounds": 230, "cv_auprc": 0.76204}, "d4_lr0.05": {"rounds": 241, "cv_auprc": 0.76957}, "d4_lr0.1": {"rounds": 143, "cv_auprc": 0.76904}}}`
Chosen: `{"logreg_C": "10", "hgb": "d4_lr0.05", "hgb_rounds": 241}`; thresholds `{"logreg": 5.055474984960866e-06, "hgb": 0.014042150175686238}`

### train_oof

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.703 | 100.0 % | 4845 | 100.0 % | 3406 | 303.5 | 0.0 | — | 599.9 |
| hgb | 0.7915 | 99.9 % | 4845 | 99.9 % | 3406 | 247 | 0.0 | — | 564.1 |
| lan_r1_T4_K2 | 0.3566 | 45.7 % | 4845 | 45.7 % | 3406 | 20 | 1.64 | — | 97.7 |
| silence_250 | 0.2855 | 33.7 % | 4845 | 16.0 % | 3406 | 3 | 22.631 | — | 35.1 |
| silence_950 | 0.2357 | 5.7 % | 4845 | 2.6 % | 3406 | 2 | 0.0 | — | 2.9 |

### heldout_evenings

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.624 | 100.0 % | 275 | 100.0 % | 109 | 446 | — | 0.544 | 600.0 |
| hgb | 0.6406 | 100.0 % | 275 | 100.0 % | 109 | 446 | — | 0.544 | 600.0 |
| lan_r1_T4_K2 | 0.2455 | 36.0 % | 275 | 20.2 % | 109 | 5.0 | — | 0.816 | 16.7 |
| silence_250 | 0.3774 | 71.3 % | 275 | 36.7 % | 109 | 3.0 | — | 2.449 | 29.0 |
| silence_950 | 0.1197 | 13.5 % | 275 | 3.7 % | 109 | 1.5 | — | 0.0 | 1.9 |

### heldout_bench5

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.7283 | 100.0 % | 184 | 100.0 % | 88 | 304.0 | — | — | 600.0 |
| hgb | 0.7547 | 100.0 % | 184 | 100.0 % | 88 | 304.0 | — | — | 600.0 |
| lan_r1_T4_K2 | 0.5799 | 95.7 % | 184 | 95.5 % | 88 | 28.0 | — | — | 474.2 |
| silence_250 | 0.5798 | 65.8 % | 184 | 38.6 % | 88 | 3.5 | — | — | 146.9 |
| silence_950 | 0.5499 | 19.6 % | 184 | 9.1 % | 88 | 3.0 | — | — | 27.3 |

### heldout_ux_r1

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.7138 | 100.0 % | 241 | 100.0 % | 85 | 452 | — | — | 600.0 |
| hgb | 0.7314 | 100.0 % | 241 | 100.0 % | 85 | 452 | — | — | 600.0 |
| lan_r1_T4_K2 | 0.3228 | 41.1 % | 241 | 25.9 % | 85 | 5.0 | — | — | 26.8 |
| silence_250 | 0.4511 | 77.2 % | 241 | 44.7 % | 85 | 3.0 | — | — | 45.7 |
| silence_950 | 0.1599 | 14.1 % | 241 | 4.7 % | 85 | 1.5 | — | — | 3.1 |

### heldout_ux_r2

| alarm | AUPRC | recall (hitch s) | n | onset recall | onsets | lead median s | FA/10 min train clean | FA/10 min held-out clean | alarm s/10 min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logreg | 0.1778 | 100.0 % | 34 | 100.0 % | 24 | 285.5 | — | 0.544 | 600.0 |
| hgb | 0.1939 | 100.0 % | 34 | 100.0 % | 24 | 285.5 | — | 0.544 | 600.0 |
| lan_r1_T4_K2 | 0.0349 | 0.0 % | 34 | 0.0 % | 24 | None | — | 0.816 | 2.9 |
| silence_250 | 0.0967 | 29.4 % | 34 | 8.3 % | 24 | 3.0 | — | 2.449 | 6.1 |
| silence_950 | 0.0471 | 8.8 % | 34 | 0.0 % | 24 | None | — | 0.0 | 0.3 |

### the named moments

```
{
 "sunday_0506_burst": {
  "E": "2026-10-20T05:06:00",
  "logreg": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "hgb": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "lan_r1_T4_K2": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  },
  "silence_250": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_at": [
    3,
    2,
    1,
    0
   ]
  },
  "silence_950": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": [
    0
   ]
  }
 },
 "death_045455": {
  "E": "2026-10-21T04:54:55",
  "logreg": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "hgb": {
   "fires_ge2s_before": true,
   "first_alarm_s_before": 10,
   "alarm_at": [
    11,
    10,
    9,
    8,
    7,
    6,
    5,
    4,
    3,
    2,
    1,
    0
   ]
  },
  "lan_r1_T4_K2": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  },
  "silence_250": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": [
    0
   ]
  },
  "silence_950": {
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_at": []
  }
 }
}
```
