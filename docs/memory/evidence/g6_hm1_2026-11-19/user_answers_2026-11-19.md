# G6-HM1 — the user's answers to the design's open questions (2026-11-19)

The design `design_written_before_code.md` (sha256 `c38dbd82f54b130f28c1d8a69820fa869f502d43acf23b33791cc6832e2953da`,
`design.sha256`) is not edited. These answers settle its §10 and are read with it. G6-HM2 starts only on the user's
word.

| Q | The user's answer | What it fixes in the design |
|---|---|---|
| Q1 | **(c)** | When a real pad is P1, the lower region shows a small status panel (players joined, the link notice's line), not the touch pad. |
| Q2 | **(d)**, confirmed: the reading below | **Handheld mode only, and only against the touch pad.** A real pad's hold joins it as the next player at 0.5 s, as today. If the same hold goes on to **2 s**, that pad moves to P1, its earlier slot is freed, and the touch pad goes inert (the lower region becomes Q1's panel). A real pad never takes P1 from another real pad, and the onn's behaviour is unchanged. This deliberately extends D2's "does not displace" for the touch pad only. |
| Q3 | **(b), (i)** | The 5 s count from the gameplay release (`NSA:3494`): hook H6 `onGameplayReleased()` is added and H5 is not. After every unpause the 5-s rule runs again, as for real pads. |
| Q4 | **(b)** | Today's prompt line, plus a "Touch controls: P1 in 5…" countdown in the pad region. A touch during the wait does not join early. |
| Q5 | **(c)** (after the plain-words re-ask; the first answer was "A I think") | In handheld mode, Back does nothing during a game: a Back key, an edge swipe, or a controller's Back. A small **End** button in the touch area ends the game to the paused picture (SAVE / LOAD / END). It stays there when the status panel (Q1) replaces the touch buttons. |
| Q6 | **(b)** | Every system gets the touch pad in stage 1, with the PS1 layout (buttons a system lacks do nothing) until its own layout exists. |

## What the answers add to the design (proposed; for G6-HM2)

- **Q2:** one more additive `PlayerPrompt` method, used only by the handheld subclass. It notices a joined pad's
  joining key still held at 2 s (the hold that joined it at 0.5 s), and moves that pad to slot 0 only when slot 0's
  holder is the touch pad's key `01097c`. It never runs on the onn, because nothing there calls it and no touch pad
  exists. JVM tests: a 0.5-s hold → P2; held on to 2 s → P1, and the touch pad has no slot; lifted at 1.9 s → stays P2;
  slot 0 held by a real pad → no takeover; the takeover when P2 was the pad's own slot frees P2.
- **Q5:** the subclass overrides `dispatchKeyEvent` (`NSA:4618`) to swallow `KEYCODE_BACK` and then calls `super` for
  every other key. The base gains one more hook, **H9**: `protected fun endToPausedFrame() = capturePausedFrameAndFinish()`
  (`NSA:4345`). It is a new member that the base never calls, so the onn's Back (`NSA:4641-4653`) is unchanged. The End
  button calls it. The edge-swipe exclusion (§7) stays, so that a swipe does not show the system bars mid-game.
- **Q3:** H6 is added and H5 is not, as above.

All the design's questions are now answered. G6-HM2 (the bench logic and its JVM tests) starts on the user's word.
