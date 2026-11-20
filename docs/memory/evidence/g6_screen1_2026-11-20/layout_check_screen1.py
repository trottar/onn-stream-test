"""G6-SCREEN1: the PS2 layout under the 4:3 box (from layout_check_b.py via layout_check_hm4b.py), on the tablet's
1200 x 2000 screen: box 1200 x 900, pad region 1200 x 1100. The cluster's y is B2's minus 225 (the same on-screen
place); SELECT / START stay at y 70 of the region (225 px lower on the screen); End at x 1080, y 70.
px per cm: 240 / 2.54 = 94.49 (the figure G6-HM4b used, "94.5"). B4's checks 1, 2, 3 and 5 gate; 4 is reported."""
import math, sys

SCREEN_W, SCREEN_H = 1200, 2000
BOX_HM4B, BOX = 675, 900                      # 16:9 then, 4:3 now
W, H = SCREEN_W, SCREEN_H - BOX               # 1200 x 1100
GROW = BOX - BOX_HM4B                         # 225
PX_CM = 240 / 2.54
BOTTOM = 0.9 * H
STICK_R, STICK_PRESS = 132.0 * 0.875, 132.0 * 1.2
END_X = 1080

# B2 / G6-HM4b (region 1200 x 1325, under the 675 box): name -> (kind, x, y, a, b, press a, press b)
HM4B = {}
def circle(d, n, x, y, r, hr): d[n] = ("c", x, y, r, r, hr, hr)
def rect(d, n, x, y, hw, hh, s): d[n] = ("r", x, y, hw, hh, hw * s, hh * s)
def b2(d, dy, end_x):
    circle(d, "LS", 300, 1030 - dy, STICK_R, STICK_PRESS)
    circle(d, "DPAD", 300, 520 - dy, 125, 125 * 1.25)
    circle(d, "L3", 540, 1040 - dy, 48, 48 * 1.2)
    for n, ox, oy in (("TRIANGLE", 0, -90), ("CIRCLE", 90, 0), ("CROSS", 0, 90), ("SQUARE", -90, 0)):
        circle(d, n, 900 + ox, 1030 - dy + oy, 52, 52 * 1.2)
    circle(d, "RS", 900, 520 - dy, STICK_R, STICK_PRESS)
    circle(d, "R3", 690, 790 - dy, 48, 48 * 1.2)
    for n, x in (("L2", 56), ("L1", 170), ("R1", 1030), ("R2", 1144)):
        rect(d, n, x, 774 - dy, 50, 100, 1.1)
    rect(d, "SELECT", 400, 70, 75.5, 47.5, 1.2)
    rect(d, "START", 600, 70, 75.5, 47.5, 1.2)
    rect(d, "END", end_x, 70, 75.5, 47.5, 1.0)          # End is a Button: its press area is its rectangle
b2(HM4B, 0, 960)
NOW = {}
b2(NOW, GROW, END_X)
CLUSTER = [n for n in NOW if n not in ("SELECT", "START", "END")]

def gap(p, q, press):
    """The clearance between two shapes (negative = overlap), drawn or press areas."""
    pk, px, py, pa, pb, pha, phb = p
    qk, qx, qy, qa, qb, qha, qhb = q
    if press: pa, pb, qa, qb = pha, phb, qha, qhb
    if pk == "c" and qk == "c": return math.hypot(px - qx, py - qy) - pa - qa
    if pk == "r" and qk == "r":
        dx, dy = abs(px - qx) - pa - qa, abs(py - qy) - pb - qb
        return math.hypot(max(dx, 0), max(dy, 0)) if (dx > 0 or dy > 0) else max(dx, dy)
    (cx, cy, cr), (rx, ry, ra, rb) = ((px, py, pa), (qx, qy, qa, qb)) if pk == "c" else ((qx, qy, qa), (px, py, pa, pb))
    return math.hypot(max(abs(cx - rx) - ra, 0), max(abs(cy - ry) - rb, 0)) - cr

fails, lines = [], []
cm = lambda px: f"{px:.2f} px = {px / PX_CM:.3f} cm"

# 1 the cluster's on-screen centres equal G6-HM4b's (within 1 px)
worst = 0.0
for n in CLUSTER:
    _, x0, y0, *_ = HM4B[n]
    _, x1, y1, *_ = NOW[n]
    d = math.hypot(x1 - x0, (BOX + y1) - (BOX_HM4B + y0))
    worst = max(worst, d)
    if d > 1: fails.append(f"1 {n} moved {d:.2f} px")
