# B58 — `PRIVYHUB_IMPORT` absent = today byte for byte, hunk by hunk

`b58.diff` against the baseline copy (`d618a20a`): 5 files (`tools/import_usb.py`, `companion/import_marks.py`,
`companion/plugins/games.py`, `tests/import_usb/test_b58.py` new, `docs/IMPORT.md`).

| file | hunk | why absent is today |
| --- | --- | --- |
| `tools/import_usb.py` | every change | `main()` still returns 9 before parsing or opening any path when `PRIVYHUB_IMPORT` is not exactly `1` (unchanged first lines). Nothing in the companion imports the tool. |
| `companion/import_marks.py` | `JOURNAL_REL`, `pending()` | the plugin imports the module only with the flag (B56's `_import_marks = None` otherwise); nothing else imports it. |
| `companion/plugins/games.py` | the hidden ids | inside B56's `if _import_marks is not None:`; absent, the block is never entered. |
| `docs/IMPORT.md` | the user's page | words only. |
| `tests/import_usb/test_b58.py` | tests | new. |

**Shown:**
- **The tool, in the tree, with no flag** (`env -u PRIVYHUB_IMPORT`): `inspect --source … --system snes`, `plan --source
  … --system snes`, `inspect <mount>`, `apply`, `verify` → each "PRIVYHUB_IMPORT=1 is not set: nothing was read or
  written.", exit 9 (`absent_cli.txt`; the source path given does not exist, and no error about it appears: nothing was
  opened).
- **The tests:** `Absent.test_the_tool_refuses_both_forms_and_nothing_changes` (four non-`1` values × five commands, the
  fixture tree's listing — names, sizes, mtimes — equal before and after); `Journal.…never_listed…` (the plugin without
  the flag lists a journaled file: today's list, which reads no journal); B56's `List.test_absent_is_todays_list`.
- **With the flag, PS1 as B56:** B56's 21 tests unchanged and green. Two behaviour changes, disclosed: (1) re-applying
  a plan whose titles are already whole in the library is `already_placed` (exit 0) where B56 gave `target_exists`
  (exit 4); a final with other bytes is still never overwritten (B56's test unchanged); (2) the free-space check reads
  the `games/` filesystem instead of `games/ps1/` (the same filesystem on the hub).
- **Every host suite** in the B58 copy equals the baseline copy except `tests/import_usb` (21 → 40 tests); in the
  combined copy (B57 + B58) only `tests/import_usb` and `tests/relaunch_ports` differ; the same six `tools/` tests fail
  in all three, identically.

**Result: PROVEN.**
