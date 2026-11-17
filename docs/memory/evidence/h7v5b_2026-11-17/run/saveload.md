# H7-V5b — step 12b: SAVE and LOAD during the T88 mini game (slot 9, the hub's — never the users' slot 1)

- `POST save-state?slot=9` (06:58:55.393Z) → **400 `{"ok": false, "error": "not during a mini game: nothing was saved"}`**
- `POST load-state?slot=9` (06:58:55.403Z) → **400 `{"ok": false, "error": "not during a mini game: nothing was loaded"}`**
- `party.jsonl`: **two rows `minigame_state_refused`** — `what` save / load, `state` playing.
- RetroArch's session log: Saving / Loading lines **2 before, 2 after** (the begin's load only) — none from them.
- `party-minigame-result` → still **`playing`**.
- **T88's setup's 7 files, every sha256 = step 8's**; no new file in the setup (`s12b.txt`).
- Why slot 9 is safe twice over: B131's refusal is checked before anything else in the POST path; slot 9 is outside the
  onn's slots 1-3, so even an unrefused SAVE would not have reached a user slot.
