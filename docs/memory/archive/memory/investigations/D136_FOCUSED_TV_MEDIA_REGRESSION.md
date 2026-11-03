# D-136 — Focused TV/media regression

**Date:** 2026-09-17
**Status:** regression gate active

## Purpose

Close the bounded post-D5 TV/EPG UX/performance sequence with the smallest
existing regression seam.

## Automated gate

Reuse `tools/probes/d122_d5_tv_media_regression_probe.py`, which checks:
- companion status;
- source catalog;
- EPG readiness;
- exact Linux/onn TV-state parity;
- sync diagnostic baseline.

D-136 additionally requires:
- D-133 guide status/layout acceptance;
- D-135 Favorites queue/contention acceptance.

## Manual smoke

The automated probe does not prove visible/audio playback. Repeat the established
short onn smoke:
1. play one Live TV channel;
2. browse Favorites/guide and confirm navigation/display remains normal;
3. play one VOD item.

If automated and manual checks are clean, D5 bounded TV/media work can close.

<!-- PRIVYHUB_D136_FIRST_RUNTIME_RESULT:BEGIN -->
## First runtime result — diagnostic false negative identified

D-136 classification:
`D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_FAILED`

Sub-gates:
- D-133: accepted;
- D-135: accepted;
- D-122: `D122_TV_STATE_PARITY_FAILED`.

Inspection showed D-122's D-116 local projection omitted TV user-state schema-v2
guide-intent fields, so this result does not establish production state divergence.

**Status: rerun required after D-137 diagnostic repair.**
<!-- PRIVYHUB_D136_FIRST_RUNTIME_RESULT:END -->

<!-- PRIVYHUB_D136_ACCEPTED_AFTER_D137:BEGIN -->
## Automated acceptance after D-137

Fresh rerun:

`D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED`

D-122, D-133 and D-135 all pass. Problems: none.

**Status: automated regression accepted; manual playback/navigation smoke pending.**
<!-- PRIVYHUB_D136_ACCEPTED_AFTER_D137:END -->

<!-- PRIVYHUB_D136_MANUAL_CLOSEOUT:BEGIN -->
## Manual closure smoke — passed

Final onn smoke after automated acceptance:
- Live TV playback: passed;
- Favorites/guide navigation: passed;
- VOD playback: passed.

**Status: D-136 complete; D5 closeout criteria satisfied.**
<!-- PRIVYHUB_D136_MANUAL_CLOSEOUT:END -->
