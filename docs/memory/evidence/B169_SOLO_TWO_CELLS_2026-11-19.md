---
memory_schema: 1
as_of: 2026-11-19
status: BUILT (session B, queue BD) — two cells for the add-a-game tool's solo: "the board showed one card" (the board's own `cards <n>, chose …` line, bar 1), and a title already added gets its files' before written at solo's first run, so close compares the users' files after every solo (in-game saves recorded as before). No companion change. Nothing adopted; nothing committed
---

# B169 — two cells for solo

Queue: `handoffs/QUEUE_2026-11-19BD.md` §B169. The directory is `b169_2026-11-19/`: the design + `.sha256` (hashed
23:22:29Z, before any code), the checks, `manifest.sha256`. The code is in `b167_2026-11-19/b167_b169.diff` (one tool
file holds both). Patch: `patches/B169_SOLO_TWO_CELLS.md`.

- **The card count:** `solo --read` takes the first `cards <n>, chose …` line of the board's own log after solo's mark
  — cell **"the board showed one card"**, read `n`, bar 1. The one-title setting (B162) is then proved by the board's
  line; the first use read it by hand beside the title cell (`cards 1, chose 0`).
- **The files' before at solo:** solo's first run (the one that writes its mark) writes `files_before.json` as bench
  does (the users' slots and slot pictures, both indexes, every rules file, the kept folders) — for a title already in
  the rules folder always (it has no bench), for a new title only when bench left none. close's cell keeps its name
  ("every file = bench's before"); the in-game saves are left out of it and recorded, as B162 made them.
- **Switch:** none needed (the tool; no companion change).

**Tests (`tests/b169_solo_cells/`, 5; B157's solo fixture and B162's close fixture reused):** `cards 1` → met; `cards 2`
→ not met, read 2, solo FAIL; no card line → not met, read null; a title already added: solo writes the before, an
in-game save changed → close PASS with it recorded "changed", the user's slot saved over → close FAIL "every file =
bench's before"; a new title's bench before not overwritten. **5 OK ×3** (`b167_2026-11-19/tests_x3.txt`); B157's and
B162's suites green; **mutations 2 / 2 caught** (the card cell always met; no before at solo).

**B162's harness test changed (disclosed):** with the before now written at T90's solo, its close compared the files —
and that test itself rewrites one made-up sidecar in its rules folder (to list three two-player titles) after T90's solo:
close FAIL "every file = bench's before", 1 changed (the file listed by a one-off scratch run of the harness, made-up
names). B169 working as built; the test now expects exactly that cell (`tests_after_fix.txt`: 17 OK ×2). Before B169,
close compared nothing for a title already added.
