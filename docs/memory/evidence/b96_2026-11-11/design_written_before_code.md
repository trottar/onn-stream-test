# B96 — "decided" by held-out states and families (design, written before code; queue AJ, 2026-11-11)

Baseline: HEAD at the start (`baseline_head.txt`). Changes `tools/h7_rule_search.py` and `tests/h7_rule_search/` only;
the companion unchanged. B97 (hints, template b2) builds on this and has its own design.

## Why

H7-P1: on three real states the search found 8,520 / 3,084 / 163,475 candidates; B94's "decided only when a template
leaves exactly one" cannot be met on a real game. "Decided" becomes: a rule that names the winner in states it never
saw (held-out folds), counted once per place in memory (families), with the evidence level said in words and as data.

## Families (per template)

B94's candidate search and its merge (the same changing bytes = one candidate, `count` as before) are kept. On top,
candidates of one template are **linked** when they are the same place read another way:

1. **an overlapping read** — the same stride, and P1's fields overlap in memory (bases at most 1 byte apart: a 1- and
   a 2-byte read at one address, a 2-byte read one byte early);
2. **a copy** — the same stride and width, **identical values for every player in every labelled state**, and bases
   at most `WINDOW = 0x100` (256) bytes apart.

A family is a connected set of links (pairwise links; a chain of copies each within the window is one family — stated).
Implemented by hashing (no all-pairs): rule 1 by a dict on (stride, base); rule 2 by grouping on (stride, width,
values) and linking neighbours sorted by base whose gap ≤ WINDOW (the same components as all pairs within the window).
The family is reported once: its **rule = its lowest aligned member** (base % width == 0; at one base the wider read,
as B94 kept; when no member is aligned, the lowest), its member count, and up to 5 member reads (`width@address`).
Template (c) the same with stride 0 (a single field). Tested: a copy at +WINDOW joins, a copy at +WINDOW+1 with
nothing between does not; a 1-byte read inside a 2-byte read joins.

**Family order** (within a template): a hinted family first (B97; until then nobody is hinted), then every player's
field changing in some state (any member), aligned, stride a multiple of 4, smaller stride, lower address (the rule's).

## Held-out folds (per template)

With the labelled states, for every "end" state e in turn (state order):
- if no other "end" in the set is won by e's winner → **the fold is skipped**, counted, and said: "no other 'end'
  won by Pk";
- else the template is searched on all states but e (B94's search + families: the *training* families); the held-out
  state is read with each training family's rule (B93's reading: `winner: max`, the field strictly the largest names
  that player, otherwise nobody; (c): the value that the training states gave to a winner names that winner).
  Reported per fold: training families, how many named the held-out winner, how many did not (the first few rules).

A family found on **all** states **passes** when, in every fold that ran, one of its members is in a training family
and its rule names the held-out winner. (Every template is a conjunction of per-state conditions, so a family found on
all states is found in every training set; the folds' power is against families that fit the training states and miss
the held-out one — the decoys; stated in the record.) With every fold skipped, "passes" holds vacuously and the level
is at most "weak".

## The evidence level (per template, in words and as data)

- `"strong"`: every winner seen has at least two "end" states (so no fold is skipped), at least one fold ran, at least
  one family passes; **the top passing family by the order above is the template's answer**;
- `"weak"`: at least one family passes but a winner was seen only once (its folds skipped and counted);
- `"none"`: no family passes (or the template is not testable).
With "weak" (and "none" when states are missing) the tool names the states that would make it strong:
`would_make_strong` = "one more 'end' won by P1 and one more won by P2" (each seen winner with fewer than two ends).
**"decided" = "strong" only.** Across templates the answer is the first strong template in the order: a template whose
answer is hinted first, then a, b, c (then B97's b2 and hinted pairs); the other strong templates are `also_fits`.

Output (replacing B94's `decided` meaning; keys kept where they mean the same): per template `count` (B94's merged
candidates, unchanged), `families_found`, `families` (top 10), `passing_count`, `passing` (top 10), `folds` (one row per
"end" held out), `evidence` {`level`, `words`, `ends_per_winner`, `folds_run`, `folds_skipped`, `would_make_strong`};
top level `evidence`, `decided`, and when decided `rule` / `template` / `also_fits`; when not, `not_decided`
{`passing` per template, `evidence` per template, `would_make_strong`, `would_split` (the same text, B94's key)}.

## Template (c) tightened (B94's own note)

At every "end" the field's value must be the winner as a **player number or flag**: one scheme for all seen winners —
index from 0 (P1 0, P2 1 …), number from 1 (P1 1, P2 2 …) or bit flag (P1 1, P2 2, P3 4, P4 8); the "begin" value
none of the scheme's values for any player. The rule then carries a value for **every** player (from the scheme) and
`none_value` = the begin value. The before / after counts on the fixture are taken with a module knob
`C_PLAYER_VALUES` (True = tightened; False = B94's (c), for the count only).

## Fixtures (`tests/h7_rule_search/`)

The PS-X EXE and the SNES ROM unchanged; the planted states extended (2 players):
`begin`; `P1` (rounds 2 / 1, level 37 / 0); `P2` (1 / 2, 0 / 55); **`P1b`** (rounds 2 / 0, level 80 / 0 — the
winner's level not full, another tally); **`P2b`** (rounds 0 / 2, level 25 / 90 — the loser above 0, a contest stopped
by the clock; template (b) then fails on it, B97's (b2) holds); **`begin2`** (a second "begin", other noise) — five
and six states. Noise per state as B94 (PS1: random bytes written per state in one paused session; SNES: the program's
own counter and buffer, states at different moments). Added plants: **a mirrored copy of the planted block** at
+0x100 (PS1; SNES +0x80) — the same values; **decoys that fit three states but fail a fourth**: a counter pair and a
level pair that fit begin + P1 + P2 and fail P1b (the counter one at a smaller stride, 0x20, so it would rank above the
planted pair by the order), and a single field 255 / 0 / 1 that reads P2 at P1b; **a per-player score pair** (values
above 31, the high bytes equal at every end — no template fits it; for B97's direct hint test); B94's two decoys kept.
4 players: begin, P3, P1, **P3b**, **P1b**, P4 (six states).

Tests (B94's kept, rewritten where "decided" changed meaning; new ones):
- begin + P1 + P2 → (a) `"weak"`, the planted family among those passing, both folds skipped and counted,
  `would_make_strong` names one more end per winner; `decided` false; the planted rule among the candidates (B94's
  three-state result unchanged in content);
- + P1b + P2b → (a) `"strong"`, the planted family the answer and `decided`; the mirror a member of the planted family
  (counted once); the decoys absent from the families and present among a fold's "did not name" rows;
- a fold with no other example of its winner is skipped and counted (P1 + P1b + P2: P2's fold skipped → "weak");
- (c) counts before / after tightening (printed for the record); the (c) decoy fails a fold;
- 4 players: begin + P3 + P1 → weak; + P3b + P1b → strong, the planted family the answer; + P4 → weak again
  (`would_make_strong` names P4); SNES five states → strong, the planted family;
- no emulator: the window (a copy at +0x100 joins, at +0x101 not); overlapping reads join; the order; unstable bytes
  dropped (B94's); the time of the folds on a random 2 MiB, 5 states (printed).

Tests clean their temp dirs; RetroArch headless (B61's form, disclosed), counted 0 after. Mutations run as B94's.
