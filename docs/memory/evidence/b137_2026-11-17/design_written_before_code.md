# B137 — design, written before any companion code (hashed: `design.sha256`, the time in `design_hashed_at.txt`)

Queue: `handoffs/QUEUE_2026-11-17AV.md` §B137. T88 = H7's two-player PS1 title; T89 = the users' four-player N64 title.
Behind `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1` (the mini-game layer exists only then) and only for a held start
(`hold=1`); either flag absent → today byte for byte; a start without `hold` → B110 / B114's path unchanged.

## What the settle showed (B61's form, made-up fixtures, disclosed; `scripts/`, the results in this folder)

1. **A state loaded into a paused core, then `FRAMEADVANCE`** (the hub's RetroArch; a made-up N64 ROM drawing a frame
   counter and pad 1's buttons with the RDP — GLideN64 as the hub has it; the PS1 core's built-in OpenBIOS animation —
   my made-up PS-EXE is not side-loaded under OpenBIOS, so no counter and no pad read on PS1):
   - **PS1 core:** the load leaves the paused window as it was (identical to before the load, 2.5 s); **one
     `FRAMEADVANCE` shows the loaded state** (the picture one frame from the saved one; 74 grey levels from the old).
   - **N64 core:** **the load itself runs one frame** — the paused window shows the loaded state at once — **and that
     frame reads the pads** (pad 1 held through the load: the loaded frame shows it). Each `FRAMEADVANCE` runs exactly one
     more frame, reading the pads.
   - Both: **`GET_STATUS` `PAUSED`** throughout; the window keeps the advanced frame (redrawn); RetroArch's notices run
     out on their timer while paused. Commands 2 ms apart merge into one frame; **≥ 50 ms apart every one counts (5 / 5,
     twice); 20 ms apart once lost one.**
   - **The number sent: 2 frames, 60 ms apart** (PS1 needs 1, N64 0 — 1 frame of margin), then 60 ms for the last to
     run.
2. **RetroArch draws "Paused." in the window's top-right corner for as long as the core is paused** (measured 0.5-25 s,
   still there after an advance; the same text size, 783 bright pixels, in a 960 × 720 and a 1920 × 1080 window; the box
   ~170 × 55 px). **Offline (nothing started; T88's spec and the watcher's own kept pictures, read only): with that label
   pasted, 0 of T88's 150 kept start pictures read as the start (all `other`; the 15 end pictures too)** — the label's
   text lies in T88's right black bar and the reader's bar cut fails. **With the label's corner painted black: 150 / 150
   (the same margins), 335 / 335 `other`, 15 / 15 ends.** T89 (no kept start picture; its start mask has 251 of its
   8,826 cells in that corner): the label moves the screen distance of its one kept begin picture by +0.0014 against a
   gap of 0.067 (worst learnt start 0.026, threshold 0.093) — shown small, not proven: A's bench shows it.
3. **The hub's loads** (`h7_results` rows, 30): RetroArch's load line 24-58 ms after the command.

So the frame advance gives the window the begin on both cores, **and the watcher can read it paused only with the
label's corner masked** — built below. The fallback (the pads' reports dropped for the whole run-behind preparation) is
**not needed by what the bench shows and not built**; if A's bench shows a title not recognised paused, that is the next
change (said in the reply).

## The order (a held start)

**From the launch's answer to the go the title is never resumed.**

