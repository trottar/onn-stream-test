---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 94c05e4a
---

# B70 — the two pointers: `-draw_mouse 0` in the capture, the pads' touchpad swallowed in a game (NOT adopted; default on)

**Result:** `evidence/B70_POINTERS_2026-11-09.md` (tests, mutations, proof).

- **Apply:** `git apply evidence/b70_2026-11-09/b70.diff` (against `94c05e4a`). It is applied to the tree first of
  B70-B72, uncommitted.
- **Live:**
  - the host: at the companion's next restart (no drop-in; default on);
  - the client: with the APK `64d02f31…85dd` (`PrivyHub/app/build/queue_z_built/`), at its install.
- **Off:**
  - the host: `PRIVYHUB_CAPTURE_POINTER=1` in the companion's environment (today's argv, byte for byte);
  - the client: `adb shell setprop debug.privyhub.pointer_hide 0` (today: nothing consumed, no icon, no capture).
- **Rollback:** `git apply -R` of `b72.diff`, `b71.diff`, then `b70.diff`, in that order
  (`evidence/b70_2026-11-09/diff_check.txt`).
