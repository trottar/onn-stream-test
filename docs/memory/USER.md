---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Collaboration Preferences

This file records project-working preferences, not personal biography.

- Validate deterministic work before handing it to the user. “Validate everything always” is a hard project rule.
- Do not ask for IP addresses or request that network addresses be pasted into chat.
- Prefer one focused diagnostic and one resulting log over broad troubleshooting lists.
- Use the local working tree as the source of truth between checkpoints.
- Preserve stable subsystems unless evidence specifically points to them.
- Explain terminology precisely. In controller work, distinguish `Player 1 / Player 2` from `BUTTON A / BUTTON B` and from internal RetroPad controls.
- Use Xbox-style names in the user-facing input editor; internal libretro terminology should stay internal unless technically necessary.
- Deliver patch ZIPs with exact hashes, validation, rollback behavior, and a single complete install/test procedure.
- Do not continue polishing a feature after the user has declared it done unless a real regression appears.
- Keep status communication concise but explicit: what is proven, what is only source-audited, what remains, and the exact next step.
