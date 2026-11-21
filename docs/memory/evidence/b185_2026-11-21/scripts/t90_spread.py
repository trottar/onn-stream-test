#!/usr/bin/env python3
"""Queue BI B186: T90's five end saves — for every digit two saves show, how far apart its glyphs are across saves
against within one save (B178's local measure, at the hub's capture: the label stage's first picture of each save).
Numbers only (my readings as the label stage took them). usage: t90_spread.py <pictures folder> <tools folder> (run with python3 -I)"""
import sys, csv, itertools
sys.path.insert(0, sys.argv[2])
import numpy as np, h7_endscreen as es
from PIL import Image
P = sys.argv[1].rstrip("/") + "/"
LS = {"end_P1": ([9, 2, 2, 2, None, None], 15, [0, 0, 2, 0, None, None], 2),
      "end_P1_2": ([7, 7, 7, 7, 7, None], 35, [7, 7, 7, 7, 0, None], 28),
      "end_P2": ([0, 0, 0, 0, None, None], 0, [2, 9, 2, 9, None, None], 22),
      "end_P2_2": ([0, 0, 0, 0, None, None], 0, [9, 9, 2, 9, None, None], 29),
      "end_P2_3": ([0, 6, 0, 8, None, None], 14, [9, 3, 6, 6, None, None], 24)}
COLS = [(225, 232), (278, 286), (332, 339), (386, 393), (440, 447), (494, 501)]
FIN = (547, 563)
def glyphs(r, f):
    with Image.open(P + r + "/" + f) as im: a = es.score_picture(im)
    out = []
    c1, f1, c2, f2 = LS[r]
    for top, bot, cells, fin in ((396, 411, c1, f1), (424, 439, c2, f2)):
        for kind, (x0, x1), v in [("Q", c, v) for c, v in zip(COLS, cells) if v is not None] + [("F", FIN, fin)]:
            pl = {"pol": 1, "r": 8, "top": top, "bot": bot, "x0": x0, "x1": x1}
            gl = es.place_glyphs(a, pl)
            assert gl and len(gl) == len(str(v)), (r, kind, x0, v, gl)
            for i, (ch, g) in enumerate(zip(str(v), gl)):
                out.append((ch, r, (top, x0, i), es.glyph_cell(a, g, pl)))
    return out
def d(a, b): return float(es.cell_dists(a, b[None])[0])
first = {}
second = {}
for r in LS:
    rows = [x["file"] for x in csv.DictReader(open(P + r + "/index.csv"))]
    first[r] = glyphs(r, rows[0]); second[r] = glyphs(r, rows[2])
inst = [g for r in LS for g in first[r]]
from collections import Counter
print("the hub's capture: 640 x 480, each save's first picture (the label stage's .1); a glyph 16 px tall")
print("digits (glyphs; saves):", {c: (sum(1 for g in inst if g[0] == c), len({g[1] for g in inst if g[0] == c})) for c in "0123456789"})
W_all, A_all = [], []
print("per digit shown by two saves: within one save (max, mean, n pairs) | across saves (max, mean, n pairs)")
for ch in "0123456789":
    gs = [g for g in inst if g[0] == ch]
    if len({g[1] for g in gs}) < 2:
        continue
    w = [d(a[3], b[3]) for a, b in itertools.combinations(gs, 2) if a[1] == b[1]]
    x = [d(a[3], b[3]) for a, b in itertools.combinations(gs, 2) if a[1] != b[1]]
    W_all += w; A_all += x
    fw = f"{max(w):.3f} {np.mean(w):.3f} {len(w)}" if w else "- - 0"
    print(f"  {ch}: within {fw} | across {max(x):.3f} {np.mean(x):.3f} {len(x)}")
print(f"all those digits: within max {max(W_all):.3f} mean {np.mean(W_all):.3f} ({len(W_all)} pairs); across max {max(A_all):.3f} mean {np.mean(A_all):.3f} ({len(A_all)} pairs)")
print(f"  across max - within max = {max(A_all) - max(W_all):+.3f}; across mean - within mean = {np.mean(A_all) - np.mean(W_all):+.3f}")
# the same glyph in two pictures of one save (the capture's own noise)
nz = [d(a[3], b[3]) for r in LS for a, b in zip(first[r], second[r])]
print(f"the same glyph, two pictures of one save: max {max(nz):.3f} mean {np.mean(nz):.3f} ({len(nz)})")
for ch in "467":
    gs = [g for g in inst if g[0] == ch]
    w = [d(a[3], b[3]) for a, b in itertools.combinations(gs, 2)]
    print(f"digit {ch} (one save, {len(gs)} glyphs): within max {max(w) if w else float('nan'):.3f} mean {np.mean(w) if w else float('nan'):.3f} ({len(w)} pairs)")
diff = min(d(a[3], b[3]) for a, b in itertools.combinations(inst, 2) if a[0] != b[0])
pair = min(((d(a[3], b[3]), a[0], b[0]) for a, b in itertools.combinations(inst, 2) if a[0] != b[0]))
print(f"two different digits at least {diff:.3f} apart ({pair[1]} / {pair[2]})")
# leave one glyph out: each glyph of a digit one save shows several times, against the mean of its save's other glyphs
# of that digit, and every other digit's template (all glyphs)
keys = sorted({g[0] for g in inst})
for ch in "467":
    gs = [g for g in inst if g[0] == ch]
    for i, g in enumerate(gs):
        rest = np.mean([h[3] for j, h in enumerate(gs) if j != i], axis=0)
        own = d(g[3], rest)
        others = min(d(g[3], np.mean([h[3] for h in inst if h[0] == k], axis=0)) for k in keys if k != ch)
        print(f"  {ch} glyph {i + 1}: to its save's other {ch}s {own:.3f}; nearest other digit {others:.3f}")
