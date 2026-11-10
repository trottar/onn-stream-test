---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT INSTALLED (session B, queue AE) — the Input Profile editor shows a small controller picture drawn by the app with what each of the pad's controls sends now, and reads in one set of letters ("Bottom (✕) → B"); in APK c801caab… (pinned, NOT installed). Default on; debug.privyhub.mapping_picture=0 = today's editor. Display only. Nothing committed. No title, serial, path or identifier in this record
---

# B86 — the mapping editor's controller picture, and one set of letters (2026-11-10)

**Why:** HOME-12's wrap-up: "it would be much easier to interpret changes if there were a little image of a controller
with the current mappings showing"; the editor printed the game's letters (RetroPad, Nintendo layout) and the pad's
(Xbox) side by side, so the hub's default — the identity by position — read A ← B, B ← A, X ← Y, Y ← X.

**Baseline:** HEAD `c514c543`. **Design** hashed before code at 21:23:25Z (`b86_2026-11-10/design.sha256`).

## What was built (`b86.diff`)

- **`streaming/MappingPicture.kt`** (pure): your pad's buttons **by position and glyph** — Bottom (✕), Right (○),
  Left (□), Top (△), L1 / R1 / L2 / R2 / L3 / R3, Select, Start, the d-pad and sticks by direction; what the game
  receives **by its letter** (A / B / X / Y and the same names for the rest); a row "**Bottom (✕) → B**"; the picture's
  labels (the mapping inverted: on each of your controls, what it sends now; two on one control "A+B"; nothing "—");
  the controls changed from the default; a layout box; the legend "… A, B, X, Y are the game's buttons: B bottom,
  A right, Y left, X top."
- **`streaming/ControllerPictureView.kt`:** an Android `View` drawing **a plain original outline** with canvas
  primitives — a rounded body and two grips, a cross for the D-pad, four round face buttons, two round sticks, shoulder
  and trigger tabs; no brand marks — with each control's label, the changed ones in an accent colour (stick directions
  shown only when changed, to keep the picture readable).
- **`MainActivity.kt`, the editor**, only with the property on: the picture and the legend under "Current mapping";
  each row reads "<your pad's button> → <the game's button>" (the separate "Current:" line hidden); the Change list
  names your pad's buttons by position and glyph; its title "Change what sends the game's <letter> — now: …"; every
  refresh redraws the picture. Save, the stored mapping and its JSON are untouched.

## The switch

`debug.privyhub.mapping_picture=0` (or `off`) → today's editor, the same calls and strings (`proof_flag_absent.md`).

## Tests (`B86MappingPictureTest.kt`, 7, JVM)

**The default** reads by position (Bottom → B, Right → A, Left → Y, Top → X; the picture's face labels B / A / Y / X;
nothing highlighted); **a bottom / right swap** (Bottom → A, Right → B; both highlighted); **a Square / Triangle swap**
(Left → X, Top → Y; both highlighted); **a row change updates the label** (L1 sending R2, R2 sending nothing, two on
one control "A+B"); **the stored mapping never touched** (equal to a copy and the same string after the editor's
calls three times); the layout (every source the hub lists, inside the box, no two on one spot, Bottom below Top);
the property and the legend.

- 3 runs: 7 / 7 each (`tests_x3.txt`). Mutations: **4 / 4 caught** (`tests_mutations_jvm.txt`).

## The APK (`apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`, `tests_jvm_apk_copy.txt`)

- **The tree:** HEAD's client (B5 … + B74 + B80's client part) + **B84 + B86**, with `b29.diff` / `b27.diff` reversed on
  the client paths, as queues AA / AC.
- **`c801caabe6f121d979afa873668b0c48b47d310067cad8ec57cfa8cbdd48582b`** (9,749,968 B, 945 entries), built offline
  (`:app:assembleDebug --offline --rerun-tasks --no-configuration-cache`) **twice → the same bytes**; the baseline
  (HEAD, B29 / B27 reversed) rebuilds **`de6682db…` byte for byte**; the same signer (`455bde4e…`); JVM 283 / 283 in
  the APK tree (294 / 294 in the work copy).
- **Pinned** at `PrivyHub/app/build/queue_ae_built/app-debug.apk`. **NOT installed.** `85220f99…` stays on the onn.

## Disclosed

- The glyphs are PlayStation's (✕ ○ □ △), by position; with another pad the positions still hold (the legend says what
  the letters are). The design picked the glyphs for the user's pads; not asked.
- **The Android view is not exercised on the JVM** (no Robolectric); the picture is HOME-12's C50 at the TV.

## Files

`b86_2026-11-10/`: start files, the design + hash, `b86.diff`, `proof_flag_absent.md`, `tests_x3.txt`,
`tests_mutations_jvm.txt`, the APK's files, the host-suite comparison and the queue's tree checks, `scripts/`
(`mutate_jvm.sh`, `apk_and_jvm.sh`), redact / title checks, `manifest.sha256`. Patch note:
`patches/B86_MAPPING_PICTURE.md`.
