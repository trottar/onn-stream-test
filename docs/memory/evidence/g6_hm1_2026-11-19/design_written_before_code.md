# G6-HM1 — portrait handheld mode: the design, written and hashed before any code (2026-11-19)

Task: `handoffs/G6-HM1_PORTRAIT_DESIGN_TASK.md`. Plan: `architecture/G6_HANDHELD_PLAN_2026-11-19.md` (§4–§6). Brief:
`handoffs/G6_PORTRAIT_INVESTIGATION_HANDOFF_2026-11-19.md`. Context: `evidence/G6_S1_TABLET_FIRST_INSTALL_2026-11-19.md`.
Code read at `f52ce75b` (the tree as committed; nothing under `PrivyHub/` changed). **No code exists for this design.**
It is hashed here (`design.sha256`) and waits for the user's approval; G6-HM2 starts only on the user's word.

**Labels.** **Verified** = read in the code at the cited `file:line`. **Proposed** = this design, not built.
**Assumption** = not checked here; the stage named checks it. **Question** = for the user (§10); not picked here.
Paths: `NSA` = `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`, `NCS` = `…/streaming/NativeControllerSender.kt`,
`PS` = `…/streaming/PadSlots.kt`, `PP` = `…/streaming/PlayerPrompt.kt`, `PG` = `…/streaming/PointerGuard.kt`,
`MA` = `PrivyHub/app/src/main/java/MainActivity.kt`, `MF` = `PrivyHub/app/src/main/AndroidManifest.xml`.

## Fixed inputs (the user, 2026-11-19)

- **D2:** the touch pad becomes **P1** when no real pad has joined as P1 (today's hold-to-join) within **5 s** of the
  game starting. A real pad that joins later takes the next player and does not displace the touch pad.
- **D3:** the **PS1 layout first**: D-pad, four face buttons, L1 / R1 / L2 / R2, Select / Start. Sticks and L3 / R3 come
  in G6-HM5.
- **D4:** tablet landscape keeps today's full-screen fill; no letterbox.
- **D1 (part):** stage 1 picks the mode at launch with a Settings choice, "TV / landscape" (the default) or "Handheld".
  Following the rotation live is G6-HM6.
- **The onn is unchanged.** Today's `<activity>` entry stays byte for byte; the onn never launches the new activity.

## 1. The activity split

**Verified, today:**
- `NativeStreamActivity` is a final Kotlin class (`NSA:33`, `class NativeStreamActivity : Activity(), SurfaceHolder.Callback`).
- Its manifest entry is `MF:53-56`: `.streaming.NativeStreamActivity`, `exported="false"`, `screenOrientation="landscape"`,
  no `configChanges`.
- `onCreate` locks landscape a second time (`NSA:364-365`) and builds everything in one `FrameLayout root`
  (`NSA:377-529`), then `setContentView(root)` (`NSA:531-533`).
- It is launched from one place only: `MA:9178-9182`, in `openNativeGameStream()` (`MA:9166`). No other
  `NativeStreamActivity::class` in the app.

**Proposed:**
- `open class NativeStreamActivity` (the only change to its declaration).
- A new `HandheldStreamActivity : NativeStreamActivity()` in a new file `streaming/HandheldStreamActivity.kt`.
- A new manifest entry, added after `MF:56` and leaving `MF:53-56` byte for byte:
  `<activity android:name=".streaming.HandheldStreamActivity" android:exported="false" android:screenOrientation="portrait" />`.
- **No `configChanges` in stage 1.** Portrait is fixed, so a rotation of the tablet changes nothing. Anything else that
  recreates today's activity recreates this one the same way, because it is the same code. Live rotation (and its
  `configChanges`) is G6-HM6.

**The hooks the base gains.** Each default body is the expression it replaces, character for character, so the onn
runs today's path:

