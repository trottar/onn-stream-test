"""G6-HM4b: addendum B2 re-checked with the sticks' throw 0.875 x G6-HM4's (the user: "10-15% smaller").
The drawn ring = the throw radius = 132 x 0.875 = 115.5 px; the press area unchanged (132 x 1.2 = 158.4 px).
Every other control as B2 (layout_check_b.py, B2), and every check as there. The amendment's 2.5 cm minimum for the
sticks' drawn size is REPORTED, not enforced: the user asked for the shorter throw, and the press area exceeds it."""
import math, sys

W, H = 1200, 1325
PX_CM_240 = 240 / 2.54
PX_CM_224 = math.hypot(2000, 1200) / 10.4 / 2.54
BOTTOM = 0.9 * H
SHOULDER_BOTTOM = BOTTOM - PX_CM_240
STICK_R_HM4, THROW = 132.0, 0.875
STICK_R = STICK_R_HM4 * THROW
STICK_PRESS = STICK_R_HM4 * 1.2

C = []
def circle(n, x, y, r, hit_r, main=False): C.append((n, "c", x, y, r, r, hit_r, hit_r, main))
def rect(n, x, y, hw, hh, s): C.append((n, "r", x, y, hw, hh, hw * s, hh * s, False))
circle("LS", 300, 1030, STICK_R, STICK_PRESS, True)
circle("DPAD", 300, 520, 125, 125 * 1.25, True)
circle("L3", 540, 1040, 48, 48 * 1.2)
for n, dx, dy in (("TRIANGLE", 0, -90), ("CIRCLE", 90, 0), ("CROSS", 0, 90), ("SQUARE", -90, 0)):
    circle(n, 900 + dx, 1030 + dy, 52, 52 * 1.2)
circle("RS", 900, 520, STICK_R, STICK_PRESS, True)
circle("R3", 690, 790, 48, 48 * 1.2)
rect("SELECT", 400, 70, 75.5, 47.5, 1.2)
rect("START", 600, 70, 75.5, 47.5, 1.2)
rect("END", 960, 70, 75.5, 47.5, 1.2)
for n, x in (("L2", 56), ("L1", 170), ("R1", 1030), ("R2", 1144)):
    rect(n, x, 774, 50, 100, 1.1)

def overlap(p, q):
    _, pk, px, py, _, _, pa, pb, _ = p
    _, qk, qx, qy, _, _, qa, qb, _ = q
    if pk == "c" and qk == "c": return math.hypot(px - qx, py - qy) < pa + qa
    if pk == "r" and qk == "r": return abs(px - qx) < pa + qa and abs(py - qy) < pb + qb
    (cx, cy, cr), (rx, ry, ra, rb) = ((px, py, pa), (qx, qy, qa, qb)) if pk == "c" else ((qx, qy, qa), (px, py, pa, pb))
    return math.hypot(max(abs(cx - rx) - ra, 0), max(abs(cy - ry) - rb, 0)) < cr

fails, reported = [], []
for c in C:
    n, k, x, y, a, b, ha, hb, main = c
    wc, hc = 2 * a / PX_CM_240, 2 * b / PX_CM_240
    if min(wc, hc) < 1.0: fails.append(f"{n} under 1 cm")
    if n in ("L1", "L2", "R1", "R2") and hc < 2.0: fails.append(f"{n} under 2 cm tall")
    if main and wc < 2.5:
        (reported if n in ("LS", "RS") else fails).append(f"{n} drawn {wc:.2f} cm < 2.5 cm (press area {2*ha/PX_CM_240:.2f} cm)")
    if x - ha < 0 or x + ha > W or y - hb < 0 or y + hb > BOTTOM: fails.append(f"{n} outside / in the bottom tenth")
    if n in ("L1", "L2", "R1", "R2") and y + hb > SHOULDER_BOTTOM: fails.append(f"{n} within 1 cm of the bottom tenth")
pairs = 0
for i in range(len(C)):
    for j in range(i + 1, len(C)):
        pairs += 1
        if overlap(C[i], C[j]): fails.append(f"overlap {C[i][0]} {C[j][0]}")
print(f"sticks: G6-HM4 drawn r {STICK_R_HM4:.1f} px -> G6-HM4b r {STICK_R:.1f} px (x {THROW}); press area r {STICK_PRESS:.1f} px (unchanged)")
for label, r in (("G6-HM4", STICK_R_HM4), ("G6-HM4b", STICK_R)):
    print(f"  {label} drawn diameter {2*r:.0f} px = {2*r/PX_CM_240:.2f} cm (240 dpi) / {2*r/PX_CM_224:.2f} cm (224 ppi); full deflection at {r:.1f} px = {r/PX_CM_224*10:.1f} mm of finger travel (224 ppi)")
print(f"  press area diameter {2*STICK_PRESS:.0f} px = {2*STICK_PRESS/PX_CM_240:.2f} cm (240 dpi) / {2*STICK_PRESS/PX_CM_224:.2f} cm (224 ppi)")
print(f"hit-area pairs checked: {pairs}")
print("REPORTED (kept at the user's request):", "; ".join(reported) if reported else "none")
print("ALL CHECKS OK" if not fails else "FAILED: " + "; ".join(fails))
sys.exit(0 if not fails else 1)
