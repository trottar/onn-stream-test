---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: a55d73d
---

# G-A3 — `PRIVYHUB_LINK_REPORT=1` adopted: the ninth line

**Result: INSTALLED SUCCESSFULLY.** It was applied directly in session A on 2026-10-23
(`handoffs/G-A3_AND_CL-B10_TASK.md` PART 1 §1; record `evidence/G_A3_LINK_REPORT_ADOPTION_2026-10-23.md`). The user's
decision ("Yes to both").

The diff is session B's, prepared in `G-A3_LINK_REPORT_ADOPTION_PREPARED.md` (B13). That file is kept: the rename
its §4 asks for would remove the old name, and nothing is deleted.

- **The drop-in (outside the repo):** `~/.config/systemd/user/privyhub-companion.service.d/link-report.conf` =
  `[Service]` / `Environment=PRIVYHUB_LINK_REPORT=1`. It was written ~18:23Z, then daemon-reload and a restart at
  18:24:02Z. The environ read nine lines.
- **The small patches** (`evidence/g_a3_2026-10-23/g_a3_applied.diff`, `docs.diff`; `predecessor_sha256.txt` /
  `after_sha256.txt`):

  | # | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- | --- |
  | 1 | `tools/e1_suite.py` | `9b4926f1bafc8f8a` | `a5d8a5182d4cd4c1` | `LINK_REPORT` in `ADOPTED` (nine); the preflight's `drop_in_link_report` (the comment's `<date>` filled: 2026-10-23) |
  | 2 | `tools/e3_state.py` | `31bc54b44942eac7` | `b45e6ded07dea78f` | the docstring ("since G-A3, nine") |
  | 3 | `tools/e1_remote.py` | `4f8dbd54430d0375` | `772302650a8da52f` | the comment ("nine lines since G-A3") |
  | 4 | `tools/test_e1_remote.py` | `ae6fca193f6bead7` | `828768d8bb49d460` | the comment |
  | 5 | `docs/REMOTE_TRUST.md` | `61e3f9b8c642b10d` | `5372d34b158d3618` | §10: the link report, what leaves the onn, how to turn it off |
  | 6 | `docs/ROADMAP.md` | `c7ab90e4d764e885` | `f24c938d388310c4` | §G4: the G-A3 line |

- **Listed, not changed:**
  - `ADOPTED_E3` in `tools/d7_regression.py` and `tools/c3_l4_nft_night.py` (stale since G-A1);
  - past evidence drivers' "adopted8" strings;
  - the running `link_n1_watch.py`.
- **Validation:**
  - `e1_suite --self-test` OK, `test_e1_remote` 21 OK, `test_c3_l4_nft_night` 33 OK, all from the tree;
  - `git diff --check` clean;
  - `--check` ok on nine lines;
  - the confirmation window VALID with host gates met: 346 / 346 heartbeats with the link keys by the drop-in alone.
- **Revert (written, not applied):**
  1. Delete `link-report.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Reverse `g_a3_applied.diff` (#1-#4; #5-#6 are documentation).
