# ML-R1 POST-HOC SUPPLEMENT (not pre-registered; the frozen run; nothing refit)

## k = 1

| operating point | set | recall (hitch s) | onset recall | lead median s | alarm s / 10 min | FA s / 10 min, train clean | FA s / 10 min, held-out clean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| silence_250 | heldout_evenings | 58.2 % | 15.6 % | 5.0 | 29.0 | — | 3.537 |
| silence_250 | heldout_ux_r1 | 62.7 % | 18.8 % | 5.5 | 45.7 | — | — |
| silence_250 | heldout_ux_r2 | 26.5 % | 4.2 % | 4.0 | 6.1 | — | 3.537 |
| silence_250 | heldout_bench5 | 46.7 % | 14.8 % | 4.0 | 146.9 | — | — |
| silence_250 | train_oof | 22.5 % | 4.7 % | 2.0 | 35.1 | 36.311 | — |
| logreg_strict θ=0.5837 | heldout_evenings | 39.3 % | 11.0 % | 2.5 | 15.3 | — | 1.088 |
| logreg_strict | heldout_ux_r1 | 43.6 % | 12.9 % | 2.0 | 24.8 | — | — |
| logreg_strict | heldout_ux_r2 | 8.8 % | 4.2 % | 4.0 | 2.1 | — | 1.088 |
| logreg_strict | heldout_bench5 | 27.7 % | 9.1 % | 1.0 | 63.3 | — | — |
| logreg_strict | train_oof | 35.6 % | 33.2 % | 1.0 | 30.1 | 0.875 | — |
| logreg_duty_matched θ=0.1557 | heldout_evenings | 68.4 % | 36.7 % | 4.0 | 37.0 | — | 6.531 |
| logreg_duty_matched | heldout_ux_r1 | 72.6 % | 43.5 % | 6.0 | 56.6 | — | — |
| logreg_duty_matched | heldout_ux_r2 | 38.2 % | 12.5 % | 3.0 | 10.0 | — | 6.531 |
| logreg_duty_matched | heldout_bench5 | 69.0 % | 50.0 % | 2.0 | 272.7 | — | — |
| logreg_duty_matched | train_oof | 67.9 % | 63.6 % | 1.0 | 92.7 | 32.92 | — |
| hgb_strict θ=0.6773 | heldout_evenings | 24.0 % | 9.2 % | 1.5 | 9.0 | — | 0.544 |
| hgb_strict | heldout_ux_r1 | 26.1 % | 10.6 % | 1.0 | 14.5 | — | — |
| hgb_strict | heldout_ux_r2 | 8.8 % | 4.2 % | 3.0 | 1.3 | — | 0.544 |
| hgb_strict | heldout_bench5 | 15.8 % | 5.7 % | 1.0 | 31.7 | — | — |
| hgb_strict | train_oof | 36.2 % | 38.8 % | 1.0 | 27.3 | 0.875 | — |
| hgb_duty_matched θ=0.173 | heldout_evenings | 72.7 % | 41.3 % | 9.0 | 42.4 | — | 6.803 |
| hgb_duty_matched | heldout_ux_r1 | 77.6 % | 49.4 % | 11.5 | 64.6 | — | — |
| hgb_duty_matched | heldout_ux_r2 | 38.2 % | 12.5 % | 3.0 | 11.8 | — | 6.803 |
| hgb_duty_matched | heldout_bench5 | 76.6 % | 61.4 % | 3.0 | 301.8 | — | — |
| hgb_duty_matched | train_oof | 71.5 % | 67.1 % | 1.0 | 89.7 | 31.717 | — |

Moments:
```
{
 "silence_250": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    0
   ]
  }
 },
 "logreg_strict": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "logreg_duty_matched": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    0
   ]
  }
 },
 "hgb_strict": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    1
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "hgb_duty_matched": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    0
   ]
  }
 }
}
```

## k = 2

