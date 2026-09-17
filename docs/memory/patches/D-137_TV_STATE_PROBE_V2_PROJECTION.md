# D-137 — TV-state probe schema-v2 projection

**Date:** 2026-09-17

Production changes: none.

Changed:
- `tools/probes/d116_android_tv_state_sync_probe.py`

The diagnostic projection now includes D-127 TV-state schema-v2 guide-intent
fields and guide-incorrect-only rows.

Validation:
- Python compile;
- D-116 self-test;
- D-122 self-test;
- D-136 self-test;
- git diff --check;
- memory health.

Runtime target remains the D-136 automated regression classification after a
fresh rerun.
