#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess, urllib.request
from pathlib import Path
from typing import Any
SCHEMA="privyhub_b4_6_physical_legacy_cleanup_runtime_v1"; OK="B4_6_PHYSICAL_LEGACY_CLEANUP_RUNTIME_CONFIRMED"; FAIL="B4_6_PHYSICAL_LEGACY_CLEANUP_RUNTIME_NOT_CONFIRMED"
MAIN_REL="PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt"; MANIFEST_REL="PrivyHub/app/src/main/AndroidManifest.xml"; GAMES_REL="companion/plugins/games.py"
EXPECTED_MAIN_SHA="394d2b839fdb01f2988a0054b42e139e419e02207728f914e1713287992733cc"; EXPECTED_MANIFEST_SHA="ab1140c3230582f9dbbbf3c179d8fa08363971d9289e08442487f3849c7ac8a2"; EXPECTED_GAMES_SHA="f1271c865cdf88b971da4116d7eb887bf9855864ce1ae848baafc7a3452e0f9c"
TARGETS=("runtime/streaming/sunshine","runtime/downloads/sunshine","runtime/downloads/moonlight","data/games/sunshine","scripts/setup_sunshine_portable.ps1","scripts/install_sunshine_firewall.ps1","scripts/remove_sunshine_firewall.ps1","scripts/open_sunshine_web_ui.ps1","scripts/install_moonlight_onn.ps1")
NON_TARGETS=("runtime/emulators/retroarch-nightly-20260907/info/moonlight_libretro.info","runtime/emulators/retroarch-nightly-20260907/shaders/shaders_glsl/procedural/stellabialek-moonlight-sillyness.glsl","runtime/emulators/retroarch-nightly-20260907/shaders/shaders_slang/procedural/stellabialek-moonlight-sillyness.slang","runtime/emulators/retroarch/info/moonlight_libretro.info","runtime/emulators/retroarch/RetroArch-Win64/info/moonlight_libretro.info","runtime/emulators/retroarch/RetroArch-Win64/shaders/shaders_glsl/procedural/stellabialek-moonlight-sillyness.glsl","runtime/emulators/retroarch/RetroArch-Win64/shaders/shaders_slang/procedural/stellabialek-moonlight-sillyness.slang","runtime/emulators/retroarch/shaders/shaders_glsl/procedural/stellabialek-moonlight-sillyness.glsl","runtime/emulators/retroarch/shaders/shaders_slang/procedural/stellabialek-moonlight-sillyness.slang")
BASE_URL="http://127.0.0.1:8765"
def sha256(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def get_json(path:str)->tuple[bool,dict[str,Any],str]:
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE_URL+path,method="GET"),timeout=5.0) as r: raw=r.read(1024*1024)
        value=json.loads(raw.decode("utf-8")); return (True,value,"") if isinstance(value,dict) else (False,{},"NON_OBJECT_JSON")
    except Exception as exc: return False,{},type(exc).__name__
def sunshine_running()->tuple[bool|None,str]:
    try: c=subprocess.run(["tasklist.exe","/FI","IMAGENAME eq sunshine.exe","/FO","CSV","/NH"],text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=8.0,check=False)
    except Exception as exc: return None,type(exc).__name__
    if c.returncode!=0: return None,"TASKLIST_FAILED"
    return any(line.strip().casefold().startswith('"sunshine.exe"') for line in c.stdout.splitlines()),""
def adb_state()->dict[str,Any]:
    adb=shutil.which("adb.exe") or shutil.which("adb")
    if not adb: return {"available":False,"error":"ADB_UNAVAILABLE","connected":0,"ready":0,"moonlight_installed":0,"connection_attempted":False,"identifiers_logged":False}
    try: c=subprocess.run([adb,"devices"],text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=8.0,check=False)
    except Exception as exc: return {"available":True,"error":type(exc).__name__,"connected":0,"ready":0,"moonlight_installed":0,"connection_attempted":False,"identifiers_logged":False}
    if c.returncode!=0: return {"available":True,"error":"ADB_DEVICES_FAILED","connected":0,"ready":0,"moonlight_installed":0,"connection_attempted":False,"identifiers_logged":False}
    serials=[]; connected=0
    for line in c.stdout.splitlines()[1:]:
        parts=line.strip().split()
        if len(parts)<2: continue
        connected+=1
        if parts[1]=="device": serials.append(parts[0])
    installed=0
    for serial in serials:
        try: p=subprocess.run([adb,"-s",serial,"shell","pm","path","com.limelight"],text=True,encoding="utf-8",errors="replace",stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=8.0,check=False)
        except Exception: continue
        if p.returncode==0 and "package:" in p.stdout: installed+=1
    return {"available":True,"error":"","connected":connected,"ready":len(serials),"moonlight_installed":installed,"connection_attempted":False,"identifiers_logged":False}
