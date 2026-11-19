# G6-HM1b — layout addendum B: L1 and L2 side by side (the user's Q-L2 (b)), re-checked (2026-11-19)

This amends §3 of `design_amendment_written_before_code.md` (`2272705f…`) for the shoulders only; that file is not
edited. Script: `layout_check_b.py`, a copy of `layout_check.py` with the shoulders changed and nothing loosened.
Output: `layout_check_b_output.txt`. Both are hashed in `layout_addendum_b.sha256`.

**The rule from the task:**
- change only the four shoulder rectangles;
- each at least 1 × 2 cm;
- at least 1 cm from the design's named gesture strip (the bottom tenth, for the home gesture; the design names no
  side-edge strip width);
- clear of every other control's press area;
- at the height that brings both shoulders within about 4–5 cm of the thumb base, assumed at the side edge, y 1042.

**The result: no height meets every check and the 4–5 cm target while only the shoulders move.** Every check still
holds where noted; the 4–5 cm target is the part that cannot be met.

## The shoulders (all three variants)

- **Size:** drawn 100 × 200 px = **1.06 × 2.12 cm** at 240 dpi. The press areas are 110 × 220 px (×1.1).
- **Side by side at one height, L2 on the outside:**
  - L2: centre x 56 (6 px from the edge);
  - L1: centre x 170 (the press areas are 4 px apart);
  - R1: centre x 1030;
  - R2: centre x 1144.
- **The bottom limit:** the shoulders' press areas end by y 1098, which is 1 cm above the bottom tenth.

## B0 — only the shoulders moved (the task's rule): every check passes, but not within 5 cm

The search over every height finds 174 heights that pass every check (y 237–410), and **none within 5 cm**.

**Why:**
- the pair's press areas need 225 px of width from the edge;
- across that width, the D-pad's press area covers y ≈ 504–816;
- the left stick's covers y ≈ 842–1158;
- the gap between them (≈ 64 px at x 225) is far less than the 220 px a shoulder needs;
- below the stick is the bottom tenth;
- the right side is the same against the right stick and the ○ button;
- so the pair can only sit above the D-pad.

The nearest passing height is **y 410**:

| Control | Centre (px) | From the thumb base (cm, 224 ppi) |
|---|---|---|
| L2 | (56, 410) | 7.2 |
| L1 | (170, 410) | 7.4 |
| R1 | (1030, 410) | 7.4 |
| R2 | (1144, 410) | 7.2 |

That is **farther than the amendment's stacked shoulders** (L1 3.9 cm, L2 6.6 cm).

```
B0 (y 410)
+------------------------------------------------+
|             ssssss  SSSSSS        EEEEEE       |
|             ssssss  SSSSSS        EEEEEE       |
|                                                |
|                                                |
|                                                |
|                                                |
|2222 1111                              1111 2222|
|2222 1111                              1111 2222|
|2222 1111                              1111 2222|
|2222 1111                              1111 2222|
|                                                |
|        ++++++++                RRRRRRRR        |
|       ++++++++++              RRRRRRRRRR       |
|       ++++++++++              RRRRRRRRRR       |
|        ++++++++               RRRRRRRRRR       |
|          ++++            333    RRRRRR         |
|                          333                   |
|          LLLL                    ^^^^          |
|        LLLLLLLL                  ^^^^          |
|       LLLLLLLLLL              ###    ooo       |
|       LLLLLLLLLL   333        ###    ooo       |
|        LLLLLLLL    333           xxxx          |
|          LLLL                    xxxx          |
|                                                |
|................................................|
|................................................|
+------------------------------------------------+
```

## The closest alternatives (each passes every check; each moves other controls, so each is the user's choice)

### B1 — the arcs 90 px inward; shoulders at y 700

**What moves:** the D-pad and the left stick move to x 390, the face cluster and the right stick to x 810. L3 goes to
(580, 1120) and R3 to (630, 800).

**Distances from the thumb base (cm, 224 ppi):**
- the shoulders: L2 / R2 **3.9**, L1 / R1 **4.3**;
- the sticks and face buttons pay for it: left stick 4.4 (was 3.4), D-pad 6.2 (was 5.5), right stick 6.2 (was 5.5),
  face buttons 3.4–5.5 (were 2.4–4.4), L3 6.6, R3 7.0.

```
B1 (shoulders y 700)
+------------------------------------------------+
|             ssssss  SSSSSS        EEEEEE       |
|             ssssss  SSSSSS        EEEEEE       |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|            +++++++         RRRRRRRR            |
|2222 1111  +++++++++       RRRRRRRRRR  1111 2222|
|2222 1111  ++++++++++      RRRRRRRRRRR 1111 2222|
|2222 1111  +++++++++        RRRRRRRRR  1111 2222|
|2222 1111     ++++      333   RRRRR    1111 2222|
|                        333                     |
|              LLL              ^^^              |
|           LLLLLLLLL          ^^^^              |
|          LLLLLLLLLLL      ####   oooo          |
|          LLLLLLLLLLL      ####   oooo          |
|           LLLLLLLLL   3      xxxx              |
|              LLL    3333      xxx              |
|                                                |
|................................................|
|................................................|
+------------------------------------------------+
```

### B2 — the D-pad and right stick up 140 px, the left stick and face cluster down 30 px; shoulders at y 774

**What moves:** the D-pad goes to (300, 520), the right stick to (900, 520), the left stick to (300, 1030) and the
face cluster's centre to (900, 1030). L3 and R3 stay where they were.

**Distances from the thumb base (cm, 224 ppi):**
- the shoulders: L2 / R2 **3.1**, L1 / R1 **3.6**;
- the left stick 3.4 and the face buttons 2.4–4.4 keep their reach;
- the D-pad and the right stick go to **6.8** (were 5.5).

```
B2 (shoulders y 774)
+------------------------------------------------+
|             ssssss  SSSSSS        EEEEEE       |
|             ssssss  SSSSSS        EEEEEE       |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|                                                |
|         ++++++                 RRRRRRRR        |
|       ++++++++++              RRRRRRRRRR       |
|       ++++++++++              RRRRRRRRRR       |
|        ++++++++               RRRRRRRRRR       |
|         ++++++                  RRRRRR         |
|2222 1111                              1111 2222|
|2222 1111                              1111 2222|
|2222 1111                 333          1111 2222|
|2222 1111                 333          1111 2222|
|                                                |
|         LLLLLL                   ^^^^          |
|       LLLLLLLLLL                 ^^^^          |
|       LLLLLLLLLL   333       ####    oooo      |
|       LLLLLLLLLL   333        ##  xx  oo       |
|        LLLLLLLL                  xxxx          |
|                                                |
|................................................|
|................................................|
+------------------------------------------------+
```

**For the user (Q-L2b; not picked):**
- **(i) B0:** shoulders side by side above the D-pad, 7.2–7.4 cm away; nothing else moves.
- **(ii) B1:** shoulders at 3.9–4.3 cm; the sticks, D-pad and face buttons about 1 cm farther.
- **(iii) B2:** shoulders at 3.1–3.6 cm; the D-pad and right stick 1.3 cm farther; the left stick and face buttons
  unchanged in reach.
- **(iv) The amendment's stacked shoulders** (L2 above L1, 3.9 / 6.6 cm), which Q-L2 (b) replaced.

Every variant is judged by the user's hands at G6-HM4. The thumb base at y 1042 remains an **assumption**.
