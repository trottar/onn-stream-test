# B105 — the watcher's gaps: the design, written before code (session B, queue AN)

Baseline HEAD `d61f9b56` (+ B104's `tools/h7_endscreen.py`, which the watcher reads through). Code:
`companion/h7_minigame.py` and two guarded lines in `companion/plugins/games.py`. **Everything behind
`PRIVYHUB_H7=1`**: `plugins/games.py` imports `h7_minigame` only with the flag (as B99 / B101 / B103); absent / `0` =
today byte for byte, proved through the real HTTP server on HEAD's companion (`git archive d61f9b56`) against this one
(the three routes' answers, the launch's).

## 1. A start while a watch is on replaces it

- `h7-start` no longer refuses "a mini game is already being watched". When a watch is `watching`, a start goes through
  the same checks as any start (no game, no spec, the system / kind, no state, the stream down, a bad `load` / `keep`
  word: **the other refusals stay**, and a refused start leaves the running watch as it was); then the load (when
  asked) — **if the load fails (503, "the game is as it was") the running watch also goes on**; then, under the lock,
  the old watch is ended (its thread sees its token gone and stops without another row) and **one row `replaced`**
  (`game`, the old watch's `reads`, `since_s`, `class`) is written before the new watch's `watching` row. The answer
  carries `"replaced": true` (false otherwise).
- A finished watch (`ended`) is followed by a new start as today (no `replaced` row: nothing was being watched).
- Starts are serialised by a start lock (two at once cannot both load).

## 2. "Is the screen recognised?" — `recognised` in `h7-result`

- `RECOGNISE_S = 8` seconds (stated; at one read a second ≈ 8 reads, room for RetroArch's own "state loaded" notice
  over the first pictures).
- **After a start with the load:** `recognised` is `null` until either **a read names the start class** (one read is
  enough: a read names a class only under its threshold and with the margin) → `true`, or **`RECOGNISE_S` pass since
  the watch began without one** → `false` (pictures that could not be grabbed count as time passing: a picture the hub
  cannot read is not recognised). **`false` means: the load was done but the picture in front of the hub is not read
  as this game's start — the caller must not send players into a match.**
- **With `?load=0`:** `true` once a read names the start class; otherwise it stays `null` (never `false`: nobody said
  the start is on screen).
- **Once settled it does not change**, and the watch goes on as before (a later `ended` is still said; the caller's
  rule on `false` is to stop). **One row `recognised`** when it settles (`value`, `after_s`, `reads`, and the last read's
  distances and class).
- `h7-start` answers at once as today (the load, then `started`); `recognised` is read from `h7-result`, beside
  `seen_start` (which stays as B103's: true after a load or K start reads).

## 3. `POST /plugins/games/h7-stop`

- A watch `watching` or `ended` for the running game → the watch dropped (its thread stops at its next second without a
  row), **one row `stopped_by_call`** (`game`, `reads`, `state`), answer `{"ok": true, "watch": "stopped", "game", "reads"}`;
  **nothing is sent to the game** (no command, no load, no picture). `h7-result` is then `idle`.
- No watch → `{"ok": true, "watch": "none"}`, no row (nothing changed). No game → the same.

## 4. The watcher's own pictures on request: `h7-start?keep=1`

- `keep` is `0` / `1` (else 400 "keep is 0 or 1"); off unless asked.
- With `keep=1`: a folder **`runtime/h7_frames/<game id>_<UTC stamp YYYYMMDDTHHMMSSZ>/`** under the project
  (git-ignored: `runtime/` is in `.gitignore`; the test proves `git check-ignore` on the real repo for that shape);
  **every picture the watcher reads is saved as it was read** (the grabbed window picture, before any cut) as JPEG
  (quality 90) `f000001.jpg`, … and one `index.csv` row per picture: `seconds` (since the watch began), `utc`, `file`,
  `class`, `screen` (the screen distance), `margin`, `distances` (JSON of every distance), `keep_ms` — the folder is a
  run B104's `learn` / `score` / `replay` read directly (labels added beside it).
- The save happens in the watcher's thread after the read, so the read's timing is the same; a folder or a picture
  that cannot be written → one row `keep_failed` and keeping stops for that watch (the watch goes on).
- The result carries `"keep": {"folder": <the folder's name>, "pictures": n}` (null when off); the `watching` row too.
- **Its cost**, stated in the record: ms per picture (JPEG encode + write, a 1920 × 1080 picture) and CPU per picture;
  and a fixture's frames over 60 s with and without keeping — the fixture is **a synthetic 60-fps frame loop** (a
  process drawing 1920 × 1080 frames with numpy, paced to 60 a second, counting frames done) beside the watcher reading
  and keeping a 1920 × 1080 picture a second through the real module (a fake picture source; no RetroArch, no game).

## 5. `last` in the result

`last` = `{"class", "distances", "margin", "thresholds": {"screen", "classes", "margin_needed"}, "spec_version"}` —
the read's distances, what they are held against, and the spec's version (B104's `thresholds(spec)`).

## 6. An old-measure spec

`load_spec` refuses a version-1 spec with B104's line. `h7-result` → `{"state": "no_spec", "why": "this end-screen spec
was learnt with the old measure (absolute grey levels): learn it again"}` (the line itself, not wrapped); `h7-start`
→ 400 with the same line.

## Tests (`tests/b105_h7_watcher/`; B103's harness: the real HTTP server on loopback, the fake RetroArch with its
command log, the fake picture source, synthetic pictures, a spec learnt in the test; temp dirs removed)

Start, start again → `replaced` (one row, the old thread silent after, two loads) and the second watch ends rightly;
the load done but the fake shows a screen the spec does not know (an unseen tally; a fight) → `recognised` false
within `RECOGNISE_S` (scaled down in the test) and no `ended` ever; the start screen shown → true; `load=0` → null then
true; stop → `idle`, the fake's command log showing nothing sent after the start's load, a stop with no watch →
`none`; `keep=1` writes the pictures and the index (columns, one row per read, the files there), absent writes none;
`git check-ignore` on the repo for the keep folder's shape; an old-measure spec → `no_spec` with the plain line and the
start refused with it; `last` carries the thresholds and version; the flag absent / 0 → HEAD's answers byte for byte
(`h7-stop` included: "Unknown Games plugin POST action"). B99 / B101 / B103's tests run; **B103's test is updated only
where B105 changes B103's behaviour** (its two "already being watched" refusals become `replaced`; `last`'s keys a
superset) — disclosed in the record. Mutations with B101's runner. The keep cost on the fixture as above.
