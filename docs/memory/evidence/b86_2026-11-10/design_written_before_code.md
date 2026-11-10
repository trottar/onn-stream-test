# B86 — the mapping editor's controller picture, and one set of letters (client; design, hashed before code)

**Baseline:** HEAD `c514c543`. **Switch:** default on; `debug.privyhub.mapping_picture=0` (or `off`) = today's editor.
**A display change only:** the stored mapping, its JSON and the save path are untouched.

## What exists (read at HEAD)

- Options → Input Profile → "Edit Player n Mapping" (`showEditInputProfilePlayerDialog`): one row per **target** — the
  button the game receives, in RetroArch's RetroPad names (Nintendo layout: `b` bottom, `a` right, `y` left, `x` top,
  `l` / `r` / `l2` / `r2` / `l3` / `r3`, `select`, `start`, the d-pad, both sticks) — showing "Current: <source>", where
  the **source** is your pad's button in Xbox names (`a` bottom, `b` right, `x` left, `y` top, `LB` / `RB` / `LT` /
  `RT`, `Back`). Both are printed as bare letters, so the hub's default (`a ← b`, `b ← a`, `x ← y`, `y ← x` — the
  identity by position) reads as a swap (HOME-12's wrap-up).
- "Change" opens a list of sources; Save posts the mapping (`inputProfileSavedMapping` → `saveInputProfileMapping`).

## The design

1. **`streaming/MappingPicture.kt`** (new), pure Kotlin:
   - `PROPERTY = "debug.privyhub.mapping_picture"`, `parse()` / `fromSystem()` as `Ps2Patches`.
   - **Your pad's buttons by position and glyph** (`padLabel(source)`): `a` → "Bottom (✕)", `b` → "Right (○)", `x` →
     "Left (□)", `y` → "Top (△)", `l` / `r` → "L1" / "R1", `l2` / `r2` → "L2" / "R2", `l3` / `r3` → "L3" / "R3"
     (stick presses), `select` → "Select", `start` → "Start", the d-pad and the sticks by direction.
   - **What the game receives** (`gameLabel(target)`): the RetroPad's letters `A` / `B` / `X` / `Y` and the same
     names for the rest (L1 … R3, Select, Start, directions).
   - **A row** (`rowText(target, source)`): "<your pad's button> → <what the game receives>", e.g. "Bottom (✕) → B";
     unmapped → "nothing → B". The default reads Bottom → B, Right → A, Left → Y, Top → X: positions, never a swap.
   - **The picture's labels** (`pictureLabels(mapping)`): for each of your pad's controls, what it sends now
     (the mapping inverted; two targets on one control joined "A+B"; a control sending nothing: "—"); `changed(mapping,
     default)`: the controls whose label differs from the default's (highlighted).
   - `LAYOUT`: each control's place on the picture in a 0..1 box (the outline's parts: two grips, a D-pad, four face
     buttons, two sticks, shoulders and triggers, Select / Start); `LEGEND` = "The picture shows what each of your
     pad's buttons sends to the game. A, B, X, Y are the game's buttons: B bottom, A right, Y left, X top."
2. **`streaming/ControllerPictureView.kt`** (new): an Android `View` that draws a **plain original outline** from
   `LAYOUT` with `Canvas` primitives (rounded body and grips, a cross, circles, rectangles; no brand marks, no copy of
   any product's shape) and writes each control's label on it; changed controls in an accent colour.
3. **`MainActivity.kt`, the editor**, only when the switch is on: the picture and the legend above the rows; each row's
   title = `rowText(target, working[target])` and its "Current:" line hidden; the Change dialog's title "Change what
   sends the game's <gameLabel>" and its list of your pad's buttons by `padLabel`; every refresh redraws the picture.
   The switch off → today's editor (the same calls, the same strings).

## Tests (`app/src/test/java/streaming/B86MappingPictureTest.kt`, the code the editor runs)

The picture's labels equal the profile's mapping **for the default** (Bottom B, Right A, Left Y, Top X — and nothing
highlighted), **for a bottom / right swap** (Bottom A, Right B, both highlighted) and **for a Square / Triangle swap**
(Left X, Top Y, both highlighted); **a row change updates the label** (the working map changed, the labels
recomputed); the rows read by position (the default never shows two different positions for a letter pair); **the
stored mapping unchanged by opening and closing** (every function leaves its input map equal to a copy taken before;
nothing is written); the property; the layout has every control, inside the box, no two on one spot. Mutations. The
Android view is not exercised on the JVM (no Robolectric) — disclosed; HOME-12's C50 is its check.