| # | Hook (proposed) | Replaces | Default = today |
|---|---|---|---|
| H1 | `protected open val streamOrientation: Int get() = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE` | the value at `NSA:365` | landscape |
| H2 | `protected open fun wrapStreamLayer(streamLayer: FrameLayout): View = streamLayer` | the argument of `setContentView` at `NSA:531-533` | `root` itself |
| H3 | `protected open fun exemptFromPointerGuard(event: MotionEvent): Boolean = false` | a new first operand at `NSA:4713`: `if (!exemptFromPointerGuard(event) && pointerGuard.consumeTouch(event.source))` | `false`: the guard runs as today |
| H4 | `protected open fun connectedPads(): List<PadDevice> = AndroidPadDevice.connected()` | the five calls at `NSA:795`, `NSA:960`, `NSA:2712`, `NSA:2736`, `NSA:2772` | the same call |
| H5 | `protected open fun onPlayersOpened(selfRestart: Boolean) {}` | a call right after `playerPrompt?.onStartResponse(…)` at `NSA:955-961` | nothing |
| H6 | `protected open fun onGameplayReleased() {}` | a call after `gameplayReleased = true` at `NSA:3494` | nothing |
| H7 | `protected open fun putHandheldReport(report: JSONObject) {}` | one call in `buildSessionReport()` (`NSA:1448`) | nothing: no key added |
| H8 | read-only accessors: `protected val streamSender get() = controllerSender`, `protected val streamPrompt get() = playerPrompt`, `protected val streamSlots get() = padSlots`, `protected val gameplayLive get() = gameplayReleased` | none (new members) | not called by the base |

**H5 and H6:** only the one that the user's answer to Q3 (§10) needs is added; the other is not written.

**Overridden, with no base change.** In Kotlin an `override fun` member of an open class stays open. So the subclass
overrides these and calls `super` first:
- `onCreate` (`NSA:357`);
- `onPause` (`NSA:639`);
- `onWindowFocusChanged` (`NSA:4601`);
- `dispatchKeyEvent` (`NSA:4618`), only if Q5's answer changes Back.

**Stays private (unchanged):**
- `startSession` / `stopSession` / `stopLocalPipeline`;
- the decoder, the receivers and `SurfaceHold`;
- stabilization, link recovery and the gameplay release;
- `capturePausedFrameAndFinish` (unless Q5 needs it);
- the report builder's own body, `pointerGuard` and `pointerHost`;
- every field.

## 2. The portrait layout

**Verified:**
- The `SurfaceView` is `MATCH_PARENT × MATCH_PARENT` in `root` (`NSA:386-397`). That full-screen fill is D4's landscape
  behaviour, and the handheld activity does not change it.
- `surfaceChanged` is empty (`NSA:582-588`): the decoder renders to whatever size the surface has. Its size is set in
  the view, not the codec.
- The overlays are children of the same `root`:
  - status (`NSA:399-437`, top-start);
  - the "Stabilizing" overlay (`NSA:439-470`, `MATCH_PARENT`);
  - the link notice (`NSA:472-485`, bottom-start, 24 px margins);
  - the prompt line and badge (`NSA:487-505`, bottom-centre, bottom margins 48 / 130 px);
  - the N64 card (`NSA:506-528`).
- Keep-screen-on is at `NSA:367-369`, and immersive sticky (fullscreen, hide navigation) at `NSA:371-375`.
- **The paused bar is not in the stream activity.** B73's bar (SAVE · LOAD · CHANGE DISC · END) is drawn by
  `MainActivity` after the stream ends (`MA:15602`). `MainActivity`'s manifest entry has no `screenOrientation`
  (`MF:58-69`), so on the tablet it follows the device.

**Proposed:**
- The subclass's `wrapStreamLayer` (H2) returns a new `HandheldLayout` (a `ViewGroup`) with two children:
  - `root`, unchanged: the video and every overlay. It is laid out at **the full width W × `videoBoxHeight(W)`**,
    where `videoBoxHeight(w) = w * 9 / 16` (integer). This is computed in `onMeasure` from the real measured width,
    never a constant; for W = 1200 it gives 675.
  - the `TouchPadView`, which fills the rest: W × (H − box). On a 1200 × 2000 window that is 1200 × 1325.
- **Every overlay is therefore inside the video box with no change to its code.** Its gravity and margins are
  relative to `root`, which is now the box. The "Stabilizing" overlay covers the box, not the pad.
