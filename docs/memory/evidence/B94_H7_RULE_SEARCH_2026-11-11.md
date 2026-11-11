---
memory_schema: 1
as_of: 2026-11-11
status: BUILT (session B, queue AI) — tools/h7_rule_search.py: from a few labelled save states, the candidate win rules in B93's rule JSON (a per-player counter, a per-player level that empties, a single winner field), "decided" only when a template leaves exactly one. Settled how to read a state's whole memory (loaded paused, 16 KiB reads; exact, 0 frames). On fixtures: begin + a P1 end is never decided; adding a P2 end decides the planted rule. Synthetic fixtures only; the user's states not touched; no real title started. Nothing committed. No title, serial, code name, character name or path in this record
---

# B94 — the win-rule search (2026-11-11)

**Why:** H7's real proof needs the memory that says who won in T88 (HOME-12V: a 2-player PS1 fight, a "begin" state and
an "end" state, player 1 won). **Baseline:** HEAD `0f881ae5`. **Design** hashed before code (`b94_2026-11-11/design.sha256`).

## Settled (synthetic fixtures, B61's form; `settle/`)

| | SNES (snes9x) | PS1 (Beetle PSX HW) | N64 (Mupen64Plus-Next) |
| --- | --- | --- | --- |
| largest chunk one read answers | 21,000 B (21,840 not) | 21,000 B | 21,000 B |
| whole main memory, 16 KiB reads | 128 KiB, 0.11 s | 2 MiB, 1.66 s | 4 MiB, 3.33 s (8 MiB with the expansion: ≈ twice, not measured) |
| a state loaded **paused**: frames passed / bytes ≠ saved / bytes differing between 3 loads | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| loaded running, then paused: bytes differing between 3 loads | 0 | **104** | 0 |
| the state file (RZIP, zlib chunks) holds main memory as one block equal to the read | yes | yes | yes (the read's byte order) |

The file's block was located only by planting a pattern on a fixture — no documented layout — so **the search loads
states (paused) and reads them; it does not parse files.** The PS1 fixture's own code does not run headless (no BIOS in
the temp system folder): its noise is written per state.

## Built — `tools/h7_rule_search.py`

`--content --system ps1|snes --states FILE.json [--players] [--loads 3] [--time]`; states.json:
`[{"state", "label": "begin"|"end", "winner": "P1"…|null}]`. Each state loaded paused `--loads` times in B93's
session (the game read in place, temp folders); RetroArch's load line required (`Loading state … N bytes`, N > 0, no
failure line) — a state that fails to load is an error, never a rule; an address differing between loads is dropped.
1- and 2-byte fields; strides 1 … 0x400. Templates (every candidate holds in every labelled state):
- **(a) a per-player counter:** values ≤ 31; all equal at "begin"; at "end" the winner's strictly the largest and above
  its "begin" value;
- **(b) a per-player level that empties:** all equal and ≥ 8 at "begin"; at "end" none above "begin", the winner's
  strictly the largest and > 0, every loser at 0;
- **(c) a single winner field:** constant over "begin"; one value per winner at "end", different winners different
  values, the "begin" value none of them; fields of (a) / (b) candidates excluded; **not testable** without ends won by
  two players.
Reads of the same memory are one candidate (the same changing bytes: a 1- and a 2-byte read, or a 2-byte read one byte
early); ranked: every player's field changes in some state, aligned, stride a multiple of 4, smaller stride, lower
address. **"decided"** only when a template leaves exactly one (the first in a, b, c order is "rule", the others with one
are "also_fits"); otherwise the counts and the state that would split them (an end won by a player not yet seen; else a
second end won by the same player). Each rule carries `"none_when": "equal"` (B95).

## Fixtures and tests (`tests/h7_rule_search/`, 10)

`fixtures.py`: a synthetic PS-X EXE and SNES ROM (no game); the SNES one runs a frame counter and a xorshift buffer (noise
that differs between states — each state saved at a different moment); on PS1 random noise written per state, every
state from one paused session (see "Disclosed"). Planted
through B93's `--make-state --write`: the per-player block (a round counter ≤ 2 and a level 120 at "begin"), a decoy
where P1 is larger in every state, a decoy block (a counter and a level) that fits begin + a P1-won end but not a P2-won
end. Results:
- **PS1, begin + P1-won + P2-won → decided: the planted round counter** (a: 1), the planted level the one `also_fits`
  (b: 1); (c) many (the noise) — not chosen;
- **begin + P1-won → not decided**, a > 1 and b > 1 (the decoys among them), c not testable, "would split: an 'end' state
  won by P2"; the planted rule among the candidates;
- the decoys are not candidates once the P2-won state is in;
- **4 players** (begin, P3-won, P1-won): the counter not decided (a half-stride block whose never-winning players read 0
  also fits; the planted one ranked first) — the level decided (b: 1); **+ a P4-won end → the counter decided too**;
- SNES (the program's own noise): decided, the planted rule;
- unstable addresses dropped (an injected reader: the would-be extra candidate unstable → one candidate; stable → two);
- a state that fails to load → an error, no rule: a corrupt file (read as 0 bytes) and a well-formed container the core
  refuses (RetroArch's failure line);
- **the time on PS1's 2 MiB: 3 states × 3 loads read in 44.2 s (≈ 4.9 s a load: start, paused load, 2 MiB in 16 KiB
  reads, close), the search itself 0.17 s** (79 s to read before B95 stopped waiting 5 s for a paused RetroArch to quit).
3 runs, 10 / 10 each (`tests_x3.txt`); mutations **7 / 7 caught** (`tests_mutations.txt`) — after one test change: M4
(the failure line ignored) was first missed (the corrupt file also fails the 0-bytes check); the refused-container case
was added, then caught.

## What the search decides with two states against three (the fixture)

**Begin + one end is never decided** — the counts of both block templates stay above one (decoys and zero-padded
blocks fit) and the single-field template cannot be tested; **an end won by the other player decides it** (the planted
rule alone in its template). For T88 that means: begin (slot 3) + the P1 end (slot 2) will most likely answer "not
decided" with counts; one more state — the same fight with player 2 winning — should decide it.

## Disclosed

- **Found while testing — chance fits from memory that changes with time:** with no BIOS, Beetle PSX still changes
  about 243 bytes (near 0x43E00-0x44EC0) as time passes. When the fixture's PS1 states were saved at different moments,
  small time-like values there **sometimes fitted the counter template in all three states** — one run found 6
  candidates (not decided), another 1. The tool's answer was the honest one ("not decided", with the count). The PS1
  test states are therefore made in one paused session (written, saved, written, saved); the SNES ones at different
  moments with the program's own noise. **For T88:** a real game's memory changes far more between a "begin" and an
  "end"; extra candidates are likely, and the answer may need a further state.

- Templates are this design's (stated above), not a general search; a game whose winner lives in another shape (a
  4-byte value, a big-endian field, a bitmask, stride > 0x400) is not found — the output then says 0 candidates.
- N64 is not searched yet (its memory reads come word-swapped; the read is measured, the search is not built for it).
- The thresholds (≤ 31, ≥ 8) are chosen to keep random noise out on 2 MiB; a counter above 31 is not a candidate.

## Files

`b94_2026-11-11/`: start files, the design + hash, `settle/` (the two settle scripts), `b94.diff`, `tests_x3.txt`,
`tests_mutations.txt`, `scripts/`, redact / title checks, `manifest.sha256`. Patch note: `patches/B94_H7_RULE_SEARCH.md`.
