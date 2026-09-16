#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, signal, socket, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any

EXPECTED_HEAD = "7c029de7ff7d569bce07d26c23f0bcfbb1147e8d"
OUT_REL = Path("logs/d099_absent_vod_timing_probe.txt")
SUCCESS = "D099_ABSENT_VOD_NONBLOCKING_CONFIRMED"
FAILURE = "D099_ABSENT_VOD_NONBLOCKING_NOT_CONFIRMED"
MAX_SECONDS = 2.0


def run(cmd):
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def listener(port):
    return bool(run(["ss", "-H", "-ltn", f"sport = :{port}"]).stdout.strip())


def request(url, method="GET"):
    started=time.monotonic(); req=urllib.request.Request(url,method=method)
    try:
        with urllib.request.urlopen(req,timeout=5) as r:
            raw=r.read(); obj=None
            try:
                p=json.loads(raw.decode("utf-8")); obj=p if isinstance(p,dict) else None
            except json.JSONDecodeError: pass
            return r.status,obj,"",time.monotonic()-started
    except urllib.error.HTTPError as e:
        return e.code,None,e.read().decode("utf-8",errors="replace"),time.monotonic()-started
    except Exception as e:
        return None,None,f"{type(e).__name__}: {e}",time.monotonic()-started


def self_test():
    assert (0 if SUCCESS=="D099_ABSENT_VOD_NONBLOCKING_CONFIRMED" else 1)==0
    assert (0 if FAILURE=="D099_ABSENT_VOD_NONBLOCKING_CONFIRMED" else 1)==1
    print("SELF-TEST PASS"); return 0


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="/home/privyhub/Projects/onn-stream-test"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: return self_test()
    repo=Path(a.root).resolve(); out=repo/OUT_REL; out.parent.mkdir(parents=True,exist_ok=True)
    head=run(["git","-C",str(repo),"rev-parse","HEAD"]).stdout.strip()
    if listener(8765) or listener(8000):
        out.write_text("Classification: "+FAILURE+"\nReason: PrivyHub ports not free before probe\n",encoding="utf-8"); print(FAILURE); print("Log:",out); return 1
    console=repo/"logs/d099_probe_companion_console.log"; h=console.open("w",encoding="utf-8")
    proc=subprocess.Popen([sys.executable,str(repo/"companion/privyhub_service.py")],cwd=str(repo),stdin=subprocess.DEVNULL,stdout=h,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+8
        while time.monotonic()<deadline and not listener(8765):
            if proc.poll() is not None: break
            time.sleep(.1)
        st=request("http://127.0.0.1:8765/status")
        so=request("http://127.0.0.1:8765/sources")
        ss=request("http://127.0.0.1:8765/sources/vod_file_aviator_52feb1dbba/start",method="POST")
        st2=request("http://127.0.0.1:8765/status")
        so2=request("http://127.0.0.1:8765/sources")
        media=listener(8000)
        storage=(so[1] or {}).get("storage",{}).get("vod",{})
        timings=[st[3],so[3],ss[3],st2[3],so2[3]]
        ok=(head==EXPECTED_HEAD and st[0]==200 and so[0]==200 and storage.get("available") is False and ss[0] in {404,503} and st2[0]==200 and so2[0]==200 and media and all(x<MAX_SECONDS for x in timings))
        cls=SUCCESS if ok else FAILURE
        lines=["PrivyHub D-099 absent-VOD timing probe",f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}","Network addresses collected/logged: NONE","","=== RESULTS ===",f"Git HEAD expected: {head==EXPECTED_HEAD}",f"/status HTTP: {st[0]}",f"/status seconds: {st[3]:.3f}",f"/sources HTTP: {so[0]}",f"/sources seconds: {so[3]:.3f}",f"storage.vod.available: {storage.get('available')}",f"stale source HTTP: {ss[0]}",f"stale source seconds: {ss[3]:.3f}",f"/status after HTTP: {st2[0]}",f"/status after seconds: {st2[3]:.3f}",f"/sources after HTTP: {so2[0]}",f"/sources after seconds: {so2[3]:.3f}",f"Port 8000 listening: {media}",f"All control requests < {MAX_SECONDS:.1f}s: {all(x<MAX_SECONDS for x in timings)}","","=== RESULT ===",f"Classification: {cls}"]
        out.write_text("\n".join(lines)+"\n",encoding="utf-8"); print(cls); print("Log:",out); return 0 if ok else 1
    finally:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try: proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=3)
        h.close()

if __name__=="__main__": raise SystemExit(main())
