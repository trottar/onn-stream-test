"""G6-SCREEN1b: a launch request WITHOUT `display=handheld` is the identical launch -- the committed companion (git
HEAD, exported read only to a temp dir) against the working tree, on the same made-up fixture (B49's PCSX2 rig: fake
Popen and Session; nothing started). Compared: PCSX2's command line, its full environment and cwd, every file the
launch leaves in the project (bytes), the game settings files as PCSX2 would read them at its spawn, the game log
(timestamps stripped), and status() (pid / elapsed stripped). Files that differ between two runs of the committed
code itself (the formatted memory cards carry a time) are listed as noise and compared by size only. Also the plugin's launch call for every system id.
Run from the repository root: python3 docs/memory/evidence/g6_screen1b_2026-11-20/no_field_identity_check.py"""
import hashlib, json, os, re, shutil, subprocess, sys, tarfile, io, tempfile
from pathlib import Path

ROOT = Path.cwd()
TMP = Path(tempfile.mkdtemp(prefix="g6s1b_identity_", dir=os.environ.get("TMPDIR")))
SERIAL, CRC = "SLUS-99901", "1234ABCD"      # made up

CODE = r'''
import json, os, sys, types, subprocess, hashlib
from pathlib import Path
sys.path.insert(0, "companion")
from games import emulator_manager as em
proj = Path(os.environ["P"])
calls = []
class FakePopen:
    def __init__(self, cmd, **kw):
        gs = proj / "data/games/ps2/config/PCSX2/gamesettings"
        calls.append({"cmd": cmd, "env": kw.get("env"), "cwd": kw.get("cwd"), "new_session": kw.get("start_new_session"),
                      "gs": {p.name: p.read_text() for p in sorted(gs.glob("*.ini"))} if gs.is_dir() else {}})
        self.pid = 4242; self.returncode = None; self.stdin = None
    def poll(self): return self.returncode
    def wait(self, timeout=None): self.returncode = 0; return 0
em.subprocess.Popen = FakePopen
P = em._ps2
class FakeSession(P.Session):
    def __init__(self, pid, log, **kw):
        clock = [0.0]
        def run(cmd, **k):
            if "search" in cmd: return types.SimpleNamespace(stdout="77\n")
            if cmd[:3] == ["pactl", "list", "sink-inputs"]: return types.SimpleNamespace(stdout=f'application.process.id = "{pid}"\n')
            return types.SimpleNamespace(stdout="")
        super().__init__(pid, log, run=run, status=lambda: None, kill=lambda p, s: None,
                         sleep=lambda d: clock.__setitem__(0, clock[0] + d), clock=lambda: clock[0],
                         pine_path=proj / "no-pine.sock", **kw)
P.Session = FakeSession
P.default_runner = lambda cmd: "deviceName = AMD Fake (RADV FAKE)\n"
m = em.EmulatorManager(proj, config_path=Path("companion/games/config/emulators.json").resolve())
game = {"id": "game_ps2_x", "system": "ps2", "title": "made-up", "relative_path": "ps2/one.chd"}
r = m.launch(game)
st = m.status()
for k in ("pid", "elapsed_seconds"): st.pop(k, None)
print(json.dumps({"calls": calls, "status": st, "launch_keys": sorted(r.keys())}))
'''


def fixture(where: Path, toggles):
    games, bios, proj = where / "games", where / "bios", where / "proj"
    for d in (games, bios, proj / "runtime/emulators/pcsx2", proj / "data/games/ps2/logs"):
        d.mkdir(parents=True)
    (games / "one.chd").write_bytes(b"1")
    sys.path.insert(0, str(ROOT / "companion"))
    import ps2_session as ps2, ps2_patches as pp
    (bios / "image.bin").write_bytes(b"\0" * ps2.BIOS_IMAGE_BYTES)
    (bios / "image.nvm").write_bytes(b"n")
    (proj / "runtime/emulators/pcsx2/pcsx2-fake.AppImage").write_bytes(b"x")
    (proj / "runtime/h3_p1_paths.txt").write_text(f"BIOS_DIR={bios}\nGAMES_DIR={games}\n")
    (proj / "data/games/ps2/logs/20261101T000000Z-pcsx2.log").write_text(
        f"[    1.3691] Disc changed to one.chd.\n[    1.3691]   Serial: {SERIAL}\n[    1.3691]   CRC: {CRC}\n")
    if toggles is not None:
        pp.set_toggles(proj, "game_ps2_x", toggles, ["ws", "ni", "60"])
    return proj


def norm(text: str, proj: Path) -> str:
    text = text.replace(str(proj), "<proj>").replace(str(proj.parent), "<fx>")
    return re.sub(r"\d{8}T\d{6}Z|\d{8}-\d{6}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", "<t>", text)


