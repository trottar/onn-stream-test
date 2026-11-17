---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AT) — the onn's SAVE / LOAD while a hub mini game is starting or playing, behind PRIVYHUB_PARTY=1. Settled first, and a correction: B127's record said a SAVE during a mini game would write the users' setup slots — wrong; since B110 the manager refuses SAVE / LOAD whenever the board is the session or set aside (every moment of a mini game): 503 "Saving and loading are not offered for the board game; nothing was sent." — nothing sent, no slot touched (HEAD's code in the test: the same). The onn shows "Save state failed" / "Load state failed" and a "Game State" dialog with "HTTP 503: " and the answer's JSON. Built: during a starting / playing mini game 400 "not during a mini game: nothing was saved" / "… loaded", one party row each, the title untouched; otherwise today. Tests 5 (3 runs): during both mini games under the setups refused, nothing sent, every setup file byte-equal; after them and with the flags absent HEAD's answers. Nothing adopted; nothing committed
---

# B131 — the onn's SAVE / LOAD during a hub mini game

Queue: `handoffs/QUEUE_2026-11-17AT.md` §B131. The directory is `b131_2026-11-17/`: the design + `.sha256` (hashed
06:22:46Z, before any code), `b131.diff`, `tests_mutations.txt`, `tests_x3.txt` (every queue-AT suite and the others),
`scripts/run_all.sh`, the board repo's status before / after, the checks, `manifest.sha256`. Patch:
`patches/B131_PARTY_SAVE_LOAD_REFUSED.md`. No title, id or path.

## Settled from the code (HEAD `1fc0ced0`) — B127's item 6 corrected

- **The routes:** `POST /plugins/games/save-state?slot=n[&replace=true]` / `load-state?slot=n` → `emulator.save_state` /
  `load_state`. **Both refuse first whenever the board is the session or set aside** (B108 / B110: `if _party is not
  None and (self._launch_kind == "godot" or self._party_stash is not None): raise EmulatorError(NO_STATES)`), and a hub
  mini game runs from its first step (the board set aside) to its last (the board back) with the board set aside. So
  **today the onn's SAVE / LOAD during a mini game send nothing and touch no slot** — the answer is **503
  `{"ok": false, "error": "Saving and loading are not offered for the board game; nothing was sent."}`**
  (EmulatorError → RuntimeError → 503 on a POST). **B127's record (settled item 6, its KNOWN_ISSUES line and its
  ROADMAP sentence) said a SAVE would write the users' setup slots: wrong** — it had not read the manager's first lines.
  Corrected by insertions (KNOWN_ISSUES, ROADMAP, this record, `SESSION_B_DONE_2026-11-17AT.md`).
- **What the onn shows** (`MainActivity.kt` `requestGameStateAction` / `httpPost`): the status line **"Save state
  failed"** / **"Load state failed"** and a dialog titled **"Game State"** whose message is the exception's text — a
  refusal with no `reason` field reads **"HTTP 503: "** followed by the answer's JSON (with the line in it), an **OK**
  button; a refused LOAD is not retried (only a lost connection is). The END dialog's **"Save"** ("Save a state before
  ending?") meets the same refusal and does not stop the game (its stop runs only after a save) — the user picks END
  again and **"Don't Save"**.

## Built (`b131.diff`)

- `plugins/games.py` `handle_post_request`, before today's path (beside B114's taken calls): `save-state` /
  `load-state` → `PartyMinigames.state_refusal(action)`; while the mini game is **`starting` or `playing`** (and not
  closed) → **400 "not during a mini game: nothing was saved"** / **"not during a mini game: nothing was loaded"** and
  one party row `{"step": "minigame_state_refused", "what": "save" | "load", "state": …}`; nothing reaches the manager
  or the title. Otherwise (no mini game; `ended` / `given_up` before the end; after it) → today's path (the board's 503).
  The party layer's own calls → today's path. `PRIVYHUB_PARTY` absent → the module is not loaded: today.
- The onn then shows "Save state failed" and "HTTP 400: …not during a mini game: nothing was saved…" — the line says
  why, in the game's words rather than the board's.

## Tests (`tests/b131_party_save_load/test_b131.py`, 5; B127's run of B114's scenario with `saveload`)

| test | shown |
| --- | --- |
| during each mini game (two-player under the PS1 setup, four-player under the N64 setup) | SAVE slot 1, SAVE slot 1 `replace=true`, LOAD slot 1 → **400 with the line**; **one `minigame_state_refused` row each** (`state` "playing"); **the fake RetroArch's command log: nothing sent** (no `SAVE_STATE_SLOT` / `LOAD_STATE_SLOT`); the mini game still `playing` |
| the mini games end as without them | end_P2 [0, 1]; places [2, 1, 4, 3] → scores [3, 4, 1, 2] |
| every setup file | **byte-equal** (both setups' slots, pictures, in-game saves and the normal states); no `.state8` |
| after the mini games, the board the session | SAVE / LOAD → **503 "Saving and loading are not offered for the board game; nothing was sent."** (today's) |
| flags absent / on with no mini game | HEAD's companion and mine: the cheat launch, `cheat-profiles`, the H7 / party routes, status, stop, and **with the board launched SAVE / LOAD** — the same answers (numbers of 4+ digits, decimals, times masked) under the four flag sets |

**Mutation** (`tests_mutations.txt`): HEAD's `plugins/games.py` → test 0 fails with **(503, the board's line) ≠ (400,
the mini game's line)**; **tests 1-3 pass on HEAD too** — nothing sent and every setup file byte-equal today: the
manager's own refusal. **Runs:** 3 green; B127, B124, B114, B115, B110 and the others green (`tests_x3.txt`).
