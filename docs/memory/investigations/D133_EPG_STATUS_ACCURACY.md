# D-133 — Accurate EPG schedule-gap status

**Date:** 2026-09-17
**Status:** development patch / runtime validation required

D-132 measured 11 current-programme Favorites, 5 future-schedule/no-current
Favorites, and 5 no-known-coverage Favorites.

`MainActivity.tvChannelToNode()` currently prints `Guide data unavailable`
whenever there is no current programme, before separately appending `Next:`.

D-133 changes only that display branch:
1. current -> existing `Now:`;
2. no current + upcoming -> `No current listing`;
3. neither -> `Guide data unavailable`;
4. marked incorrect -> unchanged D-127 behavior.

Runtime target: `D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`.
