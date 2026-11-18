---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AZ) — a practice is left by Select, not Start, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). Settled: the practice's report hook sees every pad's raw report before B141's Select hold, the route and the write; Start passed through to the title and also ended the practice; Select was held from a held title's launch to a real go, practices included, and did nothing in a practice. Built: a Select press on any pad leaves a practice ("by": "select_button"); a Select already down at the hand-over counts only once let go and pressed again (the bridge keeps each pad's raw Select while the hold is on); Start is not looked at and reaches the title as in a real mini game; Select still never reaches the title before a real go; the time bound as it was. The band: "PRACTICE — press Select (Share) to go back", B147's placement — rows 36-85, columns 318-960 of 720p, all inside the inner 90 %. Tests: B151 11 (x3), B134 / B145 / B144 / B147 / B143 updated (x3); mutations 4 / 4. Nothing adopted; nothing committed
---

# B151 — a practice is left by Select, not Start

Queue: `handoffs/QUEUE_2026-11-18AZ.md` §B151. Why: both of the users' setups begin at their character screens; T88 goes
on with the face buttons, **T89 only with Start** — the button that left a practice, so a four-person T89 practice would
have ended the moment anyone tried to start the fight. The user's choice: "Select/Share". The directory is
`b151_2026-11-18/`: the design + `.sha256` (hashed 16:06:24Z, before any code), `b151.diff`, `band_extent.txt`, the
runs (`tests_x3.txt`, `tests_recent.txt`, `tests_others.txt`, `tests_mutations.txt`, `b143_again.txt`), `scripts/`,
the checks, `manifest.sha256`. Patch: `patches/B151_PARTY_PRACTICE_LEFT_BY_SELECT.md`. No game was started; no picture
in git (the band measured on a made-up picture, in a temp dir, removed).

## Settled from the code (HEAD `58bc6c42`)

- **Where a practice's Start was seen:** every onn controller report reaches the bridge's `_apply_report(player,
  buttons, …)`. Its first step calls the practice's hook (set at a practice's hand-over, after the route and the
  switch, before the resume; cleared at the way back and at every end) with the onn's player and **the raw buttons** —
  before B141's Select hold, the route and the mute. The hook took Start going from up to down on any pad, seated or
  not, as "leave".
- **What happened to that Start on its way to the title:** nothing was swallowed. After the hook, the hold clears only
  Select, the route maps the pad to the title's virtual pad, and the report — Start in it — is written there. The
  running title got Start; the way back then paused it and loaded its begin again.
- **Select from a party title's launch to a real go (B141, B145):** held — cleared from every report — from just before
  a held title's launch, through the preparation, the hold, every practice and every way back; off at a real go
  (before the route and the resume) and at every end. **In a practice Select did nothing at all.**
