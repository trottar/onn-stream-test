---
memory_schema: 1
as_of: 2026-11-09
status: BUILT, NOT ADOPTED (session B, queue AC) — N64 / PS2 / GameCube added to the hub's art and details fetcher behind PRIVYHUB_ART_SYSTEMS=1, with a dry run. Nothing fetched by B (fixture catalogs only); nothing committed. No title, serial, path or identifier in this record
---

# B76 — artwork and details for N64 / PS2 / GameCube (2026-11-09)

**The user's answer (G1):** art + details for N64 / PS2 / GameCube from RetroArch's library as PS1's — **yes**.

**Baseline:** HEAD `a96c816c` (HOME-11 committed); `git status --short` empty at the check
(`b76_2026-11-09/git_status_at_start*.txt`); only the companion and `privyhub-diag` active (`units_at_start.txt`).
**Design** hashed before code at 23:18:17Z (`design.sha256`, `design_hashed_at.txt`).

## What was built (`b76.diff`)

- **The system map** (`companion/games/metadata_importer.py`): `system_specs()` = today's NES / SNES / Genesis / PS1,
  plus, with **`PRIVYHUB_ART_SYSTEMS=1`**:
  - `n64` → **Nintendo - Nintendo 64** (`metadat/no-intro/…`);
  - `ps2` → **Sony - PlayStation 2** (`metadat/redump/…`);
  - `gamecube` → **Nintendo - GameCube** (`metadat/redump/…`);
  - all matched **by the file name** as PS1's (`title_fallback`: no hashing of large images). The names are
    RetroArch's own system names, recalled (not fetched); a wrong one shows as "list unavailable" in the dry run.
- **The provider** reads the map it was built with (`LibretroProvider(…, specs=None)` → the environment's).
- **The details** are PS1's path unchanged: developer, publisher, genre, year, players from the same records; the art
  in `media/games/box_art/<game id>.png`; the onn shows whatever the host gives (no client change).
- **The cache per system** is the existing one (`provider_cache/libretro/<system>/`).
- **The dry run:** `tools/update_game_metadata.py --dry-run [--offline] [--system s] [--json]` →
  `run_metadata_dry_run`: per system `matched`, `ambiguous`, `no_match`, `provider_unavailable`; the misses as
  labels (`n64-miss-1`, …); games of systems outside the map counted as "not offered". It never requests art or
  anything per title and writes nothing but the per-system list cache. Without `--offline` it may download
  RetroArch's whole system list per system (the same download the fetch does; it says nothing about the user's
  titles).

## The knob

`PRIVYHUB_ART_SYSTEMS=1` = on; absent / anything else = today's four systems byte for byte
(`proof_flag_absent.md`). **The companion does not need the knob for the art to show**: a later run without it
keeps the three systems' records (`prior_preserved`). So A's ART-1 runs the tool with the knob in that command's
environment only, on the user's word. Adopting the knob in the companion's drop-in later would make new N64 / PS2 /
GameCube titles fetch at companion start, as PS1's do.

## Tests (`tests/art_systems/test_b76.py`, 20)

The mapping (on / absent / "0" / "true" / ""); the provider's default from the environment; the three systems
`provider_unavailable` without any fetch with the knob off; prior records kept by a run without the knob; matches
from fixture catalogs for `.v64` / `.z64` / `.chd` / `.iso` / `.rvz` stems with `(USA)`, `(Rev 1)`, `(Disc 2)`,
`(En,Ja) (Rev 2)`; a missing title and a wrong region miss; the details from fixture fragments; the thumbnail URL per
system; the art landing by game id; the dry run's counts, labels, no title / id / path in its output, nothing
written, art never requested, "not offered" without the knob, "list unavailable" counted with no fetch.

- 3 runs: 20 / 20 each (`tests_x3.txt`). Temp dirs: none left.
- Mutations: **7 / 7 caught** (`tests_mutations.txt`; the runner `scripts/mutate.py`, `scripts/mutations.json`).

## Disclosed

- The design named the provider's parameter `system_specs`; the code calls it `specs` (the module has a function of
  that name).
- The dry run "without fetching" is read as: no request per title and no art; the whole system list may be
  downloaded (it carries nothing about the user's titles). `--offline` reads only the cache.

## Files

`b76_2026-11-09/`: start files, the design + hash, `b76.diff`, `proof_flag_absent.md`, `tests_x3.txt`,
`tests_mutations.txt`, `scripts/` (the queue's shared `mutate.py`, `snapshot_and_diff.sh`), redact / title checks,
`manifest.sha256`. Patch note: `patches/B76_ART_THREE_SYSTEMS.md`.
