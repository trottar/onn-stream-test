---
memory_schema: 1
as_of: 2026-11-24
status: BUILT (B205 synthetic training for the score kind, templates only; every gate on real glyphs). T92 learn on its six kept saves: FAIL on the two cells about 5 only — left out end_P2 now ends in 2.0 s (was 14.0, bar 2.0, met). Disclosed — the synthetic weight capped at the real glyphs' (not in the hashed design); training stopped at its round cap with 25 of 36 held out read. No bar lowered; nothing adopted; nothing committed
---

# B205 — synthetic training for the score kind (a 60-minute queue)

Queue: `handoffs/QUEUE_2026-11-24BO.md`; the read line 2026-11-24T17:10:03Z, the limit 18:10:03Z. The directory is
`b205_2026-11-24/`:
- the design + `.sha256` (hashed 17:10:54Z, before any code);
- the tests, the mutation, the checks, `scripts/`;
- `b205.diff` (applies on `9dc4cc10`), `apply_check.txt`, `manifest.sha256`.

Patch: `patches/B205_SYNTHETIC_DIGITS.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty; queue BN committed
(`9dc4cc10`).

## Built

- **The real glyphs pasted:** every labelled glyph on each save's first picture at its place — finals, period cells
  and stats rows — with its crop and its ink.
- **One synthetic glyph:**
  1. a real glyph of that key is scaled to one of the heights its group is drawn at (T92: 57 px finals, 15-17 px
     cells and stats);
  2. its ink is pasted over a patch of one of T92's own end pictures at a random place, moved by up to 1 px;
  3. it is made into a cell as a real glyph is.

  No digit is made that no real glyph shows.
- **Seed and rounds:** a fixed seed from the saves (B192's `letters_seed`). Held-out glyphs are made first (6 a key);
  then rounds of 12 a key, at most 4, until every held-out glyph is read by B178's rule.
- **Training only:** `_digit_stats(cells, shown, train)`.
  - The templates are the mean of the real and the synthetic glyphs.
  - Every gate is measured on the real glyphs alone: each digit's own spread, the noise, the thresholds, separable,
    the margin needed, the glyph counts and the saves showing.
  - The read-back, the left-out saves, the replays and the every-digit cell read real pictures only.

  The spec records `score.trained`.

**Departure from the hashed design (disclosed):** a digit's synthetic glyphs weigh in its template at most as many as
its real ones. The first trial, uncapped, did the job — left out end_P2 2.0 s — but let 288 synthetic glyphs outweigh
the real ones (3-10 a digit):
- the real glyphs' margin fell to 0.0625 (bar 0.0796, not met);
- the reader learnt without end_P1 lost its stats 3.

Capped, both are met.

## T92 — learn on its six kept saves, as BN left them

No register and no label: the kept saves and your slots were not touched (kept saves sha256 the same before and
after). `status` and `native-stream-status` showed nothing running. The picture source did not run. The rules folder
is unchanged.

**learn T92 (17:33:45-17:40:55Z): FAIL (24 cells).** Not met: left out end_P1_2, and the every-digit cell (5 short).

| cell | BN | now |
| --- | --- | --- |
| **left out: end_P2** | 03 read right in **14.0 s**, not met | 03 read right in **2.0 s**, met (bar 2.0) |
| left out: end_P1 | met, 1.5 s | met, 1.5 s |
| left out: end_P2_2 | met, 2.0 s | met, 2.0 s |
| left out: end_P1_2 | not met (its 5s) | not met (its 5s: `0?…=0?`) |
| digit margin_needed | met | 0.0882, met (bar 0.0796) |
| every digit separable, the held-out frames, the replays, the same-picture cell | met | met |
| every digit 0-5 | 5 short | **5 short** (end_P1_2 alone shows it, final and cell, 0.652 apart, neither read back) |

**Counts and seconds** (the full spec):
- 36 held out; 288 trained in 4 rounds; 16.86 s.
- **25 of 36 held out were read** when the round cap stopped the training. B192's "until every held-out one is read"
  was not reached. It is training only, never a cell.
- `learn T92` took 7 min 10 s, against 4 min 04 s in BN (every left-out spec trains too).

**What it means:** B205 did what it was for — the cross-size sample now reads fast. **5 is the one digit still owed**,
and it can come only from a real save showing it a second time: the match you are saving now.

## Tests, mutation, the 60 minutes

- **B205's 3 fast tests** (`tests/b205_synthetic_digits/`): three runs OK.
  - `Gates`: no training is today's; a far synthetic glyph moves the template but never widens a digit's spread or the
    noise.
  - `Make`: deterministic for one seed, only the real glyphs' keys.
- **The mutation:** a synthetic glyph counted toward a cell (merged into the real cells before every measure) —
  **caught** (`Gates.test_2`).
- **The suites BN named worth running every time, once, all at once, on the final code** (`tests_runs.txt`): eight
  of nine OK — B204, B157, B175, B200, B198, B171, B178, B181. **B185 had not finished at the limit** (29+ min; every
  learn it makes now trains): no result.

## Checks

- `b205.diff` applies on a clean export of `9dc4cc10`, every file byte for byte the tree (`apply_check.txt`).
- **No title, id, team name, path or address** in any file this queue wrote: the four checks.
- **No picture in git.**
- **Read only:** the rules folder, the kept saves (sha256 the same), your slots, setups and in-game saves, the runtime
  pictures.
- **Nothing else run or touched:** no stream, no restart, no adb, no sudo, no nft. The app, the companion and the
  board's repo were not touched.
- **Hub calls:** read-only `status` / `native-stream-status`, once.
- **Left in my scratch folder, off the repo (not removed by hand):** the mutation's work copies, and one suite run on
  the uncapped code, set aside.
