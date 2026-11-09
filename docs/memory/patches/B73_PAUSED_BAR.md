---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a5c51e37
---

# B73 — the paused bar fits: SAVE · LOAD · DISC · END on the TV (NOT adopted; default on)

**Result:** `evidence/B73_PAUSED_BAR_2026-11-09.md` (why END ran off, the plan, tests, mutations, proof).

- **Apply:** `git apply evidence/b73_2026-11-09/b73.diff` (first, before `b74.diff`). Applied to the tree, uncommitted.
- **Live:** with the APK `85220f99…4864`, pinned and **NOT installed**. Client only.
- **Off:** `debug.privyhub.paused_bar_fit=0` (B71's bar). A one-disc bar is never touched.
- **Rollback:** `git apply -R` in the order 74, 73.
- **The APK pin:** `queue_aa_built/app-debug.apk`, sha256 `85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`
  (B5 … + B54 + B67 + B70 + B71 + B72 (a) + B73 + B74; B27 / B29 out). It has the same signer as `5f72af4b…`, which
  stays CONFIRMED until HOME-11's rule.
