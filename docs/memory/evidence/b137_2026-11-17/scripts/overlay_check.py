#!/usr/bin/env python3
"""B137 settle, offline (nothing started): would the watcher still recognise a title's start screen read from a PAUSED
window, which carries RetroArch's "Paused." label in its top-right corner for as long as the core is paused?

Reads, read only: the rules folder's end-screen spec of each party title, the kept pictures of its watches under
runtime/h7_frames/ (the watcher's own grabs, with the class the watcher gave each). For every kept picture: the real
reader (tools/h7_endscreen.py) on the picture as kept, and on the same picture with the label pasted at RetroArch's
place — (a) the label as measured (label_probe.py's crop: the translucent box and its text, pasted opaque: the worst
case), (b) an opaque black box of the same size, (c) the label pasted, then B137's mask (`h7_minigame.mask_label`,
LABEL_BOX) — what the watcher reads now. Prints numbers only: per title (T88 / T89 by its players) and class,
how many pictures keep their class, the margin before / after. No name, id, path or picture is written.
usage: overlay_check.py <repo> <label png>"""
import collections, csv, json, sys
from pathlib import Path
from PIL import Image
REPO, LABEL = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "companion"))
import h7_endscreen as es
from h7_minigame import mask_label, LABEL_BOX
RULES = Path.home() / "privyhub_h7" / "rules"
FRAMES = REPO / "runtime" / "h7_frames"
label = Image.open(LABEL).convert("RGB")
out = {}
for side in sorted(RULES.glob("*.party.json")):
    gid = side.name.split(".")[0]
    players = json.loads(side.read_text())["players"]
    who = "T88" if players == 2 else "T89"
    spec, arrays = es.load_spec(RULES / f"{gid}.endscreen.json")
    reader = es.Reader(spec, arrays)
    stats = collections.defaultdict(lambda: {"n": 0, "same_a": 0, "same_b": 0, "margin": [], "margin_a": [],
                                             "margin_b": [], "same_c": 0, "margin_c": [], "became_a": collections.Counter(),
                                             "became_b": collections.Counter()})
    for d in sorted(FRAMES.iterdir()):
        if not d.name.startswith(gid + "_") or not (d / "index.csv").is_file():
            continue
        for row in csv.DictReader(open(d / "index.csv")):
            kept_class = row.get("class")
            if not kept_class:
                continue
            img = Image.open(d / row["file"]).convert("RGB")
            w, h = img.size
            a = img.copy(); a.paste(label, (w - label.width, 0))
            b = img.copy(); b.paste(Image.new("RGB", label.size, (0, 0, 0)), (w - label.width, 0))
            c = mask_label(a)
            r0, ra, rb, rc = reader.read(img), reader.read(a), reader.read(b), reader.read(c)
            s = stats[r0["class"]]
            s["n"] += 1
            s["same_a"] += ra["class"] == r0["class"]
            s["same_b"] += rb["class"] == r0["class"]
            s["margin"].append(r0.get("margin")); s["margin_a"].append(ra.get("margin")); s["margin_b"].append(rb.get("margin"))
            s["same_c"] += rc["class"] == r0["class"]; s["margin_c"].append(rc.get("margin"))
            if ra["class"] != r0["class"]:
                s["became_a"][ra["class"]] += 1
            if rb["class"] != r0["class"]:
                s["became_b"][rb["class"]] += 1

    def mm(v):
        v = [x for x in v if isinstance(x, (int, float))]
        return [round(min(v), 4), round(sorted(v)[len(v) // 2], 4), round(max(v), 4)] if v else None
    out[who] = {c: {"pictures": s["n"], "class_kept_with_label": s["same_a"], "class_kept_with_black_box": s["same_b"],
                    "margin_min_median_max": mm(s["margin"]), "with_label": mm(s["margin_a"]),
                    "with_black_box": mm(s["margin_b"]), "class_kept_with_label_masked": s["same_c"],
                    "with_label_masked": mm(s["margin_c"]), "became_with_label": dict(s["became_a"]),
                    "became_with_black_box": dict(s["became_b"])}
                for c, s in sorted(stats.items())}
    out[who + "_start_class_is_start"] = spec["start_class"] == "start"
print(json.dumps({"label_size": list(label.size), "mask_box": list(LABEL_BOX), **out}, indent=1))
