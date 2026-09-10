---
memory_schema: 1
as_of: 2026-09-10
---

# A9 NES / Genesis no-fixture correction

No NES or Genesis games were installed during the A9 runs. The yes/no gameplay
prompts for those systems were answered without real sessions.

Therefore:
- NES A9 runtime evidence: INVALID / no fixture;
- Genesis A9 runtime evidence: INVALID / no fixture;
- repeated `<unknown>` identification is not evidence of a production defect;
- neither family may be called runtime validated from A9;
- the correct state is `SKIPPED_NO_LOCAL_FIXTURE` when library count is 0.

The corrected finish probe machine-checks each system's current library count
before deciding whether to require a runtime launch.

This does not invalidate the genuinely exercised A9 stages: SNES, ordinary PS1,
Save/Load, pause/resume, frozen preview, host coexistence, direct launch, cheats,
mods, named input profiles, teardown, CTR multitap evidence, and repository
audit.
