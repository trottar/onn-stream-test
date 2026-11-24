---
memory_schema: 1
as_of: 2026-11-24
status: FIXED TASK (session A, hardware) — add one party mini game or duel by its code on the new path (queues BP, BQ): register, survey, label, plan, train, bench, solo, close. Replaces ADD_GAME_TASK.md for score and letters titles. The same page for every title; only the code changes (ADD_GAME_PROMPT_TEMPLATE.txt). Nothing adopted by it
---

# ADD-GAME STEPS — one title, by its code

The user's procedure, and the whole task: **(1) three saves, (2) you find where the result is and what kind it is,
(3) the user adds only what the tool says is missing — made-up pictures fill the rest, (4) train, (5) test on the
board.** The tool (`tools/party_add_game.py`) decides every verdict. You look at pictures only where a step below says
so; you never choose a threshold, edit a rule or change a bar.

## Rules

- **The window:** not between 04:30 and 05:30Z, and not within 45 min before it — else reply only "YOU, now: the hub's
  nightly window runs until 12:30 am Eastern; send the read line again after that".
- **Before anything:** `git status --short` empty but for the prompt files, and `grep -c VARIANT_DRAWS
  tools/party_steps.py` at least 1 — else "YOU, now: commit first, then send the read line again". Only
  `privyhub-companion` and `privyhub-diag` active.
- **Every reply to the user begins "YOU, now:"**, is one step, short, in plain words. Nothing about adb is ever asked.
- **Never ask the user for a save the tool has not named as missing. Never ask for a save again that is already kept.
  Slot 1 is the game's start: it is read, never saved over — every later save goes to slot 2 or 3.**
- The code is the title's only name in anything written: no title, id, path, team, character or picture in any record
  or command line you write down. The user's swearing is left out of quoted words.
- Nothing adopted; nothing committed by you. No stream started by you; the companion is restarted only by bench and
  close.

## A. A new title (no binding yet)

1. Ask once, in one message: "YOU, now: which game is <code> (I won't write its name), two players or four, and does
   it need anything unlocked first? Then make three saves with the onn's SAVE, the shortest match, the way you always
   play: slot 1 at the start (before the match), slot 2 in the middle of a match, slot 3 on the final screen that shows
   who won. Reply with who won the slot 3 match." (A setup made in Extras → Cheats: `--setup slot1`, else `none`.)
2. `python3 tools/party_add_game.py register <code> --players <2|4> --system <ps1|n64|snes> --result score --find
   "<the user's words>" --setup <none|slot1> --collect begin=1 --collect other=2 --collect end_P<the winner>=3`
   (`score` is the first guess; step 3 corrects it. "<n> titles match": ask which one, names in chat only.)
3. `survey <code>` → open `~/privyhub_h7/add_game/<code>/survey/boxes.png`. **What kind is it?**
   - each player's number, more wins → `score`;
   - letters of a word in each player's corner, the full word loses → `letters`;
   - anything else (a "player N wins" screen, places, a time) → stop: one sentence to the chat (Cowork), then close.
   If it is not `score`, run register again with the right `--result` (letters: `--word <WORD>`), no `--collect`.
   For a `score` title ask once: "YOU, now: what's the highest score one side reaches in a match the way you play
   (for example 5)?" and run register again with `--max-score <N>`, no `--collect`.
4. `survey <code> score <P1> <P2>` (letters: `survey <code> letters <WORD> <P1> <P2>`): for each player the numbered
   box that holds that player's result and nothing else, or `x0,y0,x1,y1` read off the grid. Open
   `survey/regions.png`: each region holds the whole result with a little room → `survey <code> ok`; else
   `survey <code> again P<k>`, then `survey <code> P<k> <box or rectangle>`.

## B. Label, plan, train — also where a title with kept saves starts

5. `label <code>` → open `regions/<role>.1.png` and `.2.png` for every end save and read each region as drawn
   (leading zeros too): `label <code> end_P1=<P1>-<P2>,<P1>-<P2> …` (letters: `<P1>/<P2>`). Then open
   `regions/look.png`: every glyph in the row of what you read it as → `label <code> look=all`; else
   `look=<symbol>:<i>` and read that save again. "read again: <role>" → read it afresh, at most twice, then stop.
6. `plan <code>`. Its last line is the whole ask.
   - "Nothing more is needed." → step 7.
   - "Still needed: …" → look at plan's rows. **A symbol marked "never"** is the user's: "YOU, now: I still need
     <plan's words for the never symbols only>. Play a match that ends that way, press SAVE on the final screen to
     slot 2 or 3, and tell me the slot and who won." Then step C. **A symbol marked "once (not counted: asked)" is
     never the user's**: when only such symbols are left, stop — one sentence with plan's row for each, back to the
     chat (Cowork) — then close.
7. `train <code>` → PASS, last line "Nothing more is needed.". Anything else: stop.

## C. One more save (only when plan asked, or the prompt names one)

`register` again with the title's own arguments and one `--collect end_P<winner>_<n>=<slot>` (`<n>`: the next number
free for that player, 2 to 4). For a title that has a binding, take the arguments from it — never ask the user again:

```
python3 - <<'PY'
import sys; sys.path.insert(0, "tools"); import party_add_game as t
code, role_slot = "<code>", "end_P<winner>_<n>=<slot>"
b = t.load_binding(code)
argv = ["register", code, "--players", str(b["players"]), "--system", b["system"], "--result", b["result"],
        "--find", b["title"], "--setup", "slot1" if b.get("cheat") else "none", "--collect", role_slot]
argv += ["--max-score", str(b["max_score"])] if b.get("max_score") is not None else []
argv += ["--word", b["word"]] if b.get("word") else []
sys.exit(t.main(argv))
PY
```

Then tell the user "YOU, now: slot <n> is free again", and go on at step 5 (a title without a survey yet: `survey
<code>` and step 4 first, its kind as registered).

## D. The test

8. `bench <code>` — about 5 min, nobody at the TV. Not PASS: stop.
9. The board's two checks, as ADD_GAME_TASK.md's standing rules name them — not PASS: "YOU, now: in the board's repo
   pull the PC side's latest, then send the read line again", then close.
10. `solo <code>` — it sets the board to offer only this title. Pass its "YOU, now:" lines to the user one by one. If
    the user is not at the TV: close; solo can run alone on a later read line. When the user says who won:
    `solo <code> --read --winner <seat|draw>`. If the user says the hub got it wrong, record their words; that is the
    result of the test, not a fault of theirs.
11. `close <code>` — always last, also after any stop.

**Stop** = one plain sentence (the cell not met and by how much, from the stage's page), then close. Never run a stage
again with anything changed to make it pass.

## The record and the end

`docs/memory/evidence/ADD_<code>_<date>.md` (a letter after the date when that page exists): each stage's verdict in
order as the tool's last line says it, plan's rows, train's gate cells, solo's switches and its result cell, the
user's words verbatim (titles replaced by the code). Your last reply: the verdicts in order, then "YOU, now: commit"
with the exact line: `cd ~/Projects/onn-stream-test && git add -A && git commit -m "ADD <code>: <the verdicts in a
few words>" && git push`.
