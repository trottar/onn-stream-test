"""B122: fold M1's one tone change, picture by picture. usage (from the repo): python3 -I <this> <repo>"""
import sys, json
sys.argv = ["x", sys.argv[1], "t89_c1_20261117T003035Z", "unused", "--procs", "4"]
sys.path.insert(0, sys.argv[1] + "/docs/memory/evidence/b122_2026-11-17/scripts")
import t89_eval as T
ms = T.matches(); lab, lo, hi = ms[0]
inside = lambda a, b: a > lo + 1e-6 and b <= hi + 1e-6
spec, arrays, rep = T.E.learn(T.FR, T.cut(lambda a, b: not inside(a, b)))
its = T.items(T.cut(inside))
base = T.read_set(spec, arrays, its)
for tk in T.TONES[1:]:
    res = T.read_set(spec, arrays, its, tk)
    for a, b in zip(base, res):
        if (a[2], a[3]) != (b[2], b[3]):
            print(tk, a[:5], "->", b[:5])
