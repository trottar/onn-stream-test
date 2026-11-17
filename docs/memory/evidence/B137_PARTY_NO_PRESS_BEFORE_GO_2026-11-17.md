---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AV) — nothing a player presses reaches a held title before the go, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). Settled first (B61's form, made-up fixtures, disclosed): a state loaded into a paused PS1 core shows only after a frame — one FRAMEADVANCE shows it; the N64 core's load runs a frame itself (shown at once) and that frame reads the pads; each FRAMEADVANCE is one frame, GET_STATUS stays PAUSED, the window keeps it; >= 50 ms apart every command counts. And RetroArch draws "Paused." in the window's top-right corner for as long as a core is paused: offline, 0 of T88's 150 kept start pictures read as the start with it pasted (its text breaks the reader's black-bar cut), 150 / 150 with that corner painted black. Built: paused → the bridge's mute (every pad neutral, every report dropped) → the watch's load → 2 FRAMEADVANCE 60 ms apart → the mute off (~0.2-0.3 s; the board loses those presses too) → the watcher reads the paused window with the label's corner masked → ready; the go: route, switch, resume — no second load; a practice's way back pauses first. Tests 10 (3 runs), HEAD's code with the same presses → "not recognised". Nothing adopted; nothing committed
---

# B137 — nothing a player presses reaches the title before the go

Queue: `handoffs/QUEUE_2026-11-17AV.md` §B137. T88 = H7's two-player PS1 title; T89 = the users' four-player N64
title. The directory is `b137_2026-11-17/`: the design + `.sha256` (hashed 21:42:16Z, before any companion code; the
settle's probes ran before it), `scripts/` (the fixtures and probes), the results (`advance_probe_*_result.json`,
`label_probe_*_result.json`, `overlay_check_result.json`, `t89_begin_check_result.json`), `b137.diff`, `tests_x3.txt`,
`tests_mutations.txt`, `tests_others.txt`, the checks, `manifest.sha256`. Patch: `patches/B137_PARTY_NO_PRESS_BEFORE_GO.md`.
No title, id, `profile_id`, character or cheat name or path; no picture in git (the label's crop and the probes'
grabs stayed in a scratch folder, removed). **Disclosed probes (B61's form):** the hub's RetroArch AppImage with its
N64 core on a made-up ROM (`scripts/fixture_counter_rom.py`, built on B61's) and with its PS1 core on a made-up PS-EXE
(`scripts/fixture_counter_psexe.py` — not side-loaded under the core's built-in OpenBIOS, so **the PS1 runs show
OpenBIOS's own boot animation**; no BIOS file exists on the hub and none was used), temp config / states / saves /
system / XDG folders, read-only copies of the hub's two core option files (one run with the PS1 option file's
"skip BIOS" turned on in the copy), the joypad driver null (it fell back to udev: the hub has no joypad device, so it
read nothing), RetroArch's network remote standing in for pad 1; no stream, no game, no title; nine runs of ~40 s
(21:21Z-21:35Z) on the hub's display. **Offline, nothing started:** T88's / T89's end-screen specs (the rules
folder), the watcher's kept pictures (`runtime/h7_frames/`) and T89's kept begin picture, read only. **Godot headless
only**, once: B111's own check of the board in its scratch copy (the board's repo not touched, its status unchanged).

## Settled first

1. **A state loaded into a paused core, then RetroArch's `FRAMEADVANCE`** (`scripts/advance_probe.py`). The N64
   fixture draws a frame counter (two bits a colour channel) and a bar that is white while any pad-1 button is down,
   both with the RDP, so the hub's GLideN64 renders them; it reads pad 1 through the PIF every frame.

   | | N64 core (counter) | PS1 core (OpenBIOS animation; whole-picture difference, 0-255) |
   | --- | --- | --- |
   | the window after the load, paused | **the saved frame at once** (counter = the saved one, 2.5 s) — **the load runs a frame** | **unchanged**: identical to before the load (difference 0.0 from it, 74 from the saved picture), 2.5 s |
   | after 1 `FRAMEADVANCE` | saved + 1 | **the saved picture, one frame on** (1.0 from it, 74 from the old) |
   | after each further one | + 1 each (5 / 5) | moves one frame each (1.3, 1.8, 2.2, 2.4) |
   | `GET_STATUS` | `PAUSED` throughout | `PAUSED` throughout |
   | the window, 4 s after | the advanced frame, kept (redrawn) | the same |
   | 5 commands 2 ms / 20 ms / 50 ms / 100 ms apart | 1 / 4 (5 in the other run) / 5 / 5 frames | moves as the frames |
   | pad 1 held, paused, no advance | the bar stays black: **a paused core reads nothing** | — (OpenBIOS reads no pad) |
   | pad 1 held, 1 advance | **the bar white: the advanced frame read the pad** | not shown |
   | pad 1 held through the load | **the loaded frame's bar white: the load's own frame read the pad** | the picture unchanged (no frame) |

   **The number sent: 2 frames, 60 ms apart, then 60 ms** (the PS1 core needs 1, the N64 core 0: one frame of margin;
   ≥ 50 ms apart every command counted in both runs, 20 ms apart once lost one). **What the PS1 core cannot show
   without a title:** the frames' count by a counter and whether its advanced frames read the pads (the made-up
   program never ran under OpenBIOS); RetroArch reads every port at every frame it runs on any core, and A's bench (the
   real title) shows the rest.
