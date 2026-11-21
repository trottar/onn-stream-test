#!/usr/bin/env python3
"""Queue BJ B190: why learn could not use T91 at all — settled from the tool's pictures of its six kept saves (made from
exactly those states; read only; the picture source never ran). No title, no path printed. usage:
  t91_settle.py <tools folder> <T91's pictures folder>"""
import csv, json, sys
import numpy as np
from PIL import Image
sys.path.insert(0, sys.argv[1])
import h7_endscreen as es
P = sys.argv[2]
RUNS = ["begin", "other", "end_P1", "end_P1_2", "end_P2", "end_P2_2"]
SIDES = {"end_P1": ["---", "WOW"], "end_P1_2": ["---", "WOW"], "end_P2": ["WOW", "W--"], "end_P2_2": ["WOW", "W--"]}
def rows(r):
    return [(float(x["seconds"]), x["file"]) for x in csv.DictReader(open(f"{P}/{r}/index.csv"))]
def small(r, f):
    with Image.open(f"{P}/{r}/{f}") as im:
        return np.asarray(im.convert("L").resize((64, 48)), dtype=np.float64)
print("1. Does each picture hold still? (64 x 48 grey; B140's moved share: cells moved > 16 levels; H7-V1's same-"
      "picture measure: mean |difference| < 1.0)")
for r in RUNS:
    rs = rows(r)
    sm = [small(r, f) for _t, f in rs]
    steps = [float(np.abs(sm[i] - sm[i - 1]).mean()) for i in range(1, len(sm))]
    moved = [float((np.abs(sm[i] - sm[i - 1]) > 16).mean()) for i in range(1, len(sm))]
    still_from = next((rs[i][0] for i in range(len(sm)) if all(s < 1.0 for s in steps[i:])), None)
    print(f"  {r}: {len(rs)} pictures over {rs[-1][0]:.1f} s; steps (mean |diff|) max {max(steps):.2f}, "
          f"first {steps[0]:.2f}; moved share max {max(moved):.3f}; identical from {still_from} s on")
print("2. Why the begin was never recognised under `winner` (B102's whole-screen learner on the labels learn used)")
lab = f"{P}/labels.json"
spec, arrays, rep = es.learn(P, lab)
sc = rep["screen"]
print(f"  screen mask {rep['screen_mask']['px']} px ({rep['screen_mask']['share']:.1%}); the screens' own worst "
      f"distance {sc['worst_own']} vs the nearest `other` picture {sc['best_foreign']} -> gap {sc['gap']}: "
      f"{sc['verdict']}; spec usable {spec['usable']} (no screen threshold: every read `other`, so nothing is unknown "
      f"or an end, the begin included)")
print("3. The begin as its own still picture (B122's one-screen learner against the mid-match save and the end saves)")
def grey(r, f, black):
    with Image.open(f"{P}/{r}/{f}") as im:
        return es._final(es.mid(es.corner_black(im) if black else im.convert("RGB")))
for black in (False, True):
    st = np.stack([grey("begin", f, black) for _t, f in rows("begin")]).astype(np.float32)
    oth = np.stack([grey("other", f, black) for _t, f in rows("other")]).astype(np.float32)
    ends = np.stack([grey(r, f, black) for r in RUNS[2:] for _t, f in rows(r)]).astype(np.float32)
    m, ref, g = es._learn_one_screen(st, [oth, ends])
    print(f"  B137's corner {'black' if black else 'as it is'}: own worst {g['worst_own']}, nearest other picture "
          f"{g['best_foreign']}, gap {g['gap']}, threshold {g['threshold']} ({g['verdict']}); mask {g['mask_px']} px, "
          f"{g['shared_px_left_out']} px it shares with them left out")
print("4. Where each player's letters sit, how big; how the backgrounds differ (the letters learner, all four end saves)")
def paths(r, idx):
    rs = rows(r)
    return [f"{P}/{r}/{rs[i][1]}" for i in idx]
spec, arrays, rep = es.learn_letters(paths("begin", range(len(rows("begin")))), paths("other", range(2, len(rows("other")))),
                                     {r: paths(r, [1, 3]) for r in SIDES}, SIDES, "WOW", 2)
lt = spec["letters"]
print(f"  places (x0, y0, x1, y1 at 640 x 480): {json.dumps(lt['places'])}; found in: {json.dumps(lt['found_in'])}")
rd = es.Reader(spec, arrays)
for r in SIDES:
    with Image.open(paths(r, [1])[0]) as im:
        a = es.letters_area(im)
    for p in (1, 2):
        m, gl = es.letters_glyphs(a, rd.places[p], rd.bins[p], rd.glyph_min)
        x0, y0 = rd.places[p][:2]
        print(f"  {r} P{p} ({'/'.join(SIDES[r])}): glyphs " + ", ".join(
            f"{w}x{h} px at x {x0 + g[1]}-{x0 + g[3]}, y {y0 + g[0]}-{y0 + g[2]}" for g in gl
            for w, h in [(g[3] - g[1] + 1, g[2] - g[0] + 1)]))
A = {r: es.letters_area(Image.open(paths(r, [1])[0])) for r in SIDES}
print("  pixels the same (within 12 levels) in two end saves, whole picture / each corner's box:")
for i, a in enumerate(SIDES):
    for b in list(SIDES)[i + 1:]:
        eq = np.abs(A[a] - A[b]).max(axis=2) <= 12
        box = [float(eq[y0:y1, x0:x1].mean()) for x0, y0, x1, y1 in (rd.places[1], rd.places[2])]
        print(f"    {a} / {b}: {eq.mean():.3f} / P1 {box[0]:.3f}, P2 {box[1]:.3f}")
print(f"  synthetic training: {json.dumps({k: rep['synthetic'][k] for k in ('held_out', 'trained', 'rounds', 'every_held_out_read')})}; learn {rep['learn_s']} s")
