# B73 — a one-disc bar (and the off switches) = today, hunk by hunk (`b73.diff`)

**Client only, default on.** The new code changes views only when the bar shows **four** buttons, which means a
multi-disc session (B71's `discs > 1`) with `debug.privyhub.disc_change` on and **`debug.privyhub.paused_bar_fit` on**.
- **A one-disc session never reaches a setter:** `applyPausedBarPlan(false)` goes to `restorePausedBar()`, which returns
  at once because nothing was applied.
- **`paused_bar_fit=0` with four buttons:** the plan equals `TODAY.copy(fourButtons = true)`, which is B71's bar, so the
  same early return.
- **`disc_change=0`:** no fourth button, which is the installed `5f72af4b…`'s bar.

Tests: `oneDiscBarIsTodays` (fit on and off → `PausedBar.TODAY`, END at 940 dp as today); `b71sBarReproducesHome10`
(the property off → B71's 150-dp CHANGE DISC, END at 998 dp). Mutation M3 (the one-disc plan changed) is caught.

| file | hunk | on a one-disc bar / with the property off |
| --- | --- | --- |
| `streaming/PausedBar.kt` | new | `plan()` returns `TODAY` (or B71's) |
| `MainActivity.kt` | `import …PausedBar` | an import |
| | fields `pausedBarFitOn`, `pausedBarSaved`, `pausedBarSavedDiscText`, `pausedBarApplied` | lazy / null / false |
| | `showGameSessionBannerUi`: `applyPausedBarPlan(gameDiscButton.visibility == VISIBLE)` after B71's lines | `false` (or B71's plan) → `restorePausedBar()` → returns (nothing applied) |
| | new `applyPausedBarPlan`, `restorePausedBar` | as above |
| | `showMediaNowPlayingControls` / `hideNowPlaying`: `restorePausedBar()` after the buttons are hidden | returns (nothing applied) |
| | | **after a four-button bar**: the captured widths, margins, disc label, status width and end padding are put back, so the next bar (media, one disc) is today's |
| `B73PausedBarTest.kt` | new | — |

**What can differ after a four-button sitting:** nothing visible. The captured values are the views' own (read from
`layoutParams` / `paddingEnd`), and they are put back exactly, including the XML end padding in px. They are not
recomputed through `dp()`.
