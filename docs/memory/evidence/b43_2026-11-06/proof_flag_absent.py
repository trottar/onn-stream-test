#!/usr/bin/env python3
"""B43: flag absent = the CONFIRMED build's (0132b944...) behaviour, from the files. Usage: proof_flag_absent.py BASE NEW
(two copies of companion/ PrivyHub/). Prints one line per check and PROVEN / NOT PROVEN."""
import ast, subprocess, sys
from pathlib import Path
B, N = Path(sys.argv[1]), Path(sys.argv[2])
ok = True
def check(name, cond):
    global ok
    ok &= bool(cond)
    print(("OK  " if cond else "FAIL"), name)
J = "PrivyHub/app/src/main/java/"
# 1. the range server and the identity layer are not edited
for f in ["companion/range_server.py", J + "identity/IdentitySession.kt", J + "identity/AndroidIdentity.kt",
          J + "identity/MediaDataSource.kt"]:
    check(f"{f} byte-equal to the base", (B / f).read_bytes() == (N / f).read_bytes())
# 2. MainActivity: only added lines, all inside B35's flag-only construction of VodRetryAndroid
old = (B / J / "MainActivity.kt").read_text().splitlines()
new = (N / J / "MainActivity.kt").read_text().splitlines()
import difflib
ops = [o for o in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes() if o[0] != "equal"]
# Kotlin needs a comma after the old last argument: the one changed line is `{ player }` -> `{ player },`, then the
# new argument; nothing else
check("MainActivity: one change -- `{ player }` gains a comma, two lines follow it; nothing else",
      len(ops) == 1 and ops[0][0] == "replace" and [x.strip() for x in old[ops[0][1]:ops[0][2]]] == ["{ player }"]
      and [x.strip() for x in new[ops[0][3]:ops[0][4]]] == ["{ player },", "// B43: the host the media token is refetched for",
                                                           "{ getCompanionHost() }"])
tag, i1, i2, j1, j2 = ops[0]
added = new[j1:j2]
print("     old:", [a.strip() for a in old[i1:i2]], " new:", [a.strip() for a in added])
start = max(k for k in range(j1) if "VodRetryController.wanted(VodRetryFlag.read(), isLive)" in new[k])
end = min(k for k in range(j2, len(new)) if new[k].strip() == "} else {")
check("MainActivity: the insertion sits inside `if (VodRetryController.wanted(VodRetryFlag.read(), isLive)) { … }`",
      start < j1 and j2 <= end and end - start < 16)
# 3. the flag's parse is B35's, untouched
def flag_block(p):
    t = p.read_text(); a = t.index("object VodRetryFlag"); return t[a:t.index("\n}\n", a)]
check("VodRetryFlag (the property's parse) unchanged", flag_block(B / J / "vod/VodRetry.kt") == flag_block(N / J / "vod/VodRetry.kt"))
check("VodRetryController.wanted unchanged (no controller without the flag)",
      "fun wanted(flag: Boolean, isLive: Boolean): Boolean = flag && !isLive" in (N / J / "vod/VodRetry.kt").read_text())
# 4. vod_log: base top-level nodes all present; the changes are two new constants and accept()'s three branches
ob, nb = ast.parse((B / "companion/vod_log.py").read_text()), ast.parse((N / "companion/vod_log.py").read_text())
od = [ast.dump(n) for n in ob.body]
new_nodes = [ast.unparse(n).split("=")[0].strip() for n in nb.body if ast.dump(n) not in od]
check("vod_log: the only new / changed top-level nodes are CLIENT_REASONS, CLIENT_KINDS and class ClientLog",
      sorted(new_nodes) == sorted(["CLIENT_REASONS", "CLIENT_KINDS", ast.unparse([n for n in nb.body if isinstance(n, ast.ClassDef) and n.name == "ClientLog"][0]).split("=")[0].strip()]))
# 5. a fresh process with no line imports neither module
for env in ({}, {"PRIVYHUB_VOD_DROP_TEST": ""}, {"PRIVYHUB_VOD_DROP_TEST": "0"}, {"PRIVYHUB_VOD_DROP_TEST": "yes"}):
    code = ("import sys; sys.path.insert(0, 'companion'); import range_server; "
            "print('vod_drop_test' in sys.modules, range_server.VOD_DROP_TEST is None)")
    out = subprocess.run([sys.executable, "-c", code], cwd=N, capture_output=True, text=True,
                         env={"PATH": "/usr/bin:/bin", **env}).stdout.strip()
    check(f"fresh process {env or '(no line)'}: vod_drop_test not imported, VOD_DROP_TEST None", out == "False True")
print("PROVEN" if ok else "NOT PROVEN")
