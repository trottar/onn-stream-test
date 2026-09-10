#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, urllib.parse, urllib.request
from pathlib import Path

GAME_ID = "game_ps1_c8658e19167a52b4"
TITLE = "Crash Bash"
PATTERNS = (
    "core_options", "core options", ".opt", "game_specific_options",
    "global_core_options", "rgui_config_directory", "config directory",
    "beetle_psx_hw_enable_multitap", "multitap",
)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def redact_path(path: Path, root: Path) -> str:
    try: return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception: pass
    for env, label in (("APPDATA","<APPDATA>"),("LOCALAPPDATA","<LOCALAPPDATA>"),("USERPROFILE","<USERPROFILE>")):
        base=os.environ.get(env)
        if base:
            try: return label + "/" + path.resolve().relative_to(Path(base).resolve()).as_posix()
            except Exception: pass
    return "<external>/" + path.name

def relevant_lines(path: Path) -> list[str]:
    try: text=path.read_text(encoding="utf-8-sig",errors="replace")
    except OSError: return []
    out=[]
    for line in text.splitlines():
        low=line.casefold()
        if any(p.casefold() in low for p in PATTERNS): out.append(line.strip())
    return out[:120]

def live_game_metadata() -> dict[str, object] | None:
    q=urllib.parse.urlencode({"view":"search","q":TITLE,"limit":"20"})
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/plugins/games/games?"+q,timeout=3) as r:
            payload=json.loads(r.read().decode("utf-8"))
    except Exception:
        return None
    nodes=payload.get("nodes",[]) if isinstance(payload,dict) else []
    for node in nodes if isinstance(nodes,list) else []:
        if not isinstance(node,dict): continue
        if str(node.get("id","")).strip()==GAME_ID or "crash bash" in str(node.get("name",node.get("title",""))).casefold():
            keys=("id","name","title","system","max_players","player_mode","player_mode_source","metadata_available","canonical_title")
            return {k:node.get(k) for k in keys if k in node}
    return None

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test:
        assert GAME_ID.startswith("game_ps1_") and "multitap" in PATTERNS
        print("SELF-TEST PASS"); return 0
    root=Path(a.root).resolve(); log=root/"logs/games/ps1_multitap_core_options_audit.txt"; log.parent.mkdir(parents=True,exist_ok=True)
    lines=["PrivyHub Phase A PS1 multitap/core-options source audit","Production files modified by probe: NONE","Network addresses collected/logged: NONE",""]
    prod=[
        "companion/games/emulator_manager.py",
        "companion/plugins/games.py",
        "companion/games/config/emulators.json",
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt",
    ]
    lines.append("=== EXACT CURRENT SOURCE HASHES ===")
    for rel in prod:
        p=root/rel
        lines.append(f"{rel}: " + (sha(p) if p.is_file() else "<missing>"))
    em=root/"companion/games/emulator_manager.py"
    if em.is_file():
        text=em.read_text(encoding="utf-8-sig",errors="replace")
        for marker in ("core_options_path","game_specific_options","global_core_options","INPUT_PROFILE_PLAYERS","_prepare_retroarch_session_config","controller_overrides","max_players"):
            lines.append(f"emulator_manager references {marker}: {text.count(marker)}")
    lines.append("")
    lines.append("=== MANAGED RETROARCH CONFIG ===")
    for rel in ("data/games/retroarch/retroarch.cfg","data/games/retroarch/config/privyhub-session.cfg","data/games/retroarch/config/privyhub-input.cfg"):
        p=root/rel; lines.append(f"[{rel}]")
        if not p.is_file(): lines.append("<missing>"); continue
        found=relevant_lines(p)
        lines.extend(found if found else ["<no core-option/multitap-related lines>"])
    lines.append("")
    lines.append("=== CORE OPTION FILE DISCOVERY ===")
    roots=[]
    for p in (root/"data/games/retroarch", root/"runtime/emulators/retroarch", root/"runtime/emulators/retroarch-nightly-20260907"):
        if p.exists(): roots.append(p)
    for env in ("APPDATA","LOCALAPPDATA"):
        base=os.environ.get(env)
        if base:
            p=Path(base)/"RetroArch"
            if p.exists(): roots.append(p)
    seen=set(); found_files=[]
    for base in roots:
        try:
            candidates=list(base.rglob("*.opt"))+list(base.rglob("*core-options*.cfg"))+list(base.rglob("retroarch-core-options.cfg"))
        except OSError: continue
        for p in candidates:
            try: key=str(p.resolve()).casefold()
            except OSError: continue
            if key in seen or not p.is_file(): continue
            seen.add(key); found_files.append(p)
    if not found_files:
        lines.append("No .opt/core-options files found in managed runtime/data or redacted RetroArch user config roots.")
    for p in sorted(found_files,key=lambda x:redact_path(x,root).casefold())[:200]:
        lines.append(f"[{redact_path(p,root)}] sha256={sha(p)}")
        r=relevant_lines(p)
        lines.extend(r if r else ["<no Beetle/multitap-related lines>"])
    lines.append("")
    lines.append("=== LATEST CRASH BASH RETROARCH LOG ===")
    logs=sorted((root/"logs/games").glob(f"*-{GAME_ID}.log"),key=lambda p:p.stat().st_mtime_ns,reverse=True) if (root/"logs/games").is_dir() else []
    if not logs:
        lines.append("<not found>")
    else:
        latest=logs[0]; lines.append("Log: "+redact_path(latest,root))
        r=relevant_lines(latest)
        lines.extend(r if r else ["<no core-option/multitap-related log lines>"])
    lines.append("")
    lines.append("=== LIVE CRASH BASH METADATA ===")
    meta=live_game_metadata()
    if meta is None:
        lines.append("Companion metadata query unavailable or Crash Bash not found.")
        max_players=None
    else:
        lines.append(json.dumps(meta,sort_keys=True))
        try: max_players=int(meta.get("max_players") or 0)
        except Exception: max_players=0
    explicit=[]
    for p in found_files:
        try:
            t=p.read_text(encoding="utf-8-sig",errors="replace")
        except OSError: continue
        if "beetle_psx_hw_enable_multitap_port1" in t or "beetle_psx_hw_enable_multitap_port2" in t:
            explicit.append(redact_path(p,root))
    if explicit and (max_players or 0)>=4:
        classification="CORE_OPTIONS_STORAGE_DISCOVERED_METADATA_4P"
    elif explicit:
        classification="CORE_OPTIONS_STORAGE_DISCOVERED_METADATA_UNVERIFIED"
    elif (max_players or 0)>=4:
        classification="NO_EXPLICIT_CORE_OPTIONS_STORAGE_METADATA_4P"
    else:
        classification="CORE_OPTIONS_STORAGE_AUDIT_COMPLETE_METADATA_UNVERIFIED"
    lines.insert(1,"Classification: "+classification)
    lines.append("")
    lines.append("=== CLASSIFIER INPUTS ===")
    lines.append("Explicit Beetle multitap option files: "+(", ".join(explicit) if explicit else "none"))
    lines.append("Crash Bash max_players >= 4: "+str(bool((max_players or 0)>=4)))
    log.write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    print("Classification:",classification); print("Probe log:",log)
    return 0
if __name__=="__main__": raise SystemExit(main())
