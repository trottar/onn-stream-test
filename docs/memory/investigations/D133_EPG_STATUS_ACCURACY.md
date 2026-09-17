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

<!-- PRIVYHUB_D133_RUNTIME_RESULT:BEGIN -->
## Runtime result — accepted 2026-09-17

`D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED`

4/4 visible guide rows remained full-width; 2 had current programmes; 1 had
`No current listing` plus `Next:`; 0 had the old unavailable+next contradiction;
1 genuine unavailable row remained.

**Status: runtime accepted.**
<!-- PRIVYHUB_D133_RUNTIME_RESULT:END -->
