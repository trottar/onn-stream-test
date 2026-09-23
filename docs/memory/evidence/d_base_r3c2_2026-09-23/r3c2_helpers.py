#!/usr/bin/env python3
"""D-BASE-R3c2 helpers: restore the recovery copy, and check 0.

  restore   copy the N150 save, its .png and the index from
            d_base_r3c_2026-09-22/recovery_copy/ into place; verify hashes.
            The copy itself is only read.
  check0    POST /plugins/games/recovery-resume (the new path, no client),
            read the session it leaves (must be paused, a new pid), then
            unpause with PAUSE_TOGGLE (the command manager.resume() sends)
            and grab 30 s x11grab -> framemd5 of the managed window, exactly
            as r3c_probe.py did. Stops the session afterwards.
"""
import hashlib, json, os, shutil, sys, time, urllib.request
sys.path.insert(0, "/home/privyhub/Projects/onn-stream-test/docs/memory/evidence/d_base_r3c_2026-09-22")
import r3c_probe as P  # noqa: E402  (ra, ra_status, wait_status, window_for, grab, snap, http)

REPO = "/home/privyhub/Projects/onn-stream-test"
HERE = os.path.dirname(os.path.abspath(__file__))
COPY = os.path.join(REPO, "docs/memory/evidence/d_base_r3c_2026-09-22/recovery_copy")
STATES = os.path.join(REPO, "data/games/retroarch/states/Beetle PSX HW")
INDEX = os.path.join(REPO, "data/games/retroarch/privyhub_recovery_save.json")
PAIRS = [("Tekken 3 (USA).state.recovery", os.path.join(STATES, "Tekken 3 (USA).state.recovery")),
         ("Tekken 3 (USA).state.recovery.png", os.path.join(STATES, "Tekken 3 (USA).state.recovery.png")),
         ("privyhub_recovery_save.json", INDEX)]
P.HERE = HERE  # grab/snap write here


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    with open(os.path.join(HERE, "r3c2_run.log"), "a") as f:
        f.write(line + "\n")


def restore():
    for name, dest in PAIRS:
        shutil.copyfile(os.path.join(COPY, name), dest)
        ok = sha(dest) == sha(os.path.join(COPY, name))
        log(f"restore {name}: {'hash OK' if ok else 'HASH MISMATCH'}")
        if not ok:
            raise SystemExit(2)


def present():
    return {name: os.path.exists(dest) for name, dest in PAIRS}


def check0():
    P.stop_game()
    restore()
    code, body = P.http("recovery-resume", "POST")
    keep = {k: body.get(k) for k in ("ok", "action", "active", "paused", "pid", "recovery_load",
                                       "recovery_discarded", "error", "message")}
    log(f"check0 recovery-resume http {code} {json.dumps(keep)[:600]}")
    res = {"http": code, "response": keep, "files_after": present()}
    if code != 200:
        json.dump(res, open(os.path.join(HERE, "check0.json"), "w"), indent=1)
        return res
    pid = body.get("pid")
    res["ra_status_after"] = P.ra_status()
    win = P.window_for(pid)
    P.ra("PAUSE_TOGGLE")
    res["unpause"] = P.wait_status("PLAYING")
    time.sleep(2)
    res["snap_a"] = P.snap(win, "check0_a")
    res["grab"] = P.grab(win, "check0")
    res["snap_b"] = P.snap(win, "check0_b")
    g = res["grab"]
    log(f"check0 grab distinct {g['distinct']} per_s {g['distinct_per_second']} top5 {g['top5_hash_counts']}")
    res["stopped"] = P.stop_game()
    json.dump(res, open(os.path.join(HERE, "check0.json"), "w"), indent=1)
    return res


if __name__ == "__main__":
    {"restore": restore, "check0": check0}[sys.argv[1]]()
