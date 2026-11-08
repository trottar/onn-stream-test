---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 0eb115d9
---

# B56 — H0 import slice 1a (PS1): `tools/import_usb.py` behind `PRIVYHUB_IMPORT=1`

**Result: SETTLED + BUILT; `tests/import_usb` 21 green ×3; 10 mutations caught (M10 after a strengthened test);
absent = refuses / today's list PROVEN.** Record: `evidence/B56_IMPORT_SLICE_1A_2026-11-08.md`; the user's page
`docs/IMPORT.md`.

- **Files:** `tools/import_usb.py` (new), `companion/import_marks.py` (new), `companion/plugins/games.py` (4 hunks
  behind the flag), `tests/import_usb/` (new), `docs/IMPORT.md` (new).
- **Apply:** `git apply evidence/b56_2026-11-08/b56.diff` (or queue T's combined diff, applied to the tree).
- **Live:** the tool runs only with `PRIVYHUB_IMPORT=1` on its command line; the list's marks only with
  `PRIVYHUB_IMPORT=1` in the companion's environment (a bench drop-in for IMPORT-1).
- **Rollback:** reverse it; the marks file `data/import/marks.json` is then unread. Imported titles stay in the
  library as ordinary files.
