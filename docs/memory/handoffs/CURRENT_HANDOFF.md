---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 6866ee1a2b9e6dab7e0490796a7d6de74860788a
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`.

- D-133 is runtime accepted.
- D-133 probe: 4 full-width rows, 2 Now rows, 1 correct schedule-gap row with
  Next, 0 mislabeled gaps, 1 true unavailable row.
- User reports Favorites can still take >15 seconds to open.
- Current `openTvPage()` synchronously calls `hydrateCompanionGuides()` before
  posting the result UI.
- D-134 measures each existing stage without changing ordering.

Resume with D-134 runtime timing.
