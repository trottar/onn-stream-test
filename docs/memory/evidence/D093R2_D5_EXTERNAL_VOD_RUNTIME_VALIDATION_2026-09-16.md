---
memory_schema: 1
as_of: 2026-09-16
status: runtime_validated
classification: D092_EXTERNAL_VOD_NORMAL_ONN_PLAYBACK_CONFIRMED
---

# D-092 external-VOD runtime validation — 2026-09-16

## Development patch

D-092 changed dynamic VOD source-start health so scanner-generated sources may
traverse a safe scanner-mediated symlink to external storage only when the
lexical media path resolves to the exact scanner-recorded target.

Static/configured VOD did not receive a general external-path allowance.

## Post-install source-start gate

Fresh probe:
`logs/d092_dynamic_vod_source_start_probe.txt`

Result:
`D092_DYNAMIC_VOD_SOURCE_START_CONFIRMED`

Measured:
- catalog request HTTP 200;
- representative movie source found;
- source-start HTTP 200;
- `ready: true`;
- no source-start error.

## Normal onn runtime validation

The same representative movie that previously failed with HTTP 503 was tested
through the normal PrivyHub onn UI.

Observed:
- movie playback works;
- normal VOD playback behavior works;
- Continue Watching was explicitly tested and works.

## Checkpoint installer history

D-093 and D-093R1 both rolled back cleanly due to installer-only documentation
validation defects. Neither changed the runtime result.

D-093R2 is the corrected checkpoint.

## Classification

`D092_EXTERNAL_VOD_NORMAL_ONN_PLAYBACK_CONFIRMED`

The D-092 source-start regression is closed.

## Remaining architectural work

This validates the temporary symlink-backed deployment, not the permanent
storage model.

D5 next:
first-class configurable bulk-media root, followed by Linux live-source runner
work and integrated media regression.
