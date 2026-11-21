---
memory_schema: 1
as_of: 2026-11-21
status: RECORD — G6-SWAP1 part 1 done: the face buttons and the right stick trade places (the face diamond around (900, 295), the right stick at (900, 805)); every other control unchanged; the geometry check passes. Candidate 0a631e79… tablet only; the run pre-registered (4f7bdadd…, 00:59:37Z). No hub change, no restart. The onn keeps ca53df0d…. Nothing adopted. Part 2 after the run.
---

# G6-SWAP1 — face buttons up, right stick down (part 1: code, geometry, build, pre-registration; 2026-11-21)

Task: `../handoffs/G6-SWAP1_RIGHT_SIDE_SWAP_TASK.md` (a byte-for-byte copy of the Cowork file). Its Part A (G6-JOIN1S,
`../handoffs/G6-JOIN1S_SCORE_TASK.md`) is recorded as part 2 of `G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md`:
- **NOT MET** on c4 (one 283-ms output gap), c7 and c12 (the right stick short);
- the hold-to-join (c5) met.

Patch note: `../patches/G6_SWAP1_RIGHT_SIDE_SWAP.md`. Files: `g6_swap1_2026-11-21/`. G6-HM5 / G6-HM6 stay reserved.

**The user's request (verbatim, 2026-11-21):** "After playing a while on the tablet I think ergonomically it would be
better to swap the right face and analogs everything else remains unchanged"

**Context:** in G6-HM1b the user chose "right stick above the face buttons". This reverses that choice, by the user,
after play. With it the right side matches the left (the D-pad above the left stick; the face buttons above the right
stick), as on a DualShock 2.

**Preflight (00:54Z, `preflight.txt`):**
- G6-JOIN1 committed (`d82331a3`); no game running, no gradle.
- **Another Claude Code session was active:** session B's queue BI, running `tests.b185_overtime`, with its uncommitted
  files in `tools/`, `tests/` and `docs/memory/`.