- The fixed pixel margins still fit a 675-px-high box: the badge's 130 px bottom margin is the largest. This is an
  **assumption** checked at G6-HM3 by looking at the screen.
- Keep-screen-on and immersive are inherited unchanged (they run in `super.onCreate`). `streamOrientation` (H1) is
  `SCREEN_ORIENTATION_PORTRAIT` in the subclass, which matches its manifest entry.
- The paused screen after Back is `MainActivity`'s and follows the tablet's orientation as today. Whether B73's bar
  fits a 1200-px-wide portrait screen is an **assumption** checked at G6-HM3 (B73 already sizes the bar to the
  screen).
- A pure `HandheldGeometry` (no Android types) holds `videoBoxHeight` and the pad layout's fractions (§4). It is
  JVM-tested.

## 3. The touch path into the existing sender

**Verified:**
- The sender keeps four `State`s: `buttons`, `lx` / `ly` / `rx` / `ry` as shorts, `lt` / `rt` as 0–255 ints,
  `digitalLt` / `digitalRt` and `hatX` / `hatY` (`NCS:55-72`). They sit under one `lock` (`NCS:77`).
- The XUSB bits are private constants (`NCS:39-52`).
- `sendLoop` copies all four states under the lock and sends one 36-byte PHI1 packet per player every ~8 ms, whatever
  the input (`NCS:631-729`).
- `resetState` zeroes one state (`NCS:502-516`). `start()` and `stop()` reset all four (`NCS:119-125`, `NCS:145-151`).
  `neutralize()` resets all four and keeps the loop (`NCS:739-746`).
- **The stick sign:** `handleMotionEvent` stores `state.ly = toStick(-ly)` and `state.ry = toStick(-ry)`
  (`NCS:417`, `NCS:419`). Android's `AXIS_Y` is positive downward, so **the sender's `ly` is positive upward**.
- Digital L2 / R2 set `digitalLt` / `digitalRt` (`NCS:246-254`). The loop sends `max(lt, 255 if digital)`
  (`NCS:646-664`).

**Proposed: one new method on the sender, additive (no existing line changed):**

```kotlin
/** G6: one player's whole state from a source with no InputDevice (the touch pad), under the lock.
 *  False (nothing written) for a player outside 0..3. */
fun writePlayerState(player: Int, buttons: Int, lx: Short, ly: Short, rx: Short, ry: Short, lt: Int, rt: Int): Boolean
```

- It sets the eight fields, `digitalLt` / `digitalRt` = false and `hatX` / `hatY` = 0, inside `synchronized(lock)`.
- It **overwrites the whole state**: the touch pad is the only source for its player, so there is nothing to merge.
- `lt` and `rt` are clamped to 0..255.

**Coexistence:**
- `neutralize()`, `start()`, `stop()` and `resetState` zero the touch pad's state like any other. The touch pad
  writes again only on its next event, so **a reset always errs toward release**: a still finger reads released
  until it moves. The subclass also clears its own `TouchPadState` wherever it calls `neutralize()` (§7), so a
  release is never undone by a stale finger.
- The send loop is untouched and never waits on the touch pad.
- The touch pad never calls `handleKeyEvent` / `handleMotionEvent`, so the prompt's key paths (`PP:186-230`) never see
  it.

**When it writes (proposed, in the subclass):**
- `slot = streamSlots?.slotOf(touchDevice)`.
- If `slot == null`, nothing is written: no player yet, the same as an unclaimed real pad's keys going nowhere (B54).
- If `!gameplayLive`, the neutral state is written. This matches `NSA:4663-4667`, where every key is swallowed
  before the gameplay release.
- Otherwise the output of `TouchPadState` is written.

## 4. `TouchPadState` (pure Kotlin, no Android types) — proposed

**Inputs:**
- `down(id, x, y)`, `move(id, x, y)`, `up(id)`, `cancel()` and `reset()`. Coordinates are in the pad view's pixels.
- `layout(w, h)` sets the geometry from `HandheldGeometry`.

