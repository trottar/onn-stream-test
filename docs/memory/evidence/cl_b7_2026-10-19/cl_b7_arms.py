#!/usr/bin/env python3
"""CL-B7: the three arms as pre-registered (cl_b7_preregistration.txt), one suite invocation per arm, in order:
  1 pcm        -- e3_flag.conf PRIVYHUB_AUDIO_CODEC=pcm (the suite writes / verifies / removes it), idle gap 120 s
  2 opus_today -- no drop-in, the property read empty before the start, idle gap 300 s
  3 opus_lean  -- adb shell setprop debug.privyhub.opus_decode lean, read back, idle gap 300 s
Beside each arm (state reads): before the suite starts, cl_b6_onn_read.py <arm>_before then
tools/cl_b7_onn_threads.py <arm>_before; 150 s into the window, the same two (<arm>_150s), the companion's environ
(variable names and values only for PRIVYHUB_* lines). After arm 1: the companion's journal over the arm must carry
"audio stays PCM" and no opus-active line, else STOP (written). After arm 3 (or a stop): setprop "" and read back.
    cl_b7_arms.py            -> runs/<arm>/..., onn_reads.jsonl, onn_threads.jsonl, arms.jsonl, prop_reads.jsonl
"""
import datetime, importlib.util, json, re, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PRE = HERE / "cl_b7_preregistration.txt"
ONN = HERE.parent / "cl_b6_2026-10-19/cl_b6_onn_read.py"
THR = REPO / "tools/cl_b7_onn_threads.py"
PROP = "debug.privyhub.opus_decode"
ARMS = [("pcm", "E1-PS1-STREAM:1:120:PRIVYHUB_AUDIO_CODEC=pcm", None),
        ("opus_today", "E1-PS1-STREAM:1:300", ""),
        ("opus_lean", "E1-PS1-STREAM:1:300", "lean")]
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
spec = importlib.util.spec_from_file_location("e1_suite", REPO / "tools/e1_suite.py")
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)


def utc(t=None):
    return datetime.datetime.fromtimestamp(time.time() if t is None else t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(*a):
    line = f"[cl_b7 {utc()}] " + " ".join(str(x) for x in a)
    print(line, flush=True)


def append(p, row):
    with open(p, "a") as fh:
        fh.write(json.dumps(row) + "\n")


def getprop():
    return subprocess.run(["adb", "shell", "getprop", PROP], capture_output=True, text=True, timeout=20).stdout.strip()


def setprop(v):
    r = subprocess.run(["adb", "shell", "setprop", PROP, v if v else '""'], capture_output=True, text=True, timeout=20)
    return r.returncode


def reads(label):
    for script, dest in ((ONN, "onn_reads.jsonl"), (THR, "onn_threads.jsonl")):
        try:
            r = subprocess.run([sys.executable, "-I", "-B", str(script), label], capture_output=True, text=True, timeout=180)
            out = r.stdout.strip() or json.dumps({"label": label, "error": "no output", "stderr": IP.sub("<redacted>", r.stderr[-300:])})
        except subprocess.SubprocessError as e:
            out = json.dumps({"label": label, "error": repr(e)[:200]})
        with open(HERE / dest, "a") as fh:
            fh.write(IP.sub("<redacted>", out) + "\n")
    log("reads", label, "done")


def follower(arm, out, state):
    sl = out / "suite.log"
    while not state.get("done"):
        txt = sl.read_text() if sl.exists() else ""
        w = [l for l in txt.splitlines() if ": window " in l]
        if w and "read150" not in state:
            start = datetime.datetime.strptime(w[-1].split(": window ")[1][:19], "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=datetime.timezone.utc).timestamp()
            while time.time() < start + 150 and not state.get("done"):
                time.sleep(1)
            if state.get("done"):
                return
            state["read150"] = utc()
            env = [kv for kv in E1.environ_flags(E1.mainpid())]
            (HERE / f"environ_{arm}.txt").write_text("\n".join(env) + "\n")
            reads(f"{arm}_150s")
        time.sleep(2)


def journal(t0, t1):
    j = subprocess.run(["journalctl", "--user", "-u", E1.UNIT, "-o", "short-iso", "--no-pager", "--since", f"@{int(t0)}",
                        "--until", f"@{int(t1) + 1}"], capture_output=True, text=True, timeout=120).stdout
    keep = [IP.sub("<redacted>", l.split(" ", 2)[0] + " " + l.split(": ", 1)[-1]) for l in j.splitlines()
            if "PRIVYHUB_AUDIO_CODEC" in l]
    return keep


def main():
    stop_why = None
    for n, (arm, plan, prop) in enumerate(ARMS, 1):
        t0 = time.time()
        if prop is not None:
            if prop:
                rc = setprop(prop)
                append(HERE / "prop_reads.jsonl", {"at_utc": utc(), "arm": arm, "setprop": prop, "rc": rc, "getprop": getprop()})
            else:
                append(HERE / "prop_reads.jsonl", {"at_utc": utc(), "arm": arm, "getprop_before_start": getprop()})
        reads(f"{arm}_before")
        out = HERE / "runs" / arm
        out.mkdir(parents=True, exist_ok=True)
        state = {}
        th = threading.Thread(target=follower, args=(arm, out, state), daemon=True)
        th.start()
        log(f"arm {n} {arm}: suite start ({plan})")
        with open(out / "suite_console.log", "a") as fh:
            rc = subprocess.run([sys.executable, "-B", str(REPO / "tools/e1_suite.py"), "run", "--out", str(out), "--prereg", str(PRE),
                                 "--plan", plan, "--window", "600", "--e2"], stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO)).returncode
        state["done"] = True
        th.join(timeout=30)
        t1 = time.time()
        jl = journal(t0, t1)
        (HERE / f"journal_codec_lines_{arm}.txt").write_text("\n".join(jl) + "\n")
        row = {"n": n, "arm": arm, "plan": plan, "start_utc": utc(t0), "end_utc": utc(t1), "suite_rc": rc,
               "read150_utc": state.get("read150"), "journal_codec_lines": len(jl)}
        append(HERE / "arms.jsonl", row)
        log(f"arm {n} {arm}: suite rc {rc}; read150 {state.get('read150')}; codec lines {jl}")
        if arm == "pcm":
            stays = any("audio stays PCM" in l for l in jl)
            opus = any(re.search(r"\): opus \d+ kbit/s", l) for l in jl)
            if not stays or opus:
                stop_why = f"arm 1: the companion's log does not read PCM (stays_pcm {stays}, opus line {opus}); stopped"
                log(stop_why)
                break
        if (HERE / "STOP").exists():
            stop_why = "the STOP file"
            break
    rc = setprop("")
    append(HERE / "prop_reads.jsonl", {"at_utc": utc(), "arm": "teardown", "setprop": "", "rc": rc, "getprop": getprop()})
    log("teardown: property cleared, read back", repr(getprop()), "| stop:", stop_why)
    log("done")


if __name__ == "__main__":
    main()