- **Select + Start in a practice:** the hook saw Start → the practice ended (`"start_button"`); the hold cleared Select,
  so the title got Start alone (RetroArch's quit pair never formed), then was paused.

## Built (`b151.diff`)

- `companion/party_minigame.py`: `_select_hook` in place of `_start_hook` — **a Select press (the report's Back / Share
  bit) on any pad** sets `practice_end_by = "select_button"` while the practice plays. **Start is not looked at.** A
  pad's first state in the hook is its Select **as the bridge last saw it**, so a Select already down at the hand-over
  counts only once let go and pressed again. The time bound unchanged (`PRACTICE_S = 90.0`, `"by": "time"`).
- `companion/native_session_io.py`: `_party_select_down` — each onn pad's raw Select, written in `_apply_report`'s hold
  branch (after the hook, so the hook reading it sees the previous report), **only while the hold is on**; seeded from
  the pads' last reports when the hold goes from off to on (no route then); not seeded again on → on (the way back);
  emptied when the hold goes off. `party_select_down(player)`. **`set_party_route` keeps it across its own neutral
  writes** (found while building: they go through `_apply_report`, and would have marked every pad "up" at the
  hand-over).
- `companion/native_stream.py`: **`PARTY_BANNER_TEXT = "PRACTICE — press Select (Share) to go back"`**; B147's filter
  unchanged (font, `h*30/720`, centred, the box's top at `h*5/100`, 10 px above and below, 16 px to each side).
- **The band** (`band_extent.txt`, B147's method on a made-up 4:3 picture): **rows 36-85, columns 318-960** of
  1280 × 720 (643 × 50 px; B147's words 379-899), **every changed pixel inside the inner 90 %** (rows 36-683, columns
  64-1215); 4.7 % of a 4:3 title's picture (B147's 3.8 %), inside its columns (160-1119). At 1920 × 1080: rows 54-119,
  columns 486-1433, inside.
- A real mini game, and everything outside a practice, as today: the hook exists only in a practice; the record only
  while a party title is held.

## Tests

| suite | shown |
| --- | --- |
| **B151** (`tests/b151_party_select_leaves/`, 11; B114's scenario's new `select151` mode, T89-shaped: four seats 3,1,4,2, its start screen left only by a press) | practice 1: **Start from each of the four pads → still playing; the title's four pads written with Start; the title off its start screen** (the fight begins); route {2: 0, 0: 1, 3: 2, 1: 3}; **then pad 1's Select → back, ready**; practices 2-4 left by the Select of pads 2, 3, 4; **practice 5: pad 3's Select down before the go and repeated after it → still playing; let go → still playing; pressed again → ends**; practice 6: Select + Start together → `select_button`, Start written, the title alive; practice 7: **the time** (scaled) → `time`; rows `select_button` ×6, `time`; **from the hold to the real go no virtual pad written with Select (of > 20 writes), the hotkey log empty, the state folder byte-equal**; a real go: Select and Start written, nothing on the hub, no hook, ended `[2, 1, 4, 3]` / `[3, 4, 1, 2]` for seats `[3, 1, 4, 2]`, `"practices": 7`; after the end the hook, the hold and the record cleared |
| B151's bridge test | the record untouched with the hold off (Select passes); seeded at off → on; Select + Start written as Start; kept across `set_party_route`; not re-seeded on → on; emptied at off |
| B151's band test | the words; B147's placement in the filter |
| **B134** (updated) | in each practice **a Start first → still playing**; practices 1-2 left by **the second pad's Select**, the third by time → `select_button`, `select_button`, `time`; Start and Select in a real go → nothing on the hub; the ends in a practice and its way back (now started by Select) |
| **B145** (updated) | Select + L1 / R1 / R3 from every pad in a practice: **the first of them leaves it (`select_button`)**, the pairs going on through its way back — never Select written, the hotkey log empty, the folder byte-equal; the title not quit; a real go lets Select through |
| **B147 / B144** (updated) | the practices' encoder commands carry the new words, every other command equals HEAD's; B147's frame test: inside the inner 90 % at 720p and 1080p, rows 36-85; **its "narrower than half the frame" became "inside a centred 4:3 picture's columns"** (the new words are 643 px, 3 px over half); B144's frame test with the new words |
| B143 (its `b143` mode) | its practice left by **Select + Start**, so that the HEAD runs of the same scenario (B143's, B144's and B147's comparisons) still leave it: Select on this code, Start on the earlier |

**Runs:** `tests_x3.txt` — B151, B134, B145, B147, B144, B143 three times: all OK but **one error in B143's second
run** (one class's setup: 4 of its 5 tests ran; the run's summary kept no traceback) — **three more B143 runs OK**
(`b143_again.txt`), so 5 of 6; not explained, recorded as it stands; 0 temp dirs. `tests_recent.txt` — B148, B141, B140, B139, B137, B133, start_rung,
encoder_rc OK. `tests_others.txt` — B137's list, all OK (**B114 8 with its flags-absent test, B108 16 with its
flag-absent test**, B111 2 with Godot on its own scratch copy and the board's repo at `674407d`, B127 9, B124 6, the
client contract 5, audio codec 20, …); `art_systems` against the repo (its doc test reads `docs/CHEATS.md`, not in the
work copy). The older suites leave temp dirs of their own (153, as in queue AY): left in my scratch, not removed.
**Mutations 4 / 4** (`tests_mutations.txt`; the first pass's band mutation missed its anchor and ran nothing changed — redone with the anchor fixed): Start kept as the way out → B151 and B134 fail; the hook's first state "up" →
B151's held-across case fails; the route's neutral writes counted → B151's held-across case and the bridge test fail;
the old words → B151's band test and B144 fail.

**The flags absent → today:** B114's and B108's flag tests and B133's (HEAD's answers through the real routes).