def self_test()->int: assert len(TARGETS)==9 and len(NON_TARGETS)==9; return 0
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--require-active",action="store_true"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: return self_test()
    root=Path(a.root).resolve(); source_ok=sha256(root/MAIN_REL)==EXPECTED_MAIN_SHA and sha256(root/MANIFEST_REL)==EXPECTED_MANIFEST_SHA and sha256(root/GAMES_REL)==EXPECTED_GAMES_SHA
    remaining=[r for r in TARGETS if (root/r).exists()]; missing_non=[r for r in NON_TARGETS if not (root/r).exists()]
    status_ok,status,status_err=get_json("/plugins/games/status"); native=status.get("native_stream") if status_ok else None; native=native if isinstance(native,dict) else {}
    active=bool(status.get("active",False)); ready=bool(native.get("ready",False)); nactive=bool(native.get("active",False)); sunshine,sun_err=sunshine_running(); adb=adb_state()
    runtime_ok=status_ok and sunshine is False and (not a.require_active or (active and ready and nactive)); confirmed=source_ok and not remaining and not missing_non and runtime_ok; classification=OK if confirmed else FAIL
    report={"schema":SCHEMA,"classification":classification,"production_files_modified_by_probe":"NONE","network_addresses_collected_or_logged":"NONE","target_paths_remaining":remaining,"non_target_paths_missing":missing_non,"source_hashes_unchanged":source_ok,"status_available":status_ok,"status_error":status_err,"game_active":active,"native_stream_ready":ready,"native_stream_active":nactive,"native_kind":native.get("kind",""),"capture_backend":native.get("capture_backend",""),"encoder":native.get("encoder",""),"transport":native.get("transport",""),"sunshine_process_running":sunshine,"sunshine_process_check_error":sun_err,"android_package_state":adb,"android_moonlight_state_verified":bool(adb["available"] and adb["ready"]>0)}
    out=root/"logs/diagnostics"; out.mkdir(parents=True,exist_ok=True); (out/"b4_6_physical_legacy_cleanup_runtime.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    next_step=("B4_6_PROJECT_CLEANUP_CONFIRMED_DEVICE_PACKAGE_CHECK_PENDING_THEN_B5" if not report["android_moonlight_state_verified"] else ("B4_6_CLEANUP_CONFIRMED_REMOVE_DEVICE_MOONLIGHT_THEN_B5" if adb["moonlight_installed"]>0 else "B4_6_CLEANUP_CONFIRMED_BEGIN_B5_NATIVE_ONLY_REGRESSION")) if confirmed else "INSPECT_B4_6_FAILURE_BEFORE_B5"
    lines=["PrivyHub B4.6 physical legacy cleanup runtime validation",f"Classification: {classification}",f"Schema: {SCHEMA}","Production files modified by probe: NONE","Network addresses collected/logged: NONE","","=== PROJECT LEGACY ARTIFACTS ===",f"Target paths remaining: {remaining}",f"Non-target RetroArch paths missing: {missing_non}",f"B4.4 source hashes unchanged: {source_ok}","","=== ACTIVE NATIVE SESSION ===",f"Active session required: {a.require_active}",f"Companion status available: {status_ok}",f"Status error: {status_err or '<none>'}",f"Game active: {active}",f"Native stream ready: {ready}",f"Native stream active: {nactive}",f"Native kind: {native.get('kind','')}",f"Capture backend: {native.get('capture_backend','')}",f"Encoder: {native.get('encoder','')}",f"Transport: {native.get('transport','')}","","=== LEGACY PROCESS ===",f"Sunshine process running: {sunshine}",f"Process check error: {sun_err or '<none>'}","","=== ANDROID PACKAGE STATE ===",f"ADB available: {adb['available']}",f"Connected target count: {adb['connected']}",f"Ready target count: {adb['ready']}",f"Moonlight/com.limelight installed target count: {adb['moonlight_installed']}",f"ADB connection attempted: {adb['connection_attempted']}",f"Device identifiers logged: {adb['identifiers_logged']}",f"ADB error: {adb['error'] or '<none>'}",f"Android Moonlight state verified: {report['android_moonlight_state_verified']}","",f"Next step: {next_step}"]
    (out/"b4_6_physical_legacy_cleanup_runtime.txt").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n"); print(classification); print("Text:",out/"b4_6_physical_legacy_cleanup_runtime.txt"); return 0 if confirmed else 1
if __name__=="__main__": raise SystemExit(main())
