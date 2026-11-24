import sys, csv, json, itertools
sys.path.insert(0, sys.argv[1])
import h7_endscreen as es
from PIL import Image
from pathlib import Path
pics = Path(sys.argv[2])
# my readings, as drawn: finals, 1ST cells, stats table rows (SHOOT..PK, 6 rows) per side
R = {"end_P1": ("02","00",["13","00","00","00","01","00"],["00"]*6),
     "end_P1_2": ("05","04",["00"]*6,["00"]*6), "end_P2": ("02","03",["00"]*6,["00"]*6),
     "end_P2_2": ("00","02",["00"]*6,["00"]*6)}
F = [{"pol":1,"r":8,"top":82,"bot":139,"x0":184,"x1":262},{"pol":1,"r":8,"top":82,"bot":139,"x0":408,"x1":485}]
C = [{"pol":1,"r":8,"top":80,"bot":95,"x0":289,"x1":313},{"pol":1,"r":8,"top":80,"bot":95,"x0":362,"x1":384}]
out = {}
for role, (f1, f2, s1, s2) in R.items():
    rows = list(csv.DictReader((pics/role/"index.csv").open()))
    with Image.open(pics/role/rows[0]["file"]) as im: a = es.score_picture(im)
    ss = [s for s in es.score_strings(a) if s["pol"]==1 and s["r"]==8 and s["n"]==2 and s["top"]>215 and s["bot"]-s["top"]<25]
    st = {k: sorted([s for s in ss if abs((s["x0"]+s["x1"])/2 - cx) < 20], key=lambda s: s["top"]) for k, cx in ((0,215),(1,454))}
    spots = [("F", F[0], f1), ("F", F[1], f2), ("C", C[0], f1), ("C", C[1], f2)]
    for k, vals in ((0, s1), (1, s2)):
        for s, v in zip(st[k][:6], vals):
            spots.append(("S", {"pol":1,"r":8,"top":s["top"],"bot":s["bot"],"x0":s["x0"],"x1":s["x1"]}, v))
    for size, pl, v in spots:
        gl = es.place_glyphs(a, pl)
        if gl is None or len(gl) != len(v): print("unfit", role, size, v, pl); continue
        for ch, g in zip(v, gl):
            out.setdefault((size, ch), []).append((role, es.glyph_cell(a, g, pl)))
    print(role, "stats rows found", len(st[0]), len(st[1]), "heights", sorted({s["bot"]-s["top"] for s in ss}))
def d(a, b): return float(es.cell_dists(a, b[None])[0])
keys = sorted(out)
print({k: len(v) for k, v in out.items()})
res = {}
for (s1, c1), (s2, c2) in itertools.combinations_with_replacement(keys, 2):
    ds = [d(a, b) for (ra, a) in out[(s1, c1)] for (rb, b) in out[(s2, c2)] if not (s1 == s2 and c1 == c2 and a is b)]
    if not ds: continue
    kind = ("same digit" if c1 == c2 else "two digits") + (" same size " + s1 if s1 == s2 else " sizes " + "".join(sorted(s1+s2)))
    res.setdefault(kind, []).append((min(ds), max(ds), f"{s1}{c1}-{s2}{c2}"))
for k, v in sorted(res.items()):
    print(k, "min", round(min(x[0] for x in v),3), "max", round(max(x[1] for x in v),3), [ (p, round(a,3), round(b,3)) for a,b,p in v][:12])
