# Current Handoff

The authoritative resumable state is `../CURRENT.md`.

D5 media/server restoration remains COMPLETE / RUNTIME VALIDATED.
D4 Games remains COMPLETE / RUNTIME VALIDATED.

Current direction:
- Phase C Linux continuation is active;
- C1 profile/backend and C2 telemetry are complete on Linux;
- `C3.L0` actuator boundary audit is complete;
- the next work item is `C3.L1`, the Linux encoder-only restart continuity probe;
- do not begin D7 as the next major development item;
- do not begin Phase E; it measures a finalized architecture.

D6 UDP replay remains historical but active ownership is Phase C transport
validation.

## C3 entry conditions

Read `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` before proposing any
actuator work. It records what has already been audited and what is foreclosed.

Do not rebuild the Windows-era C3 record. D-063, D-067, D-068, D-069, D-070 and
D-071 are closed and remain authoritative as history.

The automatic bitrate controller is blocked until a Linux actuator interruption
cost is measured.

## Patch Procedure

Meaningful updates use the standard PrivyHub patch workflow:
- ZIP delivered into repository root;
- predecessor state/hash verification;
- wrong-state rejection before modification;
- backups under archive/patch_backups;
- one coherent change;
- validation;
- exact rollback on failure;
- git diff validation;
- commit and push;
- runtime validation when applicable.

Durable memory is part of the patch, not after-the-fact prose. Every patch
records failures, rejections and rollbacks alongside successes; see the
negative-result policy in `../MEMORY.md`.

Local testing directories such as `_patches/` and `_probes/` are development-only
and are not part of pushed changes unless explicitly intended. They are not
currently covered by `.gitignore`; confirm with `git status --short` before
committing.
