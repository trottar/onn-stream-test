---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: d618a20a
---

# B58 — H0 import slice 1b: the plain source folder, SNES / NES / Genesis, the journal (behind `PRIVYHUB_IMPORT=1`)

**Result: SETTLED + BUILT; `tests/import_usb` 40 green ×3 (B56's 21 unchanged + B58's 19; the two git checks run in
the tree); 16 mutations caught (M10 and M16 after strengthened tests); absent = refuses / today's list PROVEN.**
Record: `evidence/B58_IMPORT_SLICE_1B_2026-11-08.md`; the user's page `docs/IMPORT.md` (extended).

- **Files:** `tools/import_usb.py`, `companion/import_marks.py` (`pending()`), `companion/plugins/games.py` (one line
  inside B56's flag block), `tests/import_usb/test_b58.py` (new), `docs/IMPORT.md`.
- **Apply:** `git apply evidence/b58_2026-11-08/b58.diff` (applied to the tree, uncommitted).
- **Live:** the tool with `PRIVYHUB_IMPORT=1` on its command line; the list's journal hiding with the flag in the
  companion's environment (the bench drop-in `b56-import.conf` until HOME-7's C19), at its next restart.
- **Rollback:** reverse it; `data/import/journal.json` is then unread (none exists on the hub today).
