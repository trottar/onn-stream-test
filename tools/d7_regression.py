#!/usr/bin/env python3
"""D7-R1: the roadmap's D7 native Linux regression, scripted where it can be.

    python3 tools/d7_regression.py --out <dir> --pass-label P1

One pass = one row per D7 item, PASS / FAIL / NEEDS USER / VALIDATED (cited),
with the evidence for each, written to <dir>/d7_<label>.json and .txt.
Uses only existing companion routes, existing probes and adb; changes no
companion, client or profile code. Handoff: docs/memory/handoffs/D7-R1_LINUX_REGRESSION_TASK.md.

Rules kept:
  * the companion is restarted only through its systemd unit, only in row 1;
  * save/load uses ONE scratch player slot (SCRATCH_SLOT) of the reference
    title, empty before the pass; the slot files, the slot index and the
    title's slot-0 `.state` (+png) are backed up first and restored after,
    and every other file in the states directory is hashed before and after;
  * a failing action is retried at most twice; a failing row is FAIL with its
    evidence and the pass continues;
  * nothing written here carries an address, MAC or device identifier: the
    journal is reduced to counts, `uiautomator` text skips `status_text`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOOPBACK = ".".join(("127", "0", "0", "1"))   # built, so no address literal is stored
BASE = f"http://{LOOPBACK}:8765"
UNIT = "privyhub-companion"
TITLE_ID = "game_ps1_b0a5986638f61a11"          # Tekken 3 (USA), the PS1 reference title
TILE_RE = r"^Tekken 3 \(USA\) - PlayStation"
STEM = "Tekken 3 (USA)"
STATES = REPO / "data/games/retroarch/states/Beetle PSX HW"
SLOT_INDEX = REPO / "data/games/retroarch/privyhub_state_slots.json"
SCRATCH_SLOT = 3
PKG = "com.safeiot.privyhub"
HB_LOG = REPO / "logs/games/native_stream_heartbeat.log"
SESSDIR = REPO / "logs/games/decoder_sessions"
HOLD_S = 180


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sh(cmd: list[str], timeout: float = 30) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as exc:  # noqa: BLE001
        return f"<error {type(exc).__name__}>"


def adb(*args: str, timeout: float = 20) -> str:
    return sh(["adb", *args], timeout=timeout)


def http(method: str, path: str, timeout: float = 30) -> tuple[int, dict]:
    req = urllib.request.Request(BASE + path, method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:  # noqa: BLE001
            return e.code, {}
    except Exception as exc:  # noqa: BLE001
        return 0, {"error": type(exc).__name__}


def games_status() -> dict:
    return http("GET", "/plugins/games/status")[1]


def stream_status() -> dict:
    return http("GET", "/plugins/games/native-stream-status")[1]


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


# ---- the launcher, as r3c2_checks.py and p9_run.sh drive it ----------------
def nodes() -> list[tuple[str, str, tuple[int, int]]]:
    adb("shell", "uiautomator", "dump", "/sdcard/d7.xml")
    xml = adb("shell", "cat", "/sdcard/d7.xml")
    out = []
    for m in re.finditer(r"<node [^>]*>", xml):
        n = m.group(0)
        text = re.search(r' text="([^"]*)"', n)
        rid = re.search(r' resource-id="([^"]*)"', n)
        b = re.search(r' bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
        rid_s = (rid.group(1) if rid else "").split("/")[-1]
        if rid_s == "status_text":                      # carries an address
            continue
        if b:
            x1, y1, x2, y2 = map(int, b.groups())
            out.append((text.group(1) if text else "", rid_s, ((x1 + x2) // 2, (y1 + y2) // 2)))
    return out


def screen_has(pattern: str) -> bool:
    return any(re.search(pattern, t, re.I) or re.search(pattern, r, re.I) for t, r, _ in nodes())


def open_launcher() -> None:
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
    time.sleep(7)


def top_activity() -> str:
    out = adb("shell", "dumpsys", "activity", "activities")
    m = re.search(r"topResumedActivity=.*", out)
    return m.group(0) if m else ""


def resume_playing() -> dict:
    """p9_run.sh's path: launcher, `now_playing_preview_host`, tap RESUME PLAYING."""
    for attempt in (1, 2):
        adb("shell", "am", "force-stop", PKG)
        open_launcher()
        if screen_has("now_playing_preview_host"):
            adb("shell", "input", "tap", "1008", "298")
            time.sleep(3)
            if "NativeStreamActivity" in top_activity():
                t0 = time.time()
                while time.time() - t0 < 45:
                    st = games_status()
                    if (st.get("recovery") or {}).get("state") == "PLAYING":
                        return {"ok": True, "attempt": attempt, "seconds_to_playing": round(time.time() - t0, 1)}
                    time.sleep(1)
    return {"ok": False, "recovery_state": (games_status().get("recovery") or {}).get("state")}


