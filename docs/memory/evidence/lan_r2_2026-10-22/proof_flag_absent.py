#!/usr/bin/env python3
"""LAN-R2: PRIVYHUB_LAN_LOSS_RULE absent / =1 = the predecessors byte for byte. For each changed companion file, the WHOLE module's AST with the B4 items removed
equals the predecessor's (predecessors/ = HEAD 144e5c7). Removed: the guarded B4 statements (each `if` whose test is a
B4 guard), the module-level `_hold_rewind = None`, the additive class attributes `_input_mask` / `_input_hold_rewind`
and the new method `set_input_mask`. Also lists, per file, the functions that hold a B4 statement. Writes
proof_flag_absent.md.

    LANR2_ROOT=<a copy holding companion/> python3 -B proof_flag_absent.py
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("LANR2_ROOT", str(HERE.parents[3])))
FILES = ("companion/lan_loss_rule.py", "companion/native_session_io.py", "companion/plugins/games.py")
GUARDS = {
    "(environ.get(FLAG_ENV) or '').strip() == BIDIR_VALUE",
    "self._uplink_silences is not None and self._last_any_packet_at > 0.0 and (now_packet - self._last_any_packet_at >= 0.25)",
    "(os.environ.get('PRIVYHUB_LAN_LOSS_RULE') or '').strip() == 'bidir'",
    "_lan_bidir is not None",
}
ADDED_ATTRS = {"_uplink_silences"}
ADDED_FUNCS = {"set_uplink_silences"}
CURRENT = [""]          # the file being stripped (the new imports are lan_loss_rule.py's only)


def is_b4(node: ast.AST) -> bool:
    if isinstance(node, ast.If):
        return ast.unparse(node.test) in GUARDS
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        return node.targets[0].id in ("_lan_bidir", "BIDIR_VALUE", "SOURCE_BIDIR", "UPLINK_MIN_MS", "UPLINK_PER_WINDOW", "UPLINK")
    if isinstance(node, ast.ClassDef):
        return node.name in ("UplinkSilences", "LanBidirRule")
    if isinstance(node, (ast.Import, ast.ImportFrom)) and CURRENT[0].endswith("lan_loss_rule.py"):
        return ast.unparse(node) in ("import threading", "import time", "from collections import deque")
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
    lines = ["# LAN-R2 — `=bidir` absent: whole-module AST, LAN-R2 items removed, vs predecessors/", "",
             f"Root checked: the copy (`LANR2_ROOT`). Predecessors: `predecessors/` (lan_loss_rule.py HEAD's; native_session_io.py / plugins/games.py B7 + B1b's).", "",
             "| file | functions holding a LAN-R2 statement | LAN-R2 items removed | whole module vs predecessor |",
             "| --- | --- | ---: | --- |"]
    ok_all = True
    for rel in FILES:
        CURRENT[0] = rel
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
              "No new module: the rule lives in `lan_loss_rule.py` (imported, as LAN-R1, only with `PRIVYHUB_LAN_LOSS_RULE` set: `1` by the ladder, `bidir` by the plugin). `adaptive_bitrate_live.py` is untouched (its LAN-R1 test pins one guarded import). A fresh process with nothing set imports no `lan_loss_rule` and the bridge has no sink (tests/lan_loss_rule_bidir)."]
    (HERE / "proof_flag_absent.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