| operating point | set | recall (hitch s) | onset recall | lead median s | alarm s / 10 min | FA s / 10 min, train clean | FA s / 10 min, held-out clean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| silence_250 | heldout_evenings | 68.4 % | 30.3 % | 4.0 | 29.0 | — | 2.993 |
| silence_250 | heldout_ux_r1 | 73.9 % | 36.5 % | 4.0 | 45.7 | — | — |
| silence_250 | heldout_ux_r2 | 29.4 % | 8.3 % | 3.0 | 6.1 | — | 2.993 |
| silence_250 | heldout_bench5 | 57.6 % | 25.0 % | 2.5 | 146.9 | — | — |
| silence_250 | train_oof | 29.1 % | 10.9 % | 2.0 | 35.1 | 33.929 | — |
| logreg_strict θ=0.7148 | heldout_evenings | 52.4 % | 23.9 % | 7.0 | 19.0 | — | 0.816 |
| logreg_strict | heldout_ux_r1 | 57.7 % | 29.4 % | 8.0 | 31.1 | — | — |
| logreg_strict | heldout_ux_r2 | 14.7 % | 4.2 % | 4.0 | 2.4 | — | 0.816 |
| logreg_strict | heldout_bench5 | 45.7 % | 19.3 % | 5.0 | 107.3 | — | — |
| logreg_strict | train_oof | 46.1 % | 40.0 % | 17.0 | 52.6 | 0.985 | — |
| logreg_duty_matched θ=0.2743 | heldout_evenings | 71.3 % | 39.4 % | 9.0 | 39.6 | — | 5.442 |
| logreg_duty_matched | heldout_ux_r1 | 75.9 % | 45.9 % | 12.0 | 61.1 | — | — |
| logreg_duty_matched | heldout_ux_r2 | 38.2 % | 16.7 % | 2.5 | 10.0 | — | 5.442 |
| logreg_duty_matched | heldout_bench5 | 77.2 % | 61.4 % | 8.5 | 302.6 | — | — |
| logreg_duty_matched | train_oof | 71.1 % | 64.3 % | 19.0 | 115.6 | 26.377 | — |
| hgb_strict θ=0.6692 | heldout_evenings | 52.7 % | 18.3 % | 5.0 | 18.4 | — | 1.088 |
| hgb_strict | heldout_ux_r1 | 57.3 % | 22.4 % | 5.0 | 29.4 | — | — |
| hgb_strict | heldout_ux_r2 | 20.6 % | 4.2 % | 4.0 | 3.2 | — | 1.088 |
| hgb_strict | heldout_bench5 | 44.6 % | 20.5 % | 3.5 | 94.1 | — | — |
| hgb_strict | train_oof | 53.0 % | 47.9 % | 11.0 | 60.2 | 0.985 | — |
| hgb_duty_matched θ=0.3032 | heldout_evenings | 70.9 % | 38.5 % | 13.5 | 36.8 | — | 3.265 |
| hgb_duty_matched | heldout_ux_r1 | 75.9 % | 47.1 % | 14.0 | 57.9 | — | — |
| hgb_duty_matched | heldout_ux_r2 | 35.3 % | 8.3 % | 3.0 | 7.6 | — | 3.265 |
| hgb_duty_matched | heldout_bench5 | 69.0 % | 47.7 % | 4.0 | 241.9 | — | — |
| hgb_duty_matched | train_oof | 74.0 % | 68.8 % | 22.0 | 115.5 | 25.392 | — |

Moments:
```
{
 "silence_250": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    0
   ]
  }
 },
 "logreg_strict": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    1
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "logreg_duty_matched": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "hgb_strict": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 2,
   "alarm_s_before_in_30s": [
    2,
    1
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "hgb_duty_matched": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    0
   ]
  }
 }
}
```

## k = 3

| operating point | set | recall (hitch s) | onset recall | lead median s | alarm s / 10 min | FA s / 10 min, train clean | FA s / 10 min, held-out clean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| silence_250 | heldout_evenings | 71.3 % | 36.7 % | 3.0 | 29.0 | — | 2.993 |
| silence_250 | heldout_ux_r1 | 77.2 % | 44.7 % | 3.0 | 45.7 | — | — |
| silence_250 | heldout_ux_r2 | 29.4 % | 8.3 % | 3.0 | 6.1 | — | 2.993 |
| silence_250 | heldout_bench5 | 65.8 % | 38.6 % | 3.5 | 146.9 | — | — |
| silence_250 | train_oof | 33.7 % | 16.0 % | 3.0 | 35.1 | 31.902 | — |
| logreg_strict θ=0.8063 | heldout_evenings | 56.0 % | 28.4 % | 6.0 | 20.1 | — | 0.816 |
| logreg_strict | heldout_ux_r1 | 61.8 % | 35.3 % | 6.0 | 32.9 | — | — |
| logreg_strict | heldout_ux_r2 | 14.7 % | 4.2 % | 4.0 | 2.6 | — | 0.816 |
| logreg_strict | heldout_bench5 | 51.6 % | 28.4 % | 4.0 | 122.3 | — | — |
| logreg_strict | train_oof | 50.9 % | 45.2 % | 14.5 | 58.1 | 0.987 | — |
| logreg_duty_matched θ=0.381 | heldout_evenings | 73.8 % | 45.9 % | 7.5 | 38.1 | — | 3.81 |
| logreg_duty_matched | heldout_ux_r1 | 78.8 % | 52.9 % | 9.0 | 59.6 | — | — |
| logreg_duty_matched | heldout_ux_r2 | 38.2 % | 20.8 % | 3.0 | 8.4 | — | 3.81 |
| logreg_duty_matched | heldout_bench5 | 82.6 % | 70.5 % | 6.0 | 307.0 | — | — |
| logreg_duty_matched | train_oof | 73.8 % | 68.5 % | 18.0 | 138.1 | 22.474 | — |
| hgb_strict θ=0.7493 | heldout_evenings | 52.0 % | 22.0 % | 4.0 | 16.6 | — | 0.816 |
| hgb_strict | heldout_ux_r1 | 56.4 % | 27.1 % | 4.0 | 26.6 | — | — |
| hgb_strict | heldout_ux_r2 | 20.6 % | 4.2 % | 4.0 | 2.9 | — | 0.816 |
| hgb_strict | heldout_bench5 | 44.6 % | 20.5 % | 4.0 | 82.7 | — | — |
| hgb_strict | train_oof | 57.9 % | 52.9 % | 13.0 | 63.2 | 0.987 | — |
| hgb_duty_matched θ=0.4322 | heldout_evenings | 68.4 % | 38.5 % | 9.5 | 31.4 | — | 1.905 |
| hgb_duty_matched | heldout_ux_r1 | 73.4 % | 45.9 % | 11.0 | 49.9 | — | — |
| hgb_duty_matched | heldout_ux_r2 | 32.4 % | 12.5 % | 4.0 | 6.1 | — | 1.905 |
| hgb_duty_matched | heldout_bench5 | 70.7 % | 52.3 % | 4.0 | 210.3 | — | — |
| hgb_duty_matched | train_oof | 75.3 % | 70.9 % | 19.0 | 109.7 | 20.062 | — |

