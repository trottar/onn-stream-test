---
memory_schema: 1
as_of: 2026-11-21
baseline_commit: 13646e06 (this repo)
---

# B191-B193 — the `letters` result kind; synthetic training, never synthetic proof; the task's words

**Result:** `evidence/B191_LETTERS_KIND_SYNTHETIC_2026-11-21.md`.

- **Files:**
  - `tools/h7_endscreen.py`: spec version 5 — `VERSION_LETTERS` and the `LETTERS_*` / `SYN_*` constants;
    `letters_area`, `corner_black`, `letters_zones`, `letter_strings`, `_cue`, `letters_colour`, `letters_bins`,
    `letters_mask`, `letters_glyphs` (+ `_merge_touch`), `letter_cell`, `letter_dists`, `fit_letters`, `read_corner`,
    `_letters_places`, `synthetic_letters`, `letters_seed`, `learn_letters`, `ReaderLetters`; `check_spec`,
    `load_spec`, `Reader.__new__`, `thresholds` each gain a version-5 branch (versions 2-4 unchanged); the docstring.
  - `tools/party_add_game.py`: `--word`; register's letters cells (the word, two players, four refused with why);
    `register_inputs` carries the word for letters only; `_roles_needed` / the other-ending cell take letters as
    winner; `_sidecar`; label / learn dispatch; `learn_inputs`; `BARS["synthetic_held_wrong_max"]` (added);
    `_for_reader` (a version-5 spec read in colour, every other as today); the letters section (`parse_letters`,
    `_label_letters`, `_learn_letters`, `_letters_replay`, `_scene_under`, `_letters_sheet`, `_letters_line`, …).
  - `companion/party_minigame.py`: `LETTERS_VERSION`, `_letters_entry` (only with `PRIVYHUB_PARTY=1`, as the module).
  - `docs/memory/handoffs/ADD_GAME_TASK.md`: B193.
  - Tests: `tests/b191_letters/` (new).
  - The diff: `evidence/b191_2026-11-21/b191.diff` (sha256 in the manifest).
- **Switch:** a title registered `--result letters` (absent = today); a sidecar `"result": "letters"` with a version-5
  spec on the hub (absent = today; `flag_proof.txt`). `winner` / `places` / `score`, T88's, T89's, T90's rules
  unchanged; no bar in `BARS` lowered.
- **Rollback:** `git apply -R evidence/b191_2026-11-21/b191.diff`.
