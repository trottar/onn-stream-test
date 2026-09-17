# D-128 — Guide-style category presentation

**Date:** 2026-09-17

**Status:** rev3 development patch / runtime validation required

Rev1 failed the deterministic Kotlin compile gate because the installer inserted a second `formatTvGuideTime(Long)` member. The installer emitted `ROLLED BACK`, restoring predecessor bytes. Rev2 updated the existing formatter in place, but the supplied shell wrapper used `set -euo pipefail` plus `exit 1` and terminated the interactive shell when the run failed before installation. Rev3 keeps the corrected transform and returns from a wrapper function instead of exiting the interactive shell.

## Purpose

Use the existing paged TV/category architecture and already-cached guide data to
make Favorites and category pages readable as a compact TV guide.

## Behavior

- shared TV rows show current programme start/end/title;
- shared TV rows show next programme start/end/title when available;
- Android locale/time settings format the clock display;
- D-127 marked-incorrect channels continue to show the incorrect-guide status
  instead of trusted Now/Next content;
- the row renderer reads only `getCachedGuide()`.

## Scope boundary

D-128 does not change Linux EPG acquisition, D-125 background warming, D-126
prefetch, TV-state synchronization, channel identity, playback, Favorites, Hide,
VOD or Games.

## Runtime acceptance

Open TV then Favorites after APK installation and run:

`python3 tools/probes/d128_guide_style_ui_probe.py --repo . --verify`

Target:

`D128_GUIDE_STYLE_FAVORITES_RUNTIME_VALIDATED`
