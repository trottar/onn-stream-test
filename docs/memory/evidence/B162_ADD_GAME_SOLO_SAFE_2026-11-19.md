---
memory_schema: 1
as_of: 2026-11-19
status: BUILT (session B, queue BC) — the add-a-game tool's solo made safe for many titles, Cowork's five gaps each closed: a one-title setting on the hub (memory only; set by solo, cleared by solo --read, close and any restart) under which party-minigames lists the title under test alone for its player count; a cell that the mini game played was this title (the launches compared in memory); S as B150 words it (a switch followed within 4 s listed, not read; four read); close recording the title's own in-game saves, never a cell; solo's lines for one person, the buttons named by the pads' class. The companion's part behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1; either absent = HEAD's bytes. Nothing adopted; nothing committed
---

# B162 — the tool's solo, safe for many titles

Queue: `handoffs/QUEUE_2026-11-19BC.md` §B162. The directory is `b162_2026-11-19/`: the design + `.sha256` (hashed
04:26:25Z, before any code), `b162_b163.diff` (B162 and B163 together — one tool file holds both; applies on
`58497ab8`, checked on a clean HEAD tree: every file byte for byte), `sha256_before_after.txt`, the runs, `scripts/`,
the checks, `manifest.sha256`. Patch: `patches/B162_ADD_GAME_SOLO_SAFE.md`. B163 (`rehearse`) has its own record.

## The five gaps, each closed