def run(companion_root: Path, toggles, tag: str):
    where = TMP / tag
    proj = fixture(where, toggles)
    env = {"PATH": "/usr/bin:/bin", "P": str(proj), "PRIVYHUB_PS2": "1"}
    r = subprocess.run([sys.executable, "-c", CODE], cwd=companion_root, env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])
    out = json.loads(r.stdout.strip().splitlines()[-1])
    files = {}
    for p in sorted(proj.rglob("*")):
        if p.is_file():
            rel = norm(str(p.relative_to(proj)), proj)
            data = p.read_bytes()
            if rel.startswith("logs/games/") or rel.endswith("-pcsx2.log"):
                files[rel] = norm(data.decode(errors="replace"), proj)
            elif rel.endswith(".ps2"):
                files[rel] = (len(data), hashlib.sha256(data).hexdigest())
            else:
                files[rel] = hashlib.sha256(norm(data.decode(errors="replace"), proj).encode()).hexdigest()
    return json.loads(norm(json.dumps(out), proj)), files


head = TMP / "head"
head.mkdir()
tar = subprocess.run(["git", "archive", "HEAD", "companion"], capture_output=True, check=True).stdout
tarfile.open(fileobj=io.BytesIO(tar)).extractall(head, filter="data")
lines, ok = [], True
for name, toggles in (("ws on", {"ws": True, "ni": False, "60": True}), ("all off", {"ws": False, "ni": False, "60": False}),
                      ("no record", None)):
    a_out, a_files = run(head, toggles, "a_" + name.replace(" ", "_"))
    _a2, a2_files = run(head, toggles, "a2_" + name.replace(" ", "_"))
    b_out, b_files = run(ROOT, toggles, "b_" + name.replace(" ", "_"))
    noise = sorted(k for k in set(a_files) | set(a2_files) if a_files.get(k) != a2_files.get(k))
    sized = lambda f: {k: (v[0] if k in noise and isinstance(v, (list, tuple)) else v) for k, v in f.items()}
    same = {"command line": [c["cmd"] for c in a_out["calls"]] == [c["cmd"] for c in b_out["calls"]],
            "environment": [c["env"] for c in a_out["calls"]] == [c["env"] for c in b_out["calls"]],
            "cwd / session": [(c["cwd"], c["new_session"]) for c in a_out["calls"]] == [(c["cwd"], c["new_session"]) for c in b_out["calls"]],
            "settings at spawn": [c["gs"] for c in a_out["calls"]] == [c["gs"] for c in b_out["calls"]],
            "files left": sized(a_files) == sized(b_files),
            "status()": a_out["status"] == b_out["status"] and "widescreen" not in b_out["status"],
            "launch reply keys": a_out["launch_keys"] == b_out["launch_keys"]}
    ok &= all(same.values())
    lines.append(f"PS2 launch without the field, title {name}: " + "; ".join(f"{k} {'IDENTICAL' if v else 'DIFFERENT'}" for k, v in same.items())
                 + f" ({len(b_files)} files compared; differing between two committed-code runs, so by size only: {noise})")

# the plugin: a launch without the field calls launch() with the same arguments as the committed plugin, every system
import importlib.util, types
def plugin_kwargs(path: Path, system: str, query: str):
    spec = importlib.util.spec_from_file_location("g_" + str(abs(hash((str(path), system, query)))), path)
    G = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent.parent))
    spec.loader.exec_module(G)
    p = object.__new__(G.GamesPlugin)
    seen = []
    p._find_game_by_id = lambda gid: {"id": gid, "system": system, "relative_path": f"{system}/one.bin"}
    p._parse_cheat_launch_request = lambda q: (None, None)
    p._game_discs = lambda g: 1
    p._log_launch_ports = lambda g, pl, q: None
    p._emulator = types.SimpleNamespace(launch=lambda g, **kw: (seen.append((g, kw)), {"ok": True})[1])
    p.handle_post("launch", query)
    return seen
for system in ("ps2", "ps1", "snes", "n64", "nes", "genesis", "gamecube", "party"):
    for q in ("id=game_x", "id=game_x&players_joined=2"):
        a = plugin_kwargs(head / "companion/plugins/games.py", system, q)
        b = plugin_kwargs(ROOT / "companion/plugins/games.py", system, q)
        if a != b:
            ok = False
            lines.append(f"plugin launch call DIFFERENT: {system} {q}")
lines.append("plugin launch call without the field: IDENTICAL for ps2, ps1, snes, n64, nes, genesis, gamecube, party "
             "(with and without players_joined)" if ok else "plugin launch call: see DIFFERENT above")
shutil.rmtree(TMP, ignore_errors=True)
lines.append("ALL IDENTICAL" if ok else "NOT IDENTICAL")
print("\n".join(lines))
sys.exit(0 if ok else 1)
