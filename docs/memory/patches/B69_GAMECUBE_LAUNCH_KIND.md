---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9db5a35c
---

# B69 — the GameCube launch kind (Dolphin), behind PRIVYHUB_GAMECUBE=1 (NOT adopted)

**Result: see `evidence/B69_GAMECUBE_LAUNCH_KIND_2026-11-09.md` (tests, mutations, proof).**

- **Apply:** `git apply evidence/b69_2026-11-09/b69.diff` (one diff against `9db5a35c`; applied to the tree,
  uncommitted).
- **Live:** only with `PRIVYHUB_GAMECUBE=1` in the companion's environment (the bench drop-in `b69-gamecube.conf` for
  HOME-9+GC's cells; G-A16 on the user's word) and a companion restart. The keeper's copies of Dolphin's logs start at
  the keeper's next restart; `diag_read` reads the live logs meanwhile.
- **Off:** remove the drop-in, `systemctl --user daemon-reload`, restart the companion. Absent = today
  (`evidence/b69_2026-11-09/proof_flag_absent.md`).
- **Rollback:** `git apply -R evidence/b69_2026-11-09/b69.diff` (`diff_check.txt`).