2. **RetroArch draws "Paused." in the window's top-right corner for as long as a core is paused**
   (`scripts/label_probe.py`, the PS1 core full screen = T88's shape and 960 × 720 = T89's): there at 0.5, 3, 6, 12 and
   25 s and after an advance, gone while running; **the same 783 bright text pixels in both window sizes** (the box
   ~170 × 55 px at the top-right). B133's order never read a paused window; this one does.
3. **What the watcher makes of it — offline** (`scripts/overlay_check.py`; T88's spec and the watcher's own kept
   pictures, 515; `overlay_check_result.json`):

   | T88's kept pictures | as kept | the label pasted | a black box instead | **the label pasted, then B137's mask** |
   | --- | --- | --- | --- | --- |
   | start (150) | start, margin 0.1835-0.1871 | **0 start (all `other`)** | 150 | **150, the same margins** |
   | end_P1 / end_P2 (9 / 6) | as labelled | 0 / 0 | 9 / 6 | **9 / 6** |
   | other (335) | other | 335 | 335 | **335** |

   T88's picture has black bars; the reader finds the game inside a window by cutting edge columns no brighter than
   the darkest + 16 — the label's white text lies in the right bar, the cut fails, nothing reads as the screen.
   **T89:** no kept start picture of its window (its 90 kept pictures are B129's desktop grabs, all `other` either
   way); its start mask has 251 of its 8,826 cells in the label's corner; its one kept begin picture (a 320 × 240 core
   screenshot, no start read) moves by **+0.0014** in the screen distance with the label pasted and +0.0003 masked
   (`t89_begin_check_result.json`), against a gap of 0.067 between its worst learnt start (0.026) and its threshold
   (0.093) — **shown small, not proven; A's bench (H7-V6) shows it.**
4. **The hub's loads** (`h7_results` rows: 30): RetroArch's load line 24-58 ms after the command.

**So: the frame advance gives the window the begin on both cores, and the watcher reads it paused only with the
label's corner masked — built.** The fallback the queue names (the pads' reports dropped for a whole run-behind
preparation) is not what the bench shows is needed, and is **not built**.

## Built (`b137.diff`: `companion/party_minigame.py`, `companion/h7_minigame.py`, `companion/native_session_io.py`)

