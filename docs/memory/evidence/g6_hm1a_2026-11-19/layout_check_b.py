"""G6-HM1b: the shoulder re-check (the user's Q-L2 (b): L1 and L2 side by side on the edge at one height, L2 on the
outside; R1 / R2 mirror them). Copied from layout_check.py; the checks are unchanged and none is loosened.

Layout B0 changes ONLY the four shoulder rectangles (the task's rule) and searches every height. If no height brings
both shoulders within about 4-5 cm of the thumb base while every check passes, B1 and B2 are the closest alternatives;
they also move other controls, so they are options for the user, not the addendum's layout.

Checks (as layout_check.py, plus the shoulders' own):
  - every press area inside the region and above the bottom tenth (the home gesture);
  - the shoulders' press areas >= 1 cm above the bottom tenth (the design's named gesture strip; the design names no
    side-edge strip width);
  - no two press areas overlap; every target >= 1 cm; the D-pad, the sticks >= 2.5 cm; the shoulders >= 1 x 2 cm.
Sizes in cm at 240 dpi (94.49 px/cm, the stricter); distances from the thumb base at the panel's ~224 ppi (88.2 px/cm),
as the amendment's table."""
import math, sys

W, H = 1200, 1325
PX_CM_240 = 240 / 2.54
PX_CM_224 = math.hypot(2000, 1200) / 10.4 / 2.54
BOTTOM = 0.9 * H
SHOULDER_BOTTOM = BOTTOM - PX_CM_240          # 1 cm above the bottom tenth
PIVOT_L, PIVOT_R = (0, H - 3 * PX_CM_240), (W, H - 3 * PX_CM_240)
SH_W, SH_H, SH_HIT = 50.0, 100.0, 1.1         # half-sizes: 100 x 200 px drawn = 1.06 x 2.12 cm
L2_X = 6 + SH_W                               # L2 on the outside, 6 px from the edge
L1_X = L2_X + 2 * SH_W * SH_HIT + 4           # L1 inward, press areas 4 px apart


def base(dpad=(300, 660), ls=(300, 1000), l3=(540, 1040), face=(900, 1000), rs=(900, 660), r3=(690, 790)):
    C = []
    def circle(n, x, y, r, s, main=False): C.append((n, "c", x, y, r, r, s, main))
    def rect(n, x, y, hw, hh, s): C.append((n, "r", x, y, hw, hh, s, False))
    circle("LS", *ls, 132, 1.2, True)
    circle("DPAD", *dpad, 125, 1.25, True)
    circle("L3", *l3, 48, 1.2)
    for n, dx, dy in (("TRIANGLE", 0, -90), ("CIRCLE", 90, 0), ("CROSS", 0, 90), ("SQUARE", -90, 0)):
        circle(n, face[0] + dx, face[1] + dy, 52, 1.2)
    circle("RS", *rs, 132, 1.2, True)
    circle("R3", *r3, 48, 1.2)
    rect("SELECT", 400, 70, 75.5, 47.5, 1.2)
    rect("START", 600, 70, 75.5, 47.5, 1.2)
    rect("END", 960, 70, 75.5, 47.5, 1.2)
    return C


def shoulders(y):
    return [(n, "r", x, y, SH_W, SH_H, SH_HIT, False) for n, x in
            (("L2", L2_X), ("L1", L1_X), ("R1", W - L1_X), ("R2", W - L2_X))]


def hit(c):
    n, k, x, y, a, b, s, _ = c
    return (k, x, y, a * s, b * s)


def overlap(p, q):
    if p[0] == "c" and q[0] == "c":
        return math.hypot(p[1] - q[1], p[2] - q[2]) < p[3] + q[3]
    if p[0] == "r" and q[0] == "r":
        return abs(p[1] - q[1]) < p[3] + q[3] and abs(p[2] - q[2]) < p[4] + q[4]
    c, r = (p, q) if p[0] == "c" else (q, p)
    dx = max(abs(c[1] - r[1]) - r[3], 0)
    dy = max(abs(c[2] - r[2]) - r[4], 0)
    return math.hypot(dx, dy) < c[3]


def failures(C):
    out = []
    for c in C:
        n, k, x, y, a, b, s, main = c
        hk, hx, hy, ha, hb = hit(c)
        wc, hc = 2 * a / PX_CM_240, 2 * b / PX_CM_240
        if min(wc, hc) < 1.0: out.append(f"{n} under 1 cm")
        if n in ("L1", "L2", "R1", "R2") and (min(wc, hc) < 1.0 or max(wc, hc) < 2.0): out.append(f"{n} under 1 x 2 cm")
        if main and wc < 2.5: out.append(f"{n} main under 2.5 cm")
        if hx - ha < 0 or hx + ha > W or hy - hb < 0 or hy + hb > BOTTOM: out.append(f"{n} outside / in the bottom tenth")
        if n in ("L1", "L2", "R1", "R2") and hy + hb > SHOULDER_BOTTOM: out.append(f"{n} within 1 cm of the bottom tenth")
    for i in range(len(C)):
        for j in range(i + 1, len(C)):
            if overlap(hit(C[i]), hit(C[j])): out.append(f"overlap {C[i][0]} {C[j][0]}")
    return out


