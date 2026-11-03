#!/usr/bin/env python3
"""B35: flag absent = today, from the bytes. Usage: proof_flag_absent.py BASE_DIR NEW_DIR (two copies of the tree's
companion/ + PrivyHub/). Read-only.

Client (`debug.privyhub.vod_retry` absent): every line MainActivity.kt gains is one of
  - the three `com.safeiot.privyhub.vod.*` imports, comments, blank lines;
  - the `vodRetry` field declared `= null`;
  - the one assignment `vodRetry = if (VodRetryController.wanted(VodRetryFlag.read(), isLive)) { … } else { null }`
    (VodRetryFlag.read() is false unless the property reads exactly `1`, so it assigns null);
  - a statement whose only effect is through `vodRetry?.` (a no-op on null) or `vodRetry = null`;
and no line is removed. So with the field null the method bodies run today's calls in today's order.
Host (`PRIVYHUB_VOD_LOG` absent): range_server.py's RangeRequestHandler class AST is the base's; the top-level
additions are `VOD_LOG = None` and one `if os.environ.get('PRIVYHUB_VOD_LOG', '').strip() == '1':` block;
privyhub_service.py's additions are one such guarded block, `VOD_CLIENT_LOG = None`, and one `do_POST` branch whose
test starts `(_vod_client_log := globals().get('VOD_CLIENT_LOG')) is not None and`.
"""
import ast
import difflib
import re
import sys
from pathlib import Path

base, new = Path(sys.argv[1]), Path(sys.argv[2])
ok = True


def say(cond, text):
    global ok
    ok &= bool(cond)
    print(("MET   " if cond else "FAILED"), text)


rel = "PrivyHub/app/src/main/java/MainActivity.kt"
a = (base / rel).read_text().splitlines()
b = (new / rel).read_text().splitlines()
removed, added = [], []
for line in difflib.unified_diff(a, b, lineterm="", n=0):
    if line.startswith(("---", "+++", "@@")):
        continue
    (removed if line.startswith("-") else added).append(line[1:])
say(not removed, f"MainActivity.kt: no line removed ({len(removed)})")
# the one assignment block, as written
block = "\n".join(added)
assign = re.search(r"[ ]*vodRetry =\n\s+if \(VodRetryController\.wanted\(VodRetryFlag\.read\(\), isLive\)\) \{\n"
                   r"(?:.*\n)*?\s+\} else \{\n\s+null\n\s+\}", block)
say(assign is not None, "the field's one non-null assignment is guarded by VodRetryFlag.read() and else null")
inside = set(assign.group(0).splitlines()) if assign else set()
allowed = [
    r"^\s*$", r"^\s*//", r"^import com\.safeiot\.privyhub\.vod\.VodRetry(Android|Controller|Flag)$",
    r"^\s*private var vodRetry: VodRetryAndroid\? = null$",
    r"^\s*vodRetry\?\.\w+\(.*\)$", r"^\s*vodRetry = null$",
    r"^\s*if \(vodRetry\?\.onError\(error, exoPlayer\.currentPosition\) == true\) \{$", r"^\s*return$", r"^\s*\}$",
    r"^\s*if \(playbackState == Player\.STATE_READY\) \{$",
]
bad = [x for x in added if x not in inside and not any(re.match(p, x) for p in allowed)]
say(not bad, f"MainActivity.kt: every other added line is an import, comment, the null field, or a vodRetry?. no-op "
    f"({len(added)} added; offending: {bad})")
src = (new / "PrivyHub/app/src/main/java/vod/VodRetry.kt").read_text()
say('fun parse(raw: String?): Boolean = raw?.trim() == "1"' in src, "VodRetryFlag.parse is exactly `1` after trim")
say("fun wanted(flag: Boolean, isLive: Boolean): Boolean = flag && !isLive" in src, "wanted = flag && !isLive")

for name in ("range_server.py", "privyhub_service.py"):
    to, tn = ast.parse((base / "companion" / name).read_text()), ast.parse((new / "companion" / name).read_text())
    old = {ast.dump(n) for n in to.body}
    adds = [n for n in tn.body if ast.dump(n) not in old]
    gone = [n for n in to.body if ast.dump(n) not in {ast.dump(m) for m in tn.body}]
    if name == "range_server.py":
        say(not gone and len(adds) == 2, f"{name}: top level only gains two statements ({len(adds)}), loses none")
        say(ast.unparse(adds[0]) == "VOD_LOG = None", f"{name}: VOD_LOG = None")
        say(isinstance(adds[1], ast.If) and ast.unparse(adds[1].test) ==
            "os.environ.get('PRIVYHUB_VOD_LOG', '').strip() == '1'", f"{name}: the rest under the exact-1 test")
    else:
        classes = [n for n in adds if isinstance(n, ast.ClassDef)]
        say(len(adds) - len(classes) == 2 and len(gone) == 1 and len(classes) == 1
            and classes[0].name == gone[0].name,
            f"{name}: top level gains two statements; one class changed (the handler)")
        g = [n for n in adds if isinstance(n, ast.If)]
        say(len(g) == 1 and ast.unparse(g[0].test) == "os.environ.get('PRIVYHUB_VOD_LOG', '').strip() == '1'",
            f"{name}: the import under the exact-1 test")
        # the class: the only change is one added If in do_POST guarded by VOD_CLIENT_LOG is not None
        co = next(n for n in to.body if isinstance(n, ast.ClassDef) and n.name == gone[0].name)
        cn = next(n for n in tn.body if isinstance(n, ast.ClassDef) and n.name == gone[0].name)

        def strip(cls):
            for fn in ast.walk(cls):
                for field in ("body", "orelse", "finalbody"):
                    seq = getattr(fn, field, None)
                    if isinstance(seq, list):
                        setattr(fn, field, [s for s in seq if not (isinstance(s, ast.If) and
                                ast.unparse(s.test).startswith("(_vod_client_log := globals().get('VOD_CLIENT_LOG')) is not None and"))])
            return ast.dump(cls)
        n_branches = sum(1 for s in ast.walk(cn) if isinstance(s, ast.If) and
                         ast.unparse(s.test).startswith("(_vod_client_log := globals().get('VOD_CLIENT_LOG')) is not None and"))
        say(n_branches == 1 and strip(cn) == ast.dump(co),
            f"{name}: the handler class equals the base's but for one `(_vod_client_log := globals().get('VOD_CLIENT_LOG')) is not None and …` branch")
print("PROVEN" if ok else "NOT PROVEN")
sys.exit(0 if ok else 1)
