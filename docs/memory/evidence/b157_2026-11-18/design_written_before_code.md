# B157 — the add-a-game tool (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18BB.md` §B157. Baseline `3a9de095`. **No companion change:** the tool only reads the
hub's routes, logs and files, writes its own files and the title's rules, and (bench / close) the two flag drop-ins
the tasks have always used. A title it adds is listed by `party-minigames` only under `PRIVYHUB_PARTY=1` and
`PRIVYHUB_H7=1`, as T88 and T89 are. Nothing adopted by it.

## One command per stage

`python3 tools/party_add_game.py <stage> <code> [options]`, the code `T` + two digits. **register, learn, bench,
solo, close.** Every stage: one verdict, **exit 0 only on PASS** (1 FAIL, 2 refused, 3 waiting — solo's first half);
a verdict file `docs/memory/evidence/add_game/<code>/<stage>.json` and a page `<stage>.md` listing every cell as
**read / bar / met**; **refused** (nothing written) when the stage before has no PASS for the same inputs (its inputs'
digest recomputed now); **run twice on the same inputs → the same verdict, nothing written twice** (no clock in a
verdict; a file whose bytes would not change is not rewritten); **no title, game id, profile id, serial or path in
anything it writes to the repo or prints** — every text it writes or prints passes a guard that refuses (exit 2) if
any of the run-time names appears in it. The private things a title needs between stages (the game id, its system, its
setup) live in `~/privyhub_h7/add_game/<code>/binding.json` beside the rules folder — off the repo, as the rules are.

**Every bar is in the tool** (`BARS`, each with where it comes from); the session never judges a picture, picks a
threshold or edits a rule.

## register

`register <code> --players 2|3|4 --system ps1|n64|snes --result winner|places (--find <words> | --rules-players <n>)
[--setup none|slot1] [--collect <role>=<slot> …] [--check]`.

- **The title:** `--find`: the hub's `games?system=<s>&q=<words>` at run time — exactly one game, else FAIL ("3 titles
  match: give more of the name"); the words are never written. `--rules-players n` (describing a title already in the
  rules folder, T88 / T89): the one sidecar there with that many players.
- **The setup:** `none` (a title with nothing to unlock: no cheat) or `slot1` (the one setup the hub lists for the
  title whose slot 1 is filled, from `cheat-profiles`; more or none → FAIL naming the count).
- **`--collect role=slot`:** copies the user's own slot (from the hub's slot index — the setup's when there is one —
  read only) to `~/privyhub_h7/add_game/<code>/kept/<role>.state`; roles `begin`, `other`, `other2`…, `end_P1`…
  `end_P4` (result `winner`), `end_r<places>` (result `places`, e.g. `end_r2143`). Repeatable across runs (three slots:
  save, collect, save again).
