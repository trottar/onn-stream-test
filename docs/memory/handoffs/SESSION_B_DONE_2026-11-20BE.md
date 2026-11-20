# SESSION B — done, 2026-11-20 BE (QUEUE_2026-11-20BE: B171 several saves per ending, learn's line for one more save; B172 the solo mark ends at close; B173 the fixed task; B174 the bare board's measurement for A; run ~00:20Z-01:47Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (user units; none system-wide); `git status
--short` empty (queue BD committed in `6d4a6c44`).

**The queue's exception, used once:**
- `python3 tools/party_add_game.py rehearse T88 --collect other=2` at 00:54-00:57Z, after `status` and
  `native-stream-status` showed nothing running and no client.
- Headless (the window on the hub's display, nothing streamed), no companion restart, no flag set.
- The user's slot 2 and the kept folder were only read. **The tool now keeps a copy of slot 2** in T88's own add_game
  folder (`kept/other.state`, off the repo; B171).
- The run and its verdict are in `evidence/b171_2026-11-20/runs.md`. The real rules folder: 15 files, 0 changed. My own
  check of the kept folder and the rules folder together (22 files): before = after.
- Nothing else started a title.

**Rules kept:**
- No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive.
- Read only: the users' setups, slots and in-game saves, the kept H7 folders, the rules folder and `runtime/` pictures.
- No Godot run. No change in the board's repo. No bar in `BARS` changed; the learner (`h7_endscreen.py`) not changed.
- No title, id, path or picture in any record (the three checks).

**Disclosed:**
- One directory listing of the rules folder printed, **to my own terminal only**, the two setups' 12-character state-name
  prefixes. They were never written to any file; the id check passes on everything written.
- The tool's own page `add_game/T88/rehearse.*` in this repo now holds this run's verdict.
- The made-up experiments, the /tmp work copy (companion/, tools/, tests/, PrivyHub/'s tracked sources) and
  my scratch on the main disk are off the repo; no picture was kept.

Nothing adopted; nothing committed in either repo.

## What the learner needs to tell two near-alike end screens apart — in one line

**Every ending seen in at least two different matches whose incidental look differs** (other characters or another
stage): then what changes with the match has a spread and drops out of the outcome mask, and only what tells who won
stays. More pictures of one save, or two saves of one match, change nothing.

## B171 — BUILT (`evidence/B171_ADD_GAME_MORE_SAVES_2026-11-20.md`, `b171_2026-11-20/`, `patches/B171_…`)

- **Roles:** `end_P<k>`, `end_P<k>_2` … `_4` (and `end_r<row>_2` …), each one more source; the cap
  (`SAVES_PER_ENDING_MAX = 4`) sits beside `BARS`, not in it.
- **register:** two per ending from the start.
- **learn:** one plain line naming the next save, word for word: "One more save: end_P1_3 — the screen after a match
  player 1 won, from a match not saved yet (other characters or another stage than its saves kept); save it to a free
  slot, then register <code> … --collect end_P1_3=<slot> and learn <code> again." At four saves an ending: "The end
  screens cannot be told apart this way: … Instead: another mode whose end screen shows who won by player, or save each
  ending on another screen that shows it, and start the title's saves again." The same bars every time.
- **Pictures:** made only for an added save.
- **rehearse:** takes a kept extra the real rules end on as a source, keeps the saves it collects, and carries learn's
  line.
- **bench:** benches every save as its ending.

**T88's kept `end_p1_b` / `end_p2_b`:** mid-fight saves, never an end screen, so not second sources.

**rehearse T88, as I ran it: FAIL.**
- **On learn's own bars:** separable [end_P1, end_P2], margin_needed 0.0165 (bar 0.0796), held-out unknown 0.6552
  (bar 0.105), and the endings' replays.
- **The usable kept endings are end_p1 / end_p2 only.**
- **The line:** "One more save: end_P1_2 — … then rehearse T88 --collect end_P1_2=<slot>." Below two saves per ending:
  end_P1_2, end_P2_2.
- **T88's own rules untouched.**
- **T88's rehearsal needs** the user's `end_P1_2` and `end_P2_2`, each a match with other characters than the kept
  ones, under its setup, saved on the select screen with the tally to slots 2 and 3. Then up to `_4` each as the line
  asks. The made-up title of T88's shape passed on exactly those two.

Tests 10 ×3 (with B172's 2); B163 7 ×2, B169 5 ×2, B157 17, B162 17, B167 9 — all OK, temp dirs 0. **Mutations:**
11, each caught by some suite (`tests_mutations.txt`, `tests_mutations_2.txt`). **Not caught by B171's own suite: the margin cell alone always met.** The one-save near-alike case also fails separability and unknown there; B163's test_3 catches it. Learn's three bars off together is caught by the near-alike test.

## B172 — BUILT (in B171's record and diff; `patches/B172_SOLO_MARK_ENDS.md`)

close ends `solo_mark.json` and the files' and in-game saves' befores; register ends a mark an earlier use left (T88's
add_game folder holds the first use's from 11-19 — the next `register T88` ends it). A later solo reads only its own
rows. Tests 2; mutation caught.

## B173 — DONE (`handoffs/ADD_GAME_TASK.md`; the template unchanged, sha256 `4ba6a99a…` before = after)

- **Rounds:** two per ending. With no setup, rounds of three slots. Under a setup, rounds of two in slots 2 and 3; slot
  1 is never used.
- **The lines:** each round's line for the user, word for word.
- **One more save:** "YOU, now: play one more match of <the game> that P<k> wins, with other characters (or another
  stage) than any match saved so far, and save to slot <2 or 3> on the screen after it that shows P<k> won. Reply ok."
- **The cap:** "YOU, now: <the game> can't be added this way: after four saves of each player's win, its end screen
  still doesn't show the hub who won. If it has another mode whose end screen shows who won by player (P1 / P2, not the
  character), or another screen after a match that does, tell me and we start its saves again; otherwise it stays off
  the board." Then close, then commit.
- **§0 for T88:** the rehearse line is followed; rehearse keeps its saves.

## B174 — the bare board after a practice: the measurement for A (no code; an unattended item)

**What it settles:** B168 found by the code that neither board file draws a second of bare board after a practice; what
remains is what a grab of the board's own X window returns while the paused title's full-screen window is still mapped
above it (xfwm4's compositor, `unredirect_overlays` on). This grabs the board's window **by id, as the stream does**
(`x11grab -window_id`, B52's `grab_window` arguments), every 0.1 s for 2 s from the way back's start, and classes each
frame by numbers only. Nobody at the TV; no client stream (without one the way back's switch row says "the stream is
not up" — the start is then the `minigame_practice_end` row, the way back's first step; the windows above and below are
the same with or without the stream, which only runs a second grab of the same window). ~3 min. T88 (a title already
added; its flags put on and off by the tool's own `flags`, the companion restarted twice by it — A's).

**Before:** the A standing rules (the window, the preconditions, only the companion and diag active);
`curl -s http://127.0.0.1:8765/plugins/games/status` → `"active": false`, and `…/native-stream-status` → no client.

