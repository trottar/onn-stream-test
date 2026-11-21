# SESSION B — done, 2026-11-21 BJ (QUEUE_2026-11-21BJ: B190 why learn could not use T91; B191 the `letters` kind; B192 synthetic training, never synthetic proof; B193 the task; B194 T91 from its six kept saves; run ~16:05Z-18:45Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; T91's record committed (`13646e06`).

**The exception for B190 / B194: not used.** The picture source never ran. T91's pictures in the tool's folder were
made from exactly its six kept states, so they (read only) and a scratch copy of that folder served. Register's library
lookup asked the companion for the title's entry (a read).

**Rules kept:**
- No stream, no restart, no flag set, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the
  drive.
- Read only: the real T91 folder, the rules folder, the user's slots and in-game saves, the kept H7 folders, the
  runtime pictures.
- No bar in `BARS` lowered (one added: the training's own); `winner` / `places` / `score` and T88's / T89's / T90's
  rules unchanged. The app and the board's repo not touched; the template unchanged.
- No title, id, path or picture in any record (the four checks); the pictures I made to look at, off the repo, removed.

Mine: `tools/h7_endscreen.py`, `tools/party_add_game.py`, `companion/party_minigame.py`, `tests/b191_letters/`,
`docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md`, `handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt`, this file, the
B191 record + dir, the B191 patch, `logs/b191_git_status.txt`. Nothing adopted; nothing committed in either repo.

## B190 — settled

- **Where T91's letters sit:** each player's letters under its header in its top corner (P1 left, P2 right), the same
  place every match, centred; a letter about 28 × 22 px, a not-yet mark 8 × 6; P1 blue, P2 pink.
- **How the background differs:** each end screen is shot from wherever the match ended — two corners of different
  matches share 2-8 % of their pixels; two matches that ended at the same spot share a plain sky.
- **Every picture holds still:** the begin is one picture for 19.5 s from its first; each end save from 0.5-1 s.
- **Why the begin was never recognised:** `winner`'s screen gate could not be learnt at all. The mid-match save is the
  begin's own picture with other middle text, 0.093 from the screen reference, while the end screens themselves were up
  to 0.221 — so there was no threshold and every read was "not this screen", the begin included.
- **The user's begin serves.** Learnt as its own still picture it stands 0.27 from everything else, and the same with
  the "Paused." corner blacked out, as the hub's held start reads it. Nothing to ask the user.

## B191 — BUILT

`register --result letters --word <the word>` (two players), then label, learn, rehearse, bench, solo and close as for
`winner`. The label stage reads each player's corner (`end_P1=---/WOW,---/WOW`). The player whose letters spell the
word lost; neither or both spelled, or a corner not read, is no result.

- **Four players:** refused, and the line says why. The one who spelled the word lost, but which of the other three
  won is not on that screen. Winner-only would name a winner the game never showed. The hub could honestly report only
  "port k lost", and the board has no such result.
- **At the hub:** a winner entry. The reader sits in the tools folder, so the running companion loads it only at its
  next start (A's bench restarts it).

## B192 — BUILT

The letters' own pixels from each real end save are pasted over patches of the title's other pictures. These patches
are moved, scaled and drawn with a fixed seed. Held-out pictures are made first, then training rounds run until every
held-out one is read.

- **T91:** 32 held out and 64 trained, from 6 pictures; one round; 2.4 s.
- **Only the real saves prove:** every gate reads the real saves; a synthetic picture can fail learn, never pass it.
- **What synthetic training cannot fix:**
  - a letter no save shows;
  - a background in a player's own letter colours;
  - a corner no save shows clean.

## B193 — DONE

`ADD_GAME_TASK.md` §1 gains:
- the letters kind;
- the user's own start as the begin;
- the label lines, word for word.

The template is unchanged (`aadccb04…`).

## B194 — T91 (scratch, no new save)

| stage | verdict |
| --- | --- |
| register `--result letters --word WOW` (no `--collect`) | **PASS** (10 cells) |
| label, my four readings | FAIL on the last look only (19 cells): every reading checked, each read back by a reader learnt without it |
| the last look | `look=all` — `-` 10, `O` 4, `W` 10, every tile its letter |
| label | **PASS** (19 cells) |
| learn | **PASS** (20 cells) |

My readings, the same from both pictures of each save:
- end_P1, end_P1_2: `---/WOW`;
- end_P2, end_P2_2: `WOW/W--`.

In learn:
- each end save ended as itself in 1.5-2.0 s;
- each left-out save the same, its letters exactly;
- a moving screen never ended.

**learn passes: stopped there.** Bench and solo are session A's with you.

**Tests:**
- B191's 14, three runs, OK. B185, B181, B178, B175, B171, B163, B157, B162, B167, B169, B158, B102, B122, B103 and
  B124 once each: OK. Temp dirs left: 0.
- Mutations 4 of 4 caught: a synthetic picture counted as proof; a background read as a letter; a guess when neither
  spelled; a moving screen taken.
- Disclosed:
  - the "guess" mutation's first form went dead after a reorder and was not caught; I rewrote it, and it is caught;
  - the design changed after its hash in six places (the addendum), each found by a test or a T91 left-out run;
  - the made-up title's noise seeds are pinned per test.

## What I would change (not done — the queue is the task)

1. **The companion must restart before the hub can read a letters title** (the reader is new code in `tools/`).
   Session A's bench restarts it; if A's bench comes later than solo for any reason, the listing would show T91 while
   the running reader refuses its spec — worth a precondition line in A's task ("restarted since BJ").
2. **The label stage's last look is kept per readings, not per sheet.** If the code changes the sheet, an old
   `look=all` still stands. Keying the look to the sheet's own digest would make the session look again.
3. **The made-up title's noise depends on the test order** (as B178's): pinned here per test; at one counter a second
   left-out save of the odd-colour title also fails. Its seeds could be drawn per picture instead.

## Files

- **Code:** `tools/h7_endscreen.py`, `tools/party_add_game.py`, `companion/party_minigame.py`.
- **Tests:** `tests/b191_letters/` (new).
- **Handoffs:** `ADD_GAME_TASK.md`, `SESSION_B_STATUS.txt` (one line), this file.
- **Record:** `evidence/B191_LETTERS_KIND_SYNTHETIC_2026-11-21.md` + `b191_2026-11-21/`:
  - the design and its addendum, hashed; `t91_settle.txt`; `t91/`; `flag_proof.txt`;
  - tests, mutations, the four checks, `scripts/`;
  - `b191.diff`, `apply_check.txt`, `template_sha256.txt`, `manifest.sha256`.
- **Patch:** `patches/B191_LETTERS_KIND_SYNTHETIC.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph).
- **Logs:** `logs/b191_git_status.txt`.

## T91 now

**It passes learn on its six kept saves — no new match.** That pass was in a scratch: the real T91 folder still holds
the first run's `winner` binding. So session A runs:
- register `--result letters --word WOW` (no `--collect`);
- label with the four readings above, then the last look;
- learn — then bench (it restarts the companion, which loads the new reader) and solo with you.

**The one line you type in session A:**

```
Read docs/memory/handoffs/ADD_GAME_PROMPT_TEMPLATE.txt, put T91 where it says ____, and follow it as my prompt.
```

At the questions, answer "who won is shown how" with: a word spelled by the player who lost, WOW, in each player's
corner.
