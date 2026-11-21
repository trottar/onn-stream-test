# B196 / B197 — design, written before code (queue BK)

Predecessors (HEAD `e215bae5`): `tools/party_add_game.py` 5f4957da…, `handoffs/ADD_GAME_TASK.md` e9769358…, the
template aadccb04… (unchanged). Settled first: B195 (`t91_files.txt`) — the two files are T91's **slot 9** and **slot
9's picture** in the states root, both written at 19:08:22Z (during the solo's real match), the hub's own hold scratch
(`companion/rewind_cores.py`: `SAVE_STATE_SLOT 9` at a controller silence; "not 0, not 1-3 — the user's"). Neither is
the user's.

## B196 — close names what changed before it ends anything

- **What the befores keep:** `files_digest` keeps, per file, its sha256 **and its root and kind** (never a name; the
  key stays the 16-hex hash of its path). Roots: `states`, `setups' states` (cheat profiles), `rules`, `this title's
  kept folder`, `a kept H7 folder`. Kinds, from the file's own suffix only: a user's slot n (1-3) / slot n's picture;
  slot 0 (every SAVE rewrites it) / its picture; the hub's slot 9 / its picture; another slot; an in-game save; a rules
  file; a kept state; another file. A before written by older code (sha only) is still compared; its gone files' kind
  then reads "not known".
- **Left out, by kind and root, stated on the page:** the hub's slot 9 and slot 9's picture, under `states` and
  `setups' states` — and B169's `.state8`, which was left out silently (now stated). **Why that hides no real change:**
  the onn's SAVE / LOAD offer slots 1-3 only (and SAVE rewrites slot 0, which stays compared); RetroArch writes slot 9
  only on the hub's own `SAVE_STATE_SLOT 9` (the hold scratch, while a game plays) and slot 8 only by the hub's load
  copy; nothing of the user's is kept in either. A user's slot, slot 0, every picture of those, every rules file and
  every kept state stay compared. Applied in `files_digest`, so bench's "every file after = before" leaves out the same.
- **close:** compares, then writes the cell **"every file = bench's before"** with the list of changed files —
  `{"root", "kind", "file": <hashed name>, "is": changed | new | gone}` — and its page lists them in a line; **only
  then** ends the befores (B172). The list is also kept in the verdict's `recorded`. (Before: a count.)
- **Tests:** a user's slot changed → close FAIL naming its kind and root, the before still read (the list in the page),
  then the befores ended; the hub's slot 9 and its picture changed → close PASS, the page saying they were left out;
  no name in anything written. **Mutations caught:** the befores ended before the comparison; a user's slot left out
  (the leave-out widened to every slot).

## B197 — solo's count of readable switches

- **The real match's switches:** the go = the last planned switch into the mini game; the end = the first planned
  switch to the board after it. Every planned switch before the go is a practice's.
- **The cell** "the real match's go and end read for S (a practice's may be listed)": read — which switches were read
  and which listed, by role; met only when both the go and the end were read (not listed). The S cell stays as it is:
  every read switch must meet S. So not met only when a real-match switch is unreadable or a read switch fails S.
  `BARS["switches_read_min"]` (4) is kept, now the planned switches' bar (it was a literal ">= 4" there); a new
  `BARS["real_switches_read"]` (the go and the end). No number lowered; the count of read switches is replaced by the
  queue's rule (disclosed).
- **solo's line after a practice** gains: "then wait a few seconds on the load screen before pressing <play>" (✕ on a
  PlayStation pad).
- **Tests:** a practice listed, the go and end read → met; the go listed (the end came sooner than 4 s after it) → not
  met; the end's S failing → not met; B162's "three read" test now met (disclosed). **Mutation caught:** met with the
  go unread.
- `ADD_GAME_TASK.md`: solo's bullet as above. The template unchanged.
