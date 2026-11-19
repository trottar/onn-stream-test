# B163 — learn rehearsed on a title already added (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-19BC.md` §B163. Baseline `58497ab8`. **No companion change.** A sixth command in
`tools/party_add_game.py`: **`rehearse <code>`**, for a title already in the rules folder (registered with
`--rules-players`, its `learn` PASS — refused otherwise).

## The kept states as the tool's roles

The kept folder is `~/privyhub_h7/<code in lower case>/` (`PRIVYHUB_ADD_GAME_KEPT_ROOT`), read only. By name:
`begin.state` → **begin**; `other*.state` / `mid*.state` → **other**; `end_p<k>.state` → **end_P<k>**;
`end_p<k>_<x>.state` → another ending of end_P<k> (kept, read as an ending, not a learning role: the tool's roles take
one each); `results_<n>.state` (a `places` title) → an ending whose row is the one the real rules read from it (said
so). The page says which kept file is which role and **what is missing** (T88: no `other`; T89: no `other`, one row of
the four `register` needs). Copied to a scratch kept folder.

## Learn's whole real path, into a scratch rules folder

A scratch tree under the title's add_game folder (`rehearse_*`, removed at the end, also on a failure): its own
`home/<code>/kept/<role>.state` (the copies), a binding as `register` would write it for a new title (the game, its
system, players, result, setup; the game file from the hub's `details` for its id, in memory) with register's PASS for
those kept states, its own evidence folder, and **`PRIVYHUB_H7_RULES` pointed at an empty scratch rules folder** for
the call. Then **`learn` itself** — the capture (`party_add_game_capture`, the real picture source: the title started
headless on the hub, B95's Session), the labels, the learner, the held-out score, the replays, and on PASS the spec,
begin and sidecar written **into the scratch rules folder**. The environment is put back however it ends.

## Cells

- **learn's own bars:** every cell of the scratch `learn` verdict, named `learn: <its cell>`.
- **The scratch rules reading each of the title's kept endings as the real rules do:** every kept ending (each role's
  and the extra ones) captured the same way, its pictures replayed through the scratch spec and through the **real**
  spec (read only, `h7_endscreen.load_spec`), as learn's replays do (Reader + Ended, the begin loaded first): cell
  `<kept ending>: the scratch rules read it as the real rules` — read [scratch, real] (class and places), met when
  both ended, the same, and the role's own class (a `results_<n>` ending: the same places).
- **The real rules folder's every file sha256 before = after** — read [files before, after, changed], met when the
  same names and 0 changed.
- **The scratch removed** — met when the scratch tree is gone.

`rehearse` writes `rehearse.json` / `rehearse.md` in the title's evidence folder (the guard: no title, id or path);
the kept file names are role words only. Exit 0 only on PASS.

## What it proves, and what stays unproved here

It starts the title headless on the hub, so **it is A's to run.** My tests replace the picture source with made-up
pictures (`PARTY_ADD_GAME_CAPTURE`) and the title with a made-up one: the roles, the scratch tree, learn's call into
it, the comparisons, the real folder's sha256 and the cleanup are proven; **the real capture (RetroArch headless, the
game file, the screenshots' timing) and whether learn's bars hold on real pictures stay unproved until A runs it.**

## Tests (`tests/b163_rehearse/`)

A made-up title already in a made-up rules folder (its spec learnt from made-up pictures), a made-up kept folder
(begin, end_p1, end_p2, end_p1_b): register → learn → rehearse PASS; the roles and `other` missing on the page; the
real folder's every sha256 before = after; the scratch gone; nothing named. A kept extra ending that shows the other
player's screen → its cell not met. A learn bar raised past the made-up spec → rehearse FAIL with `learn: …` named.
Refused before learn. The mutations: learn run into the real rules folder, the ending cell always met, the scratch
kept.
