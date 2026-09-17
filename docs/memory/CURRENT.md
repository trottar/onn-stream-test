---
memory_schema: 2
state_updated: 2026-09-17
active_work_item: D-137
maintenance_status: healthy
baseline_commit: 93047ce05399744d461a2ad451fa5604c5f268a9
---

# Current Project State

## Active Objective

Finish bounded D5 TV/media regression and closeout without reopening validated
production subsystems absent new evidence.

## Current Work Item

**D-137 — repair stale TV-state regression projection for schema v2.**

D-136's automated gate failed only at D-122 TV-state parity:

`D122_TV_STATE_PARITY_FAILED`

D-133 and D-135 remained accepted.

Source inspection found the parity probe itself stale. D-122 delegates the onn
projection to `d116_android_tv_state_sync_probe.local_projection()`. That helper
still projects the original TV-state channel fields and neither selects nor emits
the D-127 schema-v2 durable fields:

- `guide_incorrect`;
- `rejected_guide_source_key`;
- `guide_incorrect_at_ms`.

The Linux `TvStatePlugin` normalizer now includes those fields in canonical state.
A durable marked-incorrect channel therefore hashes differently even when runtime
sync is correct.

## Verified State

- D-133 guide layout/status: **runtime validated**.
- D-135 Favorites executor isolation: **runtime validated**.
- D-136 current failure is isolated to D-122 canonical TV-state parity.
- D-116 projection is schema-v1-shaped while Linux authority is schema v2.

## Current Repository / Patch State

Expected D-137 predecessor:

`93047ce05399744d461a2ad451fa5604c5f268a9`

D-137 changes diagnostic tooling only:
`tools/probes/d116_android_tv_state_sync_probe.py`.

It makes the projection schema-v2 complete and strengthens D-116's self-test for
guide-incorrect durable intent.

**Status: DIAGNOSTIC PROBE REPAIR / D-136 RERUN NEXT.**

## Next Action

1. install/commit/push D-137;
2. rerun D-136 fresh;
3. if automated regression validates, perform the established short manual onn
   smoke: Live TV playback, guide/navigation, VOD playback;
4. record D5 closeout if clean.

## Success Criteria

- D-116 local projection includes all TV user-state v2 channel fields;
- guide-incorrect-only rows are included;
- D-116 self-test covers schema-v2 guide intent;
- no production code changes;
- D-136 parity is recomputed fresh rather than assumed.

## Do Not Reopen Without New Evidence

- D5.4 TV-state production semantics.
- D-125/D-126 EPG background behavior.
- D-127 incorrect-guide production behavior.
- D-129/D-133 guide presentation.
- D-131/D-135 executor scheduling.
- External VOD architecture.
- Linux Games lifecycle.
- Deferred UDP work.

## Relevant References

- `investigations/D136_FOCUSED_TV_MEDIA_REGRESSION.md`
- `investigations/D137_TV_STATE_PROBE_V2_PROJECTION.md`
- `patches/D-137_TV_STATE_PROBE_V2_PROJECTION.md`
- `architecture/TV_STATE_SYNC.md`
- `roadmap/STATUS.md`
- `2026-09-17.md`
