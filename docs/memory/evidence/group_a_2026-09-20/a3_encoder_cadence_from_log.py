#!/usr/bin/env python3
"""Group A / A3 - host-side encoder cadence from logs/games/native_video_alpha.log.

Parses every ffmpeg session block the Linux native-video backend appended
(progress lines are \r-separated). For each session: encoded frame count,
stream time, average encoder fps, ffmpeg vsync dup/drop counters, minimum
instantaneous fps between consecutive 0.5 s progress samples, x11grab errors.

This measures what the encoder EMITTED per second of stream time. It cannot
see whether consecutive grabs were pixel-identical; that needs a live capture.

Usage: python3 a3_encoder_cadence_from_log.py --repo /path/to/onn-stream-test
"""
from __future__ import annotations
import argparse, json, os, re, statistics as st

def t2s(t):
    hh,mm,ss=t.split(":"); return int(hh)*3600+int(mm)*60+float(ss)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",required=True); ap.add_argument("--out",default=None); a=ap.parse_args()
    outdir=a.out or os.path.dirname(os.path.abspath(__file__))
    raw=open(os.path.join(a.repo,"logs","games","native_video_alpha.log"),"rb").read().decode("utf-8","replace").replace("\r","\n")
    rows=[]
    for b in raw.split("Starting PrivyHub Linux native-video backend")[1:]:
        h={}
        m=re.search(r"Profile: (\S+) (\d+)x(\d+)@(\d+), (\d+)/(\d+) kbps.*?GOP=(\d+), BF=(\d+)",b)
        if m: h.update(profile=m.group(1),kbps=int(m.group(5)),gop=int(m.group(7)),bf=int(m.group(8)))
        m=re.search(r"discovered=(\d+)x(\d+)",b); h["window"]=f"{m.group(1)}x{m.group(2)}" if m else None
        m=re.search(r"Window title: (.*?)\n",b); h["title"]=m.group(1).strip() if m else None
        m=re.search(r"start: ([\d.]+)",b); h["start_epoch"]=float(m.group(1)) if m else None
        m=re.search(r"Stream #0:0: Video: rawvideo.*?, (\d+)x(\d+), .*?, ([\d.]+) fps, (\S+) tbr",b)
        h["in_tbr"]=m.group(4) if m else None
        prog=re.findall(r"frame=\s*(\d+) fps=\s*([\d.]+) q=\S+ (L?)size=\s*(\S+) time=(\S+) bitrate=\s*(\S+)(?: dup=(\d+) drop=(\d+))? speed=\s*(\S+)x",b)
        h["progress_samples"]=len(prog)
        if prog:
            last=prog[-1]; h["frames"]=int(last[0]); h["encoded_time_s"]=t2s(last[4]) if last[4]!="N/A" else None
            h["dup"]=int(last[6]) if last[6] else 0; h["drop"]=int(last[7]) if last[7] else 0
            h["encoder_avg_fps"]=round(h["frames"]/h["encoded_time_s"],3) if h["encoded_time_s"] else None
            inst=[]
            for p,c in zip(prog,prog[1:]):
                try:
                    dt=t2s(c[4])-t2s(p[4]); df=int(c[0])-int(p[0])
                    if dt>0: inst.append(df/dt)
                except Exception: pass
            h["inst_fps_min"]=round(min(inst),2) if inst else None; h["inst_fps_samples"]=len(inst); h["inst_fps_samples_below_58"]=sum(1 for f in inst if f<58)
            h["final_bitrate_kbps"]=float(last[5].replace("kbits/s","")) if last[5].endswith("kbits/s") else None
            h["speed_final"]=float(last[8]) if last[8]!="N/A" else None
        h["x11grab_errors"]=len(re.findall(r"\[x11grab @ [^\]]+\] Cannot get the image data",b))
        h["exit"]="signal 15" if "received signal 15" in b else ("other" if "Exiting" in b else "no_exit_line")
        rows.append(h)
    full=[r for r in rows if r.get("frames")]
    ps1=[r for r in full if "PSX" in (r["title"] or "")]; snes=[r for r in full if "bsnes" in (r["title"] or "")]
    def grp(g):
        f=[r["encoder_avg_fps"] for r in g]
        return {"n":len(g),"frames":sum(r["frames"] for r in g),"encoded_s":round(sum(r["encoded_time_s"] for r in g),1),"avg_fps_median":round(st.median(f),3),"avg_fps_min":round(min(f),3),"avg_fps_max":round(max(f),3),
                "dup":sum(r["dup"] for r in g),"drop":sum(r["drop"] for r in g),"inst_samples":sum(r["inst_fps_samples"] for r in g),"inst_samples_below_58":sum(r["inst_fps_samples_below_58"] for r in g),
                "inst_fps_min":min(r["inst_fps_min"] for r in g if r["inst_fps_min"] is not None),"x11grab_errors":sum(r["x11grab_errors"] for r in g)}
    summary={"sessions":len(rows),"with_progress":len(full),"all":grp(full),"ps1_beetle_psx_hw":grp(ps1),"snes_bsnes":grp(snes),"sessions_ge_60s":len([r for r in full if r["encoded_time_s"]>=60])}
    json.dump({"summary":summary,"sessions":rows},open(os.path.join(outdir,"a3_encoder_cadence_from_native_video_alpha.json"),"w"),indent=1)
    print(json.dumps(summary,indent=1))
if __name__=="__main__": main()
