# B160 — one line in my board file (record)

Queue: `handoffs/QUEUE_2026-11-18BB.md` §B160. Design + `.sha256` hashed 01:07:31Z before the edit. The board's repo:
only my two files (uncommitted there); its HEAD `bb9dcd5`; its status before 0 lines, after 2 (`logs/b160_git_status.txt`).

- `minigames/hub_minigame.gd`: **`const ELSEWHERE := true`** after `const ID := "hub"`, with a two-line comment (played
  on the hub's emulator, the board only waits; the picker's `elsewhere()` is told, it need not guess); the header's
  "its Start pressed within a poll of the hand-over" → **"its Select pressed …"** (queue AZ's item 3). sha256
  `920d0073…` (was `3f32d339…`).
- `checks/hub_minigame_check.gd`: the picker preloaded; one assertion more — the script's `ELSEWHERE` is true and the
  picker's `elsewhere()` says so. sha256 `5d51ffa2…` (was `01301ec5…`).
- **The check** (B145's wrapper: a scratch copy of the board's HEAD with my two files, Godot headless, temp XDG):
  before **PASS (97 assertions)**, the PC side's step28 **PASS (59)**; after **PASS (98 assertions)** twice, step28
  **PASS (59)** — and **one FAIL in the third run**: "no press made during a practice reaches the load screen shown
  behind it (got 1, wanted 0)", a timing assertion my change does not touch. Then, to tell: **HEAD's two files six runs, all PASS (97)** (`check_head_six.txt`; the run for my files after it was stopped at its time limit) and **my two files six runs alone, all PASS (98)** (`check_mine_six.txt`): **8 of 9 runs of my files PASS; the one FAIL not explained** (an assertion on a press during a practice, timing-shaped; my change adds a constant, a comment and an assertion).
- `b160.diff` (the board's `git diff`), `check_before.txt`, `check_after.txt`, `check_head_six.txt`, `check_mine_six.txt`, `sha256_after.txt`, `design_written_before_code.md` + `.sha256`.
