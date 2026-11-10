---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT INSTALLED (session B, queue AF) — the mapping picture redrawn from one geometry (a plain original gamepad, one stroke width, labels in boxes that never overlap) and capped at a fifth of the screen's height; rendered off the device (render/: SVG and PNG, three cases); in APK 3f21e2c6… (pinned, NOT installed). Switch: debug.privyhub.mapping_picture=0 = today's editor (no picture). Nothing committed
---

# B89 — the mapping picture, smaller and better drawn (2026-11-10)

**Why:** HOME-12R's C50: "Much clearer" — but "It's a big poorly drawn controller at the top." B86's view measured half
its width in height (most of the TV's dialog) and placed labels by point, without boxes.

**Baseline:** HEAD `051bb4d0`. **Design** hashed before code at 22:59:45Z (`b89_2026-11-10/design.sha256`).

## What was built (`b89.diff`)

- **`streaming/MappingPicture.kt` — one geometry the JVM reads:** `ASPECT` 0.62; one stroke width; **the outline** —
  one closed polygon built from arcs (a flat top with rounded corners, two rounded grips, a raised middle; symmetric by
  construction; a plain gamepad, no brand marks, no product's shape); triggers and shoulders (rounded rectangles above),
  the D-pad (a cross, left), four face buttons (circles, right), two sticks (circles, lower middle), Select / Start
  (small rounded rectangles, centre); **a label box per control** (inside it, or beside it: under Select / Start, around
  the sticks); **short labels** (A B X Y, L1 … R3, SEL / START, arrows; a stick's directions as L↑ …, drawn only when
  changed); **`pictureSize`**: the height at most **a fifth of the screen's**, never wider than the space; `svg()`.
- **`streaming/ControllerPictureView.kt`:** draws those shapes (the outline as one path), each label scaled to fit its
  box, the changed ones in the accent colour; `onMeasure` = `pictureSize` with the display's height.
- `MainActivity.kt` unchanged (B86's gate, rows and legend).

## The render (`render/`, made by the JVM test from the same geometry; looked at by B before this record)

`default.svg|png`, `swap_bottom_right.svg|png`, `many_button_remap.svg|png` (800 px wide). The default reads B at the
bottom, A right, Y left, X top, the shoulders / triggers / centre / D-pad / stick presses by name, nothing highlighted;
the many-button remap shows the eleven changed controls in yellow (the face pair, shoulders and triggers side for side,
Select / Start, the left stick's press as X and Top as L3, the D-pad's Up and the stick's Up swapped). **The
SVG / PNG renderers are the test's (java.awt, headless); the device draws the same shapes with `Canvas`** — fonts and
anti-aliasing differ, the geometry does not.

## Switch

`debug.privyhub.mapping_picture=0` (or `off`) → B86's gate: no picture, today's editor (unchanged in `MainActivity.kt`).

## Tests (`B89MappingPictureTest.kt`, 7, JVM; B86's 7 stay green)

The labels per case equal the mapping (default, the bottom / right swap, the many-button remap; every control's label is
the inverse of the stored map); **no two label boxes overlap**, all inside the picture, every control has a shape and a
box; **the height rule** (a TV: ≤ 216 px of 1080; a narrow space; a small screen); the outline closed and symmetric;
the SVG holds every label and one stroke width; the switch; the render (with `B89_RENDER_DIR`).

- 3 runs: 7 / 7 each, B86's 7 / 7 (`tests_x3.txt`). Mutations **5 / 5 caught** (`tests_mutations_jvm.txt`) — after
  one fix: the first run missed K1 (only the first of two labels on a control) because no case put two game buttons
  on one control; the test gained that case, K1 then caught; K3's text first did not match the source line (not
  applied), corrected and caught. JVM in the working copy 301 / 301.

## The APK (`apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`, `tests_jvm_apk_copy.txt`)

- **The tree:** HEAD's client (B5 … + B74 + B80's client part + B84 + B86) + **B89** (B88 has no client part), with
  `b29.diff` / `b27.diff` reversed on the client paths.
- **`3f21e2c6aa8caa517b0a76b69701b853ada890a99dbde3295b62551f34e223b1`** (9,759,932 B, 945 entries), built offline twice
  → the same bytes; the baseline rebuilds **`c801caab…` byte for byte**; the same signer (`455bde4e…`); JVM 290 / 290 in
  the APK tree.
- **Pinned** at `PrivyHub/app/build/queue_af_built/app-debug.apk`. **NOT installed.** `85220f99…` stays on the onn.

## Disclosed

- The picture's look on the TV is C53's; the renders are the geometry's, not the device's pixels.
- The many-button case in the test was first written with two game buttons on one control (the test caught it: "Y+L3");
  corrected to a one-to-one remap.

## Files

`b89_2026-11-10/`: start files, the design + hash, `b89.diff`, `render/` (6 files), `proof_flag_absent.md`, `tests_x3.txt`,
`tests_mutations_jvm.txt`, the APK's files, the host-suite comparison and the queue's tree checks, `scripts/`,
redact / title checks, `manifest.sha256`. Patch note: `patches/B89_MAPPING_PICTURE_REDRAWN.md`.