- This session stopped and said so. The user (verbatim): **"Proceed I'll commit those after"**. It went on without
  touching those files (onn check 5 lists them as another session's).

## 1. B1 — the change (`TouchPadState.kt` `layoutPs2`, reference 1200 x 1100)

| Control | G6-JOIN1 (region) | G6-SWAP1 (region) | On the screen (+900) |
|---|---|---|---|
| △ | (900, 715) | **(900, 205)** | (900, 1105) |
| ○ | (990, 805) | **(990, 295)** | (990, 1195) |
| ✕ | (900, 895) | **(900, 385)** | (900, 1285) |
| □ | (810, 805) | **(810, 295)** | (810, 1195) |
| right stick | (900, 295) | **(900, 805)** | (900, 1705) |

- The diamond keeps its spacing (90 px), radii (52) and hit scale (1.2).
- The right stick keeps its ring (115.5), press area (158.4), the 0.875 throw, the DS2 mapping and ownership.
- **Unchanged:**
  - the D-pad, the left stick, L3 (540, 815), **R3 (690, 565)**, L1 / L2 / R1 / R2, SELECT, START, **End (1080, 70)**;
  - the footer, the video box, the crop, the join rules and the stick mapping;
  - the side-edge exclusions, which still follow the shoulders.
- **The report:** `layout_version` `"ps2-swap1"` (`Ps2TouchLayout.LAYOUT_VERSION`).

## 2. B2 — the geometry check (`layout_check_swap1.py`, output `layout_check_swap1_output.txt`; 94.49 px per cm)

1. **The 11 other controls vs G6-JOIN1:** largest move **0.00 px**. **OK.**
2. **The five moved controls:** where B1 says, 0.00 px each. **OK.**
3. **No overlap**, drawn or press (240 pairs, End included). **OK.** The closest press areas:
   - inside the diamond 2.48 px (as before);
   - the right stick ↔ R1 **5.74 px**, the mirror of the left stick ↔ L1;
   - ✕ ↔ R1 30.02 px.
4. **End ↔ every press area ≥ 0.5 cm (47.2 px). OK.** Nearest first:

   | Press area | Clearance |
   |---|---|
   | **△** | **73.90 px = 0.782 cm** |
   | ○ | 115.69 px = 1.224 cm |
   | □ | 200.92 px = 2.126 cm |
   | ✕ | 224.79 px = 2.379 cm |
   | START | 3.322 cm |
   | R1 / R2 | 3.403 cm |
   | R3 | 5.179 cm |
   | SELECT | 5.439 cm |
   | right stick | 5.683 cm |
   | (the rest farther) | |

5. **SELECT / START / End:** 151 x 95 px, smaller side 1.01 cm each. **OK.** Every press area is inside the region and
   above its bottom tenth.

## 3. Tests and build (`tests_jvm.txt`, `build_console.txt`)

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL, 389 tests, 0 failures** (00:58Z;
  G6-JOIN1: 384).
- **New, `G6Swap1Test` (5):**
  - the five moved centres, the diamond unchanged around (900, 295), sizes and press areas unchanged;
  - every other control at G6-JOIN1's centre, End at (1080, 70);
  - the face buttons' bits and the right stick (full up, full left, a full corner) in their new places, R3 unchanged;
  - End ≥ 0.5 cm from every press area, the nearest △ at 73.9 px;
  - `layout_version` `"ps2-swap1"`.
- **Updated, disclosed** (they pinned the five controls' old places):
  - `G6TouchPs2Test.theLayoutIsAddendumB2`: the five new centres.
  - `G6Screen1Test.theClusterDoesNotMoveOnTheScreen`: the five swapped controls are out of its "unchanged since
    G6-HM4b" map; `G6Swap1Test` pins them.
  - `G6Screen1Test.endMovesRightTo1080`: End's x was chosen against the right stick at its SCREEN1 place (900, 295),
    which is now pinned explicitly, not read from the moved stick. The first build failed this one test before that.
  - Every other test unchanged and passing.
- **Candidate:** `PrivyHub/app/build/g6_swap1_candidate/app-debug.apk`, sha256
  **`0a631e7939821a1b673603ef738a95a9b2219a2d558eb9e6531bf1d3f58e59b7`** (also `PrivyHub-handheld-preview-0a631e79.apk`).
  G6-JOIN1's `6d2fff76…` was copied first to `PrivyHub/app/build/g6_swap1_preserved_outputs/`.

## 4. Checks

- **The onn unchanged** (`onn_unchanged_checks.txt`, by `onn_checks_swap1.py`, against HEAD):
  1. the manifest's element `4d36c0bb…` as pre-G6;
  2. `NativeStreamActivity` not changed, hook defaults 10 / 10;
  3. `PadSlots.kt` and `PointerGuard.kt` unchanged since pre-G6;
  4. `MainActivity` not changed;
  5. nothing under `companion/`, `tools/` or `data/` changed by this task.
  - Session B's uncommitted files (present at this task's start) are listed apart, untouched.
  - The onn keeps `ca53df0d…`; the pins are not moved. No restart needed.
- **The diff** (`g6_swap1.diff`, this task's five files only): `git diff --check` clean, `git apply -R --check` OK.
  The redaction check is clean.

## 5. The run, pre-registered (`preregistration.md`)

- sha256 **`4f7bdaddf22544502d2969a57715e9f43d2de49392904702366c3a4036f8d925`**, hashed at **2026-11-21T00:59:37Z**.
- G6-JOIN1's, copied exactly, changing only:
  - the candidate's hash;
  - "Which session": a report with `layout_version` `"ps2-swap1"`; older apps noted and skipped;
  - c14: `handheld.layout_version` = `"ps2-swap1"` (so the rule's range is c1–c14);
  - the words at the start of step 3, and the stick step's "push the **right** stick fully up and fully left too:
    last time it stopped short";
  - one remark: whether the swap feels better, and whether anything on the right side is now hard to reach.

## 6. Part 2 — the run (after it)

Not run yet.
