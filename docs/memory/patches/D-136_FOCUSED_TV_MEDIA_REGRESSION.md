# D-136 — Focused TV/media regression gate

**Date:** 2026-09-17

Production changes: none.

Added:
- D-135 runtime acceptance evidence;
- `tools/probes/d136_focused_tv_media_regression_probe.py`;
- D-136 investigation and durable-memory state.

The D-136 probe runs the established D-122 automated regression probe fresh and
requires accepted D-133 and D-135 runtime results.

Automated target:

`D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED`

Manual closeout remains one Live TV playback, guide/navigation smoke, and one VOD
playback.

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