**Output:** `Output(buttons: Int, lx: Short, ly: Short, rx: Short, ry: Short, lt: Int, rt: Int)`, which is exactly
the sender's fields. `TouchPadState` carries its own copy of the XUSB values (`NCS:39-52` are private). A JVM test pins
each value: up 0x0001, down 0x0002, left 0x0004, right 0x0008, Start 0x0010, Back (Select) 0x0020, L1 0x0100,
R1 0x0200, A 0x1000, B 0x2000, X 0x4000, Y 0x8000.

**Pointer ownership:**
- A map `pointerId → Control`. At `down`, the finger belongs to the control whose hit area contains it, or to nothing.
- It keeps that control through every `move` until its `up`, or until `cancel()` / `reset()`.
- A finger that slides off its button keeps the button held. A finger that slides onto another button does not press
  it.
- A finger that went down on nothing stays on nothing.

**The D-pad (8-way by angle, with a roll):**
- Each `move` re-reads the angle from the D-pad's centre.
- The circle is cut into eight 45° sectors centred on the four axes and the four diagonals, as half-open intervals
  `[k·45° − 22.5°, k·45° + 22.5°)`. A diagonal sets two bits.
- Inside an inner dead radius of 0.25 r, no direction is set.
- So a thumb rolls from one direction to the next without lifting.

**Face buttons, shoulders, Select / Start:**
- One finger, one button: if hit areas overlap, the nearest centre wins.
- The hit area is the drawn shape scaled ×1.3 (face, Select / Start) or ×1.15 (shoulders), and the D-pad's is 1.5 r.
- **L2 / R2 are digital:** `lt` / `rt` = 255 while held, else 0. L1 / R1 are bits.
- Several fingers at once are independent: two buttons and the D-pad can be held together.

**Release:**
- `up(id)` drops that finger's control.
- `cancel()` and `reset()` drop every finger.
- The output is recomputed from the fingers still held, so a button is held while at least one finger owns it.

**The layout (proposed draft, fractions of the pad region W × H; customization is G6-HM6):**
- L2 (0.03–0.22 W) and L1 (0.24–0.44 W) on the left, R1 (0.56–0.76 W) and R2 (0.78–0.97 W) on the right, all in the
  band y 0.03–0.13 H.
- The D-pad is centred at (0.25 W, 0.50 H) with r = 0.17 W.
- The face diamond is centred at (0.75 W, 0.50 H), with each button's radius 0.07 W, spaced 0.12 W from the centre.
- Select is at (0.40 W, 0.82 H) and Start at (0.60 W, 0.82 H).
- Nothing sits in the bottom 0.10 H, which is kept clear of the home gesture.

**The JVM test list for G6-HM2:**
1. Each control alone: down → its bit (or `lt` / `rt` 255), up → 0.
2. Several fingers at once: the D-pad, a face button and R2 together, then each lifted in turn.
3. `cancel()` with three fingers down → every field 0.
4. A finger sliding off its button keeps it; a finger moving onto another button does not press it.
5. The D-pad's angle edges: just either side of 22.5°, 67.5°, … 337.5°; the dead zone; a roll right → down-right →
   down without lifting.
6. `reset()` mid-press → 0; a later `move` by an old pointer id is ignored.
7. The hit-area margin: a touch just outside the drawing but inside ×1.3 presses; outside it does nothing.
8. Overlapping hit areas → the nearest centre.
9. The XUSB values pinned (above).
10. The stick sign, stubbed for HM5: a finger above the stick's centre → `ly > 0` (the sender's sign, `NCS:417`).
11. `HandheldGeometry.videoBoxHeight(1200) == 675`, and other widths are integer-exact.
12. `HandheldInput.isTouchscreen` (§6) on the touchscreen, stylus, mouse, touchpad, mouse-relative, gamepad and
    joystick source values.
13. The slot rules of §5 on `PadSlots` / `PlayerPrompt` fakes.

## 5. Slots and D2's 5-s rule

**Verified:**
- `PadDevice` is an interface (`PS:45-57`), so a device with no `InputDevice` can implement it.
- `PadSlots.eligible` requires `!isVirtual`, GAMEPAD or JOYSTICK sources, a gamepad button, and (B38) a face button
  plus stick or hat axes (`PS:185-190`).