def heartbeats_between(t0: str, t1: str) -> list[dict]:
    rows = []
    if HB_LOG.exists():
        for line in HB_LOG.read_text(errors="replace").splitlines()[-4000:]:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if t0 <= r.get("received_at_utc", "") <= t1:
                rows.append(r)
    return rows


def find_key(d, key):
    if isinstance(d, dict):
        for k, v in d.items():
            if k == key and isinstance(v, (int, float)):
                return v
            r = find_key(v, key)
            if r is not None:
                return r
    return None


def journal_since(since: str) -> list[str]:
    return sh(["journalctl", "--user", "-u", UNIT, "--since", since, "--no-pager", "-o", "cat"], 30).splitlines()


def back_and_report(before: set[str]) -> dict:
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    for _ in range(30):
        time.sleep(1)
        new = sorted(set(os.listdir(SESSDIR)) - before)
        if new:
            return {"report": new[-1]}
    return {"report": None}


# ---- rows --------------------------------------------------------------
def row_boot() -> dict:
    t0 = time.time()
    sh(["systemctl", "--user", "restart", UNIT], 60)
    owner = mp = None
    for _ in range(30):
        mp = sh(["systemctl", "--user", "show", "-p", "MainPID", "--value", UNIT]).strip()
        m = re.search(r":8765 .*pid=(\d+)", sh(["ss", "-lntp"]))
        owner = m.group(1) if m else None
        if mp and owner == mp:
            break
        time.sleep(1)
    secs = round(time.time() - t0, 1)
    code, st = http("GET", "/status")
    ns = stream_status()
    o, c, r = ns.get("encoder_overrides") or {}, ns.get("audio_cushion") or {}, ns.get("audio_redundancy") or {}
    env_n = sum(1 for l in Path(f"/proc/{mp}/environ").read_bytes().split(b"\0")
                if l.startswith(b"PRIVYHUB_")) if mp and mp != "0" else None
    adopted = (o.get("any_override") is False and o.get("max_frame_size_bytes") == 90000
               and (c.get("queue_target_packets"), c.get("queue_capacity_packets")) == (12, 17)
               and (r.get("copies"), r.get("offset_packets")) == (2, 4)
               and (ns.get("fec") or {}).get("version") == "xor8_1")
    ok = bool(mp and owner == mp and code == 200 and st.get("service") == "PrivyHub" and adopted and env_n == 0)
    return {"verdict": "PASS" if ok else "FAIL",
            "evidence": {"mainpid_owns_8765": owner == mp, "seconds": secs, "status_http": code,
                         "service": st.get("service"), "native_stream_ready": ns.get("ready"),
                         "profile_adopted": adopted, "fec": (ns.get("fec") or {}).get("version"),
                         "privyhub_env_in_companion": env_n}}


def row_discovery() -> dict:
    since = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    adb("shell", "am", "force-stop", PKG)
    open_launcher()
    time.sleep(3)
    lines = journal_since(since)
    remote = lambda pat: sum(1 for l in lines if pat in l and not l.startswith(LOOPBACK))  # noqa: E731
    sources, gstatus = remote('"GET /sources '), remote('"GET /plugins/games/status ')
    library = screen_has(r"^GAMES") or screen_has("now_playing_preview_host")
    ok = sources > 0 and gstatus > 0 and library
    return {"verdict": "PASS" if ok else "FAIL",
            "evidence": {"client_get_sources_lines": sources, "client_get_games_status_lines": gstatus,
                         "launcher_shows_library": library,
                         "note": "controller transport checked in the video/audio/controller row"}}


def row_media(out: Path) -> dict:
    sh([sys.executable, str(REPO / "tools/probes/d136_focused_tv_media_regression_probe.py"), "--repo", str(REPO)], 180)
    p = REPO / "logs/tv/d136_focused_tv_media_regression_probe.json"
    try:
        d = json.loads(p.read_text())
    except Exception as exc:  # noqa: BLE001
        return {"verdict": "FAIL", "evidence": {"error": type(exc).__name__}}
    shutil.copy(p, out / f"d136_{int(time.time())}.json")
    ok = d.get("classification") == "D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED" and not d.get("problems")
    return {"verdict": "PASS" if ok else "FAIL",
            "evidence": {"classification": d.get("classification"), "problems": d.get("problems"),
                         "generated": d.get("generated_at") or d.get("generated"),
                         "note": "D136 re-runs D122 fresh; D133/D135 are read from their 2026-09-17 files"}}


