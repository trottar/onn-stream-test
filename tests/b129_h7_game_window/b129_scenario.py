# B129 / B130's child scenario (appended to B103's harness head; run by test_b129.py / test_b130.py). Not a test module.
# B129: the watcher's own WindowPicture against a fake window table (the xdotool calls answered from it: which windows
# a pid's search lists, each window's owner and geometry) and a fake screen (Pillow's X11 grab returns a 1920 x 1080
# desktop picture with the game's picture pasted at its window's place; every grab's rectangle kept). Large fake pids
# (no real process has them). B130: B103's scripted pictures, the session under a fake cheat setup or not.
import PIL.ImageGrab as _IG
os.environ["DISPLAY"] = ":99"
out = {"steps": {}}
S = out["steps"]
WINDOWS = {}                       # window id -> {"listed": pid, "owner": pid, "geo": (x, y, w, h)}
SCREEN = {"rect": None, "tok": "start"}
GRABS = []
_head_run = subprocess.run


def _ns(rc, text):
    return types.SimpleNamespace(returncode=rc, stdout=text, stderr="")


def _xrun(cmd, *a, **k):
    if cmd and cmd[0] == "xdotool":
        if cmd[1] == "search":
            pid = int(cmd[cmd.index("--pid") + 1])
            listed = "".join(f"{w}\n" for w, v in sorted(WINDOWS.items()) if v["listed"] == pid)
            return _ns(0 if listed else 1, listed)
        v = WINDOWS.get(int(cmd[-1]))
        if v is None:
            return _ns(1, "")
        if cmd[1] == "getwindowpid":
            return _ns(0, f"{v['owner']}\n")
        if cmd[1] == "getwindowgeometry":
            x, y, w, h = v["geo"]
            return _ns(0, f"WINDOW={cmd[-1]}\nX={x}\nY={y}\nWIDTH={w}\nHEIGHT={h}\nSCREEN=0\n")
        return _ns(1, "")
    return _head_run(cmd, *a, **k)


subprocess.run = _xrun
with Image.open(frames / "other_0.png") as _d:
    DESK = _d.convert("L").resize((1920, 1080))


def _grab(bbox=None, include_layered_windows=False, all_screens=False, xdisplay=None):
    GRABS.append(list(bbox))
    canvas = DESK.copy()
    if SCREEN["rect"] is not None:
        x, y, w, h = SCREEN["rect"]
        with Image.open(frames / f"{SCREEN['tok']}_0.png") as gp:
            canvas.paste(gp.convert("L").resize((w, h)), (x, y))
    return canvas.crop(tuple(bbox)).convert("RGB")


_IG.grab = _grab
rules_ = Path(rules)
rules_.mkdir(parents=True, exist_ok=True)
for name in os.listdir(args["spec_dir"]):
    shutil.copyfile(Path(args["spec_dir"], name), rules_ / name.replace("GAME", args["id"]))
(rules_ / f"{args['id']}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
mini = g._h7_minigame_runner()
log = root / "logs/games/h7_results.jsonl"


def h7_rows():
    return [json.loads(l) for l in log.read_text().splitlines()] if log.is_file() else []


def settled(bound):
    end = time.monotonic() + bound
    while time.monotonic() < end:
        b = result()
        if b.get("recognised") is not None:
            return b
        time.sleep(0.03)
    return dict(result(), timeout=True)


if args["mode"] == "window":
    mini.read_every = 0.2
    mini.recognise_s = 1.6

    def case(tag, pid, windows, rect, tok="start"):
        call("POST", "/plugins/games/stop")
        call("POST", f"/plugins/games/launch?id={args['id']}")
        fake["ra"].paused = False
        fake["ra"].pid = pid
        WINDOWS.clear()
        WINDOWS.update(windows)
        SCREEN.update(rect=rect, tok=tok)
        g0, r0 = len(GRABS), len(h7_rows())
        S[tag + "_start"] = start()["body"]
        b = settled(6)
        time.sleep(0.5)
        S[tag] = {k: b.get(k) for k in ("state", "recognised", "class", "reads", "picture_failures", "timeout")}
        S[tag + "_grabs"] = sorted({tuple(x) for x in GRABS[g0:]})
        S[tag + "_rows"] = sorted({r["step"] for r in h7_rows()[r0:]})
        S[tag + "_failures_why"] = sorted({r.get("why", "")[:60] for r in h7_rows()[r0:]
                                           if r["step"] == "picture_failed"})
        call("POST", "/plugins/games/h7-stop")

    case("full", 999999001, {11: {"listed": 999999001, "owner": 999999001, "geo": (0, 0, 1920, 1080)}},
         (0, 0, 1920, 1080))
    # the H7-V5 order: a full-screen game, then a windowed one in the same companion
    case("windowed", 999999002, {21: {"listed": 999999002, "owner": 999999002, "geo": (960, 384, 960, 720)}},
         (960, 384, 960, 720))
    # a larger window listed for the process but owned by another (the desktop's size), and the game's own window
    case("foreign_listed", 999999003, {31: {"listed": 999999003, "owner": 999998999, "geo": (0, 0, 1920, 1080)},
                                       32: {"listed": 999999003, "owner": 999999003, "geo": (300, 200, 960, 720)}},
         (300, 200, 960, 720))
    case("no_window", 999999004, {}, (960, 384, 960, 720))
    case("only_foreign", 999999005, {51: {"listed": 999999005, "owner": 999998999, "geo": (0, 0, 1920, 1080)}},
         (960, 384, 960, 720))
    call("POST", "/plugins/games/stop")

if args["mode"] == "recognise":
    mini.picture = pic
    mini.read_every = 0.1
    mini.recognise_s = 0.8
    mini.recognise_setup_s = 1.5
    SETUP = {"session_kind": "cheat", "profile_id": "AB" * 32, "savestate_directory": "data/games/retroarch/states"}

    def case(tag, setup, script):
        call("POST", "/plugins/games/stop")
        call("POST", f"/plugins/games/launch?id={args['id']}")
        fake["ra"].paused = False
        m._active_cheat_session = dict(SETUP) if setup else None
        pic.set(script)
        r0 = len(h7_rows())
        S[tag + "_start"] = start()["body"]
        b = settled(5)
        time.sleep(0.3)
        rows_ = h7_rows()[r0:]
        S[tag] = {k: b.get(k) for k in ("recognised", "timeout")}
        S[tag + "_watching_recognise_s"] = [r.get("recognise_s") for r in rows_ if r["step"] == "watching"]
        S[tag + "_recognised_rows"] = [[r.get("value"), r.get("after_s")] for r in rows_ if r["step"] == "recognised"]
        call("POST", "/plugins/games/h7-stop")
        m._active_cheat_session = None

    case("setup_covered_then_start", True, ["other"] * 10 + ["start"] * 80)
    case("setup_never", True, ["other"] * 200)
    case("plain_never", False, ["other"] * 200)
    case("plain_covered_then_start", False, ["other"] * 10 + ["start"] * 80)
    call("POST", "/plugins/games/stop")

httpd.shutdown()
print(json.dumps(out))
