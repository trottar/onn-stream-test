# B85 — the cheat list cleaned on the hub, every system (design, written and hashed before code)

**Baseline:** HEAD `c514c543`. **Knob:** `PRIVYHUB_CHEAT_CLEAN` — default on; `0` = today's raw list and today's
launch, byte for byte. `raw=1` on `cheat-catalog` returns today's raw list with the knob on.

## Settled from the hub's own files (counts only: `settle_counts.txt`, `settle_shapes.txt`, `scripts/`)

The cached RetroArch cheat files the manifest names, read in memory (N64 18 files / 7,562 entries, biggest 2,092;
PS1 116 / 2,486; SNES 13 / 610):

- **Repeats** (a name seen earlier in the same file): N64 2,441, PS1 28, SNES 83. Almost never identical code (N64 9);
  N64's are single-line writes of **the same value to another address** (1,472) or another address and value (294):
  the same cheat for another target (a player, a slot, a character) whose distinguishing heading was lost. They are
  distinct cheats → **listed under the first as "variant n"**, never merged into one; identical code → folded.
- **"Enabler / activator" entries:** N64 903 by name, of which **884 are lone joypad conditionals** (every line
  `D0`-`D3`: "if this button is held, then …" with no write after it). In a RetroArch cheat each entry is applied on
  its own (`cheatN_code`), so a lone conditional writes nothing: it is a cheat cartridge's button trigger meant to be
  typed in front of another code by hand → **hidden, never applied** (on N64 and PS1 by the code type, whatever the
  name). The rest — names saying "must be on", "(M)", "enable code", "master code", "enabler", "key code" **with real
  writes** (N64 17 with `F1` / `DE` / `EE` / `FF` / write lines, PS1 15, SNES 6) — are what the cheat list's authors
  say other codes need. The hub cannot prove per core whether each is needed (no core documentation on the hub says),
  so B follows the list's own instruction: **applied automatically with any selection from that file, and not shown**.
  With the code unreadable (names only), such a name is **shown under "Other" with its plain name** — never dropped.
- **P1-P4:** N64 1,934 entries, PS1 456 carry a player tag (player-specific cheats). The **bare "P1" / "P2" rows**
  (N64 133) carry codes: they are cheats, not headers; they come in runs right after a named cheat (7 runs; 126 bare
  rows follow another bare row) → **labelled "<that cheat's name> — Player n"**, in that player's section.
- **No-code entries** (N64 67, PS1 4, SNES 5): heading rows of the source file → hidden (nothing to apply).
- **Split parts** ("n of m"): N64 24, PS1 2 → folded into one entry that enables every part.

## The design

1. **`companion/cheat_clean.py`** (new, pure): `clean(catalog, project_root) -> catalog` and
   `expand(clean_catalog, source_index, indexes) -> real indexes`. Per source, by provider:
   - **RetroArch (`libretro`: PS1, SNES, N64, …):** the source file's codes read again from its `local_path` (the
     manager has already checked its sha and count); then, in the file's order:
     1. no code → hidden (`header`); 2. N64 / PS1 and every line a `D0`-`D3` conditional → hidden (`trigger`);
     3. a "must be on" name with a write → hidden, into the source's `requires` (`enabler`); 4. "n of m" parts with a
     common base and ≥ 2 members → one entry (the first part's index) with `parts` = all of them, labelled by the base;
     5. a bare "P1"-"P4" / "Player n" → "<the last shown entry's label> — Player n", group `player<n>`;
     6. the label tidied: whitespace collapsed, `P1` / `1P` → "Player 1", a trailing `(M)`, a trailing bracketed or
        dashed hex code and empty / dangling brackets removed, a `\` separator → " — ";
     7. the group: `player<n>` from the first player tag, else `general` (`other` for an enabler name shown by name);
     8. repeats of a tidied label: identical code → folded (`duplicate`); different code → shown right after the first
        as "<label> — variant k" with `variant_of` = the first's index.
     Every shown entry: `index` (its first real index — what the client sends), `description` = the label, `group`,
     `parts`, `requires` (the source's enablers), `variant_of`. The source: `clean: true`, `raw_count`, `shown_count`,
     `hidden` (`header`, `trigger`, `enabler`, `duplicate` counts), `folded_parts`.
   - **The user's own files** (`user` — B81's `.cht`; `user_pnach` — B81's PS2 `.pnach`): as they are, group `yours`;
     nothing hidden, folded or relabelled.
   - **GameCube** (`dolphin_bundled`, B79): labels tidied and grouped by player tag; nothing hidden or folded.
   - Any other provider: as it is.
2. **`companion/plugins/games.py`:**
   - `cheat-catalog`: the manager's catalog → `cheat_clean.clean(…)` unless `raw=1` or the knob is `0`.
   - `launch` (the one place the onn's cheat query is parsed, `handle_post`): after `_parse_cheat_launch_request`, with
     the knob on and no `cheat_raw=1`, the indexes → `expand(clean(manager.cheat_catalog(game)), source, indexes)`:
     each sent index that is a shown entry's index → its `parts`; plus the source's `requires` (any selection); any
     other index passes as sent (a saved profile's real indexes: the union is unchanged). The manager stages exactly
     those real indexes (today's code: the `.cht` enable flags, RetroArch's toggles, Dolphin's / PCSX2's files).
   - `cheat-profiles` unchanged (a saved profile's real indexes and the names it was saved with).
3. **What every client sees:** the cleaned list (also today's dialog on `85220f99…` / `de6682db…`), whose `index`
   values expand at the launch. `raw=1` / `PRIVYHUB_CHEAT_CLEAN=0` → today's catalog and launch, byte for byte.

## Tests (`tests/art_systems/test_b85.py`, through the plugin as the companion builds it)

B83's harness (a child `python3 -I` on a fixture tree with its own `companion/`; `from plugins import PLUGINS`; the
real `handle_post_request("cheat-catalog")` and `handle_post("launch")` with the emulators faked; no network). Fixture
`.cht` files (made-up names and codes) with every shape above: **the folded counts** (repeats → variants, identical →
one, headers / triggers / enablers hidden); **a split cheat staged as all its parts**; **the enabler applied and not
shown**; **"Player 1"** and a bare-row run labelled from its cheat; **`raw=1` and `PRIVYHUB_CHEAT_CLEAN=0` → today's
list byte for byte** (HEAD's handler output on the same tree); **a launch with a cleaned selection stages the right
indexes** (the staged `.cht`'s enable flags, N64 and PS1); GameCube tidied, nothing hidden; the user's files as they
are under "yours". The hub's before / after counts per system (counts only) in the record. Mutations; ×3.
