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

<!-- PRIVYHUB_D137_RUNTIME_RESULT:BEGIN -->
## Runtime result — accepted 2026-09-17

D-137 corrected the D-116 schema-v2 projection. A fresh D-136 rerun then passed
D-122 canonical parity and the full focused automated regression.

**Status: diagnostic repair accepted.**
<!-- PRIVYHUB_D137_RUNTIME_RESULT:END -->
