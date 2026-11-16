---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AN) — behind PRIVYHUB_H7=1 only (absent / 0 = today byte for byte, proved through the real HTTP route against HEAD d61f9b56's companion): a start over a running watch **replaces** it (the load again, one row `replaced`; never H7-V2's refusal); **`recognised`** in `h7-result` — after a start with the load the watcher must read the start screen itself within **8 s**: true / false / null (false = the picture in front of the hub is not this game's start: nobody may be sent into a match); **`POST /plugins/games/h7-stop`** (the game untouched, one row, idle after); **`h7-start?keep=1`** keeps every picture the watcher reads (JPEG + index.csv with the class and distances) under the git-ignored runtime/h7_frames/<game id>_<UTC stamp>/ — ~5.3 ms and ~5 ms CPU a picture, a 60-fps fixture's frames unchanged (3,600 / 3,600); **`last`** carries the thresholds and the spec's version; an old-measure spec → `no_spec` with B104's plain line. Tests through the real HTTP server on loopback: 12, 3 runs green; B103 (13), B99 (15), B101 (14), B102 (16), B104, the client contract (5) and B90 (10) green; mutations 13 / 13 caught. B103's test updated only where B105 changes its behaviour (disclosed). Nothing adopted; nothing committed. No title, code name, character name, path or picture in this record
---

# B105 — the watcher's gaps (`companion/h7_minigame.py`, behind `PRIVYHUB_H7=1`) (2026-11-16)

**Why (H7-V2):** A saw at the first reads after "ready" that the hub was not recognising the select screen, and the
user still played two matches — `seen_start` was true because the load was done, and nothing said the screen itself
was not recognised; after the missed end `h7-start` refused ("a mini game is already being watched") until the user
ended the game and launched again; A's hand-made picture keeper looked up the window by the wrong process for 34 s.
**Baseline:** HEAD `d61f9b56` + B104. **Design** hashed 04:43:18Z, before code (`b105_2026-11-16/design.sha256`); no
amendment.

## What it does (with the flag; absent / 0 = today)

- **A start while a watch is on replaces it.** The start goes through every other check first (no game, no spec, the
  system, no state, the stream down, a bad `load` / `keep` word — **the other refusals stay, and a refused or failed
  start leaves the running watch as it was**), then the load, then — under the watcher's lock — the old watch is
  dropped (its thread stops at its next second without another row; rows are written under the lock, so none of the
  old watch's rows can follow) and **one row `replaced`** (the old watch's reads, class, seconds) comes before the new
  `watching` row. The answer carries `"replaced": true`. Starts are serialised (a start lock). A finished (`ended`)
  watch is followed by a new start as before, with no `replaced` row.
- **`recognised`** (`RECOGNISE_S` = 8 s, stated: ~8 reads, room for RetroArch's own notice after a load): after a start
  with the load, `null` until **a read names the start class** (one read: a class is named only under its threshold and
  with the margin) → `true`, or **8 s pass since the watch began without one** → `false` (pictures that cannot be
  grabbed count as time passing). With `?load=0`: `true` once a read names the start class, else `null` — never
  `false`. **Settled once; one row `recognised`** (value, seconds, reads, the read's class and distances); the watch
  goes on (an `ended` is still said). `h7-start` still answers at once; `seen_start` stays as B103's.
- **`POST /plugins/games/h7-stop`:** a watch (watching or ended) → dropped, **one row `stopped_by_call`**, answer
  `{"ok": true, "watch": "stopped", "game", "reads"}`; **nothing is sent to the game**; `h7-result` → `idle`. No watch →
  `{"ok": true, "watch": "none"}`, no row.
- **`h7-start?keep=1`:** `runtime/h7_frames/<game id>_<UTC stamp>/` (git-ignored — `runtime/` in `.gitignore`;
  `git check-ignore` proved in the test on the repo), **every picture the watcher reads saved as it was read** (the
  window picture before any cut; JPEG quality 90; `f000001.jpg`, …) with **`index.csv`: `seconds,utc,file,class,screen,
  margin,distances,keep_ms`** — a run B104's `learn` / `score` / `replay` read directly once labels are beside it. Off
  unless asked; `keep` other than 0 / 1 → 400 "keep is 0 or 1". A folder or picture that cannot be written → one row
  `keep_failed` and keeping stops (the watch goes on). The result and the `watching` row name the folder; `"keep":
  {"folder", "pictures"}` in the result. The picture of the read that ends the watch is kept too.
- **`last`** = `{"class", "distances", "margin", "thresholds": {"screen", "classes", "margin_needed"}, "spec_version"}`.
- **An old-measure spec:** `h7-result` → `{"state": "no_spec", "why": "this end-screen spec was learnt with the old
  measure (absolute grey levels): learn it again"}`; `h7-start` → 400 with the same line.
- **The route:** `plugins/games.py` passes `keep` to `h7-start` and adds `h7-stop` — both inside B103's
  `_h7_minigame is not None` (the module is imported only with the flag).

## The cost of keep=1 (`keep_cost.py`, `keep_cost_results.jsonl`; no game, no RetroArch; synthetic pictures)

- **Per picture** (the watcher's own `_keep`, a 1920 × 1080 RGB window picture, 60 times): **5.27 ms** median (worst
  5.45), **CPU 5.27 ms**, ~210 KB a JPEG.
- **A fixture's frames over 60 s** (a child process drawing 1920 × 1080 frames with numpy, paced to 60 a second) beside
  the watcher's work once a second in this process (B104's read of the picture, ± `_keep`), twice each: **without
  keeping 3,600 and 3,600 frames; with keeping 3,600 and 3,600**; the watcher's CPU over the 60 s 434 / 430 ms without,
  735 / 758 ms with (≈ +5 ms a second). Temp dir removed.

## Tests (`tests/b105_h7_watcher/`, 12; B103's harness through the real HTTP server on loopback)

The child `python3 -I` on B82 / B83's fixture tree, the companion's handler on a ThreadingHTTPServer at 127.0.0.1:0,
network beyond loopback blocked, B101's fake RetroArch with its command log, the fake picture source (B102's synthetic
tallies), a spec learnt in the test with B104's tool; `RECOGNISE_S` scaled to 1.6 s at 0.2-s reads (8 reads).

- **Replace:** a start, 5+ reads of a fight, a start again → `replaced` true, **two loads** in the fake's log, **one
  `replaced` row**, after it only the new watch's rows; the new watch ends rightly (`end_P2`, 6 reads, `recognised`
  true).
