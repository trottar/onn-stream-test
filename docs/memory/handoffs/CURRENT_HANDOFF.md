# Current Handoff

The authoritative resumable state is `../CURRENT.md`.
The compact Phase C brief is `../PHASE_C_CONTEXT.md`; start there.

D5 media/server restoration remains COMPLETE / RUNTIME VALIDATED.
D4 Games remains COMPLETE / RUNTIME VALIDATED.

Current direction:
- Phase C Linux continuation is active;
- C1 profile/backend and C2 telemetry are complete on Linux;
- `C3.L0` boundary audit and `C3.L1` / `C3.L1R1` encoder-only actuator runs are
  complete, the actuator is runtime validated at 287-318 ms decoder output gap;
- `C3.L2` classified Linux as `video_only_restart`, authorized for start-time,
  manual, fallback and characterization use and not for automatic in-game
  adaptation;
- the next work item is `C3.L2a`, the first-IDR acceptance investigation, which
  starts from existing decoder-session evidence rather than a code change;
- do not begin D7 as the next major development item;
- do not begin Phase E; it measures a finalized architecture.

D6 UDP replay remains historical but active ownership is Phase C transport
validation.

## C3 entry conditions

Read `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` and
`investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` before proposing any actuator
work. They record what is classified, what is authorized, what is foreclosed and
what is merely assumed.

Do not rebuild the Windows-era C3 record. D-063, D-067, D-068, D-069, D-070 and
D-071 are closed and remain authoritative as history.

The automatic bitrate controller is blocked; its gate is the `C3.L2a` result,
not a further re-measurement of the actuator itself.

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
