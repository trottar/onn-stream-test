---
memory_schema: 1
as_of: 2026-11-11
status: BUILT, NOT INSTALLED (session B, queue AG) — the mapping picture beside the rows (left pane, outside the rows' scroll), every label at the rows' own text size (34 px at 1080p, from B89's ~11 px), B89's drawing kept and scaled to fill its side, labels placed without overlap (moved ones get a leader line); the whole editor rendered at 1920 × 1080 off the device. In APK 218d9a82… (pinned, NOT installed). Switch: debug.privyhub.mapping_picture=0 = today's editor. Nothing committed. No title, serial, code name, path or identifier in this record
---

# B91 — the mapping picture, readable from the couch (2026-11-11)

**Why:** HOME-12T's C53: "It looks much better although may be a little too small now, hard to read unless up close."
The cap (at most a fifth of the screen's height) was the queue's own rule; B89's drawing had answered HOME-12R.

**Baseline:** HEAD `d1df1f86`. **Design** hashed before code at 02:02:31Z (`b91_2026-11-11/design.sha256`).

## Found

- B89 fitted each label into its box: at 1080p (density 2.0) **a face button's letter ≈ 10.6 px, a stick direction ≈
  6.5 px — against 34 px for the rows' text** (17 sp), which the user reads from the couch. Measured from the constants
  (`labelTextIsNeverSmallerThanTheRows` asserts B89's face label ≤ 11 px).
- The picture sat at the top of the same scroll as the rows: at the model's numbers only **one** row was in view under
  it without scrolling.

## What was built (`b91.diff`, client only)

- **`streaming/MappingEditorLayout.kt` — the layout in one place:** `ROW_TEXT_SP = 17` (the rows now use it — today's
  literal value) and `LABEL_TEXT_SP = ROW_TEXT_SP`; the dialog's window 92 % of the screen; the left pane 45 % of the
  content width (the picture and its legend), a 24-px gap, the right pane the rest (the heading, status, copy button and
  rows in their own scroll); the picture view sized to its pane; the rows visible without scrolling (a row-height model:
  the 17-sp line, the 48-dp "Change" button, today's padding). On a screen taller than wide the picture stays above (B89).
- **`MappingPicture.kt`:** B89's geometry unchanged (outline, shapes, one stroke width, label boxes for the B89 path);
  new: the controller drawn at 86 % of the view's width (view height / width 0.74), **anchors** per control (B89's box
  centres; the triggers' and shoulders' spread apart within their shapes; the D-pad arrows at the arms' ends; Select's
  label under it, Start's above it; the stick directions further out), and **`placeLabels`**: every label at the given
  text size, its box = text width + ½ text height × 1.3 text heights; pass 1 at its anchor if it overlaps no placed box
  and no other control's shape; pass 2 outward in rings (¼ text height, 16 directions, outward first) to the first free
  place inside the view, **with a leader line**. It never returns overlapping boxes.
- **`ControllerPictureView.kt`:** `beside(labelTextPx)` — measures to its pane, draws the shapes scaled, the labels at
  the rows' size with the device's own font widths (`Paint.measureText`), leaders in the label's colour; changed
  controls in the accent colour; stick directions only when changed (B89's rule).
- **`MainActivity.kt`:** with the picture on and a wide screen: a horizontal layout — the left pane (picture + legend,
  fixed) and the right pane (today's scroll with the heading, status, copy button and rows); after `show()`, the
  dialog's window set to the plan's size. Rows, wording, Change flow, Save / Cancel unchanged.

## The number (1080p, density 2.0)

**The picture's label text: 34 px (17 sp) — the rows' text: 34 px (17 sp).** B89's largest label was ≈ 10.6 px (a face
button), its smallest ≈ 6.5 px. (DejaVu Sans at 34 px: ascent + descent 40 px, a capital ≈ 25 px; `render/numbers.txt`.)
The plan: dialog 1766 × 993, content 1718 × 705, left pane 773, right 921, the picture 773 × 572; **rows in view: 3
beside vs 1 with the picture above** (the model's estimate).

## Renders (`b91_2026-11-11/render/`, the whole editor at 1920 × 1080, PNG; looked at by B before this record)

`default.png`, `swap_bottom_right.png`, `many_button_remap.png` (B89's three cases) + `numbers.txt`. The default places
every label at its control (no leader); the swap the same (A / B lit); the many-button remap moves three labels with a
short leader (the Top button's "L3", Select's "START", the left stick's Up). Drawn with java.awt (DejaVu Sans) from the
same model and placement the view uses; the device's font (Roboto) is narrower — the placement uses its own widths there.

## Switch

`debug.privyhub.mapping_picture=0` (or `off`) → B86's gate: no picture, the dialog as today (the scroll alone, the
theme's width, no `setLayout`); the row text constant has today's value. `MappingPicture.parse` is B86's, unchanged.

## Tests (`B91MappingBesideTest.kt`, 6, JVM; B89's 7 and B86's 7 stay green)

- the label text ≥ the rows' text (constants; 1080p and 4K); 34 px; ≥ 3 × B89's face label;
- **no two label boxes overlap and all are inside the view** in the three cases and the **worst case — all 24 controls
  labelled "START"** — with java.awt's widths and with a wider bound (0.75 text heights per character), and with
  Android's font set 1.3× larger (java.awt's widths); every label placed;
- a leader exactly when a label is not at its anchor; anchors where the model says; the default moves none of the face
  buttons, shoulders, triggers;
- the rows in view beside ≥ today's; the picture inside its pane, outside the scroll; a tall screen keeps B89's layout;
- the switch; the render (with `B91_RENDER_DIR`).
- 3 runs (`tests_x3.txt`); full JVM in the work copy (`tests_jvm_work_full.txt`) and in the APK tree 296 / 296.
- Mutations **7 / 7 caught** (`tests_mutations_jvm.txt`) — after one test change: K3 (the bounds check removed) was
  first missed; the worst case gained the 1.3× font run, then caught.

## The APK (`apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`, `tests_jvm_apk_copy.txt`)

- **The tree:** queue AF's APK tree (HEAD's client with `b29.diff` / `b27.diff` reversed) + **B91** (B90 has no client
  part) — equal to the working tree's client minus B27 / B29.
- **`218d9a82d564e0d63e8bc6cd5b8e9de95bddb033e8f6d0635dd870e19f62cd53`** (9,772,736 B, 945 entries), built offline
  twice → the same bytes; the baseline rebuilds **`3f21e2c6…` byte for byte**; the same signer (`455bde4e…`); JVM
  296 / 296 in the APK tree.
- **Pinned** at `PrivyHub/app/build/queue_ag_built/app-debug.apk`. **NOT installed.** `85220f99…` stays on the onn.

## Disclosed

- **The onn's density is the 1080p TV norm (2.0), not read on the onn** (no adb in this queue), as B73's was; the dialog
  title and button bar (64 dp each) and the row height are a model of the theme's, not measured on the device.
- **A limit found by the tests:** with Android's font 1.3× larger *and* the wide width bound *and* all 24 controls
  labelled "START", the last 4 labels find no free place and are left out (never drawn over another). At the rows' real
  size every case places every label. The onn's font scale is the default unless the user changed it.
- The renders are the model's and java.awt's, not the device's pixels; C56 is the user's reading at the TV.

## Files

`b91_2026-11-11/`: start files, the design + hash, `b91.diff`, `diffs_apply_in_order.txt` (HEAD + b90 + b91 = the
tree; reversed → HEAD; 0 differences each way), `proof_flag_absent.md`, `render/` (3 PNG + numbers), `tests_x3.txt`,
`tests_mutations_jvm.txt`, `tests_jvm_work_full.txt`, the APK's files, `scripts/` (the mutation and build scripts),
redact / title checks, `manifest.sha256`. Patch note: `patches/B91_MAPPING_PICTURE_BESIDE_ROWS.md`.
