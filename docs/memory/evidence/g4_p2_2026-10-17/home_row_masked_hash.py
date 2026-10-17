#!/usr/bin/env python3
"""G4-P2: the home row's code path, HEAD vs today -- whole-file sha256 and a masked AST hash.

    python3 docs/memory/evidence/g4_p2_2026-10-17/home_row_masked_hash.py

Read-only. The masked hash: each named function's AST (`ast.dump`, no line numbers), with
`main`'s guarded `if "--remote" in argv:` branch replaced by a fixed placeholder (the
only place the remote row is reached), hashed per function, from HEAD (git show) and
from the working tree.
"""
import ast
import hashlib
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
FILES = {
    "tools/e1_suite.py": ("main", "run_suite", "run_once", "preflight", "stop_game", "heartbeat_figures",
                          "telemetry_figures", "poll_figures", "decision_rows"),
    "tools/e1_sampler.py": ("run", "summarize", "e2_extras", "encoder_loop", "title_loop", "ra_fps", "host_loop"),
}


def head(rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"], capture_output=True, text=True,
                          check=True).stdout


class Mask(ast.NodeTransformer):
    def visit_If(self, node):
        if ast.unparse(node.test) == '"--remote" in argv':
            return ast.Expr(ast.Constant("<masked: the guarded --remote dispatch>"))
        return self.generic_visit(node)


def fn_hashes(src):
    tree = ast.parse(src)
    out = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            m = Mask().visit(n) if n.name == "main" else n
            out[n.name] = hashlib.sha256(ast.dump(m, include_attributes=False).encode()).hexdigest()
    return out


lines = ["G4-P2 home row, HEAD vs working tree", ""]
ok = True
for rel, names in FILES.items():
    a, b = head(rel), (REPO / rel).read_text()
    fa, fb = hashlib.sha256(a.encode()).hexdigest(), hashlib.sha256(b.encode()).hexdigest()
    ok &= fa == fb
    lines.append(f"{rel}: file sha256 HEAD {fa[:16]}… today {fb[:16]}… -> {'identical' if fa == fb else 'DIFFER'}")
    ha, hb = fn_hashes(a), fn_hashes(b)
    for n in names:
        same = ha.get(n) == hb.get(n) and ha.get(n) is not None
        ok &= same
        lines.append(f"  {n}{' (the --remote branch masked)' if n == 'main' and rel.endswith('suite.py') else ''}: "
                     f"{(ha.get(n) or '-')[:16]}… / {(hb.get(n) or '-')[:16]}… -> {'identical' if same else 'DIFFER'}")
lines += ["", f"-> the home row's code path: {'byte for byte as HEAD' if ok else 'CHANGED'}"]
print("\n".join(lines))
raise SystemExit(0 if ok else 1)