- The key is the first 3 bytes of sha256(`vendor:product:descriptor`) in hex (`PS:192-196`). The class comes from the
  vendor id, and an unknown vendor is `"gamepad"` (`PS:200-208`).
- The slots live once per process (`PS:212-215`).
- The prompt clears the map at every start that is not a self-restart, which includes every unpause
  (`PP:170-178`, `PP:12-13`). It then shows "Hold any button to join" (`PP:329`).
- `join` is private (`PP:342-368`). It claims the lowest open slot, badges "P<n>", and raises the stored "highest
  joined count" for the title (`PP:365-367`). That count is a private preference file on **this** device
  (`PlayerChoiceStoreAndroid.kt:11,30`).
- **`openSlot` counts a slot as open when its holder is not in the connected list** (`PP:371-376`). The connected list
  today is `AndroidPadDevice.connected()` (`PS:86-87`).
- A 1-player title closes the join after P1 (`PP:330`, `PP:343`).
- Select + Start held 2 s releases a slot, but only on the key path (`PP:214-230`, `PP:383-392`).

**Proposed:**
- **`TouchPadDevice : PadDevice`**, in a new file:
  - `descriptor = "privyhub-touchpad"`, `vendorId = 0`, `productId = 0`, `controllerNumber = 0`;
  - `sources = 0x01000411` (GAMEPAD | JOYSTICK);
  - `hasGamepadButton = hasFaceButton = hasStickOrHat = true`, `isVirtual = false`.
  - Its key is fixed: **`01097c`**, computed from `0:0:privyhub-touchpad`. Its class is `"gamepad"`; `PS:200-208` is not
    changed. The handheld report (H7) names its slot, so it can be told apart.
- **Eligibility:** `isVirtual = false` and the declared sources pass `PS:185-190` unchanged. `isVirtual` exists for
  Android's own virtual input devices, and the touch pad never appears in `AndroidPadDevice.connected()`.
  **Nothing in `PadSlots` changes.**
- **It must be "present":** the subclass's `connectedPads()` (H4) returns `AndroidPadDevice.connected() + touchDevice`.
  Without this, `openSlot` (`PP:371-376`) would treat the touch pad's P1 as open, and a real pad's hold would take P1,
  which breaks D2. The same list also reaches the sender's `connectedPads` (`NSA:795`).
- **Claiming P1 without a hold:** a new additive `PlayerPrompt` method. Nothing existing calls it.

  ```kotlin
  /** G6: a device with no keys (the touch pad) joins now as a hold would: the lowest open slot, the badge, the stored
   *  count. Null = no join (not JOINING, already holding a slot, a 1-player title already has P1, or no slot below the
   *  ports). Never asks for a relaunch. */
  fun joinWithoutHold(pad: PadDevice, nowMs: Long, connected: List<PadDevice>): Int?
  ```

  It runs under `lock`, uses the same `openSlot` / `claim` / `badge` / store lines as `join`, and returns `null`
  instead of setting `relaunchAsk`.
- **The 5-s rule (the subclass):**
  - A timer is armed at the start event (Q3).
  - At 5 s, if `streamSlots?.holderOf(0) == null`, it calls `joinWithoutHold(touchDevice, …)`.
  - If a real pad already holds P1, nothing happens (Q1).
  - The timer is cancelled by `onPause`, by `onDestroy` and by a new start.
  - On a self-restart the map is kept (`PP:170-173`), and the touch pad keeps its slot with no timer.
- **What the prompt shows meanwhile:** today's line, unchanged ("Hold any button to join", `PP:329`, in the video
  box). Whether the pad region adds a countdown is Q4.
- **The stored "highest joined count":** the touch pad counts as a player, because it takes a port. Touch P1 and one
  real pad store 2, so the next launch asks for 2 ports, as B54 maps 1 / 2. Touch P1 and two real pads store 3, so
  the next launch asks for the multitap. The store is this device's own file, so the onn's counts are untouched.
- **A real pad joining afterwards:** its hold runs as today. `openSlot` now sees P1's holder (`01097c`) as present,
  so the real pad gets P2 (`PP:371-376`), as D2 says. On a 1-player title the join is closed after P1, so the real
  pad gets nothing (Q2).
