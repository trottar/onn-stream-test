#!/usr/bin/env python3
"""B137 settle, offline: T89 has no kept start picture of its window; its one kept begin picture (a core screenshot,
320 x 240, read only) through the real reader as kept, with RetroArch's label pasted (scaled to a 960 x 720 window: T89's),
and with the label pasted then B137's mask — the screen distance each time, against T89's start threshold and its
worst learnt start distance (the spec's own numbers). It is no start read (the picture is no window grab): only the
label's effect on the distance is shown. Numbers only. usage: t89_begin_check.py <repo> <label png>"""
import json, sys
from pathlib import Path
from PIL import Image
REPO, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
sys.path.insert(0, str(REPO / "tools")); sys.path.insert(0, str(REPO / "companion"))
import h7_endscreen as es
import h7_minigame as h7m
R = Path.home() / "privyhub_h7" / "rules"
gid = [p.name.split(".")[0] for p in R.glob("*.party.json") if json.loads(p.read_text())["players"] == 4][0]
spec, arr = es.load_spec(R / f"{gid}.endscreen.json")
img = Image.open(Path.home() / "privyhub_h7" / "t89" / "begin.png").convert("RGB")
s = img.width / 960
lab = Image.open(LABEL).convert("RGB"); lab = lab.resize((round(lab.width * s), round(lab.height * s)))
def rd(im):
    r = es.Reader(spec, arr).read(im)
    return {"class": r["class"], "screen": round(r["distances"]["screen"], 4) if isinstance(r.get("distances"), dict) and "screen" in r["distances"] else None}
a = img.copy(); a.paste(lab, (img.width - lab.width, 0))
box = (round(h7m.LABEL_BOX[0] * s), round(h7m.LABEL_BOX[1] * s))
print(json.dumps({"picture": list(img.size), "as_kept": rd(img), "label_pasted": rd(a),
                  "label_pasted_then_masked": rd(h7m.mask_label(a, box)),
                  "start_threshold": spec["screens"]["start"]["threshold"], "start_worst_learnt": spec["screens"]["start"]["own_worst"],
                  "start_mask_cells": int(spec["screens"]["start"]["mask_px"])}, indent=1))