- **From the launch's answer to the go the title is never resumed.** `_prepare` (the first preparation and every way
  back): `preparing` → paused → **the bridge's mute on** (`party_mute`: every pad written neutral — a companion-injected
  meta button kept — then every report dropped; the flag set and read under the meta lock, so no report is written
  after the neutral one) → **the watch's start with the load** (the begin; the watch told to mask the label) →
  **`FRAMEADVANCE` × 2, 60 ms apart and 60 ms after** (each its own manager call) → `GET_STATUS` (`PAUSED`, else paused
  again and said) → **the mute off** → **`minigame_frame_advance` `{"frames": 2, "mute_ms", "paused"}`** → the watcher
  reads the redrawn, paused window while the notices run out → `recognised` → `ready`. The mute is released on every
  way out (`finally`; the end's steps clear it too).
- **The mute covers the load as well as the advances** (the N64 core's load runs a frame that reads the pads): **~0.2-0.3
  s on the hub** (the scratch copy + the load line, 24-58 ms + 2 × 60 ms + 60 ms). **The board loses the players'
  presses in that instant too** (it reads the same virtual pads); the PC side's load screen says "Getting the game
  ready" meanwhile.
- **The label mask** (`h7_minigame`): `start(…, mask_label=True)` (only the party layer passes it; the HTTP `h7-start`
  never does) and `label_mask(on)`; while on, the top-right `LABEL_BOX` (200 × 70 px: the box with a margin) of every
  picture is painted black before it is read; the `watching` row says `"label_mask": true` only then. **Off at the go**
  (before the resume): the playing title is read as today.
- **The go:** the route → the planned switch → (a practice: the Start hook) → the mask off → **resume** — **no second
  load when the title has not run since its begin was loaded** (always so now: no `minigame_reloaded`, no "state
  loaded" notice in the players' first seconds); were it ever otherwise, the begin is loaded again under the mute.
- **A practice's way back:** **paused first, while its pads are still routed**, then the route cleared, the planned
  switch to the board, then `_prepare` (the begin loaded again under the mute, the frames advanced). The onn sees the
  paused title ("Paused.") for the switch's ~1-4 s, then the board.
- **Not changed:** what is pressed before the launch's answer (RetroArch starting the title, unrouted, before the
  pause — whatever reaches it then is replaced by the begin's load); RetroArch's hotkeys while paused (two-button
  pairs with the pad's Select; the board's buttons are A, B, Y and the d-pad); the bounds; B134's practice; B133's
  ends, Home, END, a second start; a start without `hold` (B110's order).

## Tests (`tests/b137_party_no_press/`, 10; B114's scenario, its new `nopress` mode — the real HTTP server)

B101's fake RetroArch taught `FRAMEADVANCE` and a title: running, it reads the virtual pads every 1/60 s and **leaves
its start screen when any button but neutral reaches it**; an advance runs one frame; its load puts the begin back
(PS1-shaped: shown at the next frame; N64-shaped: the load runs a frame, reading the pads); notices cover its picture
0.6 s after a load; its own log. The watcher's picture follows the fake ("Paused." drawn in its corner while paused);
every write to a virtual pad recorded. **A confirm press (A) from each player through the bridge every 0.2 s from the
start call to the go.**

| test | shown |
| --- | --- |
| T88-shaped | `ready`, `recognised` true; **from the launch's answer to the go: no resume, every frame the fake ran saw neutral pads, it never left its start, 1 load, 2 advances**; presses sent inside each mute, **none written to a pad there** |
| the go | `taken`; **rows start, launch, watch, frame_advance, ready, go, route, stream, playing — no `minigame_reloaded`, no load after the go**; `playing` on the begin; frames 2, `paused` true, the mute's ms in its row; ended end_P1 [1, 0] |
| the label | every paused read had the corner masked; no running read after the go had it |
| three practices, presses throughout | each way back: **paused while still routed** (3 / 3), then the same checks to the next go; `practices` 1, 2, 3; then a real go → end_P2 [0, 1]; 4 frame-advance rows, no reload |
| T89-shaped (N64, four pads, a remembered go) | **the load's own frame and the 2 advanced saw neutral pads**; `playing` on the begin; places [2, 1, 4, 3] → scores [3, 4, 1, 2] for seats 3,1,4,2 |
| never the start (the begin shows a fight) | `given_up` "…not recognised", no route, no switch, **never resumed** |
| during the mute (the advance slowed) | the board's end, the onn's Home (then RESUME → the board), a second start (400), the onn's END (the board quits): **the mute released**, the title gone, closed, no route, no switch |
| routes | every route < 2 s; nothing left running |
| **HEAD's code** (`498ff031`, B133's order), the same presses | **`given_up` "the title's start screen was not recognised"** — the fault; **with no presses → `ready`** (the control) |
| flags absent | HEAD's companion and mine: the party routes, status, Home, stop byte for byte (three flag sets) |

**Mutations** (`tests_mutations.txt`), each on my code: the mute a no-op → 4 fail; the label mask off → 1; the reload
kept at the go → 3; B134's way back (the pause after the switch) → 1. **B133's test** expected B133's rows: its two
row lists updated for B137's order (`minigame_frame_advance` at the preparation; no `minigame_reloaded` at the go) —
its other checks unchanged and green. **Runs** (`tests_x3.txt`): B137 10, B133 9, B134 5 — three runs each; the others
once (`tests_others.txt`).