**The commands** (the repo root; the hub's display from the user manager, as the companion's RetroArch gets it; nothing
written to disk but the printed table — no picture kept anywhere):

```
export $(systemctl --user show-environment | grep -E '^(DISPLAY|XAUTHORITY)=' | xargs)
python3 - <<'EOF'
import os, subprocess, sys, time
import numpy as np
sys.path.insert(0, "tools")
import party_add_game as pag
pag._private_paths()
b = pag.load_binding("T88")
D = os.environ["DISPLAY"]
def win(pid):                                   # the process's visible window (the stream finds it by its process too)
    w = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(pid)], capture_output=True, text=True).stdout.split()
    return w[-1] if w else None
def grab(w, n, fps):                            # B52's grab, n frames at fps: 64 x 36 grey, in memory only
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-f", "x11grab", "-framerate", str(fps), "-window_id", w,
                             "-i", D, "-frames:v", str(n), "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"],
                            stdout=subprocess.PIPE)
def frames(p):
    return np.frombuffer(p.communicate(timeout=60)[0], np.uint8).reshape(-1, 36, 64).astype(np.int16)
print("lines with the flags:", pag.flags(True))
print("board:", pag._board_up())
bw = win(pag.hub("GET", "status")["body"].get("pid"))
ref = frames(grab(bw, 10, 5))                   # the bare board, 2 s, nothing above it
noise = max(float(np.abs(ref[i] - ref[i + 1]).mean()) for i in range(9))
bare = np.median(ref, axis=0)
r0 = len(pag.party_rows())
start, res = pag._held_ready(pag._token(b), "1,2")
print("held start:", start["code"], (res or {}).get("phase"))
pag.hub("POST", "party-minigame-go", {"practice": "1"})
pag._wait(lambda x: x.get("state") == "playing", 20)
tw = win(subprocess.run(["pgrep", "-n", "retroarch"], capture_output=True, text=True).stdout.split()[0])
while not any(x.get("step") == "minigame_practice_end" for x in pag.party_rows(r0)):
    time.sleep(0.02)                            # the practice ends by time (90 s); the way back starts
pb, pt = grab(bw, 20, 10), grab(tw, 20, 10)     # both windows, every 0.1 s for 2 s
fb, ft = frames(pb), frames(pt)
pag._wait(lambda x: x.get("phase") == "ready" or x.get("state") in ("ended", "given_up"), 30)
pag.hub("POST", "party-minigame-end"); pag._wait(lambda x: x.get("closed") or x.get("state") == "none", 20)
pag.hub("POST", "stop")
print("lines after:", pag.flags(False))
thr = max(8.0, 3 * noise)
print(f"the bare board's own frame-to-frame change {noise:.2f}; the threshold {thr:.2f} (grey levels, 0-255)")
print("| frame | s from the way back | to the bare board | to the title's own window | class |")
print("| --- | --- | --- | --- | --- |")
for i, (a, t) in enumerate(zip(fb, ft)):
    db, dt = float(np.abs(a - bare).mean()), float(np.abs(a - t).mean())
    cls = "title" if dt < thr and dt <= db else "board" if db < thr else "load screen (neither)"
    print(f"| {i} | {i * 0.1:.1f} | {db:.1f} | {dt:.1f} | {cls} |")
EOF
```

