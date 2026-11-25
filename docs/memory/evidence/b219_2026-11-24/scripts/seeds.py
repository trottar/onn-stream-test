"""B219 item 3 (reported, never a gate): each once-seen symbol's verdict under the title's seed and four others, with
today's code (nothing changed). Prints JSON."""
import json, sys
sys.path.insert(0, sys.argv[1])
import party_add_game as pag, party_steps as st
code = sys.argv[2]
base_seed = st.seed_of
b = pag.load_binding(code); kept = pag.kept_states(code)
out = {}
for k in range(5):
    st.seed_of = lambda texts, k=k: base_seed(texts) + k
    g = st.score_gates(code, b, kept, pag.Cells())
    out[f"seed{'' if k == 0 else '+' + str(k)}"] = {s: ("counted" if s in g["seen_once"] else
                                                       f"not counted ({g['once'][s]['variants read as itself']})")
                                                   for s in sorted(g["once"])}
print(json.dumps(out, indent=1))