def row_launch() -> dict:
    http("POST", "/plugins/games/stop")
    for _ in range(20):
        if games_status().get("active") is False:
            break
        time.sleep(1)
    code, lr = http("POST", f"/plugins/games/launch?id={TITLE_ID}", timeout=90)
    rp = resume_playing()
    st = games_status()
    ns = stream_status()
    ok = code == 200 and st.get("active") is True and rp.get("ok")
    return {"verdict": "PASS" if ok else "FAIL",
            "evidence": {"launch_http": code, "active": st.get("active"), "game": (st.get("game") or {}).get("title"),
                         "resume_playing": rp, "recovery_state": (st.get("recovery") or {}).get("state"),
                         "any_override_at_playing": (ns.get("encoder_overrides") or {}).get("any_override")}}


def row_av(ctx: dict) -> dict:
    s0 = stream_status()
    t0 = now()
    time.sleep(HOLD_S)
    t1 = now()
    s1 = stream_status()
    hb = heartbeats_between(t0, t1)
    fps = None
    if len(hb) >= 2:
        a, b = hb[0], hb[-1]
        dt = (b["elapsed_ms"] - a["elapsed_ms"]) / 1000.0
        fps = (b["rendered_frames"] - a["rendered_frames"]) / dt if dt > 0 else None
    arx = (hb[-1].get("audio_rx_packets", 0) - hb[0].get("audio_rx_packets", 0)) if len(hb) >= 2 else 0
    asent = (find_key(s1.get("audio"), "packets_sent") or 0) - (find_key(s0.get("audio"), "packets_sent") or 0)
    c0, c1 = s0.get("controller") or {}, s1.get("controller") or {}
    ctrl = (c1.get("packets_received") or 0) - (c0.get("packets_received") or 0)
    ctx["controller_active"] = bool(c1.get("active")) and ctrl > 0
    ok = len(hb) >= 0.8 * HOLD_S / 2 and fps is not None and fps >= 59.5 and asent > 0 and arx > 0 and ctrl > 0
    return {"verdict": "PASS" if ok else "FAIL", "needs_user": "controller feel and the picture on the TV",
            "evidence": {"hold_s": HOLD_S, "heartbeats": len(hb), "rendered_fps": round(fps, 2) if fps else None,
                         "audio_packets_sent_delta": asent, "client_audio_rx_delta": arx,
                         "controller_active": c1.get("active"), "controller_packets_received_delta": ctrl,
                         "video_lost_delta": (hb[-1]["lost_packets"] - hb[0]["lost_packets"]) if len(hb) >= 2 else None}}


def row_pause_resume(ctx: dict) -> dict:
    """No pause route exists: the user's pause is BACK (the game stays active,
    paused), resume is RESUME PLAYING (paused false, recovery PLAYING)."""
    before = set(os.listdir(SESSDIR))
    br = back_and_report(before)
    ctx["report_after_back"] = br["report"]
    time.sleep(3)
    st = games_status()
    paused_ok = st.get("active") is True and st.get("paused") is True
    rp = resume_playing()
    time.sleep(30)
    st2 = games_status()
    t1 = now()
    hb = heartbeats_between(datetime.fromtimestamp(time.time() - 25, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), t1)
    resumed_ok = rp.get("ok") and st2.get("paused") is False and len(hb) >= 5
    return {"verdict": "PASS" if paused_ok and resumed_ok else "FAIL",
            "evidence": {"after_back": {"active": st.get("active"), "paused": st.get("paused"), "report": br["report"]},
                         "resume_playing": rp, "after_resume": {"paused": st2.get("paused"),
                                                                "recovery_state": (st2.get("recovery") or {}).get("state"),
                                                                "heartbeats_last_25_s": len(hb)}}}


def _others_hashes() -> dict:
    return {p.name: sha(p) for p in sorted(STATES.iterdir())
            if p.is_file() and not p.name.startswith(f"{STEM}.state")} if STATES.exists() else {}