- **Releasing the touch pad's slot:** it has no key path, so today's Select + Start release does not reach it. Q2
  covers this.
- **With the prompt flag off** (`debug.privyhub.player_prompt=0`, not the default): `PadSlots.beginStart` pre-assigns
  every connected eligible pad at the start (`PS:99-108`, `NCS:130`). The touch pad sorts last by controller number 0
  (`PS:198`). D2's timer needs the prompt, so it does not run. Disclosed; the default is the prompt on (`PP:26-27`).

## 6. The pointer guard

**Verified:**
- `PG:27` `consumeTouch(source)` → `take(source)` (`PG:31-35`) consumes when the guard is enabled and
  `isPointerSource(source)`.
- `isPointerSource` is true for any source with the pointer class bit 0x0002, or the full pattern of mouse, touchpad,
  mouse-relative or touch-navigation (`PG:67-68`). `SOURCE_TOUCHSCREEN` (0x1002) carries 0x0002, so **every touch
  is consumed in a game**.
- `dispatchTouchEvent` asks the guard first (`NSA:4711-4717`).
- The guard is on unless `debug.privyhub.pointer_hide=0`, and it captures the pointer at focus
  (`NSA:4601-4606`, `PG:43-52`).

**Proposed:**
- A pure `HandheldInput.isTouchscreen(source) = (source and 0x1002) == 0x1002`, in a new file. `PointerGuard.kt` is
  not changed. The values:
  - touchscreen 0x1002 → true;
  - stylus as reported with the screen, 0x5002 → true. The S Pen then acts as a finger; this is disclosed.
  - mouse 0x2002 → false;
  - touchpad 0x100008 → false;
  - mouse-relative 0x20004 → false;
  - touch-navigation 0x200000 → false;
  - gamepad 0x401 / joystick 0x1000010 → false.
- The subclass's `exemptFromPointerGuard(event)` (H3) returns `HandheldInput.isTouchscreen(event.source)`. So mice,
  touchpads and a DualShock's touchpad (reported as mouse / touchpad) **stay consumed** in handheld mode.
- **The onn's path is unchanged:** H3's default is `false`, and `!false && pointerGuard.consumeTouch(…)` is today's
  expression. `consumeMotion`, `consumeKey` and `consumeTrackball` (`NSA:4622`, `NSA:4687`, `NSA:4720`) are not touched.
- **Assumption, for G6-HM3:** the pointer capture requested at focus (`NSA:2690-2697`) does not hold back
  touchscreen events. Android's capture is for mouse-class devices. HM3 checks this with the pad live, by counting
  touch events.

## 7. Release safety

**Verified:**
- `onPause` calls `controllerSender?.neutralize()` when the surface hold exists (`NSA:639-646`). The hold is on by
  default (`SurfaceHold.kt:25-27`).
- The send loop never stops while the sender runs (`NCS:631-729`), so every player is sent every ~8 ms.
- Back's key-up ends the game to the paused frame (`NSA:4641-4653`).

**Proposed:** each event below clears the touch pad. "Clears" means `TouchPadState.reset()`, then the neutral state
written for its slot.

| Event | Where |
|---|---|
| A finger's up | `TouchPadView.onTouchEvent` `ACTION_UP` / `ACTION_POINTER_UP` → `up(id)` (that finger only) |
| Cancel (a system gesture or a parent intercepting) | `ACTION_CANCEL` → `cancel()` |
| Focus loss (the shade, a dialog) | the subclass's `onWindowFocusChanged(false)`, after `super` |
| The view hidden or detached | `TouchPadView.onVisibilityChanged(≠ VISIBLE)` / `onDetachedFromWindow` |
| `onPause` | the subclass's `onPause`, after `super` (which already calls `neutralize()`) |
| A new start / unpause (the map is cleared) | H5 or H6, then the 5-s rule again |

- **The hub's input hold is never tripped by the touch pad.** It only changes the state's values, never the loop. A
  cleared touch pad sends neutral packets, the same as an idle real pad.
