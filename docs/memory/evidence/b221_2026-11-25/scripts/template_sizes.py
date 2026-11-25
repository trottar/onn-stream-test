"""B221, reported only (nothing changed): the templates' synthetic glyphs re-made exactly as score_gates makes them
(stream 0, the same calls in the same order); for each, whether its cut box is within VARIANT_SIZE_TOL px of its real
glyph's box. Prints JSON by symbol (no names)."""
import json, sys
sys.path.insert(0, sys.argv[1])
import party_add_game as pag, party_steps as st
code = sys.argv[2]
E = st.es()
calls = []
orig = st.synthetic_glyphs
def recording(sources, backgrounds, place, region, rng, per):
    out = {}
    for si, (a, g) in enumerate(sources):
        t, l, bt, r_ = g[0], g[1], g[2], g[3]
        ink = E._ink(a, place["pol"], int(place["r"]), E._contrast(a))[t:bt + 1, l:r_ + 1]
        pix = a[t:bt + 1, l:r_ + 1]
        h, w = bt - t + 1, r_ - l + 1
        cells, rec = [], []
        for _ in range(per):
            bg = backgrounds[int(rng.integers(len(backgrounds)))]
            dx, dy = int(rng.integers(-st.SYN_DX, st.SYN_DX + 1)), int(rng.integers(-st.SYN_DY, st.SYN_DY + 1))
            pic = bg.copy()
            cx = (region[0] + region[2]) // 2 - w // 2 + dx
            ty = t + dy
            if cx < 0 or ty < 0 or cx + w > pic.shape[1] or ty + h > pic.shape[0]:
                cells.append(None); rec.append("not cut"); continue
            dst = pic[ty:ty + h, cx:cx + w]
            dst[ink] = pix[ink]
            gl = E.place_glyphs(pic, place)
            if gl and len(gl) == 1:
                c = gl[0]
                cells.append(E.glyph_cell(pic, c, place))
                ok = abs((c[3] - c[1] + 1) - w) <= st.VARIANT_SIZE_TOL and abs((c[2] - c[0] + 1) - h) <= st.VARIANT_SIZE_TOL
                rec.append("own size" if ok else f"other size ({c[2] - c[0] + 1}x{c[3] - c[1] + 1} for {h}x{w})")
            else:
                cells.append(None); rec.append("not cut")
        out[si] = cells
        calls.append(rec)
    return out
st.synthetic_glyphs = recording
b = pag.load_binding(code); kept = pag.kept_states(code)
items = [it for it in st.glyph_items(code, b, kept) if it[5] is not None and it[1] == 0]
g = st.score_gates(code, b, kept, pag.Cells())
by = {}
for it, rec in zip(items, calls):
    row = by.setdefault(it[4], {"real glyphs": 0, "made": 0, "own size": 0, "would fail the size rule": 0, "not cut": 0,
                                "sizes failed": []})
    row["real glyphs"] += 1
    for x in rec:
        if x == "not cut":
            row["not cut"] += 1; continue
        row["made"] += 1
        if x == "own size":
            row["own size"] += 1
        else:
            row["would fail the size rule"] += 1; row["sizes failed"].append(x)
assert len(items) == len(calls), (len(items), len(calls))
print(json.dumps({"code": code, "by symbol": dict(sorted(by.items()))}, indent=1))
