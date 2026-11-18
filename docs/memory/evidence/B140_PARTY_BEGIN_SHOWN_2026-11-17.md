---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AW) — the paused begin made sure of before it is read, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). B137's fixed 2 frames replaced: a grab of the window before the load; after the paused load, frames in steps of 0, 2, 4, 8, 16, 30 (cumulative 0, 2, 6, 14, 30, 60 — the cap), 50 ms apart, 80 ms, a grab — done when the grab moved >= 0.20 from the pre-load one (the share of 64 x 48 cells moved by more than 16 grey levels; H7-D2: a paused window 0.0, RetroArch's notices <= 0.10, the boot frame → the begin >= 0.51) or the watch has read the start; never → given up at once, "the title did not show its starting point". The mute: ~0.3-0.4 s for T88 (2 frames), ~0.15-0.2 s for a begin shown by the load, ~2 s if T89 needs 30; the cap ~3.9 s, paid only by a title that then fails. Row minigame_frame_advance {frames, batches, mute_ms, changed, moved, paused}. Tests 3 (x3); mutation 1 / 1. Nothing adopted; nothing committed
---

# B140 — the paused begin made sure of before it is read

Queue: `handoffs/QUEUE_2026-11-17AW.md` §B140. The directory is `b140_2026-11-17/`: the design + `.sha256` (hashed
00:25:47Z, before any code), `change_measure.py` + `change_measure_result.json`, `b140.diff` (on B139's), the checks,
`manifest.sha256`; the runs in `b139_2026-11-17/`. Patch: `patches/B140_PARTY_BEGIN_SHOWN.md`. Offline only, read only
(H7-D2's kept pictures); nothing started.

## The facts and the measure (`change_measure_result.json`)

T88 shows its begin from 2 frames after the paused load (H7-D2 pass P); T89 showed it with no frame advanced in pass P,
not for 15 s after the party's load + 2 immediate frames (H7-V6), and after 30 more (pass Q) — a fixed count is a
guess. **The measure:** both grabs grey, 64 × 48 (BOX); **the share of cells moved by more than 16 grey levels.**

| pair (H7-D2's pictures) | moved |
| --- | --- |
| a paused window against itself (T88's boot frame, 9-12) | **0.0** |
| RetroArch's notices fading (T88, 3-8 against 12) | ≤ 0.035 |
| T88's paused begin among itself (13-47) | ≤ 0.048 |
| T89's begin with its banner and notices changing (2-10) | ≤ 0.096 |
| **the boot frame → the begin** | **T88 0.513-0.526; T89 0.565** |
| (with RetroArch's content banner on the boot frame, T88 1-2: what B139 removes) | up to 0.636 |

**Threshold `BEGIN_MOVED = 0.20`.**

## Built (`b140.diff`: `companion/party_minigame.py`)

- `_prepare`: paused → **a grab of the window before the load** (the watch's own picture source) → the mute on → the
  watch's load → **`_advance`: steps `ADVANCE_STEPS = (0, 2, 4, 8, 16, 30)`** — each step's `FRAMEADVANCE`s 50 ms apart
  (`ADVANCE_GAP_S`; each counted 1:1 at ≥ 50 ms, B137's settle), **80 ms** (`ADVANCE_SETTLE_S`), a grab: done when it
  **moved ≥ 0.20 from the pre-load grab**, else when **the watch has already read the start**; the cap: the steps' sum,
  **60 frames** → the mute off → **`minigame_frame_advance` `{"frames", "batches", "mute_ms", "changed", "moved",
  "paused"}`** → `changed` false: **given up at once, "the mini game did not start: the title did not show its starting
  point"** (no route, no switch, the title stopped — not "not recognised" 15 s later). A pre-load grab that fails leaves
  the read as the only way out, the same cap.
- **The mute** (the board loses the players' presses for it): the scratch copy + the load line (~25-60 ms) + per step
  (frames × 50 ms + 80 ms + the grab, ~20-60 ms) — **T88 (2 frames, 2 steps): ~0.3-0.4 s; a begin shown with the load
  (step 0): ~0.15-0.2 s; T89 if it needs 30 frames (5 steps): ~2 s; the cap (60 frames, 6 grabs): ~3.9 s**, paid only by a
  title that never shows its begin — whose preparation then fails.

## Tests (`tests/b140_party_begin_shown/`, 3; B137's `nopress` scenario — the fake title shows its begin N frames after a load)

| test | shown |
| --- | --- |
| begin after 0, 2, 12 frames | `ready`; rows **frames 0 / 2 / 14 in 1 / 2 / 4 steps**, `changed` true, `moved` ≥ 0.20, `paused` true; **from the launch's answer to the go: never resumed, every frame it ran saw neutral pads, it never left its start, the advances the row names**; nothing but neutral written inside the mute; `playing` on the begin; scored |
| never | **`given_up` "…the title did not show its starting point" in under 10 s**, the row 60 frames in 6 steps, `changed` false; never resumed; no frame with a button; no route, no switch; the title gone |
| the ways back (a 12-frame title, two practices) | `ready` after each, practices 1, 2; the same checks from each practice's end to the next go; 3 rows of 14 frames / 4 steps |

B137's T89-shaped case now advances 0 frames (the N64-shaped load shows the begin) — its expectation updated; its
"never the start" case keeps "not recognised" (the fake's fight is no longer the same picture as its boot frame).
**Mutation:** B137's fixed 2 frames back (`ADVANCE_STEPS = (2,)`) → 3 fail. **Runs:** `b139_2026-11-17/tests_x3.txt`,
`tests_others.txt`.
