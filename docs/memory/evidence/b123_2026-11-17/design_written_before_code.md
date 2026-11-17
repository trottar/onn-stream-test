# B123 — design, written before code (hashed before the first edit for B123)

Baseline HEAD `cb16e0c8` + B122 (the tool). Behind `PRIVYHUB_H7=1` (`h7_minigame.py`, `h7_contest.py` are imported
only with it) and, for the sidecar, `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1` (`party_minigame.py`). Either absent → today.

## The N64 begin state through `h7-start` (settled from the code)

- **Today:** `h7-start` with the load refuses N64 ("not supported yet — a state cannot be loaded into a running N64
  game"); the load (B101's `_load`) takes the manager's lock, copies the kept `<game id>.state` to the core's state
  folder as `<stem>.state8`, sends `LOAD_STATE_SLOT 8`, waits for RetroArch's own load line (`[State] Loading state
  "…", N bytes.`), removes the scratch, and refuses plainly on any failure; the folder from `CORE_FOLDERS` by the
  core file, the stem from `_active_state_stem()` (the content's stem).
- **What differs for N64:** (1) **the folder** — the core `mupen64plus_next_libretro.so` keeps its states in
  `Mupen64Plus-Next/` (the core's library name; the hub's states root holds it beside `Beetle PSX HW`, `Snes9x`,
  `bsnes`); (2) **the stem and the slot file** — the same rule (`<content stem>.state8`; the hub's own N64 SAVE found
  its `<stem>.state` the same way at H7-C1); (3) **the core on load** — RetroArch hangs on a **save** sent into a
  running N64 core (B61, HOME-8 C23/C25), and B65 sends an N64 load only into a core that answers `PAUSED` within
  1.5 s ("every N64 save that worked was into a paused core"). The mini game's start launches the title paused (B110)
  and B112's bench leaves it paused until `bench-release`, so **the N64 load is sent only when `GET_STATUS` answers
  `PAUSED`** — else refused plainly, nothing sent: "the N64 game is not paused: its state is loaded only into a paused
  core; nothing was sent". A paused core shows the loaded picture at its first frame after the release (the watch's
  `recognised` reads it then).
- **Built:** `CORE_FOLDERS` + `mupen64plus_next_libretro` → `Mupen64Plus-Next`; `h7_minigame.SYSTEMS` + `n64` (the
  watcher alone already took any system); the N64 refusal replaced by the paused check. B101's contest stays PS1 /
  SNES (its own list, untouched).
- **The watch with places (B122's version 3):** the watcher feeds the places to `Ended`; an ended watch carries
  `places`; its row says them. A version-2 spec's watch and answers are byte for byte as today (no `places` key).

## The mini-game sidecar for four players

- Today's two-player form unchanged: `{"players": 2, "scores": {"<end class>": [two numbers], …}}` with a version-2
  spec naming those end classes.
- **The places form:** `{"players": n, "places_to_scores": [s1, …, sn]}` with a **version-3 spec of n ports** — a
  place's points, higher better; **`places_to_scores` may be left out: the default is n, n−1, …, 1** (4, 3, 2, 1 for
  four players). Listed only when the spec's ports = `players` and the list has n numbers.
- **The result's `scores` in the order of the seats given:** seat k plays port k (B110's route), so seat k's score =
  `places_to_scores[place of port k − 1]`. An `ended` watch without a whole row of places → `given_up` ("an end the
  places do not name"), never a guess.

## Tests (`tests/b123_h7_n64_start/`, the real HTTP server, B101's fake RetroArch on an N64 session)

The load line and the scratch removed; the users' slots byte-equal; no `.state8` left; a core answering `PLAYING` →
refused, no load sent; a four-player end read (the version-3 spec, a fake reader's places) → the scores for seats
[1, 2, 3, 4] and [3, 1, 4, 2]; the two-player sidecar as today; each flag absent → today (the real routes against HEAD's
code).
