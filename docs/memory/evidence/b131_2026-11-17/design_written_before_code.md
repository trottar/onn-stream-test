# B131 — the onn's SAVE / LOAD during a hub mini game: the design (written and hashed before any code)

Only with `PRIVYHUB_PARTY=1` (the party layer; absent → today). No title, id or path in this folder.

## Settled from the code (HEAD `1fc0ced0`) — **B127's item 6 was wrong**

- **The routes:** `POST /plugins/games/save-state?slot=n[&replace=true]` / `load-state?slot=n` (`plugins/games.py`
  `handle_post`) → `emulator.save_state` / `load_state`. **Since B110 (queue AP) both refuse first whenever the board
  is the session or set aside** — `if _party is not None and (self._launch_kind == "godot" or self._party_stash is not
  None): raise EmulatorError(NO_STATES)` — and a mini game always runs with the board set aside (its first step is the
  stash, its last the stash's end). So **today the onn's SAVE / LOAD during a mini game already send nothing and touch
  no slot**: the answer is **503 `{"ok": false, "error": "Saving and loading are not offered for the board game;
  nothing was sent."}`** (EmulatorError → RuntimeError → 503 on a POST). B127's record said a SAVE would write the
  users' setup slots — it did not read the manager's first lines; corrected in this queue's records (insertions).
- **What the onn shows** (`MainActivity.kt` `requestGameStateAction`): the status line "Save state failed" / "Load
  state failed" and a dialog titled "Game State" whose message is the exception's text — for a refusal without a
  `reason` field, **"HTTP 503: " followed by the answer's JSON** (the line inside it), an OK button; a refused LOAD is
  not retried (only transport failures are). The END dialog's "Save" path ("Save a state before ending?") gets the same
  refusal and then does not stop (its stop runs only on success) — the user chooses END again and "Don't Save".

## Build (behind `PRIVYHUB_PARTY=1`)

- In `handle_post_request`, before today's path (beside B114's taken calls): `save-state` / `load-state` while the
  party layer's mini game is **`starting` or `playing`** (and not closed) → **400 "not during a mini game: nothing was
  saved"** / **"not during a mini game: nothing was loaded"**, one party row `{"step": "minigame_state_refused",
  "what": "save" | "load", "state": <the mini game's state>}`; nothing reaches the manager or the title. Outside those
  states (no mini game, `ended` / `given_up` before the end, after it) → today's path and answer (the board's 503
  refusal). Calls the party layer makes itself (`inside()`) → today's path.
- **Tests** (`tests/b131_party_save_load/`, B114's scenario with B127's setups — B101's fake RetroArch under a fake
  setup folder, B108's stand-in board): during the two-player mini game under the PS1 setup and the four-player one
  under the N64 setup, a SAVE (slot 1, and `replace=true`) and a LOAD (slot 1) → 400 with the line, one party row each,
  **the fake's command log showing nothing sent** (no `SAVE_STATE_SLOT` / `LOAD_STATE_SLOT`), the mini game still
  `playing` and then ended as without them, **every setup file byte-equal**; after the end → today's answers (the
  board's 503 line) — mine = HEAD's; the flag absent → today's answers through the real routes (HEAD's companion
  against mine); B110 / B114 / B115 / B124 / B127 green.