- **Not recognised:** the load done and the fake showing an unseen tally (1-1) → `recognised` **false** at 1.6-2.2 s,
  `watching`, **no `ended`**; the same with a fight; the same when no picture can be grabbed (`reads` 0, the failures
  counted).
- **Recognised:** the start shown → true within 2 reads. **load=0:** null past the 1.6 s through a fight, then true.
- **Stop:** `{"watch": "stopped"}`, `idle` at once and a second later, **nothing in the fake's command log after the
  call**, one `stopped_by_call` row; a second stop → `none`; a stop with no watch at all → `none`.
- **keep=1:** one new folder named `<game id>_…`, `index.csv` with the header above and one row per read, the JPEGs
  `f000001…` one per read (the ending read's included), the distances column agreeing with `screen`; **absent → no new
  folder**; **`git check-ignore` on the repo for that shape → ignored**.
- **`last`:** exactly class / distances / margin / thresholds / spec_version; version 2.
- **Old measure:** `no_spec` with the plain line; the start refused with it. No `.state8` left.
- **The flag absent and `0`** (`FlagAbsentIsToday`): `h7-result`, `h7-start`, `h7-start?keep=1` and **`h7-stop`**
  answer as **`git archive d61f9b56`'s companion**, code and body byte for byte ("Unknown Games plugin POST action:
  h7-stop"); the launch the same.
- **B103's test updated where B105 changes B103's behaviour** (disclosed; `test_b103.py`, five places, 15 diff lines):
  its two "a mini game is already being watched" refusals → `replaced` (200), the first case's command log → two loads,
  the second's replacement watch given a start then a 1-0 (it ends `end_P1` after 6 reads), `last`'s keys a superset.
  Everything else in B103's test unchanged.
- **Results:** `tests_x3.txt` — **3 runs, 12 / 12 each**; once: B103 13, B99 15, B101 14, B102 16, B104 15 (the
  snapshot's B104 tests at that time; B104's 19 run in B104's own batch), the client contract 5, B90 10 — all OK;
  RetroArch left 0; temp dirs left 0. `tests_mutations.txt` — **13 / 13 caught** (replace, recognised never / wrongly
  false, any screen as recognised, stop leaving the watch on, keep ignored / unasked, `last` without thresholds, the
  old-measure line wrapped, the ending picture not kept, the stop route gone, `keep` not passed by the route, failed
  pictures not counted as time). **Disclosed:** the batch's background run was stopped by the session's 30-minute
  limit during the last mutation (N13); its 7 temp folders (its own work copy and its tests' fixture trees) were
  removed by me and N13 run again alone (caught).

## Disclosed

- **A slip of mine while writing the code:** a scripted edit replaced an empty string (my slice's end marker matched
  an earlier `_row` in the file) and wrote a 2-million-line file; seen at once (it did not parse), the file restored
  from HEAD (`git show HEAD:…`, compared with my saved copy: equal) and the edit redone with the slice checked. No test
  or companion ever read the broken file.
- The first run of the new test found a real bug (the picture of the read that ends the watch was not kept: the
  keeper looked for a watch still `watching`) — fixed (`_mine`), and the test's own slip (an ended watch is shown until
  the next start or stop, so the old-spec case stops it first).
- The keep cost is a fixture's, not a game's: no RetroArch or title was started.
- The mutation runner is B101's with one change (several suites; here one).

## Files

`b105_2026-11-16/`: start files, the design + hash, `b105.diff` (applies on `d61f9b56` + `b104.diff`),
`diffs_apply_in_order.txt`, `sha256_before_after.txt`, `keep_cost.py` + results, `tests_x3.txt`,
`tests_mutations.txt`, `scripts/` (`run_all.sh`, `mutate.py`, `mutations.json`), redact / title checks,
`manifest.sha256`. Patch note: `patches/B105_H7_WATCHER_GAPS.md`.
