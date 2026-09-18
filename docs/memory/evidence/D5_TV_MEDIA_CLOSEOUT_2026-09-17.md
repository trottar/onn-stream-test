# D5 TV/media closeout — 2026-09-17

## Classification

**D5_MEDIA_SERVER_RESTORATION_COMPLETE_RUNTIME_VALIDATED**

## Automated acceptance

Fresh D-136 result after D-137:

`D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED`

Sub-gates:
- D-122 automated TV/media baseline: validated;
- D-133 guide layout/status: validated;
- D-135 Favorites executor isolation/state reconciliation: validated;
- problems: none.

Representative accepted performance:
- Favorites total: 1,599 ms;
- Favorites executor queue wait: 2 ms;
- Linux TV-state sync still completed and reconciled.

## Manual closure smoke

Final onn smoke passed:

1. Live TV playback — passed;
2. Favorites/guide navigation and presentation — passed;
3. VOD playback — passed.

## Closed D5 boundaries

Validated:
- configurable/external VOD storage behavior;
- Live TV catalog/categories/playback;
- Linux EPG acquisition/cache and Android guide consumption;
- durable Linux TV-state authority and onn synchronization;
- incorrect-guide durable user intent;
- one-column guide presentation and accurate schedule-gap status;
- non-blocking top-level TV entry;
- Favorites executor isolation and responsive page loading;
- focused automated and manual media regression.

## Deferred / not reopened

- D6 UDP replay remains deferred;
- broad guide-grid/timeline redesign;
- fuzzy EPG matching;
- centralized multi-client stream-health redesign;
- browser/camera generalized native-source work remains outside this closed D5
  milestone.

## Conclusion

D5 media/server restoration is closed. Proceed to D7 native Linux regression,
then D8 Linux baseline checkpoint.
