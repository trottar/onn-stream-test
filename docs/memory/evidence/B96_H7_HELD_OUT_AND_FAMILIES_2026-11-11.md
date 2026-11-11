---
memory_schema: 1
as_of: 2026-11-11
status: BUILT (session B, queue AJ) — tools/h7_rule_search.py: "decided" now means STRONG evidence — a rule found on some labelled states names the winner in every "end" state it never saw (held-out folds), counted once per place in memory (families), with the evidence level in words and as data ("strong" / "weak" / "none") and the states that would make it strong. Template (c) tightened (player number or flag values). On the fixtures: begin + P1 + P2 → "weak", the planted family passing; two ends per winner → "strong", the planted family the answer, its mirror in the same family, the decoys failing a fold. Synthetic fixtures only; the user's states not touched; no real title started. Nothing committed. No title, serial, code name, character name or path in this record
---

# B96 — "decided" by held-out states and families (2026-11-11)

**Why:** H7-P1 searched T88's three real states (begin, end P1, end P2): **8,520 / 3,084 / 163,475 candidates — not
decided**. B94's "decided only when a template leaves exactly one" was the queue's rule and cannot be met on a real game;
one more state will not take 8,520 to 1. **Baseline:** HEAD `2e30c1cf` (H7-P1 committed in `132e6f2f`). **Design**
hashed before code at 16:47:18Z (`b96_2026-11-11/design.sha256`); **addendum 1** (one winner is never "strong") hashed
at 16:50:41Z before its code.

## Built — `tools/h7_rule_search.py`

- **Families.** B94's candidates (and its merge: `count` unchanged) are linked when they are one place read another
  way: **(1) an overlapping read** — the same stride, P1's fields overlapping (bases ≤ 1 byte apart: a 1- and a 2-byte
  read, a 2-byte read one byte early, now also when both bytes change); **(2) a copy** — the same stride and width,
  identical values for every player in every labelled state, bases **≤ `WINDOW` = 0x100 (256) bytes apart** (single
  linkage: a chain of copies each within the window is one family — stated). Hashed, no all-pairs (a dict on
  stride + base; neighbours in a value group). A family is reported once: its **rule = its lowest aligned member**
  (at one base the wider read), its member count, up to 5 member reads.
- **Held-out folds.** For every "end" state in turn: if no other "end" is won by its winner, the fold is **skipped and
  counted** ("no other 'end' won by P2"); else the template runs on the other states and the held-out state is read with
  each training family's rule (the field strictly the largest; (c) the value given to a winner). A family found on all
  states **passes** when it names the held-out winner in every fold that ran. Per fold: training families, how many
  named the winner, how many did not (the first rules).
- **Evidence, per template, in words and as data** (`evidence`: `level`, `words`, `ends_per_winner`, `folds_run`,
  `folds_skipped`, `would_make_strong`): **"strong"** = every winner seen has two "end" states, **at least two
  different winners** (addendum 1), a fold ran, a family passes — the top passing family is the answer; **"weak"** =
  families pass but a winner was seen once (or only one winner); **"none"**. **`decided` = "strong" only.** Order:
  hinted first (B97), every player's field changing, aligned, stride a multiple of 4, smaller stride, lower address.
  Across templates: a hinted top family first, then a, b, c. `would_make_strong` / `would_split`: e.g. "one more
  'end' won by P1 and one more 'end' won by P2".
