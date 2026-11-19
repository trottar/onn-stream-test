"""G6-HM1a: the proposed PS2 touch layout, checked (no Android, no code under PrivyHub/).
Pad region 1200 x 1325 px (G6-HM3's report). Sizes in cm at Android's 1.5 density (240 dpi, 94.49 px/cm, the
stricter for minimum sizes) and at the panel's own ~224 ppi (2000 x 1200 at 10.4", 88.2 px/cm).
Checks: every hit area inside the region and above the bottom tenth; no two hit areas overlap; every target
>= 1 cm; the D-pad, the sticks and the face cluster >= 2.5 cm; each control's distance from the assumed thumb pivots."""
import math, sys

W, H = 1200, 1325
PX_CM_240 = 240 / 2.54
PX_CM_224 = math.hypot(2000, 1200) / 10.4 / 2.54
BOTTOM = 0.9 * H
PIVOT_L, PIVOT_R = (0, H - 3 * PX_CM_240), (W, H - 3 * PX_CM_240)   # assumed: thumb base at the side, ~3 cm up

C = []   # (name, kind, cx, cy, a, b, hit_scale, main)   circle: a = r; rect: a, b = half-sizes
def circle(n, x, y, r, s, main=False): C.append((n, "c", x, y, r, r, s, main))
def rect(n, x, y, hw, hh, s): C.append((n, "r", x, y, hw, hh, s, False))

# left arc: stick at rest, D-pad above, L3 inner side; L1 on the edge at the D-pad's height, L2 above it
circle("LS", 300, 1000, 132, 1.2, True)
circle("DPAD", 300, 660, 125, 1.25, True)
circle("L3", 540, 1040, 48, 1.2)
rect("L1", 62.5, 700, 56.5, 104, 1.1)
rect("L2", 62.5, 465, 56.5, 104, 1.1)
# right arc: face cluster at rest (mirrors LS), right stick above it (mirrors the D-pad), R3 inner side
for n, dx, dy in (("TRIANGLE", 0, -90), ("CIRCLE", 90, 0), ("CROSS", 0, 90), ("SQUARE", -90, 0)):
    circle(n, 900 + dx, 1000 + dy, 52, 1.2)
circle("RS", 900, 660, 132, 1.2, True)
circle("R3", 690, 790, 48, 1.2)
rect("R1", W - 62.5, 700, 56.5, 104, 1.1)
rect("R2", W - 62.5, 465, 56.5, 104, 1.1)
# the top row: infrequent, away from both arcs; End kept apart from Start
rect("SELECT", 400, 70, 75.5, 47.5, 1.2)
rect("START", 600, 70, 75.5, 47.5, 1.2)
rect("END", 960, 70, 75.5, 47.5, 1.2)

def hit(c):
    n, k, x, y, a, b, s, _ = c
    return (k, x, y, a * s, b * s)

def overlap(p, q):
    if p[0] == "c" and q[0] == "c":
        return math.hypot(p[1] - q[1], p[2] - q[2]) < p[3] + q[3]
    if p[0] == "r" and q[0] == "r":
        return abs(p[1] - q[1]) < p[3] + q[3] and abs(p[2] - q[2]) < p[4] + q[4]
    c, r = (p, q) if p[0] == "c" else (q, p)
    dx = max(abs(c[1] - r[1]) - r[3], 0); dy = max(abs(c[2] - r[2]) - r[4], 0)
    return math.hypot(dx, dy) < c[3]

ok = True
print(f"region {W}x{H} px = {W/PX_CM_224:.1f} x {H/PX_CM_224:.1f} cm (224 ppi) / {W/PX_CM_240:.1f} x {H/PX_CM_240:.1f} cm (240 dpi)")
print(f"{'control':9s} {'centre px':12s} {'drawn cm (240 / 224)':24s} {'hit px':14s} {'pivot cm (224)':>14s}")
for c in C:
    n, k, x, y, a, b, s, main = c
    hk, hx, hy, ha, hb = hit(c)
    w_px, h_px = 2 * a, 2 * b
    wc, hc = w_px / PX_CM_240, h_px / PX_CM_240
    piv = PIVOT_L if x < W / 2 else PIVOT_R
    d = math.hypot(x - piv[0], y - piv[1]) / PX_CM_224
    size = f"{wc:.2f}x{hc:.2f} / {w_px/PX_CM_224:.2f}x{h_px/PX_CM_224:.2f}" if k == "r" else f"dia {wc:.2f} / {w_px/PX_CM_224:.2f}"
    hits = f"r {ha:.0f}" if k == "c" else f"{2*ha:.0f}x{2*hb:.0f}"
    print(f"{n:9s} ({x:6.1f},{y:5.0f}) {size:24s} {hits:14s} {d:14.1f}")
    if min(wc, hc) < 1.0: ok = False; print("  FAIL: under 1 cm")
    if main and wc < 2.5: ok = False; print("  FAIL: main control under 2.5 cm")
    if hx - ha < 0 or hx + ha > W or hy - hb < 0 or hy + hb > BOTTOM: ok = False; print("  FAIL: outside the region or in the bottom tenth")
face = [c for c in C if c[0] in ("TRIANGLE", "CIRCLE", "CROSS", "SQUARE")]
span = (90 * 2 + 2 * 52)
print(f"face cluster across: {span/PX_CM_240:.2f} cm (240) / {span/PX_CM_224:.2f} cm (224)")
pairs = 0
for i in range(len(C)):
    for j in range(i + 1, len(C)):
        pairs += 1
        if overlap(hit(C[i]), hit(C[j])):
            ok = False; print("OVERLAP", C[i][0], C[j][0])
print(f"hit-area pairs checked: {pairs}; bottom tenth from y {BOTTOM:.0f}; pivots at y {PIVOT_L[1]:.0f}")
print("ALL CHECKS OK" if ok else "CHECKS FAILED")

# the sketch: one character per 25 x 50 px
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
print("+" + "-" * cols + "+   (the pad region; the video box is above it)")
for r in range(rows):
    line = "".join(grid[r])
    print(("|" + line + "|") if r * 50 < BOTTOM else ("|" + line.replace(" ", ".") + "|  bottom tenth (home gesture)"))
print("+" + "-" * cols + "+")
sys.exit(0 if ok else 1)