def row_save_load(out: Path) -> dict:
    slot_file = STATES / f"{STEM}.state{SCRATCH_SLOT}"
    slot_png = STATES / f"{STEM}.state{SCRATCH_SLOT}.png"
    s0, s0png = STATES / f"{STEM}.state", STATES / f"{STEM}.state.png"
    bk = REPO / "runtime" / "d7_r1" / "slot_backup"     # gitignored: saves never enter docs/
    bk.mkdir(parents=True, exist_ok=True)
    if slot_file.exists():
        return {"verdict": "FAIL", "evidence": {"error": f"scratch slot {SCRATCH_SLOT} is not empty; not touched"}}
    pre = {"index": sha(SLOT_INDEX), "slot0": sha(s0), "slot0_png": sha(s0png),
           "user_slots": {n: sha(STATES / f"{STEM}.state{n}") for n in (1, 2)}, "others": _others_hashes()}
    for src in (SLOT_INDEX, s0, s0png):
        if src.exists():
            shutil.copy2(src, bk / src.name)
    # BACK first: load-state requires the game to be paused.
    back_and_report(set(os.listdir(SESSDIR)))
    time.sleep(3)
    ev = {"scratch_slot": SCRATCH_SLOT}
    code_s, sv = http("POST", f"/plugins/games/save-state?slot={SCRATCH_SLOT}", timeout=60)
    ev["save_http"] = code_s
    ev["saved_file_exists"] = slot_file.exists()
    ev["saved_size_bytes"] = slot_file.stat().st_size if slot_file.exists() else None
    ev["saved_sha256_16"] = (sha(slot_file) or "")[:16] or None
    code_l, ld = http("POST", f"/plugins/games/load-state?slot={SCRATCH_SLOT}", timeout=60)
    ev["load_http"] = code_l
    st = games_status()
    ev["after_load"] = {"active": st.get("active"), "paused": st.get("paused")}
    ok = (code_s == 200 and code_l == 200 and ev["saved_file_exists"] and (ev["saved_size_bytes"] or 0) > 100_000
          and st.get("paused") is True)
    # --- cleanup: the scratch slot removed, the index and slot 0 restored ----
    for f in (slot_file, slot_png):
        if f.exists():
            f.unlink()
    for src in (SLOT_INDEX, s0, s0png):
        if (bk / src.name).exists():
            shutil.copy2(bk / src.name, src)
    post = {"index": sha(SLOT_INDEX), "slot0": sha(s0), "slot0_png": sha(s0png),
            "user_slots": {n: sha(STATES / f"{STEM}.state{n}") for n in (1, 2)}, "others": _others_hashes()}
    ev["hashes_restored"] = pre == post
    ev["scratch_removed"] = not slot_file.exists() and not slot_png.exists()
    ev["other_state_files_hashed"] = len(pre["others"])
    return {"verdict": "PASS" if ok and ev["hashes_restored"] and ev["scratch_removed"] else "FAIL", "evidence": ev}


def row_profiles() -> dict:
    watch = [REPO / "data/games/cheats.json", REPO / "data/games/retroarch/cheat_profiles",
             REPO / "data/games/retroarch/mod_profiles"]

    def tree(p: Path):
        if p.is_file():
            return sha(p)
        return sorted((str(q.relative_to(p)), sha(q)) for q in p.rglob("*") if q.is_file()) if p.exists() else None
    pre = [tree(p) for p in watch]
    res = {}
    for action in ("cheat-catalog", "cheat-profiles", "mod-catalog", "mod-profiles"):
        code, d = http("POST", f"/plugins/games/{action}?id={TITLE_ID}")
        # the count lives per source (`sources[i].cheat_count`); summed here
        count = sum((src.get("cheat_count") or 0) for src in (d.get("sources") or [])
                    if isinstance(src, dict)) if isinstance(d.get("sources"), list) else d.get("cheat_count")
        res[action] = {"http": code, "status": d.get("status"), "reason": d.get("reason"),
                       "cheat_count": count,
                       "profiles": len(d.get("profiles") or []) if isinstance(d.get("profiles"), list) else None}
    code, ac = http("POST", "/plugins/games/active-cheats")
    res["active-cheats"] = {"http": code, "active": ac.get("active")}
    code, ip = http("GET", f"/plugins/games/input-profiles?id={TITLE_ID}")
    res["input-profiles"] = {"http": code, "keys": sorted(ip)[:8]}
    st = games_status()
    res["session"] = {"cheat_session": bool(st.get("cheat_session")), "mod_session": bool(st.get("mod_session"))}
    post = [tree(p) for p in watch]
    ok = (all(v.get("http") == 200 for k, v in res.items() if isinstance(v, dict) and "http" in v)
          and res["mod-catalog"]["status"] == "unsupported"
          and (res["cheat-catalog"]["cheat_count"] or 0) > 0
          and res["active-cheats"]["active"] is False and pre == post)
    res["no_residue"] = pre == post
    return {"verdict": "PASS" if ok else "FAIL", "evidence": res}


