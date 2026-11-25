"""B219 step 1 (nothing changed): today's score_gates on a scratch title; for every valid test variant of a once-seen
symbol, the reader's rule taken apart — the best template, its distance and threshold, the margin and margin_needed,
separable — and which part failed when the read is '?'. Prints JSON (no names)."""
import json, sys
import numpy as np
sys.path.insert(0, sys.argv[1])
import party_add_game as pag, party_steps as st
code = sys.argv[2]
rows, cur = [], {}
orig_once, orig_read = st._once_rule, st.read_cell

def read_cell(cell, score, refs):
    got = orig_read(cell, score, refs)
    if cur.get("sym") is not None and cur.get("phase") == "variants":
        E = st.es(); keys = list(score["keys"])
        d = E.cell_dists(cell, refs); order = np.argsort(d, kind="stable")
        best = keys[int(order[0])]; thr = score["thresholds"].get(best)
        margin = float(d[order[1]] - d[order[0]]) if len(keys) > 1 else float("inf")
        need = score.get("margin_needed")
        why = []
        if not score["separable"].get(best): why.append("separable")
        if thr is None or float(d[order[0]]) > thr: why.append("threshold")
        if need is None or margin < need: why.append("margin")
        own = keys.index(cur["sym"]) if cur["sym"] in keys else None
        rows.append({"symbol": cur["sym"], "read": got, "best": best, "distance": round(float(d[order[0]]), 4),
                     "threshold": thr, "margin": round(margin, 4), "margin_needed": need,
                     "own distance": round(float(d[own]), 4) if own is not None else None,
                     "failed": why if got == "?" else []})
    return got

def once_rule(kind, sym, rig, variants, others, read):
    cur.update(sym=sym, phase="variants")
    for c in variants:
        read(c)
    cur.update(phase="others")
    out = orig_once(kind, sym, rig, variants, others, read)
    cur.clear()
    return out

st.read_cell, st._once_rule = read_cell, once_rule
b = pag.load_binding(code); kept = pag.kept_states(code)
g = st.score_gates(code, b, kept, pag.Cells())
print(json.dumps({"code": code, "seen once": g["seen_once"], "not counted": g["dropped"], "ask": g["ask"],
                  "rows": rows}, indent=1))
