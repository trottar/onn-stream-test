---
memory_schema: 1
as_of: 2026-11-21
status: BUILT (B190 settled — T91's own start holds still and serves as the begin, recognised by its own still picture; `winner` failed at the screen gate itself; B191 the `letters` result kind behind both bench flags — register --result letters --word, two players, the label stage reads each player's corner, learn reads the real saves only (left-out included, a moving screen never ended), the hub's listing a winner entry; B192 synthetic pictures train the reader until every held-out one is read, never counted toward a pass; B193 the task's words) — T91 from its six kept saves, in a scratch: register PASS, label PASS (19 cells), learn PASS (20 cells); no bar lowered; nothing adopted; nothing committed
---

# B190-B194 — a word spelled by the player who lost, read in each player's corner

Queue: `handoffs/QUEUE_2026-11-21BJ.md`. The directory is `b191_2026-11-21/`:
- the design + `.sha256` (hashed 2026-11-21T16:30:33Z, before any code); the addendum after code + `.sha256`;
- `t91_settle.txt` (B190) and `scripts/t91_settle.py`; `t91/` (register, label, learn pages; `tool_lines.txt`);
- `flag_proof.txt`; `tests_runs.txt`, `tests_mutations.txt` (+ `tests_mutations_first_run.txt`); the checks;
  `scripts/`; `b191.diff` (applies on `13646e06`), `apply_check.txt`; `template_sha256.txt`; `manifest.sha256`.

