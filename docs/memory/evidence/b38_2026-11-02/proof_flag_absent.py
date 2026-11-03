#!/usr/bin/env python3
"""B38: absent = today, byte for byte, for an old or flag-absent client (no `pad_slots` key).

usage: proof_flag_absent.py BASE_COPY NEW_COPY   (the /tmp copies; reads only)

1. Text: in native_session_io.py and plugins/games.py every B38 change is an insertion; removing the inserted lines
   gives the base bytes. In native_stream_heartbeat.py the one changed line only widens a whitelist of keys that only
   the pad_slots path puts into `values`. pad_slots.py is imported only when the key is present (tests).
2. Behaviour: the same scripted run (a bridge fed four players' ticks with a press; a plugin given a start and a
   heartbeat with no pad_slots key) in a fresh process from each copy; the bridge status, the heartbeat row (times
   masked) and the recovery rows must be identical, and `pad_slots` must not be imported.
3. Client: PadSlots.kt is constructed only when debug.privyhub.pad_slots reads `stable` (B34's absent, PROVEN there);
   B38 edits no other client file.
"""
import difflib
import json
import subprocess
import sys
from pathlib import Path

BASE, NEW = Path(sys.argv[1]), Path(sys.argv[2])
ok = True


def insertions_only(rel):
    a = (BASE / rel).read_text().splitlines(keepends=True)
    b = (NEW / rel).read_text().splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    bad = [op for op in sm.get_opcodes() if op[0] in ("replace", "delete")]
    kept = [l for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "insert" for l in b[j1:j2]]
    same = "".join(kept) == "".join(a)
    added = sum(j2 - j1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag == "insert")
    return not bad and same, added


for rel in ("companion/native_session_io.py", "companion/plugins/games.py"):
    good, added = insertions_only(rel)
    print(f"{rel}: insertions only, the rest = base bytes: {good} ({added} lines added)")
    ok &= good

hb_a = (BASE / "companion/games/native_stream_heartbeat.py").read_text().splitlines()
hb_b = (NEW / "companion/games/native_stream_heartbeat.py").read_text().splitlines()
changed = [l for l in difflib.unified_diff(hb_a, hb_b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
print("native_stream_heartbeat.py changed lines:", json.dumps(changed))
ok &= len(changed) == 3 and "packets_by_player" in changed[-1]

SCRIPT = r'''
import json, sys, tempfile, types, importlib.util
from pathlib import Path
sys.path.insert(0, "companion")
import native_session_io as nsio
from games import link_drop_recovery as ldr
spec = importlib.util.spec_from_file_location("g", "companion/plugins/games.py"); G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
b = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b38_proof_")))
b._gamepads = [object()] * 4; b._controller_backend = "linux_uinput"; b._write_linux_report_locked = lambda *a, **k: None
for t in range(120):
    for p in range(4):
        b._apply_report(p, 0x1000 if (p == 1 and 40 <= t < 50) else 0, 7 * p, 0, 0, 0, 0, 0)
root = Path(tempfile.mkdtemp(prefix="b38_proof_root_"))
rec = ldr.LinkDropRecovery(root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
    restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True, end_session=lambda: None,
    client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
class Emu:
    def status(self): return {"active": True, "paused": True, "pid": 1}
pl = object.__new__(G.GamesPlugin); pl.PROJECT_ROOT = root; pl._emulator = Emu(); pl._recovery = rec
pl._native_stream = types.SimpleNamespace(start=lambda **kw: {"active": True}, _session_io=types.SimpleNamespace(controller=b))
pl._diagnostic_heartbeat_interval_ms = lambda: 2000; pl._adaptive_bitrate_session_ended = lambda: None
pl.handle_post_request("native-stream-start", "port=48100", "127.0.0.1")
pl.handle_post_request("native-stream-heartbeat", "sequence=1&interval_ms=2000&last_output_age_ms=16&rendered_frames=600&queued_frames=0&rx_packets=900&elapsed_ms=10000", "127.0.0.1")
def mask(r):
    return {k: ("<t>" if "utc" in k or k.endswith("_at") else v) for k, v in r.items()}
hb = [mask(json.loads(x)) for x in (root / "logs/games/native_stream_heartbeat.log").read_text().splitlines()]
rp = rec.log_path(); rr = [mask(json.loads(x)) for x in rp.read_text().splitlines()] if rp.exists() else []
print(json.dumps({"status": b.status(), "heartbeat_rows": hb, "recovery_rows": rr, "pad_slots_imported": "pad_slots" in sys.modules}, sort_keys=True))
'''
outs = {}
for name, root in (("base", BASE), ("new", NEW)):
    r = subprocess.run([sys.executable, "-B", "-c", SCRIPT], cwd=root, capture_output=True, text=True)
    if r.returncode:
        print(name, "FAILED", r.stderr[-800:])
        ok = False
        continue
    outs[name] = r.stdout.strip()
if len(outs) == 2:
    same = outs["base"] == outs["new"]
    d = json.loads(outs["new"])
    print("behaviour, no key: base and new identical:", same)
    print("  status keys:", sorted(d["status"]))
    print("  updates_by_player:", d["status"]["updates_by_player"], "| heartbeat rows:", len(d["heartbeat_rows"]),
          "| recovery rows:", len(d["recovery_rows"]), "| pad_slots imported:", d["pad_slots_imported"])
    ok &= same and not d["pad_slots_imported"] and "changes_by_player" not in d["status"]

client = subprocess.run(["git", "diff", "--no-index", "--stat", str(BASE / "PrivyHub/app/src/main"), str(NEW / "PrivyHub/app/src/main")],
                        capture_output=True, text=True).stdout
print("client main files changed:", [l.split("|")[0].strip().split("/")[-1] for l in client.splitlines() if "|" in l])
ok &= all("PadSlots.kt" in l for l in client.splitlines() if "|" in l)
print("PROVEN" if ok else "NOT PROVEN")
