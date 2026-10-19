#!/usr/bin/env python3
"""CL-B6: the onn's state over adb (state reads only): uptime, top (2 iterations, 1 s apart; the second is the sample),
thermal status and the cpu-thermal temperature, meminfo. Writes numbers only: no PID, user id, address or identifier.
    cl_b6_onn_read.py <label>   -> one JSON line on stdout"""
import datetime, json, re, subprocess, sys
PKG = "com.safeiot.privyhub"
def sh(cmd):
    return subprocess.run(["adb", "shell", cmd], capture_output=True, text=True, timeout=30).stdout
out = {"label": sys.argv[1] if len(sys.argv) > 1 else "", "at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
up = sh("cat /proc/uptime").split()
out["uptime_s"] = float(up[0]) if up else None
la = re.search(r"load average: ([\d.]+), ([\d.]+), ([\d.]+)", sh("uptime"))
out["load_avg_1_5_15"] = [float(x) for x in la.groups()] if la else None
top = sh("top -n 2 -d 1 -b")
it = top.split("Tasks:")
last = "Tasks:" + it[-1] if len(it) > 1 else top
cpu = re.search(r"(\d+)%cpu\s+(\d+)%user\s+(\d+)%nice\s+(\d+)%sys\s+(\d+)%idle\s+(\d+)%iow\s+(\d+)%irq\s+(\d+)%sirq", last)
if cpu:
    tot, user, nice, sysc, idle, iow, irq, sirq = map(int, cpu.groups())
    out["cpu"] = {"capacity_pct": tot, "user": user, "nice": nice, "sys": sysc, "idle": idle, "iow": iow, "irq": irq,
                  "sirq": sirq, "busy_pct_of_capacity": round(100 * (tot - idle) / tot, 1)}
for line in last.splitlines():
    f = line.split()
    if f and f[-1] == PKG and len(f) >= 12:
        # PID USER PR NI VIRT RES SHR S %CPU %MEM TIME+ ARGS
        out["privyhub"] = {"cpu_pct": float(f[8]), "mem_pct": float(f[9]), "res": f[5]}
th = sh("dumpsys thermalservice")
m = re.search(r"Thermal Status: (\d+)", th)
out["thermal_status"] = int(m.group(1)) if m else None
t = re.search(r"Current temperatures from HAL:\s*\n\s*Temperature\{mValue=([\d.]+), mType=0, mName=cpu-thermal", th)
out["cpu_thermal_c"] = float(t.group(1)) if t else None
mem = {k: int(v) for k, v in re.findall(r"^(MemTotal|MemFree|MemAvailable|SwapFree|SwapTotal):\s+(\d+) kB", sh("cat /proc/meminfo"), re.M)}
out["meminfo_kb"] = mem
print(json.dumps(out))
