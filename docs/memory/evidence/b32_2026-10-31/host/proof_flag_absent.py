#!/usr/bin/env python3
"""B32-host: flag absent = today, by AST. usage: proof_flag_absent.py <the copy's root>
Each edited module, with B32's additions taken out of its AST, must equal its predecessor's AST (predecessors/, the
base bytes); the additions are exactly the guarded ones (each is dead or empty without PRIVYHUB_STEP_IN_PLACE=1 / an
in-place actuator payload / an explicit cap beside the umbrella's ladder)."""
import ast, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
NEW = Path(sys.argv[1])

def load(p):
    return ast.parse(Path(p).read_text())

def strip_native_stream(t):
    t.body = [n for n in t.body if not (
        (isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "STEP_IN_PLACE" for x in n.targets))
        or (isinstance(n, ast.If) and "PRIVYHUB_STEP_IN_PLACE" in ast.unparse(n.test)))]
    for f in ast.walk(t):
        if isinstance(f, ast.FunctionDef) and f.name == "adaptive_level_transition":
            for w in ast.walk(f):
                if isinstance(w, ast.If) and ast.unparse(w.test) == "not sized":
                    w.body = [s for s in w.body if not (isinstance(s, ast.If) and "STEP_IN_PLACE" in ast.unparse(s.test))]
    return t

def strip_live(t):
    for d in ast.walk(t):
        if isinstance(d, ast.Dict):
            keep = [(k, v) for k, v in zip(d.keys, d.values) if not (k is None and "in_place" in ast.unparse(v))]
            d.keys, d.values = [k for k, _ in keep], [v for _, v in keep]
    return t

def strip_umbrella(t):
    for f in ast.walk(t):
        if isinstance(f, ast.FunctionDef) and f.name == "__init__":
            f.body = [s for s in f.body if not (
                (isinstance(s, ast.Assign) and any(ast.unparse(x) in ("self.cap_on_umbrella_ladder", "self._cap_import_obj")
                                                   for x in s.targets))
                or (isinstance(s, ast.If) and ast.unparse(s.test) == "self.cap_on_umbrella_ladder"))]
        if isinstance(f, ast.FunctionDef) and f.name == "_in_force":
            for loop in ast.walk(f):
                if isinstance(loop, ast.For):
                    loop.body = [s for s in loop.body if not (isinstance(s, ast.If) and "cap_on_umbrella_ladder" in ast.unparse(s.test))]
        if isinstance(f, ast.Assign) and ast.unparse(f.targets[0]) == "live.REMOTE_CAP" and isinstance(f.value, ast.IfExp):
            f.value = f.value.orelse                      # `<import obj> if self.cap_on_umbrella_ladder else None` -> None
    return t

ok = True
for rel, strip in (("companion/native_stream.py", strip_native_stream), ("companion/adaptive_bitrate_live.py", strip_live),
                   ("companion/remote_umbrella.py", strip_umbrella)):
    a = ast.dump(load(HERE / "predecessors" / rel))
    b = ast.dump(strip(load(NEW / rel)))
    same = a == b and a != ast.dump(load(NEW / rel))    # and the edit is real (not vacuous)
    ok &= same
    print(("PROVEN" if same else "DIFFERS"), rel, "(B32's guarded additions removed = the predecessor's AST)")
print("ALL PROVEN" if ok else "NOT PROVEN")
sys.exit(0 if ok else 1)