Moments:
```
{
 "silence_250": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    0
   ]
  }
 },
 "logreg_strict": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    1
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "logreg_duty_matched": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "hgb_strict": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": [
    1
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 },
 "hgb_duty_matched": {
  "sunday_0506_burst": {
   "E": "2026-10-20T05:06:00",
   "fires_ge2s_before": true,
   "first_alarm_s_before": 3,
   "alarm_s_before_in_30s": [
    3,
    2,
    1,
    0
   ]
  },
  "death_045455": {
   "E": "2026-10-21T04:54:55",
   "fires_ge2s_before": false,
   "first_alarm_s_before": null,
   "alarm_s_before_in_30s": []
  }
 }
}
```

## BENCH-R1 cell 8 (none + hold), the frozen models, the session forced eligible

```
{
 "session_start": "2026-10-22T04:14:59.771Z",
 "rows": 685,
 "hitch_seconds": 29,
 "k": {
  "1": {
   "logreg_hashed": {
    "alarm_s_per_10min": 600.0,
    "fa_seconds_per_10min": 574.56
   },
   "logreg_strict": {
    "alarm_s_per_10min": 1.75,
    "fa_seconds_per_10min": 1.75
   },
   "logreg_duty_matched": {
    "alarm_s_per_10min": 15.77,
    "fa_seconds_per_10min": 14.04
   },
   "hgb_hashed": {
    "alarm_s_per_10min": 600.0,
    "fa_seconds_per_10min": 574.56
   },
   "hgb_strict": {
    "alarm_s_per_10min": 3.5,
    "fa_seconds_per_10min": 2.63
   },
   "hgb_duty_matched": {
    "alarm_s_per_10min": 19.27,
    "fa_seconds_per_10min": 16.67
   },
   "silence_250": {
    "alarm_s_per_10min": 15.77,
    "fa_seconds_per_10min": 14.04
   },
   "silence_950": {
    "alarm_s_per_10min": 1.75,
    "fa_seconds_per_10min": 0.88
   }
  },
  "2": {
   "logreg_hashed": {
    "alarm_s_per_10min": 600.0,
    "fa_seconds_per_10min": 551.68
   },
   "logreg_strict": {
    "alarm_s_per_10min": 1.75,
    "fa_seconds_per_10min": 1.76
   },
   "logreg_duty_matched": {
    "alarm_s_per_10min": 14.89,
    "fa_seconds_per_10min": 11.42
   },
   "hgb_hashed": {
    "alarm_s_per_10min": 600.0,
    "fa_seconds_per_10min": 551.68
   },
   "hgb_strict": {
    "alarm_s_per_10min": 3.5,
    "fa_seconds_per_10min": 1.76
   },
   "hgb_duty_matched": {
    "alarm_s_per_10min": 11.39,
    "fa_seconds_per_10min": 7.91
   },
   "silence_250": {
    "alarm_s_per_10min": 15.77,
    "fa_seconds_per_10min": 12.3
   },
   "silence_950": {
    "alarm_s_per_10min": 1.75,
    "fa_seconds_per_10min": 0.88
   }
  },
  "3": {
   "logreg_hashed": {
    "alarm_s_per_10min": 600.0,
    "fa_seconds_per_10min": 529.62
   },
   "logreg_strict": {
    "alarm_s_per_10min": 1.75,
    "fa_seconds_per_10min": 1.76
   },
   "logreg_duty_matched": {
    "alarm_s_per_10min": 12.26,
    "fa_seconds_per_10min": 8.8
   },
   "hgb_hashed": {
    "alarm_s_per_10min": 600.0,
    "fa_seconds_per_10min": 529.62
   },
   "hgb_strict": {
    "alarm_s_per_10min": 3.5,
    "fa_seconds_per_10min": 1.76
   },
   "hgb_duty_matched": {
    "alarm_s_per_10min": 7.01,
    "fa_seconds_per_10min": 4.4
   },
   "silence_250": {
    "alarm_s_per_10min": 15.77,
    "fa_seconds_per_10min": 11.44
   },
   "silence_950": {
    "alarm_s_per_10min": 1.75,
    "fa_seconds_per_10min": 0.88
   }
  }
 }
}
```