- **Gesture exclusion:**
  - On each layout, `TouchPadView` calls `setSystemGestureExclusionRects` (API 29+, guarded because `minSdk` is 24,
    `build.gradle.kts:20`).
  - It excludes the D-pad's and the face cluster's hit areas where they meet the left / right edges.
  - Each rect is clipped to Android's 200-dp-per-edge limit, centred on the control.
  - The bottom (home) gesture cannot be excluded, so the layout keeps the bottom 0.10 H empty (§4).
  - **Assumption:** the tablet's navigation mode and density; HM3 records them in the handheld report (H7).
- **Back in handheld mode:** today's behaviour stays unless the user's answer to Q5 changes it. An edge swipe is
  Back under gesture navigation. That makes the exclusion rects matter, because a stray edge swipe would end the game.

## 8. `MainActivity`

**Verified:**
- Settings is `showCompanionSettings()` (`MA:1039`). It already holds check boxes: "Open games automatically after
  launch" (`MA:1087-1093`) and "Use paired identity (identity v2)" (`MA:1122-1130`).
- A game opens in `openNativeGameStream()` (`MA:9166-9214`), the only launch.
- `MF:13-15` declares the touchscreen feature as not required.

**Proposed:**
- A "Game screen" choice in `showCompanionSettings()`, after the identity box, with "TV / landscape" (the default) and
  "Handheld (portrait, touch controls)".
- It is stored in a private preference (`privyhub_game_screen`, key `mode`: `tv` | `handheld`).
- **It is shown only when `packageManager.hasSystemFeature(PackageManager.FEATURE_TOUCHSCREEN)`.** An **assumption**
  for the onn: it does not report a touchscreen. If it does, the choice shows but still defaults to "TV / landscape",
  so nothing changes unless someone picks Handheld.
- In `openNativeGameStream()`, the class is `HandheldStreamActivity::class.java` only when the stored mode is
  `handheld` **and** the device has a touchscreen. Otherwise it is `NativeStreamActivity::class.java`, with the same
  intent and the same extras as today (`MA:9183-9212`).

## 9. Proof that the onn is unchanged (for G6-HM2 / HM3)

**The diff checks, run at G6-HM2 on the patch:**
1. **Manifest:** the `NativeStreamActivity` element's bytes (`MF:53-56`) have the same sha256 before and after. The
   diff adds lines only.
2. **`NativeStreamActivity.kt`:** every hunk is one of: `class` → `open class`, H1–H8, and the one-operand change at
   `NSA:4713`. A script checks that each hook's default body equals the expression it replaced, verbatim.
3. **`PadSlots.kt` and `PointerGuard.kt`:** sha256 unchanged.
4. **`PlayerPrompt.kt` and `NativeControllerSender.kt`:** additive only (`git diff --numstat` shows 0 deletions).
5. **`MainActivity.kt`:** the `tv` branch builds the same intent as today, and the Settings view is added only behind
   the touchscreen test.
6. **Every existing JVM test passes unchanged,** with the new ones (§4) added. These include `B70PointerTest`,
   `PadSlotsTest`, `PlayerPromptTest`, `VirtualRemoteNoSlotTest` and `HoldAndSlotsDefaultOnTest`. The real
   `./gradlew :app:assembleDebug` runs too.

**The APK rule:**
- A G6-HM2 / HM3 build is a **candidate**. It goes on the tablet only, sideloaded as a file (no adb, plan §3).
- It **does not replace `ca53df0d…` on the onn** until a pre-registered, hashed confirmation on the onn passes
  (`CL_B7_…_2026-10-19.md` §6). Otherwise the previous CONFIRMED APK goes back on (`CURRENT.md`, the G adoption rule).
