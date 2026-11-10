# B76 — artwork and details for N64 / PS2 / GameCube (design, written and hashed before code)

**Knob:** `PRIVYHUB_ART_SYSTEMS=1` (opt-in). Absent (or any other value) = today's four systems, byte for byte.

## What exists (read in the code at HEAD)

- `companion/games/metadata_importer.py`: `SYSTEM_SPECS` = nes / snes / genesis / ps1 (the database name, the
  catalog path in RetroArch's database, the checksum mode). `LibretroProvider` reads `SYSTEM_SPECS` in three places:
  `prepare_system` (unknown system → `ProviderUnavailable`), `_artwork_url` (the thumbnail set's name) and
  `fetch_artwork` (a guard). The catalog and the metadata fragments are cached per system under
  `data/games/metadata/provider_cache/libretro/<system>/` (the cache per system exists already). Art lands in
  `media/games/box_art/<game id>.png`.
- The match: PS1 is `title_fallback` (no hashing): the scanned title (the file's stem through `_clean_name`) is
  matched exactly with its tags, then without them, then by region / disc / revision (`_variant_match`), then fuzzy.
- In-place titles (B49 / B59 / B69): the scanner lists N64 / PS2 / GameCube with the same `title` from the stem
  (`.z64` / `.v64` / `.n64`, `.chd` / `.iso` / `.cue`, `.rvz` / `.gcm` / `.iso` / `.ciso` — the suffix is dropped by
  the stem), system ids `n64` / `ps2` / `gamecube`. Today `match_game` answers `provider_unavailable` with
  `preserve_prior` for them (no network: `prepare_system` raises before any download).
- `plugins/games.py` decorates every game from `metadata.json` by game id (details, players, box art): **the onn needs
  nothing.**
- `games/startup_reconcile.py` calls `run_metadata_update` at companion start when the library changed or an
  incomplete record's retry is due; it is unchanged.
- `games/cheat_importer.py` imports `SYSTEM_SPECS` (B78 handles N64 cheats separately; this item leaves
  `SYSTEM_SPECS` itself untouched, so the cheat tool is unchanged by B76).

## The change

1. `metadata_importer.py`:
   - `ART_SYSTEMS_ENV = "PRIVYHUB_ART_SYSTEMS"`; `art_systems_on(environ=None)` → `== "1"`.
   - `EXTRA_SYSTEM_SPECS`:
     - `n64`: database / thumbnail set **"Nintendo - Nintendo 64"**, catalog `metadat/no-intro/Nintendo - Nintendo 64.dat`;
     - `ps2`: **"Sony - PlayStation 2"**, `metadat/redump/Sony - PlayStation 2.dat`;
     - `gamecube`: **"Nintendo - GameCube"**, `metadat/redump/Nintendo - GameCube.dat`;
     - all `checksum_mode: "title_fallback"` (PS1's: the file name, no hashing of large images; N64 too, so a
       `.v64`'s byte order never matters).
     The names are RetroArch's own system names (recalled; not fetched by B). The first real run confirms each set;
     a wrong path reads as `provider_unavailable` (counted, nothing written for that system).
   - `system_specs(environ=None)` → `SYSTEM_SPECS` (the same object's items) plus the three when the knob is on.
   - `LibretroProvider(..., system_specs=None)`: `self.system_specs = system_specs or system_specs(os.environ)`;
     its three reads use `self.system_specs`. Absent knob → the same four entries → today.
   - `run_metadata_update(..., provider=None)` unchanged in behaviour; it builds the provider as today.
   - **The dry run:** `run_metadata_dry_run(project_root, *, offline=False, only_system="", environ=None,
     provider=None, games=None)`:
     - scans as the update does; for each game of a system in `system_specs()` calls `match_game` only;
     - **never** calls `fetch_artwork`, never writes `metadata.json`, the art, or the update's logs;
     - the only thing that can be read from the network is RetroArch's whole system list per system (the same
       download the update does; it says nothing about the user's titles), cached per system as today; with
       `offline=True` only the cache is read;
     - returns `{"systems": {sys: {"total", "matched", "ambiguous", "no_match", "provider_unavailable"}},
       "misses": {sys: ["<sys>-miss-1", …]}}` — the misses as labels in scan order, **no title, no id, no path**;
     - games of systems not in `system_specs()` are counted under `"not_offered"` per system (so A sees them).
2. `tools/update_game_metadata.py`: `--system` choices from `system_specs()`; a new `--dry-run` that prints the
   per-system counts and the miss labels (JSON with `--json`) and returns. Without `--dry-run` the tool is today's.

## What the knob changes and what it does not

- **On:** the three systems are matched and fetched by the update (the CLI or the startup reconcile, whichever runs
  with the knob in its environment); their records land in `metadata.json` and their art in the box-art cache by game
  id, exactly as PS1's. The request per matched title carries the database's title name (as PS1's).
- **The fetch on the user's word:** A runs the CLI with the knob in that command's environment only (the dry run
  first). The companion does not need the knob for the art to show: a later start without it answers
  `provider_unavailable` + `preserve_prior` for those games, so their records are kept (tested).
- **Absent:** `system_specs()` is today's four; the provider, the update, the startup reconcile and the CLI's choices
  are today's. `--dry-run` is new and only acts when passed.

## Tests (`tests/art_systems/test_b76.py`, fixtures only, nothing fetched, temp dirs removed at exit)

- the mapping: knob on → the three specs with the names above; off / absent / "0" → exactly the four keys;
- the provider built with the knob off answers `provider_unavailable` for n64 / ps2 / gamecube without any fetcher
  call (a fetcher that fails the test if called);
- a fixture catalog (clrmamepro text) per system in an offline cache: stems with `(USA)`, `(Disc 2)`, `(Rev 1)`,
  `(En,Ja)` from `.chd` / `.rvz` / `.v64` / `.z64` file names match the right record; a title absent from the
  catalog is `no_match`;
- the dry run's counts per system and its labels; **no title in its output**; no `metadata.json`, no art written;
  `fetch_artwork` never called;
- the artwork URL uses the thumbnail set's name for each of the three;
- the details (developer / genre / year / players) from the fixture's fragments, as PS1's;
- absent → today: the provider's specs and a full offline `run_metadata_update` over a PS1 fixture write the same
  `metadata.json` games section with and without the code change's knob absent (the four-system path), and the
  three systems' prior records are preserved by a run without the knob.