def dist_cm(c):
    piv = PIVOT_L if c[2] < W / 2 else PIVOT_R
    return math.hypot(c[2] - piv[0], c[3] - piv[1]) / PX_CM_224


def report(title, C):
    f = failures(C)
    print(f"\n== {title}")
    print(f"{'control':9s} {'centre px':14s} {'drawn cm (240)':16s} {'press area px':14s} {'thumb base cm':>13s}")
    for c in C:
        n, k, x, y, a, b, s, _ = c
        size = f"{2*a/PX_CM_240:.2f}x{2*b/PX_CM_240:.2f}" if k == "r" else f"dia {2*a/PX_CM_240:.2f}"
        hits = f"{2*a*s:.0f}x{2*b*s:.0f}" if k == "r" else f"r {a*s:.0f}"
        print(f"{n:9s} ({x:6.1f},{y:6.1f}) {size:16s} {hits:14s} {dist_cm(c):13.1f}")
    print("checks:", "ALL OK" if not f else "FAILED: " + "; ".join(f))
    sketch(C)
    return not f


def sketch(C):
    cols, rows = W // 25, H // 50
    grid = [[" "] * cols for _ in range(rows)]
    mark = {"LS": "L", "RS": "R", "DPAD": "+", "L3": "3", "R3": "3", "L1": "1", "R1": "1", "L2": "2", "R2": "2",
            "TRIANGLE": "^", "CIRCLE": "o", "CROSS": "x", "SQUARE": "#", "SELECT": "s", "START": "S", "END": "E"}
    for c in C:
        n, k, x, y, a, b, s, _ = c
        for r in range(rows):
            for q in range(cols):
                px, py = q * 25 + 12.5, r * 50 + 25
                inside = math.hypot(px - x, py - y) <= a if k == "c" else (abs(px - x) <= a and abs(py - y) <= b)
                if inside: grid[r][q] = mark[n]
    print("+" + "-" * cols + "+")
    for r in range(rows):
        line = "".join(grid[r])
        print(("|" + line + "|") if r * 50 < BOTTOM else ("|" + line.replace(" ", ".") + "|"))
    print("+" + "-" * cols + "+")


print(f"shoulders: drawn {2*SH_W:.0f} x {2*SH_H:.0f} px = {2*SH_W/PX_CM_240:.2f} x {2*SH_H/PX_CM_240:.2f} cm; "
      f"press areas {2*SH_W*SH_HIT:.0f} x {2*SH_H*SH_HIT:.0f} px; L2 x {L2_X:.0f}, L1 x {L1_X:.0f} "
      f"(R1 x {W-L1_X:.0f}, R2 x {W-L2_X:.0f}); the thumb bases at y {PIVOT_L[1]:.0f}; "
      f"shoulders' press areas end by y {SHOULDER_BOTTOM:.0f}")

# B0: only the shoulders move; every height searched
ok_heights = [y for y in range(0, H + 1) if not failures(base() + shoulders(y))]
print(f"\nB0 search (only the shoulders change): heights passing every check: "
      + (f"{len(ok_heights)} (y {min(ok_heights)}..{max(ok_heights)})" if ok_heights else "none"))
best = None
if ok_heights:
    best = min(ok_heights, key=lambda y: max(dist_cm(c) for c in shoulders(y)))
    far = max(dist_cm(c) for c in shoulders(best))
    print(f"B0 best height y {best}: the farther shoulder {far:.1f} cm from the thumb base "
          f"({'within' if far <= 5.0 else 'NOT within'} about 4-5 cm)")
within = [y for y in ok_heights if max(dist_cm(c) for c in shoulders(y)) <= 5.0]
print("B0 heights passing every check AND within 5 cm:", within[:1] + within[-1:] if within else "none")
b0_ok = report(f"B0 — only the shoulders moved, y {best}", base() + shoulders(best)) if best is not None else False

# B1: the closest alternative — both arcs moved inward 90 px so the shoulder pair fits beside them at ~4 cm
b1 = base(dpad=(390, 660), ls=(390, 1000), l3=(580, 1120), face=(810, 1000), rs=(810, 660), r3=(630, 800))
b1_ok = report("B1 — alternative: the D-pad, sticks and face cluster 90 px inward; shoulders at y 700", b1 + shoulders(700))
# B2: the other alternative — the D-pad and the right stick up 140 px, the left stick and the face cluster down 30 px
b2 = base(dpad=(300, 520), ls=(300, 1030), face=(900, 1030), rs=(900, 520))
b2_ok = report("B2 — alternative: the D-pad and right stick up, the left stick and face cluster down; shoulders at y 774",
               b2 + shoulders(774))
print(f"\nsummary: B0 every check {'OK' if b0_ok else 'FAILED'}, within 5 cm {'yes' if within else 'no'}; "
      f"B1 {'OK' if b1_ok else 'FAILED'}; B2 {'OK' if b2_ok else 'FAILED'}")
sys.exit(0 if (b0_ok and b1_ok and b2_ok) else 1)
