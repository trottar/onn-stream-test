---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 42a2ab6
---

# B29 — a loss-guard hold is not a stall; the cap on the hold's own clock; APK `9719ea82…` pinned, NOT installed

**Result: SETTLED + BUILT; JVM 161 / 161 (7 new); the guard off = today's monitor, byte for byte, PROVEN; the mutation
fails 2; no host change; no live run.** Record: `evidence/B29_GUARD_QUIET_STALL_2026-10-28.md`. Nothing committed.

- **Settled:**
  - a hold ages the decoder's output, so B7's monitor sent stalls and the host paused and rewound at 400 (CL-B15:
    9);
  - "685 ms past the cap" was the episode's drop-to-IDR span, not a late cap: the hold ended at the cap and 7 frames
    passed before the IDR.
- **Built:**
  - while the guard holds, the stall monitor decides on the time since the last frame received (suppressed; a real
    stall still goes out);
  - the cap is checked by the controller loop's ~8-ms tick;
  - a new report key, `loss_guard_max_hold_ms`.
- **APK** (B5 … B27 + B29) `9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110`, 9,639,374 B. Same
  signer as `8b0fbb74…`; only `classes3.dex` differs.
- **Apply:** `git apply evidence/b29_2026-10-28/b29.diff` (the tree already carries it, uncommitted); install only
  in CL-B16.
- **Rollback:** put `8b0fbb74…` back on; or revert the three files.
