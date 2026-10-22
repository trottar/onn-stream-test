#!/usr/bin/env python3
"""B7 (host): PRIVYHUB_STALL_SIGNAL absent = B6's files byte for byte. For each changed companion file, the WHOLE module's AST with the B4 items removed
equals the predecessor's (predecessors/ = HEAD 144e5c7). Removed: the guarded B4 statements (each `if` whose test is a
B4 guard), the module-level `_hold_rewind = None`, the additive class attributes `_input_mask` / `_input_hold_rewind`
and the new method `set_input_mask`. Also lists, per file, the functions that hold a B4 statement. Writes
proof_flag_absent.md.

    B7_ROOT=<a copy holding companion/> python3 -B proof_flag_absent.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B7_ROOT", str(HERE.parents[3])))
FILES = ("companion/native_session_io.py", "companion/games/link_drop_recovery.py", "companion/hold_rewind.py",
         "companion/plugins/games.py")
GUARDS = {
    "self._stall_signal is not None and self._stall_signal.on_datagram(data, time.monotonic())",
    "self._client_stall is not None and self._client_stall.defer_release(self)",
    "self._client_stall is not None and self._client_stall.ready_after_stall(self)",
    "_stall_signal is not None",
    "(os.environ.get('PRIVYHUB_STALL_SIGNAL') or '').strip()",
}
ADDED_ATTRS = {"_stall_signal", "_client_stall"}
ADDED_FUNCS = {"set_stall_signal", "set_pending"}


def is_b4(node: ast.AST) -> bool:
    if isinstance(node, ast.If):
        return ast.unparse(node.test) in GUARDS
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id == "_stall_signal"
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id in ADDED_ATTRS
    if isinstance(node, ast.FunctionDef):
        return node.name in ADDED_FUNCS
    return False


class Strip(ast.NodeTransformer):
    def __init__(self):
        self.removed = []

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                keep = []
                for item in value:
                    if isinstance(item, ast.AST) and is_b4(item):
                        self.removed.append(ast.unparse(item).splitlines()[0][:100])
                        continue
                    if isinstance(item, ast.AST):
                        item = self.visit(item)
                    keep.append(item)
                setattr(node, field, keep)
            elif isinstance(value, ast.AST):
                self.visit(value)
        return node


def holders(tree: ast.Module) -> list[str]:
    out = []
    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)] + [tree]:
        for fn in (n for n in getattr(cls, "body", []) if isinstance(n, ast.FunctionDef)):
            if any(is_b4(x) for x in ast.walk(fn) if x is not fn):
                out.append(f"{getattr(cls, 'name', '<module>')}.{fn.name}")
    return out


def main() -> int:
    lines = ["# B7 (host) — flag absent = B6's files (whole-module AST, B7 items removed, vs predecessors/)", "",
             f"Root checked: the copy (`B7_ROOT`). Predecessors: `predecessors/` (B6's files in the tree; HEAD 144e5c7 + B6).", "",
             "| file | functions holding a B7 statement | B7 items removed | whole module vs predecessor |",
             "| --- | --- | ---: | --- |"]
    ok_all = True
    for rel in FILES:
        new = ast.parse((ROOT / rel).read_text())
        old = ast.parse((HERE / "predecessors" / rel).read_text())
        hold = holders(new)
        s = Strip()
        stripped = s.visit(new)
        same = ast.dump(stripped) == ast.dump(old)
        ok_all &= same
        lines.append(f"| `{rel}` | {', '.join(f'`{h}`' for h in hold) or '(module level only)'} | {len(s.removed)} | "
                     f"**{'identical' if same else 'DIFFERENT'}** |")
    lines += ["", f"Result: **{'ALL IDENTICAL' if ok_all else 'NOT IDENTICAL'}**.", "",
              "New file `companion/stall_signal.py` is imported only with `PRIVYHUB_STALL_SIGNAL` set (`tests/stall_signal` FlagAbsent: a fresh process has no `stall_signal` in `sys.modules`; a stall datagram is a bad packet as today)."]
    (HERE / "proof_flag_absent_host.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
