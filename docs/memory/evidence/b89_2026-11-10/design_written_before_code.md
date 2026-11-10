# B89 — the mapping picture, smaller and better drawn (client; design, hashed before code)

**Baseline:** HEAD `051bb4d0` (B86's picture in the client). **Switch:** B86's — default on;
`debug.privyhub.mapping_picture=0` = today's editor (no picture), unchanged.

**The user's line (HOME-12R C50):** "Much clearer" — but "It's a big poorly drawn controller at the top." B86's view
measured itself at half its width in height (on the TV's dialog: most of the screen) and drew a body, two grip boxes, a
cross and circles as separate strokes, the labels placed by point with no box, stick directions only when changed.

## The design

1. **One geometry, readable on the JVM** (`streaming/MappingPicture.kt`, pure Kotlin):
   - `ASPECT` (height / width) and a list of **shapes** in a unit box: the **outline** (one closed polygon: a body with
     two rounded grips, symmetric, generated from a few arcs — a plain gamepad, no brand marks, no product's shape),
     **shoulders and triggers** (rounded rectangles above the body), **the D-pad** (a cross, left), **four face
     buttons** (circles, right), **two sticks** (circles, lower middle), **Select / Start** (small rounded rectangles,
     centre). One stroke width for every line.
   - **A label box per control** (its id = the pad's control, as `pictureLabels`): inside the control (face buttons,
     shoulders, triggers, sticks' presses, the D-pad's arms) or beside it (Select / Start under theirs; the stick
     directions around their stick). No two boxes overlap (a test).
   - **Short labels** for the box: the game's letter (`A` `B` `X` `Y`), `L1` … `R3`, `SEL` / `START`, arrows for
     directions (`↑ ↓ ← →`, a stick's as `L↑` …); a control sending nothing `—`; two targets `A+B`.
   - **The size rule** (`pictureSize(availableWidth, screenHeight)`): the height at most **one fifth of the screen's
     height**, the width from `ASPECT`, never wider than the space — so the editor's rows show below without scrolling
     past the picture.
   - **`svg(mapping, default)`**: the same shapes and labels as an SVG document (for the record).
2. **`streaming/ControllerPictureView.kt`:** draws exactly those shapes and boxes with `Canvas` (the outline as one
   path, one stroke width), each label scaled to fit its box, the changed ones in the accent colour; `onMeasure` uses
   `pictureSize` with the display's height.
3. **The render off the device:** a JVM test (`B89MappingPictureTest`) writes, when `B89_RENDER_DIR` is set, the three
   cases — **the default, a bottom / right swap, a many-button remap** — as **SVG** (from `svg()`) and **PNG** (the same
   shapes through `java.awt` in headless mode), copied to `evidence/b89_2026-11-10/render/`. B looks at them before the
   record is written.
4. `MainActivity.kt`: unchanged from B86 (the gate, the rows "Bottom (✕) → B", the legend).

## Tests (`B89MappingPictureTest.kt`, the code the view runs)

The labels per case equal the mapping (default, bottom / right swap, the many-button remap — every control);
**no two label boxes overlap** and each lies inside the picture; every control has a shape and a box; one stroke width;
**the height rule** for a TV (1920 × 1080), a small screen and a narrow space; the outline closed and symmetric; the
SVG holds every label; the switch (`0` / `off`). B86's tests stay green. Mutations.
