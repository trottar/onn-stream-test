---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 94c05e4a
---

# B71 — "Change disc": the host's `disc-swap` action (RetroArch's disk commands) and the paused bar's CHANGE DISC (NOT adopted; default on)

**Result:** `evidence/B71_CHANGE_DISC_2026-11-09.md` (settled commands, tests, mutations, proof, the APK).

- **Apply:** `git apply evidence/b71_2026-11-09/b71.diff`, after `b70.diff`. It is applied to the tree second,
  uncommitted.
- **Live:**
  - the host: at the companion's next restart, on a multi-disc PS1 (`.m3u`) session only; every other session is
    today's;
  - the client: with the APK `64d02f31…85dd`, pinned and **NOT installed**.
- **Off:**
  - the host: `PRIVYHUB_DISC_SWAP=0` (no disc session is recognised; the action is today's unknown action);
  - the client: `debug.privyhub.disc_change=0` (no CHANGE DISC).
- **Rollback:** `git apply -R` in the order 72, 71, 70.
- **The APK pin:** `queue_z_built/app-debug.apk`, sha256 `64d02f3149eb9f14ac829c800388751fbe0a350c66d5981984bb9a508b7285dd`
  (B5 … + B54 + B67 + B70 + B71 + B72 (a); B27 / B29 out). It has the same signer as `5f72af4b…`, which stays
  CONFIRMED until HOME-10's rule.
