# B162 — the tool's solo, safe for many titles (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-19BC.md` §B162. Baseline `58497ab8`. Cowork's five gaps, each closed below.
**The companion change is in `companion/party_minigame.py` and one route in `companion/plugins/games.py`, both reached
only when `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1` (the party layer is imported only then); either absent = today, byte
for byte.** The tool (`tools/party_add_game.py`) is not the companion. The app is not changed.

## 1 + 2. Only the title under test is offered while its solo runs (the companion)

- **The setting:** the party layer keeps `only` in memory — `None` (today) or the title under test and its player
  count. **Never written to a file**, so **any restart clears it** (the companion's memory is gone).
- **The route:** `POST party-minigame-only?game=<game id>` sets it; `POST party-minigame-only?clear=1` clears it.
  **Loopback only** (as B112's bench: another caller → 400, nothing set). A game that is not a listed mini game → 400
  "not a listed mini game", nothing set. Answers `{"ok": true, "only": true, "players": n}` / `{"ok": true, "only":
  false}` — no title, no id. The game id is passed in memory over loopback (the tool reads it from its own binding);
  it is never written by either side.
- **While set,** `party-minigames` drops every other title **with the same player count**; the other counts are listed
  as they are. Cleared → the list as today.
- **One party row when set** `{"step": "minigame_only", "on": true, "players": n}` and **one when cleared**
  `{"step": "minigame_only", "on": false}` (only when something was set) — no title, no id.
- **The board:** `_choose` builds its cards from what fits; with one title for the count, one card (its own check's
  "one game fits: one card"). So gap 2's lottery ends with gap 1's setting.
- **Who sets / clears it (the tool):** `solo` sets it after the flags are on (after any restart the flags made) and
  confirms the list shows exactly one title for the count — else REFUSED, nothing asked of the user. `solo --read`
  clears it first (whatever its cells), `close` clears it (always), and any restart clears it.

## 1. A cell: the mini game played was this title (the tool)

Each RetroArch launch writes its own log `logs/games/<YYYYmmdd-HHMMSS>-<game id>.log` (the manager's launch).
`solo` marks the time; `solo --read` takes every such log named after the mark and compares each name's game id with
the binding's **in memory**: cell **"the mini game played was this title"**, read `{"this title": n, "another": m}`,
bar "this title >= 1, another 0". Neither id is written or printed (the guard holds the binding's).

## 3. S as B150 words it (the tool)

The switches are the party rows `minigame_stream` with `planned` (as today). Each has T (`time_unix`) and its start
T − `seconds`. **A switch whose next switch starts less than 4 s after its T is listed, not read.** For each read
switch: a heartbeat row with `audio_queue_depth` > 0 within 4 s after T, and `audio_underruns` rising ≤ 20 a row from
T to the next switch's start (or 30 s); `audio_max_arrival_gap_ms` read in the same span (B153's bound, the same
listed rule). Cells: **"switches read for S (the next starts 4 s or more after)"** read `[read, listed]`, bar ">= 4
read"; the S and gap cells keep their names and are taken over the read switches only; **the page names the listed
ones** (their number in order, window, `seconds`, how soon the next began). "planned switches", "every planned switch
switched" and "every planned switch's seconds" stay over all switches (B153: every switch ≤ 1.6 s).

## 4. close: the title's own in-game saves recorded, never a cell (the tool)

The title's in-game saves: every file under its setup's `saves/` (when it has a setup) and every file in the hub's
`data/games/retroarch/saves/<core>/` whose stem is the game file's stem (the binding's relative path; for a title
already in the rules folder, the hub's `details` for its id, read in memory). **Recorded before** (at `bench`, beside
its files' before; else at `solo`'s lines) **and after** (at `close`), each named by kind and number only ("under the
setup 1", "own 1") as changed / unchanged / new / gone — **in the verdict's `recorded` and the page's note, never a
cell.** Every other file compared as now (the in-game saves' hashed names left out of "every file = bench's before").

## 5. solo's lines (the tool)

- **Who:** two players — "you alone with two pads, or two of you"; four — "four people, or you with four pads".
- **The buttons:** by the `class` of the pads in the onn's last heartbeat row that has `pad_slots`: all `sony` →
  PlayStation words (△ practice, ✕ play, the Select button (Share)); none `sony` → Xbox words (Y, A, the View
  button (Back)); mixed → both ("△ / Y", "✕ / A", "Select / View"); no row → PlayStation.
- One more phrase, so S can be met: stay in the practice **at least ten seconds** before Select (a switch followed
  within 4 s is listed, not read, and four must be read).

## Tests (`tests/b162_solo_safe/`)

Through the real HTTP server (B114's harness, a `b162` mode in its own file): two made-up two-player titles and a
four-player one listed → the solo of one offers it alone (the four-player one as it was; one `minigame_only` row, no
name), a match of the other → **the title cell not met, named**; three two-player titles → the one under test is the
only two-player entry at every one of 20 reads; cleared by `solo --read`, by `close`, by a new layer (a restart), and
nothing written to a file by setting it; the route from a non-loopback caller refused. Unit (made-up logs): a quick
switch listed, not read, and the page names it; three read → not met; a changed in-game save recorded and close PASS;
any other changed file → close FAIL; the lines for `sony`, `xbox`, mixed, no row; two and four players. **The flags
absent → today:** B114's `today` mode on HEAD's companion (`58497ab8`) and mine, each flag absent, every route's bytes
the same (the new route included: unknown on both). **The users' sessions with the flags set:** `today` and
`cheat_today` with both flags, HEAD against mine, the same bytes (the tokens, salted per process, masked). The
mutations: the list filter off, the title cell always met, every switch read, the in-game saves compared, Xbox words
never, the clear on `--read` skipped, the clear on `close` skipped. B157's and B158's suites green — **B157's solo
tests given a made-up hub on loopback (the setting must be taken before the lines) and a launch log for their title**.
