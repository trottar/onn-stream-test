# B133 — the hub prepares the title behind the board and hands over on the board's go: the design (hashed before code)

T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title. Only with `PRIVYHUB_PARTY=1` (and
`PRIVYHUB_H7=1`, as every party mini game); absent → today; **without `hold=1` the start is today's order, its rows and
answers byte for byte**. No title, id, `profile_id` or path in this folder; no picture in git.

## Settled first (disclosed probes: made-up windows; B61's form — the hub's RetroArch and N64 core on B61's made-up ROM)

1. **What the onn sees of the board once the title's window is above it — the board.** The hub's window manager
   (xfwm4) composites (`use_compositing` true; Composite present; `unredirect_overlays` true). `scripts/cover_probe.py`:
   a made-up full-screen window A (the board's shape) with a made-up window B opened above it — 960 × 720 at (960, 384)
   (T89's shape) and full screen (T88's) — **A grabbed by its id with the stream's own arguments (`ffmpeg -f x11grab
   -framerate 60 -draw_mouse 0 -window_id <A> -i :0`, one frame) gave A's own picture (mean (255, 0, 0), 1920 × 1080)
   in both cases, while the screen at B's place showed B** (the watcher reads the screen: it sees the title). So the
   stream left on the board's window keeps the board on the TV while the title is prepared above it; nothing else is
   needed. (Godot draws into its own redirected window whether or not it is covered.)
2. **RetroArch's notices run out while the core is paused.** `scripts/notice_probe.py`: a state loaded into the paused
   core — its notice in the window from 0.6 s to 2.8 s, gone at 3.2 s and for the 20 s after, still `PAUSED`; the same
   ~2.8 s as a running core's notice. RetroArch keeps redrawing a paused core's window. **But a paused core does not
   show a state loaded into it until a frame runs** (B123's finding for N64), and the watcher must read the begin — so
   the title runs behind the board from the load until the start is read, then waits paused.
3. **Who sees the pads while the title runs behind the board.** The bridge writes onn pad *k* to virtual pad *k* when
   no route is set (`_apply_report`: `route is None` → as is); the board (Godot) and RetroArch both read the virtual pads.
   So **while the title runs behind the board (from the load until the start is read: T88 ~9 s, T89 ~2 s), the players'
   presses on the board's screens also reach the title**; a paused core takes none. Hence: the title paused as soon as
   the start is read, and **the go loads the begin again (paused) before the hand-over**, so the players start from the
   users' own screen whatever reached it before.
4. **Bounds:** `START_LIMIT_S` (30 s) — now the preparation only (launch → load → `recognised`): T88 ~3 s launch + up
   to 15 s (B130) < 30; `PLAY_LIMIT_S` (900 s) counted from the hand-over, not the start (a long hold must not eat the
   match); `POLL_GONE_S` (120 s) also through the hold (the board stops asking → given up); `UNKNOWN_LIMIT_S` playing
   only; the watch's own `recognised` window (8 s / 15 s under a setup); the board's `LIMIT_SECONDS` (1200 s) /
   `MISSED_POLLS` (10) — B135 stops `LIMIT_SECONDS` running during the ready check.

## The design

- `party-minigame-start?id=…&seats=…&hold=1` (any other value of `hold` → 400 "hold is 1"): answers `"starting"` at
  once; the actor: the board set aside → the title launched (under its setup, B127) → paused → **the watch's start with
  the load** (B103 / B123: the begin through scratch slot 8 of the session's folder; N64 only while paused) → **resumed,
  behind the board: the stream untouched (still the board's window), no pad route set** → waits for `recognised`:
  **true → the title paused, `"phase": "ready"`, held**; false (or a failed launch, a setup gone, the watch refused) →
  `given_up`, **no switch made, no pad route ever set**, the title stopped, the board back.
- **`POST /plugins/games/party-minigame-go`** (the board's; `practice=1` is B134's): taken at once; before `ready` it
  is remembered (`"go": "remembered"`) and acted on at `ready`; at `ready` → `"phase": "handing_over"`: **the begin
  loaded again into the paused title (the watch kept, `recognised` kept)** → the pads routed → the planned switch
  (B115) → the title released → `"playing"`. A second go → `{"go": "already"}`, nothing more. No mini game, or one not
  held → 400 "no mini game is waiting for the go".
- `party-minigame-result`: `"state": "starting"` with **`"phase": "preparing" | "ready" | "handing_over"`** until the
  switch (only for a held start; a start without `hold` answers as today). The hold has **no time limit of its own**:
  it ends by the go, the board's end (`party-minigame-end` → given up, the title stopped), the onn's END (as today:
  everything ends), or the board no longer asking (`POLL_GONE_S` with no result call → given up).
- **The title through a long hold:** paused on its start screen (it takes no input, its notices run out); the go loads
  the begin again, so the players start from the users' own screen.
- **The onn during the preparation and the hold** (the TV shows the board): **END** → as today (the mini game given up,
  the title stopped, the board's session back, then the board's own quit); **Home** → the mini game given up first
  ("the onn's Home during the preparation": the title stopped, the board's session back), then Home acts on the board
  as today (the stream stops, the board paused); RESUME then resumes the board as today (no mini game on). The title is
  never left running.
- **Rows** (`party.jsonl`): `minigame_start` gains `"hold": true` only when held; **`minigame_ready`
  `{"prepare_s"}`** (the start to `recognised`); **`minigame_go` `{"held_s", "remembered"}`**; **`minigame_playing`
  gains `"handover_s"`** (the go to `playing`) when held; `minigame_reloaded` `{"loaded": true}` at the go. Without
  `hold`: today's rows exactly.

## Tests (`tests/b133_party_prepare_go/`; B114's scenario, a `hold` mode; B101's fake RetroArch under a fake setup,
B108's stand-in board, B103's scripted pictures, the onn's thread and the calls every 0.1 s)

The rows in order — no `minigame_route` / `minigame_stream` before `minigame_ready` and `minigame_go`; the stream's
captured window the board's until the go; go before ready (remembered), go after ready, a second go; a hold of a few
seconds with the board asking → still `ready`, then the go → `playing` and ended as today; the board stops asking
(`poll_gone_s` scaled) → `given_up`, the title gone, no route ever; notices-like pictures then the start → `ready`;
never the start → `given_up`, no route, no switch, the title's process gone, the board's session back; END from the
board, END and Home from the onn, a second start — each during the preparation and during the hold, every route < 2 s,
nothing left running; T89-shaped (N64: the loads only while paused) and T88-shaped back to back; no `hold` → hands over
as today; the flags absent → HEAD's answers; B110 / B112 / B114 / B115 / B124 / B127 / B131 green.
