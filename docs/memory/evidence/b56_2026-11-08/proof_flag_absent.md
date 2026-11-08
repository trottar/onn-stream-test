# B56 — `PRIVYHUB_IMPORT` absent = the tool refuses, writes nothing; the list is today's byte for byte

`b56.diff` against the baseline copy (`0eb115d9`): 5 files — three new (`tools/import_usb.py`,
`companion/import_marks.py`, `tests/import_usb/*`) and one changed (`companion/plugins/games.py`, 4 hunks).

**The tool:** `main()`'s first statement tests `environ[PRIVYHUB_IMPORT] == "1"`; anything else (absent, empty, `0`,
`yes`) returns exit 9 with "PRIVYHUB_IMPORT=1 is not set: nothing was read or written" **before the arguments are
parsed** — no path is opened. Tested: `Flag.test_absent_refuses_and_writes_nothing` (four values × the four
commands; the fixture tree's file list before = after).

**The companion (`plugins/games.py`):**

| hunk | why absent is today |
| --- | --- |
| the import at the top | `_import_marks = None` unless `PRIVYHUB_IMPORT` is `1` at import (B49's pattern); `import_marks` is then never imported. |
| `_scan`: the hidden ids | inside `if _import_marks is not None:`. |
| `systems()`: the PlayStation node's name | `f"{config['name']}" + ("" when _import_marks is None) + " " + f"({count})"` = today's `f"{config['name']} ({count})"` exactly. |
| `games()`: " · NEW" | inside `if _import_marks is not None and nodes:`. |

Tested: `List.test_absent_is_todays_list` (the module loaded with the flag unset: the `.iso` listed, no tag,
"PlayStation (3)"), beside the flag-on test on the same fixture library.

**Result: PROVEN.**
