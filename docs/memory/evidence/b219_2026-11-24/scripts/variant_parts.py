"""Read only: for T92's once-seen 6, each valid test variant (today's rule) — its cut's share of foreign ink and how
much of the pasted glyph's ink the cut holds (completeness), and its read. Mirrors score_gates' test stream."""
import json, sys
import numpy as np
sys.path.insert(0, sys.argv[1])
import party_add_game as pag, party_steps as st
code, sym = sys.argv[2], sys.argv[3]
E = st.es()
b = pag.load_binding(code); kept = pag.kept_states(code)
cap = []
orig_tv = st.test_variants
def tv(a, g, backgrounds, place, region, rng):
    t, l, bt, r_ = g[0], g[1], g[2], g[3]
    ink = E._ink(a, place["pol"], int(place["r"]), E._contrast(a))[t:bt + 1, l:r_ + 1]
    h, w = bt - t + 1, r_ - l + 1
    valid, draws = [], 0
    while draws < st.VARIANT_DRAWS and len(valid) < st.VARIANTS_NEEDED:
        draws += 1
        bg = backgrounds[int(rng.integers(len(backgrounds)))]
        dx, dy = int(rng.integers(-st.SYN_DX, st.SYN_DX + 1)), int(rng.integers(-st.SYN_DY, st.SYN_DY + 1))
        cx = (region[0] + region[2]) // 2 - w // 2 + dx; ty = t + dy
        if cx < 0 or ty < 0 or cx + w > bg.shape[1] or ty + h > bg.shape[0]:
            continue
        pic = bg.copy(); pic[ty:ty + h, cx:cx + w][ink] = a[t:bt + 1, l:r_ + 1][ink]
        pasted = np.zeros(pic.shape, bool); pasted[ty:ty + h, cx:cx + w] = ink
        gl = E.place_glyphs(pic, place)
        if not gl or len(gl) != 1:
            continue
        c = gl[0]
        cut = E._ink(pic, place["pol"], int(place["r"]), E._contrast(pic))[c[0]:c[2] + 1, c[1]:c[3] + 1]
        own = pasted[c[0]:c[2] + 1, c[1]:c[3] + 1]
        share = float((cut & own).sum()) / float(cut.sum()) if cut.any() else 0
        if not cut.any() or share < st.SYN_OWN:
            continue
        valid.append(E.glyph_cell(pic, c, place))
        cap.append({"dx": dx, "dy": dy, "share": round(share, 3),
                    "complete": round(float(own.sum()) / float(ink.sum()), 3),
                    "cut box": [int(c[0]) - ty, int(c[1]) - cx, int(c[2]) - ty, int(c[3]) - cx], "glyph": [h, w]})
    return valid, draws
st.test_variants = tv
reads = []
orig_once = st._once_rule
def once(kind, s, rig, variants, others, read):
    if s == sym:
        reads.extend(read(c) for c in variants)
    return orig_once(kind, s, rig, variants, others, read)
st._once_rule = once
g = st.score_gates(code, b, kept, pag.Cells())
# cap holds every once symbol's variants in order; the sym's are the ones whose reads we kept: take the matching block
print(json.dumps({"reads": reads, "variants": cap}, indent=0))
