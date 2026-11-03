#!/usr/bin/env python3
"""B40: PRIVYHUB_VOD_DROP_TEST absent = today, byte for byte. Usage: proof_flag_absent.py BASE_COPY NEW_COPY
(1) every existing file the diff touches, other than range_server.py and B35's test, is unchanged;
(2) range_server.py: the new module's top-level nodes minus exactly two (`VOD_DROP_TEST = None` and the guarded `if`)
    are the predecessor's, node for node (AST dumps), and the class body is the predecessor's;
(3) a fresh process with the line unset / empty / 0 / true / yes: vod_drop_test not imported, the handler's copyfile
    today's, no thread named vod-drop-test."""
import ast, os, subprocess, sys
from pathlib import Path
base, new = Path(sys.argv[1]), Path(sys.argv[2])
ok = True
changed = []
for root in ("companion", "tools", "tests", "PrivyHub"):
    for p in sorted((base / root).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and "build" not in p.parts and ".gradle" not in p.parts:
            q = new / p.relative_to(base)
            if not q.exists() or q.read_bytes() != p.read_bytes():
                changed.append(str(p.relative_to(base)))
print("(1) existing files changed:", changed)
ok &= changed == ["companion/range_server.py", "tests/vod_log/test_vod_log.py"]
o = ast.parse((base / "companion/range_server.py").read_text()); n = ast.parse((new / "companion/range_server.py").read_text())
od = [ast.dump(x) for x in o.body]
added = [x for x in n.body if ast.dump(x) not in od]
rest = [ast.dump(x) for x in n.body if x not in added]
print("(2) added top-level nodes:", [ast.unparse(x).splitlines()[0] for x in added])
print("    the rest equals the predecessor node for node:", rest == od)
ok &= rest == od and len(added) == 2 and ast.unparse(added[0]) == "VOD_DROP_TEST = None" \
    and ast.unparse(added[1]).startswith("if os.environ.get('PRIVYHUB_VOD_DROP_TEST', '').strip() == '1':")
env0 = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
code = ("import sys, threading, range_server; print(range_server.VOD_DROP_TEST is None, 'vod_drop_test' in sys.modules,"
        " range_server.RangeRequestHandler.copyfile.__qualname__, any(t.name == 'vod-drop-test' for t in threading.enumerate()))")
for v in (None, "", "0", "true", "yes"):
    env = dict(env0)
    if v is not None:
        env["PRIVYHUB_VOD_DROP_TEST"] = v
    out = subprocess.run([sys.executable, "-c", code], cwd=new / "companion", env=env, capture_output=True, text=True).stdout.split()
    print(f"(3) PRIVYHUB_VOD_DROP_TEST={v!r}:", out)
    ok &= out == ["True", "False", "RangeRequestHandler.copyfile", "False"]
print("PROVEN" if ok else "NOT PROVEN")
