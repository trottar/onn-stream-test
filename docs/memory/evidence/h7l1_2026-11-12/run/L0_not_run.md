# L0 — not run (the onn offered no Continue)

**The user's line (00:12Z, verbatim):** "None of that happened it just reset"

**What the hub shows:** `POST /plugins/games/launch?…&players_joined=2` at 00:11:07Z — a plain start (no Continue, no
load); the game log has no "Loading state" line; the watcher's first reads (00:11:08Z on, `paused` true then false):
**0 / 0, "no winner yet"** — the game's start, not the saved fight (110 / 140 would have been the save). One answer
"the game is busy (a save or a load); not read" at 00:11:07Z, during the launch. The session ended by the client at
00:11:49Z (`session_end_bye`), stopped 00:11:55Z.

**Why (A's stage-1 error):** the onn's Continue is the hub's `continue_available`, which is true only while one of the
game's slots 1-3 in the hub's slot index has its file. H7-P3 erased T88's slots 1-3 (the user's request), so **Continue
is no longer offered for T88**. Stage 1 checked RetroArch's own redirected state file (`<the game>.state`, equal to the
kept `end_p2_b` copy) — that file is not what Continue loads. The check should have read `continue_available` from the
hub's game details. **→ L0 recorded "not run"** (the handoff's addition 1: "if … the onn offers no Continue, the user
starts a 2-player fight the usual way and this cell is recorded 'not run'"). The pre-registration is unchanged (its
hash stands); the other cells are as registered.
details: continue_available False
status now: active False
