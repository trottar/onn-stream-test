# D-137 — TV-state probe schema-v2 projection repair

**Date:** 2026-09-17
**Status:** diagnostic repair / validation required

## Trigger

D-136:
`D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_FAILED`

Only failed sub-gate:
`D122_TV_STATE_PARITY_FAILED`.

D-133 and D-135 remained accepted.

## Root cause

D-122 reuses `d116_android_tv_state_sync_probe.local_projection()`.

That helper's `streams` query and channel projection predate D-127. Linux
`TvStatePlugin.USER_STATE_SCHEMA` is now v2 and its canonical channel state
includes:

- `guide_incorrect`;
- `rejected_guide_source_key`;
- `guide_incorrect_at_ms`.

D-116 omits those fields and also omits rows whose only durable intent is
`guide_incorrect`. Canonical hashes therefore diverge whenever durable incorrect
guide intent exists.

## Repair

Update D-116 diagnostic projection to match v2. Do not change production sync,
database schema, plugin state, or D-127 behavior.

Then rerun D-136 fresh.

<!-- PRIVYHUB_D137_RUNTIME_RESULT:BEGIN -->
## Runtime result — accepted 2026-09-17

D-137 corrected the D-116 schema-v2 projection. A fresh D-136 rerun then passed
D-122 canonical parity and the full focused automated regression.

**Status: diagnostic repair accepted.**
<!-- PRIVYHUB_D137_RUNTIME_RESULT:END -->
