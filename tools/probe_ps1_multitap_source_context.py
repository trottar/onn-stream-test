#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

EXPECTED={
 "companion/games/emulator_manager.py":"9f944b82a5a3fa1832b7daba11e0008747fd2cc37cbb2d13dff66ddb2c305165",
 "companion/plugins/games.py":"99597dbb1b110022b839ae88a092a9b5292b7f32911651fb6910f6def35b8c00",
 "companion/games/config/emulators.json":"37af06426c2f7ae82fa43a420ae4712f65ed8811ff19a4e2953e4134f801d184",
 "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt":"ea6c711b8819ad0f67e98bdfc94983af64aeb8a0ad2a917358c8fc4e7b5a786a",
}

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(path:Path): return path.read_text(encoding="utf-8-sig",errors="replace").splitlines()
def block(all_lines:list[str], pattern:str, before:int, after:int)->list[str]:
    rx=re.compile(pattern)
    hits=[i for i,s in enumerate(all_lines) if rx.search(s)]
    if not hits: return [f"<anchor not found: {pattern}>"]
    out=[]
    for hit in hits[:3]:
        lo=max(0,hit-before); hi=min(len(all_lines),hit+after+1)
        out.append(f"--- anchor /{pattern}/ at line {hit+1} ---")
        out.extend(f"{i+1:05d}: {all_lines[i]}" for i in range(lo,hi))
    return out

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test:
        assert len(EXPECTED)==4 and all(len(v)==64 for v in EXPECTED.values()); print("SELF-TEST PASS"); return 0
    root=Path(a.root).resolve(); log=root/"logs/games/ps1_multitap_source_context_audit.txt"; log.parent.mkdir(parents=True,exist_ok=True)
    out=["PrivyHub Phase A PS1 multitap exact source-context audit","Production files modified by probe: NONE","Network addresses collected/logged: NONE",""]
    diverged=False
    out.append("=== EXACT SOURCE HASH VERIFICATION ===")
    for rel,exp in EXPECTED.items():
        p=root/rel
        got=sha(p) if p.is_file() else "<missing>"
        out.append(f"{rel}: {got}")
        if got!=exp: diverged=True
    out.append("")
    if diverged:
        out.insert(1,"Classification: SOURCE_DIVERGED_STOP")
        log.write_text("\n".join(out)+"\n",encoding="utf-8"); print(log); return 2
    out.insert(1,"Classification: EXACT_POST_A8_SOURCE_CONTEXT_CAPTURED")
    eml=lines(root/"companion/games/emulator_manager.py")
    gpl=lines(root/"companion/plugins/games.py")
    out.append("=== EMULATOR MANAGER: CONTROLLER OVERRIDE STORAGE ===")
    out.extend(block(eml,r"def _load_controller_overrides\(",8,115)); out.append("")
    out.extend(block(eml,r"def controller_profile\(",10,125)); out.append("")
    out.extend(block(eml,r"def set_controller_profile\(",8,110)); out.append("")
    out.append("=== EMULATOR MANAGER: SESSION CONFIG ===")
    out.extend(block(eml,r"def _prepare_retroarch_session_config\(",12,250)); out.append("")
    out.append("=== EMULATOR MANAGER: INPUT OVERRIDE / LAUNCH ===")
    out.extend(block(eml,r"def _prepare_input_override\(",10,190)); out.append("")
    out.extend(block(eml,r"def launch\(",12,245)); out.append("")
    out.append("=== GAMES PLUGIN: GAME LOOKUP / LAUNCH / CONTROLLER PROFILE ===")
    for pat in (r"def _game",r"controller-profile",r"\.launch\(",r"max_players",r"player_mode"):
        out.extend(block(gpl,pat,18,75)); out.append("")
    out.append("=== EMULATORS.JSON ===")
    out.extend(lines(root/"companion/games/config/emulators.json")); out.append("")
    co=root/"data/games/retroarch/controller_overrides.json"
    out.append("=== CURRENT CONTROLLER OVERRIDES (PROJECT-LOCAL) ===")
    if co.is_file():
        try:
            obj=json.loads(co.read_text(encoding="utf-8-sig")); out.extend(json.dumps(obj,indent=2,sort_keys=True).splitlines())
        except Exception as e: out.append(f"<read/parse error: {type(e).__name__}: {e}>")
    else: out.append("<missing>")
    out.append("")
    # exact active Beetle opt file content; project-local only
    opts=[root/"runtime/emulators/retroarch-nightly-20260907/config/Beetle PSX HW/Beetle PSX HW.opt",root/"runtime/emulators/retroarch/config/Beetle PSX HW/Beetle PSX HW.opt"]
    out.append("=== BEETLE PSX HW CORE OPTIONS (PROJECT-LOCAL) ===")
    for p in opts:
        try: rel=p.relative_to(root).as_posix()
        except Exception: rel=p.name
        out.append(f"[{rel}]")
        if p.is_file():
            for s in lines(p):
                if "multitap" in s.casefold() or "device" in s.casefold(): out.append(s)
        else: out.append("<missing>")
    log.write_text("\n".join(out)+"\n",encoding="utf-8"); print(log); return 0
if __name__=="__main__": raise SystemExit(main())
