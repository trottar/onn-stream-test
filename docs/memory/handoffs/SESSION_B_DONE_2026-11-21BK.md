# SESSION B — done, 2026-11-21 BK (QUEUE_2026-11-21BK: B195 which two files; B196 close names what changed; B197 solo's real-match switches; run ~19:12Z-19:50Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; T91's second record committed (`e215bae5`).

**Rules kept:**
- No title started; no stream, no restart, no flag, no adb, no sudo, no nft; nothing fetched or installed; nothing
  written to the drive; nothing deleted.
- Read only (mtimes and sha256, in process): the users' slots, setups and in-game saves, the kept H7 folders, the rules
  folder.
- No bar in `BARS` lowered (one added); the app, the companion and the board's repo not touched; the template unchanged.
- No title, id, path or picture in any record (the four checks).

Mine: `tools/party_add_game.py`, `tests/b195_close_solo/`, `tests/b162_solo_safe/test_b162.py`, `docs/KNOWN_ISSUES.md`,
`handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt`, this file, the B195 record + dir, the B195 patch,
`logs/b195_git_status.txt`. Nothing adopted; nothing committed in either repo.

## B195 — the two files (settled)

Between bench (19:05Z) and close (19:11Z), two files changed under `files_digest`'s roots, both at **19:08:22Z**,
during the real match, both T91's:
- **the hub's slot 9** in the states root;
- **slot 9's picture** in the states root.

**Neither is yours.** Slot 9 is the hub's own hold scratch: it saves the running game there when the pads go quiet,
and it is never one of your slots (the onn offers slots 1-3). None of T91's slots 0-3 or their pictures changed, and
nothing changed in the setups, the rules folder or the kept folders.

`files_digest` should leave slot 9 and its picture out, as it already left out slot 8 (the hub's load copy). Nothing
of yours is ever kept there; every user slot, slot 0, their pictures, every rules file and every kept state stay
compared.

## B196 — BUILT

- **close's file cell is the list of changed files**, each by root, kind and hashed name and whether it is changed,
  new or gone. The list is in the page and in `recorded` too.
- **It is written before the befores are ended.**
- **Left out, said on the page:** the hub's slots 8 and 9 and their pictures (by kind and root).
- **Mutations caught:** the befores ended first; a user's slot left out.

## B197 — BUILT

- **The rule:** the real match's go and end must be read; a practice's switches may be listed. Not met only when a
  real-match switch is unreadable or a read switch fails S.
- **solo's line after a practice:** "then wait a few seconds on the load screen before pressing ✕ to play it for real".
- **Mutation caught:** met with the go unread.
- **T91's last solo under the rule:**
  - the listed switch was a practice's, so that is no longer a fault;
  - the S that failed was at the go (sound back at 4.05 s against 4.0), so the same solo would still stop, on the
    sound alone.

**Tests:**
- B195's 6, three runs, OK.
- B162, B169, B171 (B172's), B157, B163, B158, B175 and B191 once each: OK. Temp dirs left: 0.
- Mutations 3 of 3 caught.
- **Disclosed:** B162's test changed in five places — the switch cell's name and read, the listed note's words, its
  "three read" case now met, the harness close's count now a list, and the Xbox line's "pressing A".

## What I would change (not done — the queue is the task)

1. **The S at the go is the one open item for T91.** The sound came back 0.05 s late at the switch into the match,
   with an underrun row after it, during a large download on the same network. If it fails again on a quiet network,
   the heartbeat rows around that switch are the place to look (B150's S). If it doesn't, the bar stands as it is.
2. **Bench's file cell** now uses the same list. A bench whose own matches leave a pad quiet long enough would have
   tripped on slot 9 too; it is now left out there as well (the same digest).
3. **A failed close cannot be repeated on its own:** it ends the befores. The task now says a failed close is run again
   only after another solo. Keeping the befores when close fails would let the session rerun close alone — a small
   change, if you want it.

## Files

- **Code:** `tools/party_add_game.py`.
- **Tests:** `tests/b195_close_solo/` (new); `tests/b162_solo_safe/test_b162.py` (disclosed).
- **Handoffs:** `ADD_GAME_TASK.md` (solo's and close's bullets), `SESSION_B_STATUS.txt` (one line), this file.
- **Record:** `evidence/B195_CLOSE_NAMES_SOLO_SWITCHES_2026-11-21.md` + `b195_2026-11-21/`:
  - `t91_files.txt`, the design (hashed 19:19:58Z);
  - tests, mutations, the four checks, `scripts/`;
  - `b195.diff`, `apply_check.txt`, `template_sha256.txt`, `manifest.sha256`.
- **Patch:** `patches/B195_CLOSE_NAMES_SOLO_SWITCHES.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted).
- **Logs:** `logs/b195_git_status.txt`.

## T91 now

**Only solo (its lines, then its read with the winner you name) and close again.** The tool requires nothing else:
- register, label, learn and bench stay passed for the same inputs (nothing here changes them);
- the second run's close ended the befores, so the new solo writes its own and close compares against them.

**The one line you type in session A:**

```
Read docs/memory/handoffs/ADD_GAME_TASK.md and, for T91 (letters, WOW), run only solo — its lines, then its read with the winner I name — and close, as §2 says; register, label, learn and bench passed in its second run.
```

At the TV: after the practice, wait a few seconds on the load screen before pressing ✕. If you can, play while nothing
big is downloading on the network.