- **`_prepare`** (the first preparation and every way back): `preparing` → **pause** → **the mute on** (the bridge:
  every pad written neutral, every report dropped from then) → **the watch's start with the load** (the begin; the watch
  told to mask the label) → **2 × `FRAMEADVANCE`, 60 ms apart** (each its own manager call), 60 ms → `GET_STATUS`
  (`PAUSED` expected; else paused again, said in the row) → **the mute off** → **the row `minigame_frame_advance`
  `{"frames": 2, "mute_ms": …, "paused": true}`** → the watcher reads the redrawn, paused window (the label's corner
  painted black) while the notices run out → `recognised` true → **`ready`** (`minigame_ready` as B133). `recognised`
  false / the watch gone → given up as today (no route, no switch). The mute is released on every way out (`finally`,
  and the end's steps clear it).
- **The mute covers the load as well as the advances** — the N64 core's load runs a frame that reads the pads. Its
  length: the scratch copy + the load line (~25-60 ms) + 2 × 60 ms + 60 ms ≈ **0.2-0.3 s**, said in the row. **The board
  loses the players' presses in that instant too** (the board reads the same virtual pads).
- **The go** (`_handover`): the route → the planned switch → (a practice: the Start hook) → the watch's label mask off →
  **resume**. **No second load when the title has not run since its begin was loaded** (`ran_since_begin` false: always
  so in this order — no `minigame_reloaded` row, no "state loaded" notice in the players' first seconds); were it ever
  true, the begin is loaded again under the mute (as B133).
- **The way back from a practice** (`_way_back`): the Start hook cleared → **pause first** (the title stops taking
  presses while its pads are still routed) → the route cleared → the planned switch to the board → `_prepare` (the begin
  loaded again, the advances under the mute). The TV shows the paused title (RetroArch's "Paused.") for the switch's
  ~1-4 s, then the board.
- **Not changed:** the presses before the launch's answer (RetroArch starting the title, ~2 s unrouted, before the pause
  and the begin's load — whatever reaches the title then is replaced by the load); RetroArch's hotkeys while paused (B133
  as before: the board's buttons are not hotkey pairs); the bounds (START_LIMIT_S for the preparation); B134's practice;
  B133's ends, Home, END, a second start.

## Code (all behind the flags)

- `companion/native_session_io.py`: **`party_mute(on)`** — on: the flag set, every pad written neutral (the forced
  meta buttons kept, as `_neutralize`); off: the flag cleared. `_apply_report` drops a report while the flag is set — the
  flag read again under the meta lock, so no report is written after the neutral one. `_party_mute = False` = today.
- `companion/h7_minigame.py`: `MiniGame.start(…, mask_label=False)` (only the party layer passes it) and
  **`label_mask(on)`** on the current watch; while set, every picture has the label's corner — the top-right
  `LABEL_BOX` (200 × 70 px: the box with a margin) — painted black before it is read; the `watching` row says
  `"label_mask": true` only then. The HTTP `h7-start` never sets it: today.
- `companion/party_minigame.py`: `_prepare` / `_handover` / `_way_back` as above; `_advance` (the commands, the status
  check); `ADVANCE_FRAMES = 2`, `ADVANCE_GAP_S = 0.06`; `mg["ran_since_begin"]`; the end's steps release the mute.

## Tests (`tests/b137_party_no_press/`, the real HTTP server; B114's scenario, a new `nopress` mode)

B101's fake RetroArch taught `FRAMEADVANCE` and a title model: a running fake reads the virtual pads every 1/60 s and
**leaves its start screen when any button but neutral reaches it** (a pick on the select screen → a fight); a frame
advance runs one frame (reads the pads); its load puts the begin back (PS1-shaped: shown at the next frame; N64-shaped:
the load runs a frame and reads the pads); notices cover its picture for a while after each load; its own log of
pauses, loads, advances and every frame's pads. The picture source follows the fake (start / a fight / an end screen;
the "label" drawn in its corner while paused). The virtual pads' writes recorded. **A confirm press from each player
through the bridge every 0.2 s from the start call to the go.**

1. T88-shaped: → `ready`; the fake never unpaused from the launch's answer to the go; every frame it ran in that span
   saw neutral pads; no report but neutral written inside the mute; the rows start, launch, watch, frame_advance, ready,
   go, route, stream, playing — **no `minigame_reloaded`**, the fake's loads 1; the go → `playing` on the begin; ended as
   today; every paused read had the label's corner masked, the mask off after the go.
2. Three practices with presses throughout (Start twice, time once): each way back paused before the route is cleared;
   the same checks from each practice's end to the next go; then a real go scored.
3. T89-shaped (N64, four seats, a remembered go): the load's own frame saw neutral pads; places scored.
4. Never the start (the begin shows a fight): given up "not recognised", no route, no switch, never unpaused.
5. END / Home / the board's end / a second start **during the mute** (the advance slowed): the mute released, the
   title gone, closed; a second start 400.
6. **HEAD's code, the same presses:** T88-shaped → given up "not recognised" (the fault); HEAD with no presses → ready
   (the control).
7. The flags absent → HEAD's answers byte for byte (B133's `Today` against `498ff031`); B133 / B134 and the earlier
   party suites green.
