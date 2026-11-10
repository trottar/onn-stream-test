---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: 051bb4d0
---

# B88 — `ps2-patches` on the onn's POST, and the client ↔ hub contract test (NOT adopted; no knob — a new route; the GET unchanged)

**Result:** `evidence/B88_PS2_PATCHES_ROUTE_AND_CONTRACT_2026-11-10.md`.

- **Apply:** `git apply evidence/b88_2026-11-10/b88.diff` (after `b87.diff`).
- **Live:** at the companion's next restart (the onn's Patches… → Save answers).
- **Off:** — (remove the route with `git apply -R`).
- **Rollback:** `git apply -R` in order (89, 88, 87).
