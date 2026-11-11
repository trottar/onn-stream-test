# B94 — the win-rule search (design, written before code; queue AI, 2026-11-11)

## Settled first (synthetic fixtures, B61's form; `settle/`)

- **One read command answers up to ~21,000 bytes** on snes9x, Beetle PSX HW and Mupen64Plus-Next (21,000 answered,
  21,840 not — the answer's datagram limit); the search reads in **16 KiB** chunks. Whole main memory: SNES 128 KiB in
  0.11 s, PS1 2 MiB in 1.66 s, N64 4 MiB in 3.33 s (8 MiB, the expansion, ≈ twice; measured with the timing below).
- **A state loaded while paused is exact:** 0 frames pass (the SNES fixture's frame counter unchanged), every byte equals
  the memory read just before the save, and 3 loads of one state read the same bytes on all three cores (0 differing).
  Loaded while running and then paused: PS1 differs in 104 bytes between loads (SNES 0, N64 0) — so the search loads
  paused, and still drops any address that differs between its loads.
- **The state file itself** (RetroArch's RZIP container, zlib chunks) holds the core's main memory as one contiguous
  block equal to the full read — SNES, PS1 and N64 (N64 in the read's own byte order) — but its offset was found only by
  planting a pattern on a fixture, not from a documented layout; so the search does **not** read files, it loads them.
- The PS1 fixture's own code does not run headless (no BIOS in the temp system folder): its noise is planted per state.

## The tool — `tools/h7_rule_search.py`

- **Input** (`--states FILE.json`): `[{"state": PATH, "label": "begin" | "end", "winner": "P1" … "P4" | null}, …]`, one
  `--system` (`ps1` | `snes`), `--content` (the game the states belong to), `--players 2..4` (else the highest winner
  named, at least 2). Each state is loaded **paused** in B93's headless session 3 times (`--loads`), the whole main
  memory read in 16 KiB chunks (`READ_CORE_RAM`); an address whose byte differs between loads of the same state is
  **unstable** and dropped. A state that fails to load → an error, never a rule.
- **Fields:** 1- and 2-byte (little-endian) values at every stable address.
- **Templates** (each candidate must hold in **every** labelled state given):
  - **(a) a per-player counter:** addresses `base + k·stride` (k = 0 … players−1, stride 1 … 0x400); every value ≤ 31
    ("small"); at every "begin" all players equal; at every "end" the winner's value strictly the largest and above its
    "begin" value. Rule: `max`.
  - **(b) a per-player level that empties:** the same block shape; at every "begin" all equal and ≥ 8; at every "end"
    every value ≤ its "begin" value, the winner's strictly the largest and > 0, every loser at 0. Rule: `max`.
  - **(c) a single winner field:** one address constant over the "begin" states; at the "end" states the same value for
    the same winner and different values for different winners; the "begin" value equal to none of the end values;
    addresses inside an (a) / (b) candidate's player fields excluded. Needs ends won by at least two players — without
    them (c) is reported **not testable**. Its rule JSON names the value each winner leaves (`"values": {"P1": v, …}`).
- **Output** (one JSON document): per template the candidate count and the candidates ranked (aligned to their size
  first, then a stride that is a multiple of 4, then the smaller stride, then the lower address), each with its rule in
  B93's JSON and its values in every state; `"decided"`: true only when a template leaves **exactly one** candidate —
  then `"rule"` is that one (the first such template in a, b, c order) and the others that also leave exactly one are
  listed as `"also_fits"`; otherwise `"decided": false` with the counts and **which extra state would split them** (an
  end won by a player not yet seen; a second end won by the same player). It never names a rule when more than one fits.
- `--time` prints the read and search seconds.

## Fixtures and tests (`tests/h7_rule_search/`)

`fixtures.py`: a synthetic PS-X EXE and SNES ROM (no game; the SNES one runs a frame counter and a xorshift buffer —
noise that differs every frame and between states; the PS1 one's noise is written per state). Planted with
`--make-state --write`: the per-player block (a round counter, ≤ 3, and a level, 120 at "begin"), decoys (a block where
P1 is larger in every state; a block — counter and level — that fits "begin" + a P1-won "end" but not a P2-won "end"),
noise bytes. States: begin, P1-won, P2-won, and a 4-player set (begin, P3-won, P1-won).
- the three states → `decided`, the planted round counter as the rule, the planted level the one `also_fits`;
- begin + P1-won → `decided: false`, the counts, the planted rule among the candidates, the split hint names a P2 end;
- the decoys never rank above the planted rule once the P2-won state is in;
- the 4-player set → the planted rule with 4 players;
- unstable addresses dropped (a reader whose loads differ at the would-be best address — no emulator);
- a state that fails to load → an error, no rule;
- the search's time on PS1's 2 MiB recorded.
RetroArch headless on the fixtures only; temp dirs removed; nothing left running.
