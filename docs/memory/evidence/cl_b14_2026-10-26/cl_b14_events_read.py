# CL-B14: CL-B13's cl_b13_events_read.py (CL-B12's), unedited
import re,subprocess,sys,datetime
out_p, lo, hi, label = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]   # lo/hi local "MM-DD HH:MM:SS"
raw=subprocess.run(["adb","logcat","-b","events","-d","-v","threadtime"],capture_output=True,text=True,timeout=60).stdout
at=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TAGS=("am_kill","am_proc_died","am_proc_start","am_proc_bound","wm_on_create_called","wm_on_destroy_called","wm_on_resume_called","wm_on_paused_called","wm_on_stop_called","wm_on_restart_called","wm_on_start_called")
rx=re.compile(r"^(\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\s+\d+\s+\d+\s+\w\s+(\w+)\s*: \[(.*)\]\s*$")
out=[]; lines=raw.splitlines(); first=last=None
for l in lines:
    m=rx.match(l)
    if not m: continue
    t,tag,body=m.groups(); first=first or t; last=t
    if tag not in TAGS or "privyhub" not in body.lower() or not (lo<=t[:14]<=hi): continue
    f=[x.strip() for x in body.split(",")]
    if tag in ("am_kill","am_proc_died"): kept=f"pid={f[1]} process={f[2]} " + ("reason="+",".join(f[4:]) if tag=="am_kill" else "procstate="+",".join(f[4:]))
    elif tag=="am_proc_start": kept=f"pid={f[1]} process={f[3]} type={f[4] if len(f)>4 else ''} component={f[5].split('/')[-1] if len(f)>5 else ''}"
    elif tag=="am_proc_bound": kept=f"pid={f[1]} process={f[2] if len(f)>2 else ''}"
    else:
        comp=next((x for x in f if "privyhub" in x.lower()), "")
        kept="activity="+comp.split("/")[-1].split(".")[-1]+" reason="+",".join(x for x in f[2:] if "privyhub" not in x.lower())
    out.append(f"{t} (local) {tag}: {kept}")
hdr=[f"# {label}: one read of `adb logcat -b events -d` at {at}; {len(lines)} lines in the buffer ({first} .. {last}, local EDT); kept: {lo} .. {hi}",
     "# the PrivyHub rows of the am_* / wm_on_* tags only -- process names, pids, activity class names; no uid, token or other field"]
open(out_p,"w").write("\n".join(hdr+out)+"\n"); print("\n".join(hdr+out))
