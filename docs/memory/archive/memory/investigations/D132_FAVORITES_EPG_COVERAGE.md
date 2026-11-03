# D-132 — Favorites EPG coverage/status classification

**Date:** 2026-09-17

**Status:** diagnostic / runtime measurement required

## Question

D-129 validated the requested one-column guide layout, but at least one visible
row showed `Guide data unavailable`. Before changing acquisition or UI wording,
classify why visible Favorites lack a current trusted programme.

## Probe

`tools/probes/d132_favorites_epg_coverage_probe.py`

The probe snapshots:

- `privyhub_tv.db`
- `privyhub_epg.db`

For visible Favorites it distinguishes:

- Android current programme;
- marked incorrect guide;
- synthetic/unmatchable channel identity;
- Android future-only schedule gap;
- Android stale-only data;
- companion current programme available while Android lacks it;
- companion programmes present but no current programme;
- legacy mapping with no programmes;
- no known guide coverage;
- companion unreachable.

Only Android-missing, canonical channel identities are checked against the local
Linux companion endpoint, bounded to 16 checks.

## Boundary

No production behavior changes. Do not alter D-125/D-126 acquisition, D-127 trust
state, D-129 layout, D-131 entry scheduling, playback, Favorites, Hide, VOD or
Games from this diagnostic.

<!-- PRIVYHUB_D132_RUNTIME_RESULT:BEGIN -->
## Runtime result — 2026-09-17

`D132_FAVORITES_GUIDE_GAPS_CLASSIFIED`

- visible Favorites: 21
- Android current programme: 11
- companion programmes but no current programme: 5
- no known guide coverage: 5

The five schedule-gap rows also had Android future programmes. D-133 owns the
bounded presentation correction.

**Status: runtime measured / closed.**
<!-- PRIVYHUB_D132_RUNTIME_RESULT:END -->
