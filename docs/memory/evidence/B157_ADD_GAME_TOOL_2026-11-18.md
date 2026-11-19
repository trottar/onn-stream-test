---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue BB) — tools/party_add_game.py, one command per stage (register, learn, bench, solo, close) for a title known only by its code; every bar in the tool with its source; exit 0 only on PASS; a verdict and a page per stage; refused without the stage before; the same verdict twice, nothing rewritten; no run-time name written or printed. No companion change (a title it adds is listed only under both bench flags). With it handoffs/ADD_GAME_TASK.md and handoffs/ADD_GAME_PROMPT_TEMPLATE.txt. Tested on made-up titles through the real HTTP server; T88 and T89 described read only. Nothing adopted; nothing committed
---

# B157 — the add-a-game tool

Queue: `handoffs/QUEUE_2026-11-18BB.md` §B157. The directory is `b157_2026-11-18/`: the design + `.sha256` (hashed
01:30:00Z, before any code), `b157.diff` (applies on top of `b158.diff`), the runs (`tests_x3.txt`,
`tests_recent.txt`, `tests_others.txt`, `tests_mutations.txt`), `scripts/`, the checks, `manifest.sha256`. Patch:
`patches/B157_ADD_GAME_TOOL.md`.

## What it is

`python3 tools/party_add_game.py <stage> <code> …` — the stages, cells and bars as the design says; the run-time
places replaceable by environment (the tests use them). **Exit codes:** 0 PASS, 1 FAIL, 2 refused / usage, 3 waiting
(solo's lines). **Written:** `docs/memory/evidence/add_game/<code>/<stage>.json` + `<stage>.md` (only when the bytes
change); the private binding, the kept copies of the user's slots and the pictures in `~/privyhub_h7/add_game/<code>/`
(off the repo, beside the rules); the title's rules (spec, begin, sidecar) only when learn PASSes, never over another
title's or another input's file; the two flag drop-ins (bench on, close off). **Every text written or printed passes
the guard** (the run-time title, words, game id, profile id, the home, rules and project paths): a hit refuses with
nothing written.