**The measure (name-free, nothing perceptual):** each frame of the board's window, 64 x 36 grey (B52's grab), its mean
absolute difference (grey levels) **to the bare board** (the median of ten grabs of the same window before the held
start, nothing above it) and **to the title's own window grabbed at the same tick**. **title** — under the threshold
to the title's window and no nearer the board (the grab returned the window above); **board** — under the threshold to
the bare board (the second of bare board); **load screen (neither)** — near neither: the board's window drawing
something else, which by B168's reading of the code can only be its load screen. The threshold: 8 grey levels, or three
times the bare board's own largest frame-to-frame change if that is more.

**The verdict:** the table of 20 frames as printed, in A's page; nothing kept but the numbers. Every frame `load screen`
→ the board's window holds the load screen across the way back (B168's reading confirmed; the flash is elsewhere —
the onn's decoder or the stream's restart); any `board` frame → the bare board is drawn for that long (the PC side's
screens to look at); `title` frames → the grab of the board's window returns the title's picture while the title is
mapped above it (the compositor; the stream's grab sees the same).


## What I would change (not done — the queue is the task)

1. **A cell that tests a match the spec did not learn from** (leave one save out: learn without it, read it, it
   must end as its own ending within the bar it has today). Learn's held-out split halves each save, so no bar tests
   another match. A made-up spec from three looks per ending passed every bar and still missed a fourth look, and
   one save per ending from matches with different characters passes on the characters alone. It adds a cell to
   learn, which is your and Cowork's call (the queue changes no bar).
2. **A save in the wrong role looks to learn like near-alike screens** (B157's T91: end_P2's slot holding P1's win).
   The line then asks for saves until the cap. When "held-out frames read as another class" is not met, the line could
   say "a save may be in the wrong role" instead.
3. **"From a different match" is the user's word only.** Two saves of one ending whose pictures are the same picture
   could be flagged as "the same match saved twice".
4. **bench now runs every save** (one held cycle each). With four saves an ending, bench could run one save per ending
   on the hub and read the rest as rehearse does.
5. From before, still open: the capture grabbing the window (about half the ticks give a picture — not what stops
   T88); the board's payout for a lone winner; B130's 15-s window; B114's harness size.

## Files

- **This repo:** `tools/party_add_game.py`.
- **Tests:** `tests/b171_more_saves/` (new: `near_capture.py`, `test_b171.py`, `test_b172.py`);
  `tests/b157_add_game/b157_scenario.py`, `test_b157.py`, `tests/b162_solo_safe/test_b162.py`,
  `tests/b163_rehearse/test_b163.py`, `tests/b169_solo_cells/test_b169.py` (updated, disclosed).
- **Handoffs:** `handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt` (one line), and this file.
- **The tool's own page:** `evidence/add_game/T88/rehearse.json` / `.md` (this run).
- **The record:** `evidence/B171_ADD_GAME_MORE_SAVES_2026-11-20.md` + `b171_2026-11-20/` (the design and its addendum,
  each hashed; `settle.txt`; `runs.md`; tests; mutations; the three checks; `b171_b172.diff`, which applies on
  `6d4a6c44`; `manifest.sha256`).
- **Patches:** `patches/B171_ADD_GAME_MORE_SAVES.md`, `patches/B172_SOLO_MARK_ENDS.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph).
- **Logs:** `logs/b171_git_status.txt`, `logs/b172_git_status.txt` (`logs/` is git-ignored).
- **Off the repo:** T88's add_game folder now holds `kept/other.state` (the tool's copy of slot 2).
- **The board's repo:** nothing.

## The user's part for a new two-player title (as the task now has it)

**Saves: 6 at the least** (the begin, a mid-match save, two wins for each player), **10 at the most** (learn may
ask for up to 4 more, one at a time, then it stops).

1. Tell the session which game the code is (in chat only; it is never written down).
2. Answer four things: two players; who won is shown on a screen after the match by player; whether the game has
   anything to unlock (if so, make its setup in Extras → Cheats first); the words to find it in Games.
3. Set the game to its shortest match (one round, items off), the same for every save.
4. Round 1:
   - **No setup:** SAVE to slot 1 on the select screen before anyone picks, to slot 2 in the middle of a match, and to
     slot 3 on the screen after a match P1 won.
   - **Under a setup:** don't save to slot 1 (it is the setup's start); slot 2 in the middle of a match, slot 3 after a
     P1 win.
5. Round 2: more matches, **each with other characters (or another stage) than any match saved so far**.
   - **No setup:** P2 wins → slot 1, P1 wins → slot 2, P2 wins → slot 3.
   - **Under a setup:** P2 wins → slot 2, P1 wins → slot 3; then round 3: one more P2 win → slot 2.
6. If the session asks for one more save, play one more match the named player wins, with other characters again, and
   save to the slot it names (2 or 3). At most four such asks.
7. Nothing during bench (unattended, a few minutes).
8. Solo: the pads on the onn; follow the session's lines (the one card, a practice, the match); say who won and whether
   the board showed one card.
9. If the session says the game can't be added this way, choose another mode or another screen that shows who won by
   player, or leave it off the board.
10. Commit.

**The user, now:** this repo — commit the tree (queue BE). The board's repo — nothing to commit.
