---
memory_schema: 1
as_of: 2026-11-21
status: BUILT (B195 settled — T91's two changed files are its slot 9 and slot 9's picture in the states root, the hub's own hold scratch, written at 19:08:22Z during the solo's real match; neither is the user's, and none of T91's slots 0-3 changed; B196 close lists each changed file by root, kind and hashed name before it ends the befores, the hub's slots 8 and 9 and their pictures left out by kind and root; B197 solo needs the real match's go and end read, a practice's switches may be listed, the line after a practice says to wait on the load screen) — no bar lowered; nothing adopted; nothing committed
---

# B195-B197 — which two files; close names what changed; solo's real-match switches

Queue: `handoffs/QUEUE_2026-11-21BK.md`. The directory is `b195_2026-11-21/`:
- `t91_files.txt` (B195) and `scripts/t91_files.py`;
- the design + `design.sha256` (hashed 2026-11-21T19:19:58Z, before any code);
- `tests_runs.txt`, `tests_mutations.txt`, the four checks, `scripts/`;
- `b195.diff` (applies on `e215bae5`), `apply_check.txt`, `template_sha256.txt`, `manifest.sha256`.

Patch: `patches/B195_CLOSE_NAMES_SOLO_SWITCHES.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty; T91's second record
committed (`e215bae5`). No title started; the users' slots, setups, in-game saves, the kept H7 folders and the rules
folder only read (their mtimes and sha256, in process).

## B195 — the two files (`t91_files.txt`)

Every file under `files_digest`'s roots whose mtime falls between 19:04Z and 19:12Z (bench 19:05Z, close 19:11Z, a
minute either side): **two**, both in the `states` root, both T91's, both at **19:08:22Z** — during the solo's real
match:
- `9ff6899534bb58ae` — **the hub's slot 9** (`.state9`);
- `05cbbdb491e6e37b` — **slot 9's picture** (`.state9.png`).

The setups' states, the rules folder, T91's kept folder and both kept H7 folders: none changed. T91's slots 0-3 and
their pictures (8 files): none changed.

**Neither is the user's.** Slot 9 is the hub's hold scratch (B9 / B12, `companion/rewind_cores.py`: `SAVE_STATE_SLOT 9`
at a controller silence while a game plays — "not 0, not 1-3 — the user's"); RetroArch writes its picture beside it.
The onn's SAVE / LOAD offer slots 1-3 only (and SAVE rewrites slot 0). **`files_digest` should leave slot 9 and its
picture out** — as it already left out slot 8, the hub's load copy (B169): nothing of the user's is ever kept there,
nothing but the hub's own release reads it, and every user slot, slot 0, their pictures, every rules file and every
kept state stay compared.

## B196 — close names what changed (built)

- The befores keep, per file, its sha256 with its root and kind (`[sha, root, kind]`; the key still the hashed path).
  A before of older code (sha only) is still compared.
- close's "every file = bench's before" cell is the list — `{root, kind, file: <hashed name>, is: changed | new |
  gone}` — the same in `recorded` and in a line of its page, **written before the befores end**.
- Left out, by kind and root, said on the page: the hub's slots 8 and 9 and their pictures under the states and the
  setups' states. Bench's own "every file after = before" uses the same digest (now a list too).

## B197 — solo's real-match switches (built)

- The go = the last planned switch into the mini game; the end = the first planned switch to the board after it;
  every one before the go is a practice's.
- The cell "the real match's go and end read for S (a practice's may be listed)" lists every switch read or listed by
  role; met only when the go and the end were both read. S stays over every read switch.
- **T91's solo under this rule:** switch 2 (a practice's, to the board) listed — allowed now; but the switch S failed
  was switch 3, **the go** (sound back at 4.05 s against 4.0, a 70-underrun row): S is still not met — the same stop,
  for the sound alone, which the user put down to a large download on the same network.
- solo's line after a practice: "… leave it with <back>, then wait a few seconds on the load screen before pressing ✕
  to play it for real, and play it to its end."
- `BARS["switches_read_min"]` (4) kept, now the planned switches' bar (it had been a literal); `BARS
  ["real_switches_read"]` added. No number lowered; **the count of four read is replaced by the queue's rule**
  (disclosed).

## Tests and mutations

- `tests/b195_close_solo/` (new, 6); the suites touched: `tests_runs.txt`.
- **Disclosed:** `tests/b162_solo_safe/test_b162.py` changed in five places: the Xbox line's "press A" now "pressing
  A" (the queue's words, "before pressing ✕"); the switch cell's new name and read (by
  role), the listed switch's page words (its role), its "three read, not met" case now met (a practice listed, the go
  and the end read), and the harness close's count now the list (its one changed file, a rules file).
- Mutations 3 of 3 caught (`tests_mutations.txt`): the befores ended before the comparison; a user's slot left out;
  met with the go unread.

## T91 now

The befores were ended by the second run's close. The next `solo` writes new ones (B169), so close compares again;
register, label, learn and bench stay passed for the same inputs (no code here changes their inputs). **solo, its
read, then close** — nothing else is required by the tool.
