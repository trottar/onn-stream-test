#!/usr/bin/env python3
"""Queue BH B181: T90's four end saves — is the line score the FINAL column's font at its size (glyph for glyph,
B178's measure), and which digits the whole line score shows. Numbers only (my readings as the label stage took them).
usage: t90_settle.py <pictures folder>"""
import sys, csv, itertools
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[5] / "tools"))
import numpy as np, h7_endscreen as es
from PIL import Image
P = sys.argv[1].rstrip("/") + "/"   # the scratch copy of the pictures session A made
# my readings of the line score (P1 row, P2 row): quarters Q1-Q4, OT1, OT2, final
LS = {"end_P1": ([9, 2, 2, 2, None, None], 15, [0, 0, 2, 0, None, None], 2),
      "end_P1_2": ([7, 7, 7, 7, 7, None], 35, [7, 7, 7, 7, 0, None], 28),
      "end_P2": ([0, 0, 0, 0, None, None], 0, [2, 9, 2, 9, None, None], 22),
      "end_P2_2": ([0, 0, 0, 0, None, None], 0, [9, 9, 2, 9, None, None], 29)}
COLS = [(225, 232), (278, 286), (332, 339), (386, 393), (440, 447), (494, 501)]
FIN = (547, 563)
inst = []
for r, (c1, f1, c2, f2) in LS.items():
    f = next(csv.DictReader(open(P + r + "/index.csv")))["file"]
    with Image.open(P + r + "/" + f) as im: a = es.score_picture(im)
    for top, bot, cells, fin in ((396, 411, c1, f1), (424, 439, c2, f2)):
        for kind, (x0, x1), v in [("Q", c, v) for c, v in zip(COLS, cells) if v is not None] + [("F", FIN, fin)]:
            pl = {"pol": 1, "r": 8, "top": top, "bot": bot, "x0": x0, "x1": x1}
            gl = es.place_glyphs(a, pl)
            assert gl and len(gl) == len(str(v)), (r, kind, x0, v, gl)
            for ch, g in zip(str(v), gl):
                inst.append((ch, kind, r, g[2] - g[0] + 1, g[3] - g[1] + 1, es.glyph_cell(a, g, pl)))
def d(a, b): return float(es.cell_dists(a, b[None])[0])
print("glyph heights (Q / F):", sorted({h for ch, k, r, h, w, c in inst if k == "Q"}), sorted({h for ch, k, r, h, w, c in inst if k == "F"}))
for ch in sorted({x[0] for x in inst}):
    q = [x for x in inst if x[0] == ch and x[1] == "Q"]; f = [x for x in inst if x[0] == ch and x[1] == "F"]
    if q and f:
        print(f"digit {ch}: Q widths {sorted({x[4] for x in q})} F widths {sorted({x[4] for x in f})}; Q-F distance max {max(d(a[5], b[5]) for a in q for b in f):.3f}; Q-Q max {max([d(a[5], b[5]) for a, b in itertools.combinations(q, 2)] or [0]):.3f}")
diff = min(d(a[5], b[5]) for a, b in itertools.combinations(inst, 2) if a[0] != b[0])
same = max(d(a[5], b[5]) for a, b in itertools.combinations(inst, 2) if a[0] == b[0])
print(f"over every labelled glyph: the same digit at most {same:.3f} apart (quarters and finals together), two digits at least {diff:.3f}")
from collections import Counter
cnt = Counter(); saves = {}
for r, (c1, f1, c2, f2) in LS.items():
    for v in [x for x in c1 + c2 if x is not None] + [f1, f2]:
        for ch in str(v): cnt[ch] += 1; saves.setdefault(ch, set()).add(r)
print("digits across the whole line score (glyphs, saves):", {d_: (cnt[d_], len(saves.get(d_, ()))) for d_ in "0123456789"})
