# B169 — two cells for solo (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-19BD.md` §B169. Baseline `df81c762`. **No companion change** (`tools/party_add_game.py`).

## The card count

`solo --read` already reads the board's own log lines after solo's mark (`PrivyParty: hub mini game: …`). New cell
**"the board showed one card"**: the first `cards <n>, chose …` line after the mark, read `n`, bar 1, met when `n` is 1
(none found → read null, not met). The one-title setting (B162) is then proved by the board's own line, not only by the
user's word. It sits beside "the mini game played was this title".

## A title already added gets its files' before

Today only `bench` writes `files_before.json` (and a title already in the rules folder has no bench), so `close` compared
none of the users' files after T88's solo. Now **solo's first run** (the run that writes solo's mark) **writes the same
before bench writes** (`files_digest`: the users' slots and slot pictures, both indexes, every rules file, the kept
folders) — for a title already added always; for a new title only when bench left none (bench's own before is kept).
`close` then compares every file after every solo, the title's in-game saves left out and recorded as now (B162).

## Tests

Made-up logs: the card line `cards 1` → met; `cards 2` → not met, named; no card line → not met. A title already added:
solo's lines write `files_before.json`; a user's slot changed after → close FAIL "every file = bench's before"; an
in-game save changed → close PASS, recorded. A new title's bench before not overwritten by solo. The mutations: the card
cell always met; solo writing no before — each caught. B157's and B162's suites green (B157's solo fixture's board log
has `cards 1`).