def row_end(ctx: dict) -> dict:
    """End/teardown: RESUME -> BACK stores a report; POST stop; banner cleared."""
    rp = resume_playing()
    time.sleep(15)
    since = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    br = back_and_report(set(os.listdir(SESSDIR)))
    time.sleep(3)
    lines = journal_since(since)
    stored = sum(1 for l in lines if "Native decoder session log:" in l)
    warn = sum(1 for l in lines if "WARNING decoder-session-log" in l)
    code, _ = http("POST", "/plugins/games/stop", timeout=60)
    act = None
    for _ in range(20):
        act = games_status().get("active")
        if act is False:
            break
        time.sleep(1)
    adb("shell", "am", "force-stop", PKG)
    open_launcher()
    time.sleep(3)
    banner = screen_has("NOW PLAYING")
    mp = sh(["systemctl", "--user", "show", "-p", "MainPID", "--value", UNIT]).strip()
    m = re.search(r":8765 .*pid=(\d+)", sh(["ss", "-lntp"]))
    serving = bool(m and m.group(1) == mp)
    ok = rp.get("ok") and br["report"] and stored >= 1 and warn == 0 and code == 200 and act is False \
        and not banner and serving
    return {"verdict": "PASS" if ok else "FAIL",
            "evidence": {"resume_playing": rp, "report": br["report"], "journal_report_stored": stored,
                         "journal_report_warnings": warn, "stop_http": code, "active_after_stop": act,
                         "now_playing_banner": banner, "companion_serving": serving}}


def row_recovery() -> dict:
    return {"verdict": "VALIDATED (cited)",
            "evidence": {"records": ["D_BASE_R3D_HAND_RUNS_2026-09-22.md (N05, N15b, E30 PASS on real loss)",
                                     "D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md (resume, copy, discard; seven checks)"],
                         "note": "not re-run: real link loss needs the user's nft, never used unattended"}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pass-label", default="P1")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ctx: dict = {}
    rows = []

    def run(name, fn, *args):
        t = now()
        for attempt in (1, 2, 3):
            try:
                r = fn(*args)
            except Exception as exc:  # noqa: BLE001
                r = {"verdict": "FAIL", "evidence": {"exception": type(exc).__name__, "detail": str(exc)[:200]}}
            if not str(r.get("verdict", "")).startswith("FAIL") or name not in RETRY_OK:
                break
            r.setdefault("evidence", {})["attempt"] = attempt
        r.update({"row": name, "started_utc": t, "ended_utc": now()})
        rows.append(r)
        print(f"[d7 {a.pass_label}] {name}: {r['verdict']}", flush=True)

    run("server boot/start", row_boot)
    run("client discovery/control", row_discovery)
    run("media", row_media, out)
    run("Games launch", row_launch)
    run("video/audio/controller", row_av, ctx)
    run("pause/resume", row_pause_resume, ctx)
    run("Save/Load", row_save_load, out)
    run("profiles/cheats/mod state", row_profiles)
    run("End/teardown", row_end, ctx)
    run("restart/recovery", row_recovery)
    # client discovery/control also requires the controller transport once a stream is up
    for r in rows:
        if r["row"] == "client discovery/control":
            r["evidence"]["controller_transport_active_in_stream"] = ctx.get("controller_active")
            if r["verdict"] == "PASS" and not ctx.get("controller_active"):
                r["verdict"] = "FAIL"
    doc = {"schema": "privyhub_d7_regression_v1", "pass": a.pass_label, "generated_utc": now(), "rows": rows}
    (out / f"d7_{a.pass_label}.json").write_text(json.dumps(doc, indent=2))
    with open(out / f"d7_{a.pass_label}.txt", "w") as fh:
        for r in rows:
            fh.write(f"{r['row']:<28} {r['verdict']:<18} {r.get('needs_user', '')}\n")
    return 0


RETRY_OK = {"Games launch", "media"}   # idempotent rows; at most two retries

if __name__ == "__main__":
    sys.exit(main())
