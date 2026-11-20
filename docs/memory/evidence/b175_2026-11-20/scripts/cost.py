#!/usr/bin/env python3
"""Queue BF B175: what one learn costs (es.learn as learn calls it), so what leaving each save out costs — made-up
pictures at 320 x 240 and at 1280 x 960 (the hub's 4x of a 320 x 240 game), 21 a save. Temp folder removed.
usage: cost.py <work copy>"""
import json, shutil, sys, tempfile, time
from pathlib import Path
W = Path(sys.argv[1]); sys.path[:0] = [str(W / "tools"), str(W / "tests/b171_more_saves")]
import numpy as np, party_add_game as pag, near_capture as nc
es = pag._endscreen()
print("| pictures | players | saves an ending | one learn (s) | every save left out (s) |"); print("| --- | --- | --- | --- | --- |")
for scale in (1, 4):
    for players, per in ((2, 2), (2, 3), (2, 4), (4, 2), (4, 3), (4, 4)):
        T = Path(tempfile.mkdtemp()); pics = T / "p"; kept = {}; rng = np.random.default_rng(0)
        roles = [("begin", "start", 0), ("other", "other", 0)] + [(f"end_P{k}" + ("" if s == 1 else f"_{s}"), f"end_P{min(k, 2)}", 10 * k + s) for k in range(1, players + 1) for s in range(1, per + 1)]
        for role, kind, look in roles:
            (pics / role).mkdir(parents=True); rows = []
            for i in range(21):
                im = nc.other(i, rng) if kind == "other" else nc.screen(kind, look, rng)
                (im.resize((320 * scale, 240 * scale)) if scale > 1 else im).save(pics / role / f"f{i:04d}.png"); rows.append(f"{i:.2f},f{i:04d}.png")
            (pics / role / "index.csv").write_text("seconds,file\n" + "\n".join(rows) + "\n"); kept[role] = role
        (pics / "labels.json").write_text(json.dumps(pag._labels(pics, kept, es)))
        t0 = time.perf_counter(); es.learn(pics, pics / "labels.json", "first", name="g"); t = time.perf_counter() - t0
        print(f"| {320 * scale} x {240 * scale} | {players} | {per} | {t:.2f} | {players * per * t:.1f} |"); shutil.rmtree(T)
