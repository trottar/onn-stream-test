# B70 — the two pointers on the TV: the design (written before any B70 code)

Baseline HEAD `94c05e4a` (HOME-9+GC committed, the tree clean). Built in `/tmp/b_q18z_work` (companion/, tools/,
tests/, PrivyHub/ only), applied to the tree after its tests. The user: "there is a mouse on the screen, this has
happened before too. Also the touchpad on the PlayStation controllers I use add a mouse feature which we don't need";
"There are two mouses. The one I saw last match was the Linux one, but the touchpads have their own different style".

## 1. Host — the hub's X pointer in the capture

- **Read:** `NativeStreamManager._build_linux_ffmpeg_command` builds `-f x11grab -framerate 60 -window_id <id> -i
  <display>` with no `-draw_mouse`, so ffmpeg's default `draw_mouse 1` draws the X server's cursor into every frame
  whenever the hub's pointer sits over the game window (the "Linux one").
- **Change:** `-draw_mouse 0` inserted as an x11grab input option (after `-framerate <fps>`, before `-window_id`).
  One module constant `CAPTURE_POINTER_ENV = "PRIVYHUB_CAPTURE_POINTER"`, one helper `_capture_pointer_args()`:
  `PRIVYHUB_CAPTURE_POINTER=1` → `[]` (**the command byte for byte today's**), anything else (absent, `0`, junk) →
  `["-draw_mouse", "0"]`. **Default on** (the queue's rule for this item: `=1` keeps today's).
- The Windows `gdigrab` builder and every other argv are untouched. Every caller of the Linux builder (the start, the
  in-place restart, B15 / B26's fast restarts, `step_in_place`, the ladder) gets the same argument because they all
  call the one builder.
- The GameCube window's own cursor: an X cursor is drawn by the server, not into the window's pixels, so
  `draw_mouse 0` covers it as well (no Dolphin change).
- **Tests** (`tests/b70_capture_pointer`): the argv with the variable absent / `0` / junk carries `-draw_mouse 0`
  exactly once, before `-window_id` and `-i`; with `1` the argv equals the baseline builder's argv (the baseline copy
  imported from a pinned string of today's argv, built with the same fakes); the level-sized (1080p rung) argv and the
  encoder-rate profile path carry it too; a test that the helper is the only reader of the variable.
- **Existing suites** that pin today's argv (if any break) are updated only to the new default, each named in the
  record.

## 2. Client — the pads' touchpad and the onn's pointer (`NativeStreamActivity`)

- **Read:** the PlayStation pads' touchpads reach Android as a pointer device (a touchpad in the pointer's
  presentation: `SOURCE_MOUSE` / `SOURCE_TOUCHPAD`). The stream activity consumes neither: `dispatchGenericMotionEvent`
  hands every motion to `NativeControllerSender.handleMotionEvent` (which takes only joystick / gamepad motion) and then
  to `super`, `dispatchTouchEvent` is today's, no pointer icon is set and no pointer capture is asked. So Android draws
  its pointer (and, for a touchpad, its own touch-spot style) over the picture — the "different style".
- **New pure class `PointerGuard`** (`streaming/PointerGuard.kt`), unit-testable with fake events (an event = its
  `source` and kind):
  - `isPointerSource(source)`: true when `source` has the pointer class bit (`SOURCE_CLASS_POINTER`: mouse,
    touchscreen, stylus, the touchpad in the pointer's presentation) **or** is `SOURCE_TOUCHPAD`, `SOURCE_MOUSE`,
    `SOURCE_MOUSE_RELATIVE` (a captured mouse) or `SOURCE_TOUCH_NAVIGATION` (each by its full bit pattern, so
    `SOURCE_KEYBOARD` / `SOURCE_DPAD` / `SOURCE_GAMEPAD` / `SOURCE_JOYSTICK` never match). The last two go beyond the
    queue's three named sources; disclosed.
  - `consumeMotion(source)`, `consumeKey(source)`, `consumeTouch(source)`: true = swallowed, only when the guard is on
    and the source is a pointer source. A pad's buttons (`SOURCE_GAMEPAD | SOURCE_KEYBOARD`), its sticks / hat
    (`SOURCE_JOYSTICK`) and the remote's D-pad / OK (`SOURCE_DPAD | SOURCE_KEYBOARD`) are never consumed.
  - `onAttach(host)` / `onFocus(host, hasFocus)`: through a small `PointerHost` interface (`hideIcon()`,
    `requestCapture()`, `releaseCapture()`), so tests use a fake host. On: the null icon at attach; capture asked when
    the window gains focus (capture needs a focused window and is dropped by Android when focus goes); nothing when off.
  - `PROPERTY = "debug.privyhub.pointer_hide"`; `parse(value)`: `0` / `off` → off (**today**), anything else (empty
    included) → on (**default on**, B54's rule); `fromSystem()` as `StartGateRearm`'s.
- **The activity (guard on):**
  - **the pointer hidden:** `PointerIcon.getSystemIcon(this, PointerIcon.TYPE_NULL)` set on the root view and on every
    view under it (the surface, the overlays, the prompt / badge / card lines), so the icon resolved over any of them
    is the null icon (`View.setPointerIcon`, API 24+; the onn is API 30+);
  - **the pointer captured:** `root.requestPointerCapture()` at focus gain, with an `OnCapturedPointerListener` that
    returns true for every event (consumed, nothing done). While captured Android draws no pointer and no touch spots
    for the touchpad and sends its events only to that listener. This is what hides the touchpad's own style, which
    an icon alone does not; so the capture is used (the queue's "the pointer-capture API if needed": needed);
  - **events consumed:** `dispatchGenericMotionEvent`: a pointer-source motion (hover, scroll, a touchpad's motion)
    returns true before the controller path and before `super` — no pointer movement, no hover, no scroll;
    `dispatchTouchEvent`: a pointer-source touch (a touchpad click / press as a mouse button) returns true — no click
    on any view; `dispatchKeyEvent`: a pointer-source key (Android's mouse-button fallbacks, e.g. a secondary click
    as `KEYCODE_BACK` from the touchpad) returns true **before** the Back handling, so the touchpad can never leave
    the game; `dispatchTrackballEvent`: consumed.
  - Order: the guard's checks come first in each dispatch; everything else in each method is today's, so the remote's
    D-pad / OK / Back and the pads' buttons and sticks reach exactly today's code.
- **The DualShock / DualSense touchpad press, settled:** it arrives from the touchpad's own input device as a
  pointer button (a click), not as a pad button: the gamepad device reports no key for it (Android's DS4 / DS5 key
  layouts map the face, shoulder, Select / Start / PS and stick buttons only). No PrivyHub mapping uses it (the PS1,
  N64 and GameCube layouts have no such button). **Default: swallowed with the rest of the touchpad, listed** in the
  record and KNOWN_ISSUES as "not a button; ask if wanted".
- **Off (`debug.privyhub.pointer_hide=0`):** no icon set, no capture asked, nothing consumed — `dispatch*` today's
  byte for byte in behaviour (the guard's methods return false and do nothing when off).
- **Tests (JVM, `B70PointerTest`, fake events and a fake host):** a touchpad motion (`SOURCE_TOUCHPAD`) → consumed,
  and the fake host got the null icon and the capture at focus; a mouse hover / a touchscreen-class touch / a
  pointer-class key → consumed; a D-pad key (`SOURCE_DPAD | SOURCE_KEYBOARD`) → passed; a pad button
  (`SOURCE_GAMEPAD | SOURCE_KEYBOARD`) → passed; a stick motion (`SOURCE_JOYSTICK`) → passed; off → nothing consumed,
  no icon, no capture; focus lost → no capture asked; the property parse (empty / `1` / `0` / `off`).
- **Mutations:** the pointer-class test removed; the guard on when off; `SOURCE_TOUCHPAD` dropped; the capture not
  asked at focus.

## 3. Files, the APK

- Host: `companion/native_stream.py` (+ the new suite). Client: `PointerGuard.kt` (new), `NativeStreamActivity.kt`,
  `B70PointerTest.kt` (new). B70's client part goes into the queue's APK (B5 … + B54 + B67 + B70 + B71; B27 / B29
  out).
- Record `evidence/B70_POINTERS_2026-11-09.md` + `b70_2026-11-09/` (this design + its hash, the diff, the tests ×3,
  the mutations, the proof, redact / title checks, the manifest); `patches/B70_POINTERS.md`.
- Live: the host default at the companion's next restart (A's sitting); the client with the new APK's install.
