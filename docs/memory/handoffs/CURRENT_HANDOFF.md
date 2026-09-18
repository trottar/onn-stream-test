# Current Handoff

The authoritative resumable state is `../CURRENT.md`.

D5 media/server restoration remains COMPLETE / RUNTIME VALIDATED.

Current direction:
- resume Phase C Linux continuation;
- do not begin D7 as the next major development item;
- preserve validated D4/D5 evidence.

D6 UDP replay remains historical but active ownership is Phase C transport validation.

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

Local testing directories such as `_patches/` and `_probes/` are development-only and are not part of pushed changes unless explicitly intended.
