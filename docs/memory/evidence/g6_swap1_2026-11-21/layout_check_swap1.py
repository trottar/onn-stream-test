"""G6-SWAP1: the right stick and the face buttons trade places (from layout_check_screen1.py), on the tablet's
1200 x 2000 screen: box 1200 x 900, pad region 1200 x 1100 (reference = px, sx = sy = 1). The face diamond, unchanged,
centres on the right stick's old centre (900, 295); the right stick goes to the diamond's old centre (900, 805).
Everything else as G6-JOIN1 (= G6-SCREEN1's places). px per cm: 240 / 2.54 = 94.49 ("94.5").
Checks 1-5 of the task gate; if one fails, nothing else is moved."""
import math, sys

W, H, BOX = 1200, 1100, 900
PX_CM = 240 / 2.54
BOTTOM = 0.9 * H
STICK_R, STICK_PRESS = 132.0 * 0.875, 132.0 * 1.2


def layout(face_c, rstick):
    d = {}
    def circle(n, x, y, r, hr): d[n] = ("c", x, y, r, r, hr, hr)
    def rect(n, x, y, hw, hh, s): d[n] = ("r", x, y, hw, hh, hw * s, hh * s)
    circle("LS", 300, 805, STICK_R, STICK_PRESS)
    circle("DPAD", 300, 295, 125, 125 * 1.25)
    circle("L3", 540, 815, 48, 48 * 1.2)
    fx, fy = face_c
    for n, ox, oy in (("TRIANGLE", 0, -90), ("CIRCLE", 90, 0), ("CROSS", 0, 90), ("SQUARE", -90, 0)):
        circle(n, fx + ox, fy + oy, 52, 52 * 1.2)
    circle("RS", rstick[0], rstick[1], STICK_R, STICK_PRESS)
    circle("R3", 690, 565, 48, 48 * 1.2)
    rect("SELECT", 400, 70, 75.5, 47.5, 1.2)
    rect("START", 600, 70, 75.5, 47.5, 1.2)
    rect("END", 1080, 70, 75.5, 47.5, 1.0)        # a Button: its press area is its rectangle
    for n, x in (("L2", 56), ("L1", 170), ("R1", 1030), ("R2", 1144)):
        rect(n, x, 549, 50, 100, 1.1)
    return d


JOIN1 = layout((900, 805), (900, 295))
SWAP1 = layout((900, 295), (900, 805))
MOVED = {"TRIANGLE": (900, 205), "CIRCLE": (990, 295), "CROSS": (900, 385), "SQUARE": (810, 295), "RS": (900, 805)}


def gap(p, q, press):
    pk, px, py, pa, pb, pha, phb = p
    qk, qx, qy, qa, qb, qha, qhb = q
    if press: pa, pb, qa, qb = pha, phb, qha, qhb
    if pk == "c" and qk == "c": return math.hypot(px - qx, py - qy) - pa - qa
    if pk == "r" and qk == "r":
        dx, dy = abs(px - qx) - pa - qa, abs(py - qy) - pb - qb
        return math.hypot(max(dx, 0), max(dy, 0)) if (dx > 0 or dy > 0) else max(dx, dy)
    (cx, cy, cr), (rx, ry, ra, rb) = ((px, py, pa), (qx, qy, qa, qb)) if pk == "c" else ((qx, qy, qa), (px, py, pa, pb))
    return math.hypot(max(abs(cx - rx) - ra, 0), max(abs(cy - ry) - rb, 0)) - cr


cm = lambda px: f"{px:.2f} px = {px / PX_CM:.3f} cm"
fails, lines = [], []
# 1 every other control's on-screen centre as G6-JOIN1's
others = [n for n in SWAP1 if n not in MOVED]
worst = max(math.hypot(SWAP1[n][1] - JOIN1[n][1], SWAP1[n][2] - JOIN1[n][2]) for n in others)
lines.append(f"1 the {len(others)} other controls vs G6-JOIN1: largest move {worst:.2f} px (<= 1 px)")
if worst > 1: fails.append("1")
# 2 the moved five where B1 says
for n, (x, y) in MOVED.items():
    _, sx, sy, *_ = SWAP1[n]
    _, jx, jy, *_ = JOIN1[n]
    d = math.hypot(sx - x, sy - y)
    lines.append(f"2 {n}: G6-JOIN1 ({jx}, {BOX + jy}) on screen -> ({sx}, {BOX + sy}); region ({sx}, {sy}), wanted ({x}, {y}): {d:.2f} px")
    if d > 1: fails.append("2 " + n)
# 3 overlaps, drawn and press
names = list(SWAP1)
pairs, near = 0, []
for press in (False, True):
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairs += 1
            g = gap(SWAP1[names[i]], SWAP1[names[j]], press)
            if g < 0: fails.append(f"3 {'press' if press else 'drawn'} overlap {names[i]} {names[j]} ({g:.1f} px)")
            if press and g < 60: near.append((g, names[i], names[j]))
lines.append(f"3 overlaps: {pairs} pairs (drawn and press, End included): {'none' if not any(f.startswith('3') for f in fails) else 'SEE FAILS'}")
for g, a, b in sorted(near):
    lines.append(f"  closest press areas: {a} <-> {b}: {cm(g)}")
# 4 End to every press area >= 0.5 cm
end = sorted((gap(SWAP1["END"], SWAP1[n], True), n) for n in names if n != "END")
lines.append(f"4 End (1080, 70) to every press area, >= 0.5 cm = {0.5 * PX_CM:.1f} px required; nearest first:")
for g, n in end:
    lines.append(f"  End <-> {n}: {cm(g)}")
if end[0][0] < 0.5 * PX_CM: fails.append(f"4 End {cm(end[0][0])} from {end[0][1]}")
# 5 drawn sizes
for n in ("SELECT", "START", "END"):
    _, _, _, a, b, *_ = SWAP1[n]
    s = min(2 * a, 2 * b) / PX_CM
    lines.append(f"5 {n} drawn {2 * a:.0f} x {2 * b:.0f} px, smaller side {s:.2f} cm (>= 1 cm)")
    if s < 1.0: fails.append("5 " + n)
for n in ("TRIANGLE", "CIRCLE", "CROSS", "SQUARE"):
    if 2 * SWAP1[n][3] / PX_CM < 1.0: fails.append("5 " + n)
# as before: inside the region and above its bottom tenth; shoulders 1 cm above it
for n, (k, x, y, a, b, ha, hb) in SWAP1.items():
    if x - ha < 0 or x + ha > W or y - hb < 0 or y + hb > BOTTOM: fails.append(f"b {n} outside / in the bottom tenth")
    if n in ("L1", "L2", "R1", "R2") and y + hb > BOTTOM - PX_CM: fails.append(f"b {n} within 1 cm of the bottom tenth")
lines.append(f"as before: every press area inside the region and above its bottom tenth (y {BOTTOM:.0f})")
print(f"G6-SWAP1 on 1200 x 2000: box 1200 x {BOX}, pad region {W} x {H}; {PX_CM:.2f} px per cm")
print("\n".join(lines))
print("ALL CHECKS OK (1-5)" if not fails else "FAILED: " + "; ".join(fails))
sys.exit(0 if not fails else 1)