- **Cells:** the system can hold a party mini game (ps1 / n64 / snes; ps2 and gamecube FAIL with B159's reason); 2 ≤
  players ≤ 4 (3 FAILs: the board has no three-player hub game); four-player PS1: the title's own four-player setting
  is on (the hub's per-title `ps1_multitap`), else FAIL "set four players for this game first"; the result kind;
  **every kept state there, non-empty, distinct**: `begin`, at least one `other`, and for `winner` `end_P1`…`end_Pn`,
  for `places` rows of n distinct places with **every place seen in every column** (B122's learner needs it); the
  companion's `PRIVYHUB_*` lines as found (their digest kept for close: eighteen).
- `--check`: nothing written, the verdict printed only.

## learn

`learn <code> [--check]`. Refused without register's PASS for the same kept states.

- **Pictures:** each kept state loaded paused in a headless RetroArch (B95's `Session`, as H7-V1's frames; temp
  folders; the hub's core options; the null joypad), then resumed and `SCREENSHOT` every 0.5 s for 20 s; frames under
  `~/privyhub_h7/add_game/<code>/pictures/` (never in git). The capture is a module the tests replace
  (`PARTY_ADD_GAME_CAPTURE`).
- **Labels from the state, never by eye:** a frame of the `begin` run is `start`, of an end state's run its class, of
  an `other` run `other` — and a frame of a begin or end run that differs from that run's first frame by more than
  `DIFFER_R` (the learner's own 0.25) is `ignore` (the screen moved on: not labelled).
- **The rules:** `tools/h7_endscreen.py`'s `learn` on the first half of every run, `score` on the second half, `replay`
  on every run; then the begin copied to the rules folder (`<id>.state`, or the setup's `<id>.<P12>.state`) and the
  sidecar written (`players`; `winner` with `end_P1`…`end_Pn`: `"result": "winner"` (B158) — or, B158 absent,
  one-hot `scores`; `places`: `places_to_scores` n…1; the setup's `cheat`). A file that exists for this title from
  other inputs → FAIL (never overwritten); the same inputs → nothing written again.
- **Bars** (from T88's and T89's specs and scores): the spec usable and **every class separable**; `margin_needed` ≥
  **0.0796** (T89's, the lower of the two kept specs); **no held-out frame read as another class** (T88 0, T89 0); a
  held-out class's frames read `unknown` ≤ **10.5 %** (T88's worst source: 34 of 38 right); **`other` read as a screen
  0** (both 0); `places_wrong` 0 (T89 0); **every end run → exactly one `ended`, its class, within 2.0 s** of its first
  end frame at K = 3 (B122 / H7-V4); **the begin run never `ended`** and recognised (start) within 8 s (RECOGNISE_S).
- `--check` (T88 / T89): the kept spec's own numbers against the same bars (usable, separable, margin, the arrays'
  sha256), the begin and sidecar as the listing needs them; nothing written.

## bench (PP-H4 part 1's shape, unattended)

`bench <code>`. Refused without learn's PASS for the same rules files.

- **The flags for the task:** if the companion has eighteen lines, the two drop-ins (`h7.conf`, `party.conf`) are
  written, `daemon-reload`, the companion restarted; twenty lines required (the systemctl and drop-in folder are
  replaced in the tests).
- **Files before:** sha256 of every user slot and slot picture of the title (both indexes), the rules folder, the kept
  folders — the digest kept for after and for close.
- **The board** up as the session (`games?system=party`'s game, `launch`, `bench-release`); the title listed by
  `party-minigames` (matched at run time, never written).
- **Cells:** a held start (`bench=1&hold=1`, seats 1…n) **ready within 6.0 s** (`prepare_s`; H7-V6b's bar for T89,
  the larger of the two); **PAUSED at every read** (RetroArch's `GET_STATUS` once a second on the launch's own command
  port, read after the launch answers) from ready to the go, at least 5 reads; **no reload** (no second
  `minigame_watch` before the go); `keys_written` true; a practice (`go?practice=1`) **ended by time** (`"by":
  "time"`) and **ready again after it** (`after_practice`) within 6.0 s; then for **each kept ending**: a held start,
  the real go, the ending loaded (copied to scratch slot 8, `LOAD_STATE_SLOT 8`; an N64 core paused first, B123) →
  **`ended` with that ending's class and scores** (and `winner` / `places` as the sidecar makes them) within 8 s
  (H7-V5's bar), the end; the scratch slot removed; **every file after = before**.

## solo (the attended check, one person with the pads)

`solo <code>` prints the "YOU, now:" lines for the session to pass on (open Games, PrivyParty, a mini game for this
many players, a practice left by Select, the real game to its end; say who won), keeps the logs' line counts as its
mark, and exits 3 (waiting). `solo <code> --read --winner <seat>` reads from the mark: **every planned switch
`switched` and `seconds` ≤ 1.6** (B153); **S** (B150: `audio_queue_depth` > 0 within 4 s of each switch, underruns
rising ≤ 20 a row to the next) and **`audio_max_arrival_gap_ms` ≤ 1200** at each switch (B153); **the band words in
the practices' encoder lines only** (one per practice); **the board's lines in order** (cards / chose, practice, load
screen again, start, scores … for seats …); `keys_written` true; **the hub's result = the winner the user named**
(`winner`, or the class / place 1 seat).

## close

`close <code>`: if twenty lines, the two drop-ins removed, `daemon-reload`, the companion restarted; then **eighteen
lines, their digest = register's**; only `privyhub-companion` and `privyhub-diag` active; **every file = bench's
before**.

## Fixed files

`handoffs/ADD_GAME_TASK.md` (the whole task under every standing rule: the window, the commits, replies beginning
"YOU, now:", nothing about adb at the TV, the close; the user's part from B156; the commands) and
`handoffs/ADD_GAME_PROMPT_TEMPLATE.txt` (session A's prompt, one blank: the code).

## Tests (`tests/b157_add_game/`)

Made-up titles in temp dirs, the B114 harness's real HTTP server and fake RetroArch for bench: **the whole path PASS
for a two-player (`winner`) and a four-player (`places`) title**; each gate failing with its cell named — an ending that
reads as another's class (learn), a start not PAUSED, a reload, a file changed (bench), a missing state (register); a
stage refused without its predecessor's PASS and after its inputs changed; the same inputs twice (same bytes, no file
rewritten); **T88 and T89 `--check` from the rules folder as it is: register and learn PASS, nothing written** (the
folder's sha256 and mtimes before = after); the guard (a run-time name never in an output); the mutations that loosen a
bar or skip a gate caught; the earlier suites green (no companion change).
