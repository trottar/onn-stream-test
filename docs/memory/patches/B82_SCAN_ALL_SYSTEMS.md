---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: 8813f06a
---

# B82 — the game scan sees every system the hub lists; the tools no longer build the companion's plugins (NOT adopted; no knob — it follows `PRIVYHUB_PS2` / `PRIVYHUB_N64` / `PRIVYHUB_GAMECUBE`)

**Result:** `evidence/B82_SCAN_ALL_SYSTEMS_2026-11-10.md`.

- **Apply:** `git apply evidence/b82_2026-11-10/b82.diff` (on `8813f06a`).
- **Live:** the tools at their next run. The companion at its next restart, whose startup reconcile then sees the
  three systems: one full metadata update, with `provider_unavailable` for N64 / PS2 / GameCube and no request while
  `PRIVYHUB_ART_SYSTEMS` is off.
- **Off:** none of the three flags = today's scan and today's tool output (byte for byte). There is no knob for the
  tools' no-registry import.
- **Writes outside the code:** none of its own (the restart's reconcile writes `metadata.json` and its logs as on any
  library change).
- **Rollback:** `git apply -R` (after B83's diff, if applied).
