# B91 — design, written before code (queue AG, 2026-11-11)

**The user's line (HOME-12T, C53):** "It looks much better although may be a little too small now, hard to read unless
up close." The cap (at most a fifth of the screen's height) was the queue's own rule; B89's drawing answered HOME-12R.

## Read before this design

- **Today's editor** (`MainActivity.kt`, the Input Profile mapping dialog): an `AlertDialog` whose view is one
  `ScrollView` → one vertical `LinearLayout` (padding 24 / 16 px): the heading "Current mapping" (18 sp), **B89's
  picture** (`ControllerPictureView`, height ≤ a fifth of the screen = 216 px at 1080p, ≈ 348 px wide), the legend,
  the status line, "Copy Mapping From Another Player", then **one row per control: its text at 17 sp** (B86's
  "Bottom (✕) → B") and a full-width "Change" button. The picture scrolls away with the rows.
- **B89's label size at 1080p:** each label is fitted to its box (`box.h × width × 0.85`): ≈ 10.6 px for a face button,
  ≈ 6.5 px for a stick direction — against **34 px** for the rows' text (17 sp at density 2.0). That is the finding.
- **The onn's density:** taken as the 1080p TV norm (1920 × 1080 px at density 2.0 = 960 dp), as B73 did; not read on
  the onn (no adb in this queue).

## The rule that replaces the height cap (hashed)

1. **Beside, not above:** with the picture on (the property absent), the editor is two panes side by side: **the
   picture in the left part** (fixed, outside the scroll — it never scrolls away), **the rows in the right part** (their
   own `ScrollView`: the heading, the status, the copy button, the rows). The dialog is made wide: its window
   `setLayout` to 92 % of the screen's width and height (today's dialog width is the theme's; the rows keep their full
   pane width).
2. **The label text is never smaller than the rows' text:** one constant `ROW_TEXT_SP = 17` (the rows use it: the same
   value as today's literal) and `LABEL_TEXT_SP = ROW_TEXT_SP`; the picture draws every label at exactly that size in
   pixels (`sp × density`), never fitted smaller.
3. **B89's drawing kept** (the one outline, shapes, one stroke width, the highlight colour for changed controls; stick
   directions drawn only when changed), **scaled to fill its side:** the controller drawn at 86 % of the left pane's
   width, centred, a top margin and a bottom strip for labels moved out (the view's height / width = 0.74), the whole
   view scaled down only if the pane is shorter than that.
4. **No overlap at that text size:** each label's box = its measured text width + ½ text height of padding, 1.3 text
   heights tall. **Pass 1:** in a fixed order, each label at its control (its anchor — B89's box centres, the D-pad
   arrows moved out to the arms' ends, Select / Start further apart) when it overlaps no box already placed. **Pass 2:**
   each label that did not fit there moves outward (rings of ¼ text height, 16 directions, the control's outward
   direction first) to the first place inside the view that overlaps no placed box and no other control's shape, and
   gets **a short leader line** from its control to its box. Deterministic; the device measures with its own font
   (`Paint.measureText`), the render and the tests with java.awt's — the placement never outputs overlapping boxes for
   any widths it is given.
5. **`debug.privyhub.mapping_picture=0` (or `off`) = today's editor** (B86's gate: no picture; the dialog as today).
   On a screen taller than wide (not the onn) the picture stays above, as B89 drew it.

## The layout model (pure Kotlin, one place: `MappingEditorLayout`)

From the screen's pixels and density: the dialog's window (92 %), the AlertDialog's title and button bar (64 dp each —
an estimate of the theme's, disclosed), today's container padding, the split (left 45 % of the content width, a 24-px
gap), the picture view's size, the label text in px, the rows' text in px, and the rows visible without scrolling in the
right pane against today's (the picture above them) — from the same row-height model (the row's 17-sp line, its
48-dp "Change" button, today's 8 / 20 px padding). The device uses the same model's split and sizes; the render draws
from it.

## Renders, off the device (`evidence/b91_2026-11-11/render/`)

The **whole editor screen at 1920 × 1080** (the dimmed app behind, the dialog, its title, the left pane's picture and
legend, the right pane's heading, status, copy button and rows with "Change" buttons, Save / Cancel), the rows' text at
its real size (34 px), drawn with java.awt (DejaVu Sans) from the model and the placement: **default**, **a bottom /
right swap**, **a many-button remap** (B89's three cases), PNG. The record gives **one number: the label text's height
in pixels at 1080p beside the rows' text height** (both 34 px by construction; and B89's 10.6 px for comparison).

## Tests (JVM, `B91MappingBesideTest.kt`)

- the label text size ≥ the rows' text size, from the constants, at 1080p and at 4K (density 4);
- **no two label boxes overlap** (and every box inside the view) in the three cases and in the **worst case: every
  control (all 24, the stick directions included) labelled with the longest label** ("START"), with java.awt's widths
  and with a wider bound (0.75 × text height per character);
- every label drawn with a leader exactly when it is not at its anchor; the default case needs none moved for the face
  buttons and shoulders;
- **the rows visible without scrolling** beside ≥ today's with the picture above; the picture fully inside the left
  pane and the left pane outside the rows' scroll (the model's flag);
- the picture's label text at 1080p = 34 px vs B89's ≤ 11 px (the number in the record);
- **the switch `0`** → today's editor (B86's gate, `parse`), and B89's / B86's own tests still green.

## Not in scope

The rows' wording and the "Change" flow (unchanged); the hub (no change); the onn's density read on the device.
