---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e
---

# B67 — the client items: the N64 layout card, "This game supports 2 players", the stored count capped, B64's order, the start gate's re-arm; APK 5f72af4b… pinned, NOT installed

**Result: see `evidence/B67_CLIENT_STRINGS_2026-11-09.md` (tests, mutations, proof).**

- **Apply:** `git apply evidence/b67_2026-11-09/b67.diff`. The four diffs go in order b65, b66, b67, b68, each
  against the previous snapshot; they are applied to the tree, uncommitted.
- **Live:** with the APK installed (HOME-9); the knobs debug.privyhub.player_prompt / debug.privyhub.start_gate_rearm = 0 turn them off.
- **Rollback:** reverse the diffs in the order b68, b67, b66, b65 (`diff_check.txt`).
