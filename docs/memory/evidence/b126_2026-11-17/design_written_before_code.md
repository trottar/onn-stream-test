# B126 — both readers taught the unlocked select screens: the design (written and hashed before the evaluation script)

T88 = H7's 2-player PS1 title (the duel); T89 = the users' N64 four-player title (the round's end). No title, character
name, cheat name, game id, serial, path or picture in this folder. Every picture outside git, read only; nothing
written beside them; every spec learnt here lives in memory or in `~/.cache/b_q30as_tmp/` (scratch, mine), never the
rules folder.

**Disclosed before this design:** one `tools/h7_endscreen.py score` of the rules folder's T88 spec (read in place, its
sha256 equal to H7-V3's `06058b7b…` / `922415bc…`) on the c2 labels, and one look at two c2 pictures (4 and 8) to see
why pictures 4-7 read `unknown` (RetroArch's notices over the screen; nothing copied). Both are the queue's first
question; the evaluation below repeats that score from a spec learnt in memory and records both.

## Sources (Cowork's labels, unchanged)

- T88: **V1** = H7-V1's screenshots (`t88/`, 640 × 525, locked grid); **LIVE** = H7-V2's window run (1920 × 1080, locked
  grid); **C2** = H7-C2's T88 run (1920 × 1080, every select screen **unlocked**; `other` = the kept mid-fight state).
- T89: **C1** = H7-C1's run (960 × 720, locked, five matches); **T89C2** = H7-C2's T89 run (960 × 720; `start` pictures
  4-41 unlocked, 86-102 locked; `end_r1234`; no `other`).

## T88 (spec version 2 — the tool's learner as it stands; no place rows)

1. **H7-V3's spec as it stands** (learnt from V1 + LIVE — in memory, checked equal in every number to the rules folder's
   spec) **scored on C2:** per class right / total, `unknown`, wrong class, `other` read as the screen; the screen and
   class distances of the C2 screens against the thresholds. The plain answer: does it read the unlocked start,
   end_P1, end_P2?
2. **Learnt from all three** (V1 + LIVE + C2) → the learn report (screen and class gaps, thresholds, margin needed, the
   masks' sizes and the outcome mask's box, `unlike_label`) and the score **per source**.
3. **Folds:** learnt without C2 (= 1.) → C2; **learnt without LIVE (V1 + C2) → LIVE**; also learnt without V1 (LIVE + C2)
   → V1. Every arrangement: `other` read as the screen (must be 0) and wrong classes (must be 0).
4. **B104's tone grid** (its 27 variants, unchanged) on the held-out C2 pictures under the spec learnt without C2, and
   under the V1 + LIVE + C2 first-halves spec on C2's second halves: readings changed, misread, `other` as the screen.
5. **One spec or one per setup:** one spec if, learnt from all three, every class is separable, every source reads
   with 0 wrong classes and 0 `other` as the screen, and its numbers per source are no worse than H7-V3's on V1 / LIVE
   apart from range-edge pictures. Else a spec per setup: the hub chooses `<game id>.<profile_id prefix>.endscreen.json`
   when the session's `cheat_session.profile_id` is set and that file exists, else the normal spec (built in B127 only
   if needed).

## T89 (spec version 3 — B122's learner as it stands)

6. **C2 held out:** B122's all-five spec (C1 alone, in memory; checked equal to B122's numbers) → T89C2's pictures:
   the unlocked start (4-41), the locked start (86-102), the results row.
7. **Learnt from C1 + T89C2** → the learn report (screens, the row, the places, the margins) and the score per source:
   the unlocked start read, the locked start still read, the results as B122 (139 / 139, every place right), `other`
   as the screen 0.
8. **C1's five folds again** (B122's stretches: each match held out) **with all of T89C2 in training** → each held-out
   match: rows right / unknown / wrong, places wrong, `other` as the screen.
9. **B104's tone grid** on T89C2's held-out pictures (6.'s spec).

## Replay (the tool's `replay`, K = 3, and per load)

10. The tool's replay (one Reader, `Ended` re-armed after each end; the start must be seen again) on **C2 (T88)** with
    the three-source spec and on **T89C2** with the C1 + T89C2 spec; and **per load** — the stretch of each end load
    read from its load line with `Ended.start_loaded()` first, as a hub watch begun with the load is: when `ended`
    would be said after each end load, its class / places, the seconds after the first end-labelled picture.
11. **The earlier runs unchanged:** the three-source T88 spec on LIVE (B104 / H7-V3: `ended` end_P1 at 153.03 s and
    end_P2 at 420.03 s, nothing else) and the C1 + T89C2 spec on C1 (B122: five ends, the right rows, within 2 s); the
    answers compared with the earlier specs' replays line by line.

## Tool

`tools/h7_endscreen.py` unchanged unless a step above cannot be run with it; any change then gets its own amendment,
hashed before it is written, a patch file and its tests. One JSON line per result in `results.jsonl`; the script in
`scripts/`. Pictures read by a fresh Reader each (as `score` does); 6 worker processes, `nice 10`; TMPDIR on the main
disk.
