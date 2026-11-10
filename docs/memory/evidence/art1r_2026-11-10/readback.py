#!/usr/bin/env python3
"""ART-1R read-back: per system, the box-art files present (from the records), one title's details by label through
the companion's control API, and whether the API's lists carry box_art_available. Counts and labels only."""
import json, sys, urllib.request, urllib.parse
from pathlib import Path
from collections import Counter
root = Path(sys.argv[1]); base = sys.argv[2]; media = sys.argv[3]  # the client fetches art from the media port
md = json.loads((root / "data/games/metadata.json").read_text())["games"]
def get(action, **q):
    with urllib.request.urlopen(f"{base}/plugins/games/{action}?{urllib.parse.urlencode(q)}", timeout=20) as r:
        return json.loads(r.read())
out = {}
for s in sys.argv[4:]:
    recs = [v for v in md.values() if v.get("system") == s]
    art = Counter((v.get("artwork") or {}).get("status") for v in recs)
    present = sum(1 for v in recs if (v.get("artwork") or {}).get("relative_path") and (root / v["artwork"]["relative_path"]).is_file())
    row = {"records": len(recs), "match": dict(Counter((v.get("match") or {}).get("status") for v in recs)),
           "artwork_status": dict(art), "box_art_files_present": present}
    # one title's details: the first matched record with art, in id order (the label only)
    pick = sorted((v for v in recs if (v.get("match") or {}).get("status") == "matched"
                   and (v.get("artwork") or {}).get("status") == "downloaded"), key=lambda v: v["id"])
    if pick:
        d = get("details", id=pick[0]["id"])
        row["detail_label"] = f"{s}-detail-1"
        row["details"] = {"release_year": d.get("release_year"), "genre": d.get("genre"), "max_players": d.get("max_players"),
                          "box_art_available": d.get("box_art_available"), "metadata_available": d.get("metadata_available"),
                          "developer": "present" if d.get("developer") else "empty", "publisher": "present" if d.get("publisher") else "empty"}
    # the list on the API: box_art_available per title on the system's list
    try:
        items, off = [], 0
        while True:  # the paged view (PS2) and the flat one (N64 / GameCube)
            lst = get("games", system=s)  # as the client opens the system
            nodes = lst.get("nodes") or []
            items += [n for n in nodes if n.get("node_type") == "game"]
            if not any(n.get("node_type") == "game" for n in nodes) and any(n.get("node_type") == "category" for n in nodes):
                for c in nodes:  # follow each page's own lazy path
                    with urllib.request.urlopen(base + c["lazy_path"], timeout=20) as r:
                        items += [n for n in json.loads(r.read()).get("nodes") or [] if n.get("node_type") == "game"]
            break
        with_art = [i for i in items if i.get("artwork_path")]
        served = 0
        for i in with_art:
            try:
                with urllib.request.urlopen(media + i["artwork_path"], timeout=20) as r:
                    served += int(r.status == 200 and len(r.read()) > 0)
            except Exception:
                pass
        dets = Counter()
        for i in items:
            with urllib.request.urlopen(base + i["lazy_path"], timeout=20) as r:
                dets[str(json.loads(r.read()).get("box_art_available"))] += 1
        row["api_list"] = {"games": len(items), "with_artwork_path": len(with_art), "artwork_served_200": served,
                           "details_box_art_available": dict(dets)}
    except Exception as e:
        row["api_list"] = {"error": type(e).__name__}
    out[s] = row
print(json.dumps(out, indent=1, sort_keys=True))
