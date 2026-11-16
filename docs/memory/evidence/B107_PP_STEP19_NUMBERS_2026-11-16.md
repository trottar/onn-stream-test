---
memory_schema: 1
as_of: 2026-11-16
status: DONE (session B, queue AO; read only, no code in this repo, nothing fixed) — step 19 on the hub, the numbers for the PC side. The Hips piece of the body as the board game's repo has it (`models/template_body.glb`, sha256 c3e5545e…) counts **front 9, sides 4, back 18** — sides 4 is not more than four, so the assertion fails. **The same after PP-H1's import, after two fresh imports, with the import's compression switched off, and on the same file read raw with no import at all (every normal equal to the imported one).** Not a value at a limit: the four side corners have |n.x| 0.9999 and 0.9626 (two each), the next corner 0.8315 against the cut 0.92 — no corner of the piece is within 0.029 of any side cut. The other three checked pieces pass with room (UpperChest 14 / 8 / 28, LeftUpperLeg 17 / 10 / 24, RightLowerLeg 16 / 10 / 24). From the hub: the committed body model gives 4 every time; whether the PC checks the same file cannot be told here. The board game's repo untouched (its tree clean before and after, its .godot cache identical); Godot headless only, in scratch copies removed after. Nothing committed
---

# B107 — step 19 on the hub: the numbers (2026-11-16)

