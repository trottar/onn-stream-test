---
memory_schema: 1
as_of: 2026-11-19
baseline_commit: df81c762 (this repo)
---

# B167 — learn's real picture source starts

**Result:** `evidence/B167_ADD_GAME_PICTURES_START_2026-11-19.md`.

- **Files:** `tools/party_add_game_capture.py` (the hub's display, core and core options; `CaptureError` and its
  reasons; RetroArch's log kept; the busy check; the screenshot read whole), `tools/party_add_game.py` (`PicturesFailed`,
  `logs_folder`, `_call_capture`, learn's "pictures made" cell, rehearse's begin from the rules folder and its extras'
  cell, `_labels` anchored on the screen that stays); `tests/b167_pictures_start/` (new: the tests, `fake_ra.py`),
  `tests/b163_rehearse/test_b163.py` (the rules folder's begin); `evidence/b167_2026-11-19/b167_b169.diff` (B167 and
  B169 together; applies on `df81c762`).
- **Switch:** none — no companion change; the capture runs only in learn and rehearse, never while a game or a client's
  stream is up.
- **Rollback:** `git apply -R docs/memory/evidence/b167_2026-11-19/b167_b169.diff` (also takes B169 out). RetroArch's
  logs in the title's add_game folder (`logs/`, off the repo) are the tool's own.