| Cowork's gap | built |
| --- | --- |
| 1. solo never checks which title was played | **`solo --read`'s cell "the mini game played was this title"**: every RetroArch launch writes `logs/games/<time>-<game id>.log` (the manager's own log); the launches after solo's lines, each name's id against the binding's **in memory** — read `{"this title": n, "another": m}`, met when n ≥ 1 and m = 0. Neither id written or printed. |
| 2. three or more titles: the one under test may not be offered | **the one-title setting**: `POST party-minigame-only?game=<id>` (loopback only; `?clear=1` clears) — while set, `party-minigames` drops every other title **of the same player count**; the other counts as they are. Kept in the party layer's memory only: **any restart clears it**; nothing written to a file. One party row when set `{"step": "minigame_only", "on": true, "players": n}` and one when cleared `{"on": false}` — no title, no id. `solo` sets it after the flags (and any restart they need) and refuses — nothing asked of the user — unless the hub lists exactly one title for the count; `solo --read` clears it first, whatever its cells; `close` clears it. The board's `_choose` then has one title to show: one card (its own check's "one game fits: one card"). |
| 3. S fails a switch that cannot be read | **S as B150 words it**: a switch whose next switch starts (T − `seconds`) less than 4 s after its T is **listed, not read**; S and the arrival gap read from T to the next switch's start (or 30 s); a new cell **"switches read for S (the next starts 4 s or more after)"** read `[read, listed]`, bar ≥ 4 read; **the page names the listed ones** ("switch 1 (to the minigame, 1.3 s; the next began 1.3 s after)"). "every planned switch's seconds" stays over all of them (B153: each ≤ 1.6 s). |
| 4. close compares the in-game saves | **close records the title's own in-game saves** — every file under its setup's `saves/` and every file in the hub's `saves/<core>/` with the game file's stem (a title already in the rules folder: the stem from the hub's `details` for its id, in memory) — before (at bench, else at solo's lines) and after, each named by kind and number only ("under the setup 1: changed", "own 1: unchanged"), **in the verdict's `recorded` and the page's note — never a cell**; every other file compared as before (the saves' hashed names left out). |
| 5. solo's lines ask for two people, PlayStation words only | "**you alone with two pads, or two of you**" / "**four people, or you with four pads**"; the buttons by the `class` of the pads in the onn's last heartbeat row with pads: all `sony` → △ / ✕ / the Select button (Share); none `sony` → Y / A / the View button (Back); mixed → both ("△ (Y on an Xbox pad)"…); no row → PlayStation. |

**Two phrases added to solo's lines beyond the item's words (disclosed):** "stay in it at least ten seconds" (a
practice left within 4 s of its hand-over makes its switch a listed one, and four must be read — an honest quick
Select would otherwise fail S); and "if two cards show, stop and tell me" (B165's stop, said where the user sees it).

## The switch and the flags (through the real HTTP routes, B114's harness)

- **Each flag absent → HEAD's bytes:** B114's `today` mode (now also calling `party-minigame-only?clear=1`) on HEAD's
  companion (`58497ab8`, `git archive`) and on mine, for `PARTY` alone, `H7` alone, neither, and `PARTY` with `H7=0`:
  **every route's code and body the same** (the clock masked), the new route "Unknown Games plugin action" on both;
  the users' launch's ports and session-config keys the same. **OK.**
- **Both flags set, the setting never set (the users' own sessions):** `today` and `cheat_today`, HEAD against mine:
  every route the same but the new route's own answer (unknown on HEAD; `{"ok": true, "only": false}` here) — the
  list, start, result, end, go, status, Home, stop, the Extras launch, h7-start / -result, the setup list, the plain
  launch. **OK** (`tests_x3.txt`: `FlagsAndUsers`, 2 tests, in every run of the suite).

## Tests (`tests/b162_solo_safe/`, 17)

`Harness` (B114's `b162` mode in its own file; the real companion, the tool against it): two made-up two-player titles
and a four-player one listed → `solo` of one: two-player list = it alone, the four-player one as it was, one row
`{"step": "minigame_only", "on": true, "players": 2}`, **no file under the tree changed by the setting**, a
non-loopback caller refused ("loopback") and the setting kept; **a match of the other title → `solo --read` FAIL with
"the mini game played was this title" not met, read this 0 / another 1**; the setting cleared by `--read` (one row
`on: false`, the list as before). **Three two-player titles → the one under test the only two-player entry at 20 reads
of 20**; a match of it → that cell met (another 0). Cleared by `close` (one row) and by a new layer (a restart's
memory). No made-up title, id or the tree's path in anything the tool wrote or printed; every `minigame_only` row only
`step`, `on`, `players`, `time_unix`. `FlagsAndUsers` (above). `Unit` (B157's solo fixture, a made-up hub on
loopback): the title cell for this / another / both / none; launches before the mark not counted; **a practice left
2.6 s after its hand-over → listed, not read, five read → PASS, the page naming it**; three read → not met; **a changed
in-game save under the setup and an own one → close PASS, recorded "changed", not a cell, no name on the page; then the
user's slot file changed → close FAIL "every file = bench's before"**; the lines for `sony` / `xbox`+`generic` / mixed /
no row, two and four players; the setting not taken (a companion without the route) → REFUSED, no line for the user, no
mark; set by solo, cleared by `--read` and by `close`.

**B157's solo tests changed (disclosed):** solo must have the setting taken before it prints a line, so B157's
`SoloReads` now runs a made-up hub on loopback (`tests/b157_add_game/made_up_hub.py`, shared with B162 / B163) and its
read fixture writes a launch log for its title; nothing else in B157's tests changed.

Runs (`tests_x3.txt`): **B162 17 OK ×3, B163 6 OK ×3, B157 17 OK ×2, B158 6 OK ×2; 0 temp dirs left.** The recent
party suites once (`tests_recent.txt`): **all 23 OK** — B114 8, B155 4, B153 6, B151 11, B148 6, B147 2, B145 4, B144 5,
B143 5, B141 4, B140 3, B139 5, B137 10, B134 5, B133 9, B127 9, B124 6, B123 6, B131 5, B108 16, B110 13, B112 7,
B115 6; 0 temp dirs left. After two test-only changes (`tests_after_fix.txt`): B163 6 OK ×3 (its made-up real spec,
below and in B163's record), **B162 17 OK ×3** (the non-loopback caller in the harness test was an IPv4-shaped
made-up string, which the record's redaction check flags; now a word — the route checks only "not loopback"), and
b139 alone once (below). The diff regenerated after them (`apply_check.txt`: applies on HEAD, every file byte for byte;
`git diff --check` clean).

## Disclosed

- My first harness run used the tree's second made-up PS1 title, an `.iso` the manager refuses ("Unsupported ps1
  content format"): it never launched, so no launch log. The test now uses the harness's N64 title as the other
  two-player one; my own assertion of "≥ 2 launch logs" at that point was wrong (only the other's launch exists then)
  and is "≥ 1".
- A title already in the rules folder (T88) has no bench, so `close` has no files' before to compare — as before
  (the item says "as now"); its in-game saves are recorded from solo's lines.
- The harness's child text is 127,705 of the kernel's 131,072 bytes with the `b162` hook (was ~127,400).

- One sync of the work copy happened while the recent suites ran (to rerun a B163 mutation): only B163's test file
  differed; the suite running then (b139) passed, and passed again alone (`tests_after_fix.txt`).
- My run scripts first had this machine's paths inline; the copies in `scripts/` take them as arguments (the same logic).

## Mutations (`tests_mutations.txt`) — B162's eight caught

The list filter off (5 harness tests fail); **the route's loopback check off** (the non-loopback caller's clear taken:
tests 1 and 3); the title cell always met (the harness's other-title match and the unit's title cell); every switch read
(the quick-switch and three-read units); the in-game saves compared (the close unit); Xbox words never (the lines unit);
the clear on `--read` skipped (4 tests); the clear on `close` skipped (2 tests). With B163's three (its record): **11 /
11 caught**, one of them only after a test fix (B163's record). 0 temp dirs left. (B162's eight ran on the tests before the non-loopback caller became a word; the assertion is the same.)