Patch: `patches/B191_LETTERS_KIND_SYNTHETIC.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty; T91's record
committed (`13646e06`).

**The exception (B190 / B194): not used.** The picture source never ran: T91's pictures in the tool's folder were made
from exactly its six kept states (`made_from.json` = the states' sha256), so they and a scratch copy of that folder
served B190 and B194. The real T91 folder, the rules folder, the user's slots and the kept H7 folders only read.
Register's library lookup asked the companion for the title's entry (a read; the title from the scratch binding in
process, never on a command line or in an output). Pictures made for looking (contact sheets, crops) stayed off the
repo under a scratch folder in the home directory and were removed after this record.

## B190 — settled (`t91_settle.txt`)

**Every picture holds still.** The begin: 21 pictures over 19.5 s, identical from the first (B140's moved share 0.000).
Each end save: identical from 0.5-1.0 s on (its first half second fades in by 3-5 grey levels; moved share at most
0.014). The mid-match save: black at the load, then held from 3.0 s.

**Where the letters sit** (640 × 480 of the game's area): player 1's under its header top-left (box x 45-166, y 81-113),
player 2's top-right (x 469-590, y 80-112), the same place in every save. A letter is about 28 × 22 px (W) or 19 × 22
(O); a not-yet mark about 8 × 6. The string is centred under the header: `---` spans x 90-122, `WOW` x 64-145.
P1's letters are blue, P2's pink, each with a dark shadow.

**How the backgrounds differ:** each end screen is shot from wherever its match ended. end_P1 and end_P1_2 share 32 %
of their pixels (the screen's own text), their corners 8 % (P1) and 44 % (P2: its letters); end_P1 / end_P2 and the
like 19-32 % (corners 2-4 %). end_P2 and end_P2_2 ended at nearly the same spot: 59 % the same, P1's corner 99.9 %
(a plain sky both times).

**Why the begin was never recognised:** not the begin's fault. Under `winner` every screen shares one screen mask and
the ending is told by what is steady inside it. With every end screen over another background, the mask kept 9.7 % of
the picture (mostly the screen's text), and **the screen gate itself could not be learnt**: the screens' own worst
distance 0.221, the mid-match save 0.093 (it is the begin's picture with other text in the middle) — a gap of -0.128,
"not separable", the spec unusable, every read `other`: the begin included.

**The begin as the user made it serves.** Learnt as its own still picture (B122's one-screen learner against the
mid-match save and the end saves, the pixels it shares with them left out): own 0.0, nearest other 0.274, threshold
0.137 (360 px of its middle text). With B137's top-right corner black (the hub's paused read masks RetroArch's
"Paused."): 0.265, threshold 0.133 — the same either way, so a paused load reads as the begin. **The hub needs
nothing else from the user**; T91's game stays as it is set up.

## B191 — the `letters` kind (built)

- **register** `--result letters --word <the word>`: the word kept in the binding and the spec; two players only. Four
  players are refused, and the cell says why: the player who spelled the word lost, but which of the other three won is
  not on that screen; winner-only would name a winner the game never showed; the hub could honestly report only "port k
  lost", and the board has no such result.
- **label**: the session reads each player's corner on two pictures of every end save (`end_P1=---/WOW,---/WOW`, `-` a
  not-yet mark, `_` nothing). Checks: the two readings the same; each corner fits the word; the role agreeing (end_P1:
  P2's letters spell the word, P1's do not); the corners at one place; read back by a reader learnt without that save;
  the last look (`label/letters.png`).
- **learn**: spec version 5; the gates read the real saves only — begin recognised within 8 s and never ended; other
  never ended; each end save ended as itself within 2.0 s; **a moving screen never ended** (each end save's corners
  over the title's other saves' pictures, a new one every read); **left out**: each end save read by a spec learnt
  without it, its letters exactly; B176's same-picture cell.
- **The reader** (hub): both corners read; exactly one spelled → `end_P<the other>`; none → other (or the begin by its
  own picture); both → unknown; a corner not read beside a spelled one → unknown with `end_unread` (B182's give-up: no
  result). A word spelled is never the begin. On a moving screen the same end is never read twice in a row, so the
  three agreeing reads of B102's `Ended` need a still screen — and still end 2 s after the first.
- **The hub's listing:** a sidecar `"result": "letters"` with a version-5 spec → B158's winner entry. The reader is in
  `tools/h7_endscreen.py`: **the running companion reads a letters title only after its next start** (session A's
  bench restarts it).

## B192 — synthetic pictures to train, never to prove (built)

- **The cut:** the letters' pixels by two cues — the pixels the same in another save showing that player's same letters
  over a different picture, and the pixels off a plain corner's commonest colour; dark pixels (the shadow) never; a
  found string whose pixels stay the same under other letters is the screen's own text (T91's `PLAYER 1` header).
  Then the colours (chromaticity) as common among the letters as `ratio` × among the backgrounds.
- **Made:** each real end save's letter pixels put back, moved up to ± 2 px, over patches cut from the title's own
  pictures (the begin, the mid-match save, the other end saves) at a random place and scale 1.0-1.4 — never over a
  letters box, the end screens' fixed text, or a patch holding the game's other text. A fixed seed from the saves'
  own pictures and readings: the same saves give the same set.
- **Trained:** 8 held-out pictures per end save made first, never trained on; rounds of 16 per end save; the colours
  from the real and training pictures' letter / background pixels, the shapes from real glyphs and the training glyphs
  a real-only reader already reads as that letter; the least ratio of 5 / 10 / 20 / 40 that reads every real save and
  every held-out picture. **T91: 32 held out, 64 trained, from 6 pictures of the title, one round, ratio 5, every
  held-out picture read; the letters learner with its training 2.4 s of learn's 19 s** (the rest is the left-out learns and the replays).
- **Never proof:** no gate reads a synthetic picture; the training's own bar (`synthetic_held_wrong_max` 0, added to
  `BARS`) can fail learn, never pass it. Mutation M1 (the left-out cell met by the training's result) is caught.
- **What synthetic training cannot fix:** a letter no real save shows (no pixels to paste: never read, no result);
  a background in a player's letters' own colours behind its corner (learn says so and that more saves would not help;
  at the hub no result); a corner no save shows cut clean (only a save can — the line says which).

## B193 — the task (done)

`ADD_GAME_TASK.md` §1: "a word spelled by the player who lost (letters in each player's corner)" → `--result letters
--word <the word>`; the begin as B190 settles (the user's own start kept when it holds still; never ask the user to
change how the game is set up); the label lines for letters word for word. §2's label stage points at them. The
template unchanged (`aadccb04…`, `template_sha256.txt`).

## B194 — T91 (scratch, no new save; `t91/`)

| stage | verdict |
| --- | --- |
| register `--result letters --word WOW` (no `--collect`) | **PASS** (10 cells) |
| label, no readings | FAIL — its line asks the readings |
| label, my four readings | FAIL on the last look only (19 cells): two readings the same, each corner fits, the role agreeing, the corners found, each read back by a reader learnt without it |
| the last look | `look=all` — every tile its row's letter (`-` 10, `O` 4, `W` 10) |
| label | **PASS** (19 cells) |
| learn | **PASS** (20 cells) |

My readings, from both pictures of each save: end_P1 and end_P1_2 `---/WOW`; end_P2 and end_P2_2 `WOW/W--`. learn: the
begin recognised at its first read; each end save ended as itself in 1.5-2.0 s; the mid-match save never ended; a
moving screen never ended (with the moving rule off in memory, the same replays end: the gate bites); each left-out
save ended as itself in 1.5-2.0 s with its letters exactly. The pages were made again with the final code (the tool's
lines in `t91/tool_lines.txt`); the sheet looked at again then.

**learn passes: stopped there.** Bench and solo are session A's with the user; A runs register, label (the same
readings, then the last look) and learn on the real folder.

## Tests and mutations

- `tests/b191_letters/` (new, 14): see `tests_runs.txt` — three runs OK; the touched suites once each.
- Mutations 4 of 4 caught (`tests_mutations.txt`): M1 a synthetic picture counted as proof; M2 a background read as a
  letter; M3 a guess when neither spelled; M4 a moving screen taken. **Disclosed:** M3's first form was not caught — its
  line became reachable only when a word is spelled (addendum 5) — and was rewritten as two changes, then caught.
- **Disclosed:** the made-up title's noise follows a state counter; each test starts it at 0 (B185's way). At one
  counter (the suite's order before pinning) the odd-colour title's second left-out save also failed to train — learn
  FAILs there too, for the right reason; the test asserts end_P2_2's left-out cell fails and only left-out cells do.
- The design changed after the hash in six places, each from a test or a T91 left-out run: the addendum.

## The three checks

`redact_check.txt`, `id_check.txt`, `title_check.txt` (BI's, reused) and `t91_check.txt` (T91's binding's names, loaded
in process, never printed) over every file this queue wrote: see the files.