- The pins (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`) move only in that
  confirmation's own task.

**The tablet-side cells for G6-HM3 (proposed; the thresholds are pre-registered at HM3's start, not here).** Each is
read from the decoder report the tablet already uploads. G6-S1's session 10 is the reference.

| Cell | Read | G6-S1 reference |
|---|---|---|
| G6-HM3.c1 decode | `decoder.codec_name`, `hardware_accelerated`, `low_latency_enabled` | `OMX.Exynos.avc.dec`, true, true |
| G6-HM3.c2 rate | `video.recent_fps`; `video.frames` against `duration_ms` | 59.4; 1641 in 27.5 s |
| G6-HM3.c3 loss / drops | `video.lost_packets`, `video.dropped_frames`, `decoder.dropped_frames`, `fec_unrecoverable_groups` | 0, 0, 6, 0 |
| G6-HM3.c4 latency | `decoder.latest_rx_to_decode_ms` / `max_rx_to_decode_ms`, `max_output_gap_ms`, `first_clean_idr_ms` | 23 / 55, 136, 370 |
| G6-HM3.c5 the box and the inert pad | the H7 keys: `handheld.mode` = `portrait`, `video_box` = `W×W*9/16`, `pad_region`, `density`, `nav_mode`, `touch_events` (> 0 when touched), `touch_writes` = 0 (inert), `pointer_exempted` | none (new keys) |
| G6-HM3.c6 the onn | the onn's own report after the candidate's onn confirmation: no `handheld` key; the existing rows as the confirmation pre-registers | n/a |

What a person sees (the picture's placement, the overlays' fit, B73's portrait bar) is the user's remark, never a cell.

## 10. Open questions for the user (options only; none picked)

- **Q1. What the lower region shows when a real pad is P1** (the touch pad did not join):
  - (a) the touch pad stays drawn but dimmed and inert;
  - (b) black;
  - (c) a small status panel (players joined, the link notice's line);
  - (d) the touch pad joins as the next free player instead (P2) and stays live.
- **Q2. Whether a later real pad should take over P1 from the touch pad.** D2 says it does not displace it; this asks
  whether there should be a way to hand over:
  - (a) never: the real pad is P2. On a 1-player title it gets no player; the touch pad keeps P1 until the session
    ends.
  - (b) an on-screen Select + Start hold of 2 s on the touch pad releases its slot (mirroring `PP:241-251`); the real
    pad then holds to join.
  - (c) on a 1-player title only, a real pad's hold takes P1 from the touch pad; otherwise (a).
  - (d) any real pad's hold of a set length (e.g. 2 s) takes P1, and the touch pad goes inert.
- **Q3. When the 5 s start:**
  - (a) at the prompt's opening (the start response, `NSA:955`). The picture may still be stabilizing.
  - (b) at the gameplay release (`NSA:3494`), when the game is playable.

  Also, at an unpause (which clears every slot, `PP:170-178`):
  - (i) the 5-s rule runs again, the same as for real pads;
  - (ii) the touch pad re-takes P1 at once if it held it before the pause and no real pad holds within the 5 s.
- **Q4. The 5-s wait on screen:**
  - (a) today's prompt line only;
  - (b) today's line, plus a "Touch controls: P1 in 5…" countdown in the pad region;
  - (c) (b), and a touch on the pad during the wait makes it P1 at once.
- **Q5. Back in handheld mode** (today: Back's key-up ends the game to the paused frame, `NSA:4641-4653`; under
  gesture navigation an edge swipe is Back):
  - (a) keep today's behaviour exactly;
  - (b) a first Back shows "Back again to end" for 2 s, and the second ends to the paused frame;
  - (c) Back does nothing in a game; an on-screen "End" control in the pad region ends to the paused frame. This needs
    `capturePausedFrameAndFinish` (`NSA:4345`) made protected.
- **Q6. Which systems get the touch pad in stage 1** (D3 says the PS1 layout first):
  - (a) PS1 only. Other systems in handheld mode get the portrait box with the pad region as Q1's answer.
  - (b) every system, with the PS1 layout (extra buttons unmapped) until their own layouts exist.

## 11. Stages after approval (from the plan, unchanged)

G6-HM2 bench logic + JVM tests (§4, §5, §9 checks 1–6) → G6-HM3 portrait video with an inert pad (§9 cells; the onn
confirmation before any APK replaces `ca53df0d…`) → G6-HM4 PS1 digital controls live → G6-HM5 sticks, L3 / R3, a
latency video → G6-HM6 live rotation, customization, the battery / heat comparison. Each starts only on the user's
word, under the plan's §3 conflict rules.
