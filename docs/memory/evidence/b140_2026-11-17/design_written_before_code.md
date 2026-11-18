# B140 — design, written before any code (hashed: `design.sha256`, the time in `design_hashed_at.txt`)

Queue: `handoffs/QUEUE_2026-11-17AW.md` §B140. Behind `PRIVYHUB_PARTY=1` (with `PRIVYHUB_H7=1`) and a held start only;
either flag absent → today; a start without `hold` → B110's order.

## The facts

T88 shows its begin from 2 frames after the paused load (H7-D2 pass P); T89 showed it with no frame advanced in pass P,
not for 15 s after the party's load + 2 immediate frames (H7-V6), and after 30 more (pass Q). A fixed count is a guess.

**The measure, from H7-D2's kept pictures** (`b139_2026-11-17/scripts/change_measure.py`, read only): both grabs grey,
64 × 48 (BOX); **the share of cells moved by more than 16 grey levels.** A paused window against itself: **0.0**;
RetroArch's notices fading (T88): ≤ 0.035; T89's begin with its banner and notices changing: ≤ 0.096; **the boot frame →
the begin: ≥ 0.513 (T88, 54 pictures), 0.565 (T89)**. **Threshold 0.20.** (With B139's settings RetroArch draws
nothing, so only the core's picture moves.)

## The rule (B137's order, the fixed 2 replaced)

`_prepare`: `preparing` → paused → **a grab of the window before the load** (the watch's own picture source) → the mute
on → the watch's load (the begin) → **steps of 0, 2, 4, 8, 16, 30 frames (cumulative 0, 2, 6, 14, 30, 60)**: each step's
`FRAMEADVANCE`s 50 ms apart (each counted 1:1 at ≥ 50 ms, B137's settle), then **80 ms**, then a grab — **done when the
grab moved ≥ 0.20 from the pre-load grab, or the watch has already named the start** → the mute off → the watcher
reads (unmasked, B139). **The cap: 60 frames** — the window never changed → **the preparation fails plainly: "the title
did not show its starting point"** (given up at once, no route, no switch, the title stopped), not "not recognised" 15 s
later. A pre-load grab that fails (no window yet) → the read naming the start is the only way out, the same cap.

- **The mute:** the scratch copy + the load line (~25-60 ms) + per step (frames × 50 ms + 80 ms + the grab, ~20-60
  ms). **T88 (2 frames): ~0.3-0.4 s. A title that shows the begin at the load (step 0): ~0.15-0.2 s. T89 if it needs
  30: ~2 s. The cap (60 frames, 6 grabs): ~3.9 s** — paid only by a title that never shows its begin, whose preparation
  then fails. The board loses the players' presses for the mute's length (it reads the same pads).
- **The row** `minigame_frame_advance` `{"frames", "batches", "mute_ms", "changed", "moved", "paused"}` (`batches` = the
  steps run, `moved` = the last measure, `changed` true / false).
- Constants `ADVANCE_STEPS = (0, 2, 4, 8, 16, 30)`, `ADVANCE_GAP_S = 0.05`, `ADVANCE_SETTLE_S = 0.08`,
  `BEGIN_MOVED = 0.20`; the layer's copies (`advance_steps`, …) scaled in tests.

## Tests (the real HTTP server; B137's `nopress` scenario extended)

The fake title shows its begin after **0, 2, 12 and never** frames following a load (PS1-shaped); presses from every pad
every 0.2 s throughout. → `ready` in the first three with the frames the row names (0, 2, 14 cumulative), the plain
failure in the fourth (`given_up` "…the title did not show its starting point", no route, no switch); never unpaused
before the go; nothing but neutral written while a frame could take it; the practices' ways back the same; B137's
cases green with the row's new fields; the flags absent → today.
