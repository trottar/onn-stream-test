# B149 — a practice that came and went unseen: design (written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AY.md` §B149. My board file `minigames/hub_minigame.gd` (`a1e648f3…`) and its check
(`95eb6f89…`), the board's repo at `32d5329`. **The hub's answer as it is:** `party-minigame-result` for a held start
carries `"practices"` in every state (`PartyMinigames.result`), so nothing more is needed from it.

## The design (my board file)

- At each go the hub takes, the board keeps the `practices` count it last saw (`practices_at_go`).
- On an answer with `state == "starting"`, while the board still waits on a go it sent (`went`), and
  `practices > practices_at_go`: the practice came and went. If the board already re-showed the load screen at its
  `"playing"` (B145's `behind`): as B145 (the gate goes, `went` false, the readiness told afresh). If it never saw
  `"playing"`: **the load screen shown again now** (`show_minigame_loading`: every mark clear, so no press made during
  the practice counts as a choice — the gate swallowed the pads until this moment), the gate goes, `went` false, the
  readiness told afresh: **the next choice accepted at once**, at the next 0.25-s read, not after the 20-minute bound.
- **One more log line at every re-show after a practice:** `PrivyParty: hub mini game: load screen again` — printed
  where the load screen is shown again behind a practice (B145's hand-over) and where it is shown again for an unseen
  practice; once a practice.
- Everything else as B145.

## The check (`checks/hub_minigame_check.gd`, extended)

- A new stand-in scenario `hunseen`: the hub's answers go `ready` → (the practice go) → `starting` / `preparing` with
  `practices` 1 and never `playing`, → `ready` → (a plain go) → playing → ended. Asserted: the load screen shown again
  (2 shows), the second go is sent within a second of `ready` (not after the bound), the go kinds `practice`, `start`;
  the lines `cards …`, `practice`, `load screen again`, `start`, the scores; no press during the practice reaches the
  re-shown screen.
- The three practices case: `load screen again` three times, in order.
- Every earlier case unchanged; the count stated; the two files' sha256; B111's counts and lines updated.
