# SESSION B — done, 2026-11-25 BT (QUEUE_2026-11-25BT: B223 bench, solo and close on a surveyed title; read line 2026-11-25T02:20:11Z, limit 02:45:11Z)

**Stopped at the limit:** 02:48Z. **B223 not built.** Nothing in the code or tests changed. The only file this
session wrote is this one.

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BS and session A's T92 page committed (`4bad91a8`).

**Rules kept:**
- No title started. No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive; nothing deleted.
- T92's real folder not opened. Your slots, the rules folder and the kept H7 folders not touched.
- Nothing in `BARS` or the gates changed. T88-T91's rules not written, so before = after; they were not hashed.

## What was done before the limit: reading only (the sweep, not finished)

`tools/party_add_game.py` at `4bad91a8`:

| line | where | what it reads | for a surveyed title | kind |
| --- | --- | --- | --- | --- |
| 3195 | `cmd_bench` | `_numbers()` → `label_record()` (1290-1291) → the old `label.json` | **the bug: `None` for an ending the old label lacks, then `max(None)` at 3196 is the TypeError** | the same kind: to fix |
| 3116 | `bench_inputs` | `learn_inputs()` (old labels and kept saves) | not reached: `surveyed(b)` at 3113 takes `train_inputs` | guarded, nothing to fix |
| 1723 | `trained` (bench's `require`) | `learn_inputs()` | not reached: `surveyed(b)` at 1721 takes train | guarded |
| 3322-3323 | `solo_after` | learn's verdict and `learn_inputs()` | only for `described` titles (T88 / T89); otherwise bench's inputs, which are train's | another kind (a surveyed title is never `described`): report only |
| 3398-3405 | `cmd_solo --read` | the winner from the hub's `minigame_ended` row and `--winner`; `b["result"]` for `draw` | no old record read | none |
| 3481-3517 | `cmd_close` | `files_before.json`, `saves_before.json`, `register_inputs`; it removes `ask_folder()/<code>_*.png` | no old record read | none |
| 3199 | `cmd_bench`, not a score title | `_expected()` → the rules sidecar (`party.json`, written by train) | the new path's record already; it raises a KeyError if `side["scores"]` lacks the ending | another kind (item 3, no traceback): not built |

Not reached before the limit: `finish`, `saves_before`, `files_digest` and `ingame_saves` were read for reads of the
old record and none was found. The callees of `_held_ready`, `_scratch_load`, `_token` and `party_rows` were not read.

## The design that was to be written (not hashed, not built)

- A new function, `_bench_numbers(code, b, ending)`. For a surveyed title, `[int(x) for x in sides_of("score",
  party_steps.label_record(code)["saves"][ending]["readings"][0])]`. Otherwise `_numbers()`, as today. `None` when
  the number is not there.
- In `cmd_bench`: the expected numbers `None` → the scores and winner cells not met (bar "the label's reading"), and
  the loop goes on to the next ending. A KeyError or IndexError from `_expected` handled the same way. The stage ends
  with its verdict and page.
- Then a title without a survey runs differently only where it would have raised before. So the old-path suites would
  run.

## The command list as it now stands (unchanged since BS)

```
python3 tools/party_add_game.py register <code> --players 2 --system <ps1|n64|snes> --result <score|letters> [--word <WORD>] [--max-score <N>] --find "<the user's words>" --setup none --collect begin=1 --collect other=2 --collect end_P1=3
  PASS: register <code>: PASS (<n> cells)            [the new path: begin, other, one ending]
  asks: register: REFUSED — <n> titles match          [the whole name as the library lists it]

python3 tools/party_add_game.py survey <code>
  last line: survey <code>: look at survey/boxes.png (<n> numbered boxes, a grid every 40 px) — answer: survey <code> <kind> <P1: a box number or x0,y0,x1,y1> <P2: a box number or x0,y0,x1,y1>
python3 tools/party_add_game.py survey <code> score <P1 box|x0,y0,x1,y1> <P2 box|x0,y0,x1,y1>
python3 tools/party_add_game.py survey <code> letters <WORD> <P1 box|x0,y0,x1,y1> <P2 box|x0,y0,x1,y1>
  last line: survey <code>: look at survey/regions.png — answer survey <code> ok, or survey <code> again P<k>
python3 tools/party_add_game.py survey <code> ok
  PASS: survey <code>: PASS (5 cells)
  asks: survey <code>: mark P<k> again — survey <code> P<k> <a box number or x0,y0,x1,y1>

python3 tools/party_add_game.py label <code>
  last line: label <code>: read the regions on label pictures regions/<role>.1.png and .2.png — label <code> end_P1=<reading>,<reading>
python3 tools/party_add_game.py label <code> end_P1=<P1>-<P2>,<P1>-<P2>          [letters: end_P1=<P1>/<P2>,<P1>/<P2>]
  last line: label <code>: look at regions/look.png — label <code> look=all, or look=<symbol>:<i> for a glyph in the wrong row
python3 tools/party_add_game.py label <code> look=all
  PASS: label <code>: PASS (<n> cells)
  asks: label <code>: read again: <role>

python3 tools/party_add_game.py plan <code>
  PASS: Nothing more is needed.
  asks: Still needed: a final score with a <d> in it (either player).      [several: "… and a final score with a <e> in it (either player; one match may show more than one)."]
        [the whole ask — never seen, or seen once and not counted; the user's match saved to slot 2 or 3, then:
         register <code> … --collect end_P<the winner>_<n>=<slot>, label <code> end_P<the winner>_<n>=…, label <code> look=all, plan <code>]

python3 tools/party_add_game.py train <code>
  PASS: Nothing more is needed.            [after: train <code>: PASS (<n> cells)]
  asks: the same line as plan's

python3 tools/party_add_game.py bench <code>
  PASS: bench <code>: PASS (<n> cells)
python3 tools/party_add_game.py solo <code>
  last line: solo <code>: WAITING — after the user's reply: solo <code> --read --winner <seat>
python3 tools/party_add_game.py solo <code> --read --winner <seat|draw>
  PASS: solo <code>: PASS (<n> cells)
python3 tools/party_add_game.py close <code>
  PASS: close <code>: PASS (3 cells)
```
