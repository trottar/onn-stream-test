---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AU) — the hub prepares the title behind the board and hands over on the board's go, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). Settled first: the onn keeps seeing the board while the title's window is open above it (the stream grabs the board's window by its id; the hub composites — a made-up full-screen window grabbed by id stayed itself under a 960x720 and a full-screen made-up window, while the screen showed the cover); RetroArch's notices run out while the core is paused (B61's form: ~2.8 s, as running), but a paused core does not show a state loaded into it, and with no route set the players' pads reach a running title too — so the title runs behind the board only from the load until its start is read, then waits paused, and the go loads the begin again. Built: party-minigame-start?…&hold=1 → preparing → ready (no route, no switch, the stream on the board, the title paused) → party-minigame-go (remembered if early) → the begin again, the route, the planned switch, playing; the hold has no limit of its own; never the start / a failed launch → given_up with no switch and no route; the onn's Home / RESUME during the preparation or the hold give the mini game up then act on the board, END ends everything. Expected start → ready: T88 ~12 s, T89 ~4-5 s. Tests 9 (3 runs). Nothing adopted; nothing committed
---

# B133 — the hub prepares the title behind the board and hands over on the board's go

Queue: `handoffs/QUEUE_2026-11-17AU.md` §B133. T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title.
The directory is `b133_2026-11-17/`: the design + `.sha256` (hashed 19:35:30Z, before any code), `scripts/cover_probe.py`
+ `cover_probe_result.json`, `scripts/notice_probe.py` (+ B61's `fixture_rom.py`, copied) + `notice_probe_result.json`,
`window_manager.txt`, `b133.diff` (B133's and B134's hunks: the same files), `tests_mutations.txt`, the checks,
`manifest.sha256`; the runs in `b134_2026-11-17/tests_x3.txt`. Patch: `patches/B133_PARTY_PREPARE_AND_GO.md`. No
title, id, `profile_id` or path; no picture in git. **Disclosed probes:** two made-up Tk windows on the hub's display
(~10 s); B61's form — the hub's RetroArch AppImage and N64 core on B61's synthetic ROM, temp folders, the joypad driver
null, no stream (~60 s); no game, no title, nothing of the users' read.

## Settled first

1. **What the onn sees of the board once the title's window is above it: the board.** The hub's window manager
   composites (xfwm4 `use_compositing` true, `unredirect_overlays` true; the Composite extension). The probe: a made-up
   full-screen window A (the board's shape) and a made-up window B opened above it — 960 × 720 at (960, 384) (T89's
   shape) and full screen (T88's): **A grabbed by its id with the stream's own grab (`ffmpeg -f x11grab -framerate 60
   -draw_mouse 0 -window_id <A> -i :0`, one frame) = A's own picture in both (mean (255, 0, 0), 1920 × 1080)**, while
   Pillow's screen grab at B's place = B (the watcher reads the screen: it reads the title). So **the stream left on the
   board's window keeps the board on the TV while the title is prepared above it** — nothing else is needed.
2. **RetroArch's notices run out while the core is paused** (`notice_probe_result.json`): a state loaded into the
   paused core — its notice in the window from 0.6 s to 2.8 s, gone at 3.2 s and for the 20 s after, `GET_STATUS`
   `PAUSED` throughout (a running core's notice: the same ~2.8 s). RetroArch keeps redrawing a paused core's window.
   **But a paused core does not show a state loaded into it until a frame runs** (B123), and the watcher must read the
   begin — so the title runs behind the board from the load until its start is read. **Who presses on it then:** with no
   route set the bridge writes onn pad *k* to virtual pad *k* (`_apply_report`), and the board and RetroArch both read
   the virtual pads — **the players' presses on the board's screens reach the running title** (T88 ~9-10 s, T89 ~2 s);
   a paused core takes none. Hence: **paused as soon as the start is read** (notices run out paused; nothing runs on
   with nobody's pads — no pick timer, no attract loop), and **the go loads the begin again**, so whatever reached the
   title before, the players start from the users' own screen.
3. **The bounds:** `START_LIMIT_S` (30 s) now bounds the preparation only (the launch to `recognised`: T88 ~12 s, T89
   ~4-5 s, the watch's own window 15 s under a setup); `PLAY_LIMIT_S` (900 s) from the hand-over; `POLL_GONE_S` (120 s)
   also through the hold; `UNKNOWN_LIMIT_S` playing only; the board's `LIMIT_SECONDS` stops running during the ready
   check (B135); `MISSED_POLLS` unchanged.

## Built (`b133.diff`: `companion/party_minigame.py`, `companion/h7_minigame.py`, `companion/plugins/games.py`)

- **`party-minigame-start?id=…&seats=…&hold=1`** (another value → 400 "hold is 1"): the board set aside; the title
  launched (under its setup, B127); **paused → the watch's start with the load → resumed behind the board — the stream
  untouched, no route set → `recognised` true → paused → `"phase": "ready"`**, held with no limit of its own. Not
  recognised, a failed launch, a setup gone → `given_up`, **no switch made and no route ever set**, the title stopped,
  the board's session back (the end's switch back skipped when the stream never left the board).
- **`POST party-minigame-go`**: taken at once; before `ready` remembered (`"go": "remembered"`) and acted on at
  `ready`; a second → `"already"`; nothing held → 400 "no mini game is waiting for the go". **The hand-over:**
  `"handing_over"` → **the begin loaded again into the paused title** (`MiniGame.reload`: the setup's begin under a
  setup; N64 only while paused; the watch, its `recognised` and its start kept) → the route → the planned switch (B115)
  → the release → `"playing"`.
- **`party-minigame-result`** for a held start: `"starting"` with **`"phase": "preparing" | "ready" | "handing_over"`**
  and `"practices"`; a start without `hold`: today's answer.
- **The hold ends** by the go, the board's end, the onn's END, or the board no longer asking (`POLL_GONE_S` with no
  result call → given up at once, the title stopped).
- **The onn during the preparation and the hold** (the TV shows the board): **END** → as today (the mini game given up,
  the title stopped, the board back, then the board's own quit); **Home / RESUME** → the mini game given up first ("the
  onn's Home during the preparation"; the title stopped, the board's session back), then the call acts on the board as
  today (Home pauses the board, RESUME resumes it). A second start → refused (400). The title is never left running.
- **Rows:** `minigame_start` `"hold": true`; **`minigame_ready` `{"prepare_s"}`**; **`minigame_go` `{"held_s",
  "remembered"}`**; `minigame_reloaded`; **`minigame_playing` `{"handover_s"}`** — only for a held start; a start
  without `hold`: today's rows exactly.

## Tests (`tests/b133_party_prepare_go/`, 9; B114's scenario, its `hold` mode)

| test | shown |
| --- | --- |
| prepared behind the board | `preparing` → `ready` (`recognised` true); the rows up to then **start, launch, watch, ready — no route, no stream switch**; the route unset, **the stream on the board**, the title paused; a 3-s hold with the board asking → still `ready` |
| the go | `taken`; the route {0: 0, 1: 1}, the stream on the title; **ended end_P1 [1, 0]**; rows `… ready, go, reloaded, route, stream, playing …`; `prepare_s` 1.2 (scaled pictures), `held_s` ≥ 3.0, `remembered` false, `handover_s` < 2 (0.61); two planned switches |
| a go before ready, T89-shaped | `"remembered"` at `preparing`, a second go `"already"`; then by itself → places [2, 1, 4, 3] → scores [3, 4, 1, 2] for seats 3,1,4,2; the go row `remembered` true |
| never the start | `given_up` "…not recognised"; **no route, no switch**; the title gone; the board's session back |
| the board no longer asking | `given_up` "the board stopped asking"; the title gone; no route |
| the board's end, a second start | during the preparation and the hold: given up, the title gone, no route, no switch; a second start 400 |
| the onn's Home / END | Home in the hold → given up, the title gone, RESUME then resumes **the board** (200, `godot`), no route ever; END in the preparation → everything ends (the board quits) |
| refusals, routes | the go with nothing held → 400; `practice=2` / `hold=2` → 400; every route < 2 s (status 0.60 s max) |
| flags absent | HEAD's companion and mine: the party routes (with `party-minigame-go`), status, Home, stop byte for byte |

**Mutation** (`tests_mutations.txt`): HEAD's `party_minigame.py` / `plugins/games.py` (no hold) → the held tests fail.
**Runs:** 3 green; B110, B112, B114 (with its scenario's new modes), B115, B124, B127, B129-B131 and the others green
(`b134_2026-11-17/tests_x3.txt`); **B111** (the board's check run by the hub's test) failed on its old counts once B135's
check grew — updated (its fake hub answers the held starts; 81 / 56 assertions) and green.

**Expected start → ready on the hub** (from H7-D1 / H7-V5b): **T88 ~12 s** (the launch under its setup ~2.3 s + its
start read at 9-10 s, RetroArch's notices), **T89 ~4-5 s** (~2.3 s + 2.0 s).