**The bars** (`BARS`, each with its source): margin_needed ≥ 0.0796 (T89's kept spec, the lower of T88 0.0921 / T89
0.0796); held-out frames read as another class 0 and `other` read as a screen 0 (T88, T89); unknown ≤ 10.5 % (T88's
worst source, 34 of 38); `places_wrong` 0 (T89); ended ≤ 2.0 s after the first end picture (B122 / H7-V4); start
recognised ≤ 8 s (`RECOGNISE_S`); `prepare_s` ≤ 6.0 s (H7-V6b, T89's); ≥ 5 PAUSED reads, all PAUSED (PP-H4 part 1);
ended ≤ 8 s after a hand load (H7-V5); switch ≤ 1.6 s, arrival gap ≤ 1200 ms (B153); sound within 4 s, underruns
≤ 20 a row (B150); 20 lines with the flags, 18 without.

**A title already in the rules folder** (T88, T89 — `register … --rules-players n`): register and learn write their
verdicts from the folder as it is (the spec's own numbers, the begin and sidecar as the listing needs them; the rules
never written); **bench is refused** (its bench was its own task's part 1, PP-H4); **solo follows learn's PASS** and,
like bench for a new title, puts the two flags on before its lines (twenty lines, else refused with nothing asked of
the user). This is B161's way: the tool's solo on T88 as it is. (Found while writing B161, after the design was
hashed: the design's solo followed bench only.)

**Never a restart in the user's own session:** bench, solo and close write or remove the flag drop-ins and restart the
companion only when no client stream is up and no game but the board is running (the hub's own `native-stream-status`
and `status`); else refused, nothing changed. (Added after the three runs below, with its test and mutation.)

**Labels from the state each picture came from, never by eye:** the begin run `start`, an end state's run its class, an
`other` run `other`; a begin / end frame whose 64×48 grey copy moved ≥ 0.20 from its run's first frame is `ignore` —
**B140's measure (`BEGIN_MOVED`), disclosed: the design named the learner's `DIFFER_R`; B140's share-of-cells measure
was used instead (the hub's own "the screen moved" test), the bar the same kind.** Consecutive frames of one label are
one range (the learner halves each range for learn / score).

**What a real run needs that the tests do not exercise (disclosed):** learn's picture source on the hub
(`tools/party_add_game_capture.py`: B95's `Session` as H7-V1's frames, headless RetroArch, the null joypad, temp
folders) was not run here — no title may be started in this queue; its first real run is A's first new title. The
library lookup (`games?system=&q=` → `name`; `details` → `relative_path`; the game file `project/relative_path`), the
slot indexes and the setup's `cheat-profiles` answer are read as the hub's code builds them, and exercised against the
harness's companion.

## Tests (`tests/b157_add_game/`, 17)

| test | shown |
| --- | --- |
| WholePath (8; B114's harness, the `b157` mode in `tests/b157_add_game/b157_scenario.py`) | a made-up two-player PS1 title (T90, `winner`): register refused nothing, a missing state FAILs naming `end_P2`, learn refused before register, register → learn → bench → close **PASS** (bench: ready, PAUSED 6/6, no reload, keys_written, a practice by time and ready again, end_P1 → `[1, 0]` winner 1, end_P2 → `[0, 1]` winner 2, every file after = before); **the gates**: the title resumed during the hold → "PAUSED at every read" 2/6; a kept file changed → "every file after = before"; a second watch row → "no reload"; an end_P2 holding end_P1's screen (T91) → learn FAIL "every class separable"; bench **refused** after a kept state changed since learn; learn **twice → the same bytes, no file rewritten** (evidence and rules mtimes); a made-up four-player N64 title (T97, `places`, six saves in two rounds) → **PASS** through close; **no run-time name** (the made-up titles, ids, the temp root) in any file written or line printed |
| SoloReads (5) | a made-up hub on loopback answering that a client's stream is up: solo refused, no flag written;  solo's lines → exit 3, every line "YOU, now:", the two flags written (a made-up drop-in folder and a made-up `systemctl` — never the hub's); a title already in a made-up rules folder: register and learn written, bench refused, solo's lines; solo's read on made-up logs PASS; each bar FAILs alone — a switch at 1.8 s, a gap of 1500 ms, no sound, the band in a real game's encoder line, the board's lines out of order, a winner the user did not name |
| BarsAndGuard (3) | every bar the number of its source (the margin = the lower of the two kept specs', read only); a PS1 title's four-player setting read from the hub's controller overrides (`games` → id → `ps1_multitap`); the guard refuses a name |
| Described (1) | **T88 and T89 from the hub's rules folder as it is: register and learn `--check` PASS, nothing written** (the folder's sha256 and mtimes before = after; no home or evidence folder made) |

Disclosed about the harness: its child's `-c` text reached the kernel's 128-KiB limit for one argument (135,773 bytes)
with the new mode inline, so the `b157` mode is its own file run by the scenario (127,400 bytes after). The stand-in
board needs its own relaunch step between benches (`board_up`), and the child's `subprocess.Popen` is the fake title,
so the scenario hands the tool a fresh `subprocess` (as B143's set-up does).

## Runs

**B157 (15 then) and B158 (6): three runs each, all OK** (`tests_x3.txt`); then two fixes and two tests: the PS1
four-player setting's lookup (my first code read the overrides file's top level — it is `games` → id; found writing
B159, a branch the made-up titles do not reach) and the no-restart guard; **B157 (17) once more after each, OK**
(`tests_b157_after_fix.txt`). The recent suites once, all OK (`tests_recent.txt`: B155, B153, B151, B148, B147, B145,
B144, B143, B141, B140, B139, B137, B134, B133, start_rung, encoder_rc; B148's and B139's one skip each); the earlier
suites once, all OK (`tests_others.txt`, 41 suites) but `art_systems`' docs test in the work copy (no `docs/` there) —
**120 / 120 against the repo** (`art_repo.txt`). **Mutations 8 / 8** (`tests_mutations.txt`): the margin bar loosened,
the predecessor gate skipped, the PAUSED and files cells always met, the guard off, the no-restart guard off, the
winner's seat as the port, `result` with `scores` listed. The older suites' own temp dirs stay in my main-disk scratch
(155, two of them from a run I stopped).