- **Template (c) tightened** (B94's own note): the end values one scheme for every seen winner — index from 0, number
  from 1, or bit flag — the "begin" value none of the scheme's values; the rule then has a value for every player.
- Output keys: per template `count`, `families_found`, `families`, `passing_count`, `passing`, `folds`, `evidence`;
  top level `evidence`, `decided`, and `rule` / `template` / `also_fits` or `not_decided`.

## Fixtures and tests (`tests/h7_rule_search/`)

The PS-X EXE and SNES ROM unchanged; the planted states extended to **five and six**: begin; P1 (rounds 2 / 1, level
37 / 0); P2 (1 / 2, 0 / 55); **P1b** (2 / 0, 80 / 0 — the winner's level not full, another tally); **P2b** (0 / 2,
25 / 90 — the loser above 0); **begin2** (other noise). Plants: **a mirror of the planted block** (+0x100 PS1, +0x80
SNES); **decoys that fit begin + P1 + P2 and fail P1b** (a counter pair at the smaller stride, 0x20 PS1 / 0x10 SNES, so
it ranks first by the order; a level pair; a single byte 255 / 0 / 1); **a per-player score pair** no template fits
(B97's direct test); B94's two decoys kept. 4 players: begin, P3, P1, **P3b**, **P1b**, P4. Noise per state as B94.

| test (fixture) | result |
| --- | --- |
| PS1, begin + P1 + P2 | `decided` false, evidence **"weak"**, (a) folds 0 run / 2 skipped, `would_make_strong` "one more 'end' won by P1 and one more 'end' won by P2"; the planted family among those passing ((a) and (b)); by the order alone the smaller-stride decoy ranks first; B94's content kept (the planted rule among the candidates) |
| PS1, + P1b + P2b | **"strong"**, `decided`, template a, **the planted pair the rule**; 4 folds run, 0 skipped; the mirror a member of the planted family (counted once, no family of its own); the three-state decoys absent from the families and listed in the P1b fold's "did not name" rows ((a) and (b)) |
| PS1, six states (+ begin2) | strong, the planted rule |
| PS1, begin + P1 + P1b + P2 | P2's fold skipped and counted (2 run / 1 skipped), "weak", "one more 'end' won by P2" |
| PS1, begin + P1 + P1b (one winner) | never "strong" (addendum 1); `would_make_strong` names an end won by P2 |
| (c) before / after on PS1 begin + P1 + P2 | **1,371 → 1** candidates (the one left: the planted single-field decoy); the (c) decoy fits three states (values P1 0, P2 1, none 255) and fails the P1b fold at five |
| 4 players | begin + P3 + P1 → weak, planted first; + P3b + P1b → strong, planted the answer; + P4 → weak, "one more 'end' won by P4", 1 fold skipped |
| SNES (the program's own noise) | three states weak, planted passing; six states strong, the planted rule, the mirror in its family |
| no emulator | the window (a copy at +0x100 joins, at +0x101 has its own family); a copy with other values its own family; overlapping reads whose both bytes change one family (B94's merge keeps three reads); the order; unstable bytes dropped (B94's); a begin and an end needed |
| time | **the pure search with 4 folds on a random 2 MiB × 5 states: 0.72 s**; PS1 2 MiB, 5 states × 3 loads read **73.7 s**, the search **0.72 s** (CLI) |

**3 runs, 22 / 22 each** (`tests_x3.txt`; each run 374 s); B93 / B95's `tests/h7_minigame_proof` 13 / 13; mutations **9 / 9 caught** (`tests_mutations.txt`: the window, overlapping reads, the lowest aligned rule, fold skipping, the held-out read, strong with a winner seen once, strong with one winner, (c) tightened, the stride in the order).

## What the fixture answers with three states against five

**Three states (begin, one end per winner): "weak"** — the planted family passes but every fold is skipped; the tool
says "one more 'end' won by P1 and one more 'end' won by P2", and by the order alone a decoy that fits those three
states ranks above the planted pair. **Five states: "strong" — the planted pair is the answer**; the decoys fail the
fold that holds out the state they don't fit; the mirror is one family with the planted block.

## Disclosed

- **The folds add nothing against a family that holds in every state** (each template is a conjunction of per-state
  conditions, so such a family is found on every training set and names every held-out winner); their power is against
  families that fit the training states and miss the held-out one — the decoys — and they make "strong" need two ends
  per winner. **"Strong" with many passing families is a ranking pick** (the stated order), not a unique fit; the count
  passing is in the output, and the proof (H7-P2) is the check.
- A cross pair — P1's field from the planted block and P2's from its mirror (stride +0x140 PS1) — is a second family by
  the stated links (another stride); it ranks below the planted one. Left as is.
- One winner seen only (addendum 1): a field where P1 is larger in every state would pass every fold; "strong" now also
  needs two different winners.
- The PS1 fixture states are made in one paused session (B94's reason: the BIOS-less core's time-varying bytes).
- RetroArch headless on synthetic fixtures only (B61's form: no game; temp folders under `~/.cache`; the companion's
  display). Counted: **0 after both items' batches** (`ps`, 19:09Z). Two intermediate counts read 2 — one RetroArch session (an AppImage's two processes) of the other item's mutation runner, which ran at the same time from its own work copy; noted in `b96_2026-11-11/tests_mutations.txt` and `b97_2026-11-11/tests_x3.txt`.

## Files

`b96_2026-11-11/`: start files, the design + addendum 1 + hashes, `b96.diff` (applies on `2e30c1cf`),
`diffs_apply_in_order.txt`, `tests_x3.txt`, `tests_mutations.txt`, `scripts/` (`run_all.sh`, `mutate.py`,
`mutations.json`), redact / title checks, `manifest.sha256`. Patch note: `patches/B96_H7_HELD_OUT_AND_FAMILIES.md`.
The mutation source was a snapshot of the B96 tree in `/tmp/b_q22aj_b96/` (`companion/`, `tools/`, `tests/`,
`PrivyHub/` only); RetroArch linked read-only from the repo's `runtime/` in each work copy under `~/.cache`.
