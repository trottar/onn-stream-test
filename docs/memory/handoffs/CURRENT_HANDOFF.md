---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree:
  `/home/privyhub/Projects/onn-stream-test`.
- D-125 is runtime accepted.
- D-126 is runtime accepted:
  `D126_ANDROID_TV_ENTRY_AND_PAGE_PREFETCH_VALIDATED`.
- The currently installed D-126 APK successfully queued 21/21 Favorites for
  guide prefetch.
- Favorites loaded immediately during the acceptance run.
- A few-second initial `Loading TV catalog...` delay remains observed but is
  separate from the fixed EPG cache-miss path.
- No D-127 production change is installed yet.

## Resume

Proceed with the exact D-127 next action in `CURRENT.md`: durable
`Mark Guide Incorrect` intent and deferred recheck. Keep it separate from the
guide-style category UI.

Do not use this file as a second chronology or second roadmap.