**What step 19 asserts** (`checks/step19_round_bodies.gd`, `_wrapped_round`): for each of UpperChest, Hips,
LeftUpperLeg and RightLowerLeg of a character built from the template body (a name and the placeholder face), the
corners whose normal (in the character's space; it faces +Z) points **front** (n.z > 0.85), to the **sides**
(|n.x| > 0.92 and |n.y| < 0.3) and to the **back** (n.z < −0.5 and |n.y| < 0.5) must each be **more than four**.
On the hub (PP-H1, three times): "Hips has a front, sides and a back" fails; the other 124 assertions pass.

**How measured** (`b107_2026-11-16/`; read only): my own script `step19_numbers.gd` (extends SceneTree, edits and
writes nothing) builds the character exactly as step 19 does (the same definition, two frames), reads the body
mesh's arrays exactly as `_pictured_corners` does, and prints for **every** piece the three counts, how many corners
lie within 0.02 of a cut, and each piece's nearest distance to each cut; then reads **the same .glb raw at run time**
with `GLTFDocument` (no import step), maps it bind by bind and compares corner by corner. `run_b107.sh` runs it, the
import and step 19 itself in **four scratch copies** of the repo (`git archive HEAD` of a clean tree): **as_is** (+ a
copy of the repo's git-ignored `.godot` cache = PP-H1's import), **fresh1** and **fresh2** (`--import` each),
**nocompress** (a fresh import with `meshes/force_disable_compression=true` in that copy's `.import` only). Godot
4.7.2-stable headless; its user-data, settings, cache and temp folders pointed into the scratch folder; the scratch
folder removed after (checked). Run twice (`results_run1.txt`, `results.txt`; the second adds the side-normal lines):
identical numbers.

## The numbers (every run, every copy the same)

| piece (checked by step 19) | corners | front (> 0.85) | sides (\|x\| > 0.92, \|y\| < 0.3) | back (< −0.5, \|y\| < 0.5) | more than four each | nearest to a cut: front / sides / back |
| --- | --- | --- | --- | --- | --- | --- |
| **Hips** | 80 (74 places) | **9** | **4** | **18** | **no — sides 4** | 0.017 / **0.029** / 0.011 |
| UpperChest | 119 | 14 | 8 | 28 | yes | 0.005 / 0.005 / 0.008 |
| LeftUpperLeg | 171 | 17 | 10 | 24 | yes | 0.013 / 0.071 / 0.005 |
| RightLowerLeg | 171 | 16 | 10 | 24 | yes | 0.004 / 0.061 / 0.009 |

- **The Hips piece's side-facing normals:** the largest |n.x| among its corners with |n.y| < 0.3 are **0.9999, 0.9999,
  0.9626, 0.9626**, then **0.8315, 0.8315, 0.8314, 0.8314, 0.8022, 0.8022** — four corners over 0.92, the fifth 0.089
  short of it. Their |n.y|: 0.016 (two), 0.271 (two). **The piece has four side corners by its geometry**, not by a
  rounding at the cut.
- **The other pieces (not checked by `_wrapped_round`, for completeness):** Head 11 / 10 / 25; both UpperArms 17 / 26 /
  40; both LowerArms 17 / 28 / 36; both UpperLegs 17 / 10 / 24; both LowerLegs 16 / 10 / 24; both Hands 4 / 22 / 24;
  both Feet 13 / 4 / 7 (hands and feet would not meet the bar either; step 19 does not ask it of them).

## What the import writes, and whether it can move a corner

- **The imported body:** one ArrayMesh, 2 surfaces — 146 vertices / 864 indices (the face) and 1,953 vertices / 10,728
  indices (the rest); tangents present; 4 bone weights a vertex; **the vertex attributes are not compressed**
  (`ARRAY_FLAG_COMPRESS_ATTRIBUTES` off on both surfaces, with the repo's `.import` saying
  `force_disable_compression=false` — the skinned body is stored uncompressed either way). 35 skin binds, the same
  count raw.
- **Imported against raw, corner by corner** (the four checked pieces, matched by place): **every corner matched, the
  largest normal difference 0.00000, no corner whose count membership differs.** Neither vertex merging, nor
  tangents, nor compression, nor the LOD and shadow meshes the import adds move any corner the check reads.
- **Repeatable on the hub:** two fresh imports and the no-compression import give the same counts, the same nearest
  distances and the same side normals as PP-H1's import. (The imported `.scn` file's bytes differ between imports —
  66,605-66,609 bytes, a different sha256 each time — while its mesh data read back identically; something in the file
  besides the mesh changes per import.)
- **Step 19 itself** in each of the four copies: the same single failure, `FAIL (1 of 125 assertions)`.

## What the hub can and cannot tell

- **Can:** with the board game's repo at `21e7e44` (the hand-back commit; the PC side has not pushed since PP-H1) and
  its `models/template_body.glb` **sha256 `c3e5545ed2045a47b0e97cb158623e1c4f2513528521cdc2fced531ddd5802ef`**, Godot
  4.7.2-stable reads a Hips piece with **4** side corners, every time, imported or not — so **with this file the
  assertion fails on any machine that reads it this way**, and nothing on the hub (import settings, compression, CPU,
  renderer — the check is headless) is the cause.
- **Cannot:** what the PC reads. The README says step 19 runs "after `blender/build_template_body.py` has written
  `models/template_body.glb` again" — if the PC's checks ran on a body built after the committed one (Blender 5.3 on
  the PC; the hub has no Blender and builds nothing), its file may differ. The body model, its Blender script and step
  19 were last committed together (`45a7feb`).
- **For the PC side, in one line:** compare the PC's `models/template_body.glb` sha256 with `c3e5545e…`; if it differs,
  commit the PC's; if it is the same, run `step19_numbers.gd` there and compare its Hips line (front 9, sides 4, back
  18; side |n.x| 0.9999, 0.9999, 0.9626, 0.9626, then 0.8315).

## Nothing touched

The board game's repo: HEAD `21e7e44`, `git status --short` empty, its `.godot` cache 772 KB / 56 files with the same
listing hash before and after (`board_repo_before.txt`, `board_repo_after.txt`); the pictures' folder not opened (step
19 uses none of the owner's pictures). Godot ran headless only, in the scratch copies; one `--version` read at the
start ran without the folder redirection (it prints and exits). No emulator, stream or restart.

## Files

`b107_2026-11-16/`: start files, `board_repo_before.txt` / `board_repo_after.txt`, `step19_numbers.gd`, `run_b107.sh`,
`results_run1.txt`, `results.txt`, redact / title checks, `manifest.sha256`. No code in this repo; no patch.