lines.append(f"1 cluster on-screen centres vs G6-HM4b: {len(CLUSTER)} controls, largest move {worst:.2f} px (<= 1 px required)")
for n in ("SELECT", "START", "END"):
    _, x0, y0, *_ = HM4B[n]; _, x1, y1, *_ = NOW[n]
    lines.append(f"  {n}: on screen ({x0}, {BOX_HM4B + y0}) -> ({x1}, {BOX + y1})")

# 2 no drawn shape overlaps another; no press area overlaps another
names = list(NOW)
pairs = 0
for press in (False, True):
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairs += 1
            g = gap(NOW[names[i]], NOW[names[j]], press)
            if g < 0: fails.append(f"2 {'press' if press else 'drawn'} overlap {names[i]} {names[j]} ({g:.1f} px)")
lines.append(f"2 overlaps: {pairs} pairs checked (drawn and press, End included): {'none' if not any(f.startswith('2') for f in fails) else 'SEE FAILS'}")

# 3 End's rectangle to every press area >= 0.5 cm
end_gaps = sorted((gap(NOW["END"], NOW[n], True), n) for n in names if n != "END")
g, n = end_gaps[0]
lines.append(f"3 End (x {END_X}) nearest press area: {n} {cm(g)} (>= 0.5 cm = {0.5 * PX_CM:.1f} px required)")
for g2, n2 in end_gaps[:3]:
    lines.append(f"  End <-> {n2}: {cm(g2)}")
if g < 0.5 * PX_CM: fails.append(f"3 End {cm(g)} from {n}")
probe = dict(NOW); b = {}; rect(b, "END", END_X - 1, 70, 75.5, 47.5, 1.0); probe["END"] = b["END"]
g79 = gap(probe["END"], NOW["RS"], True)
lines.append(f"  smallest x: at x {END_X - 1} End <-> RS would be {cm(g79)} ({'under' if g79 < 0.5 * PX_CM else 'NOT under'} 0.5 cm)")
if g79 >= 0.5 * PX_CM: fails.append("3 End's x is not the smallest")
ek, ex, ey, ea, eb, *_ = NOW["END"]
lines.append(f"  End inside the region: x {ex - ea}..{ex + ea} of 0..{W}, y {ey - eb}..{ey + eb}")
if ex + ea > W or ex - ea < 0 or ey - eb < 0: fails.append("3 End outside the region")

# 4 reported: SELECT <-> D-pad and START <-> right stick, drawn and press
for a, c in (("SELECT", "DPAD"), ("START", "RS")):
    lines.append(f"4 {a} <-> {c}: drawn {cm(gap(NOW[a], NOW[c], False))}; press {cm(gap(NOW[a], NOW[c], True))}")

# 5 SELECT / START / End drawn smaller side >= 1 cm
for n in ("SELECT", "START", "END"):
    _, _, _, a, b2_, *_ = NOW[n]
    s = min(2 * a, 2 * b2_) / PX_CM
    lines.append(f"5 {n} drawn {2 * a:.0f} x {2 * b2_:.0f} px, smaller side {s:.2f} cm (>= 1 cm)")
    if s < 1.0: fails.append(f"5 {n} {s:.2f} cm")

# as before (layout_check_b.py): inside the region, out of the bottom tenth; shoulders 1 cm above it
for n, (k, x, y, a, b2_, ha, hb) in NOW.items():
    if x - ha < 0 or x + ha > W or y - hb < 0 or y + hb > BOTTOM: fails.append(f"b {n} outside / in the bottom tenth")
    if n in ("L1", "L2", "R1", "R2") and y + hb > BOTTOM - PX_CM: fails.append(f"b {n} within 1 cm of the bottom tenth")
lines.append(f"as before: every press area inside the region and above its bottom tenth (y {BOTTOM:.0f}); shoulders >= 1 cm above it")

print(f"G6-SCREEN1 on {SCREEN_W} x {SCREEN_H}: box {W} x {BOX} (was {BOX_HM4B}), pad region {W} x {H} (was {SCREEN_H - BOX_HM4B}); {PX_CM:.2f} px per cm")
print("\n".join(lines))
print("ALL CHECKS OK (1, 2, 3, 5)" if not fails else "FAILED: " + "; ".join(fails))
sys.exit(0 if not fails else 1)
