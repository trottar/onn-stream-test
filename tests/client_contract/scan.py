"""B88: the hub paths the client's Kotlin source names (string literals), each with the HTTP helper it goes through.

A literal counts when it holds `/plugins/<plugin>/<action>` or one of the hub's root paths; `<action>` may be a
template (`$action`, `${DiscChange.ENDPOINT}`, `$endpoint`). The helper is the nearest of httpGet / httpPost /
httpPostBody / httpPostJson before the literal in the same call (up to 12 lines back), else a `requestMethod` set
near it, else "?" (read by hand: calls.json says which)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT_PATHS = ("/sources", "/stop", "/status", "/diagnostics/")
_LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')
_PLUGIN = re.compile(r"/plugins/([a-z_]+)/(\$\{[^}]+\}|\$[A-Za-z_]+|[a-z0-9][a-z0-9-]*)")
_HELPER = re.compile(r"\b(httpGet|httpPostBody|httpPostJson|httpPost|getJson|postJson)\s*\(")
_METHOD = re.compile(r'requestMethod\s*=\s*\n?\s*"?(GET|POST)')


def scan(src_root: Path) -> list[dict]:
    out = []
    for f in sorted(src_root.rglob("*.kt")):
        lines = f.read_text(encoding="utf-8").splitlines()
        if f.name == "SessionProtocol.kt":
            continue                      # the identity protocol's lists of paths to sign: names, not calls
        for i, line in enumerate(lines):
            code = line
            if line.strip().startswith(("//", "*", "/*")):
                continue
            for lit in _LIT.findall(code):
                paths = []
                for m in _PLUGIN.finditer(lit):
                    paths.append(f"/plugins/{m.group(1)}/{m.group(2)}")
                if not paths:
                    # a root path, alone or after the port (`…:$CONTROL_PORT/stop`)
                    for m in re.finditer(r"(?:^|PORT\}?)(/(?:sources|stop|status|diagnostics/[a-z-]+))(?=$|[?\"])", lit):
                        paths.append(m.group(1))
                if not paths:
                    continue
                window = "\n".join(lines[max(0, i - 12):i + 1])
                helpers = _HELPER.findall(window)
                method = None
                if helpers:
                    method = {"httpGet": "GET", "getJson": "GET"}.get(helpers[-1], "POST")
                else:
                    near = "\n".join(lines[max(0, i - 12):i + 25])
                    mm = _METHOD.search(near)
                    method = mm.group(1) if mm else "?"
                for p in paths:
                    out.append({"path": p, "method": method, "file": f.name, "line": i + 1})
    return out


if __name__ == "__main__":
    import json, sys
    for row in scan(Path(sys.argv[1])):
        print(json.dumps(row))
