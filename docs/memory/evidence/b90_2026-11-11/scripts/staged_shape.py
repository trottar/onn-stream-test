#!/usr/bin/env python3
"""B90's dry call (A's stage 1): the staged cheat file B90 would write for a game and the onn's picks — counts only,
nothing launched, nothing written. The cleaned list comes from the hub's own route (POST /plugins/games/cheat-catalog,
read-only), B85's expand() gives the real indexes, the companion's own `_staged_cheat_file` builds the bytes from the
cached source file (read in place). Prints no title, description, code or path.

    python3 -I -B staged_shape.py <repo> <game id> <picks, e.g. 3,7> [--port 8765] [--source 0]
"""
import hashlib, json, re, sys, urllib.request
from pathlib import Path

repo, gid, picks = Path(sys.argv[1]).resolve(), sys.argv[2], [int(x) for x in sys.argv[3].split(",") if x.strip()]
port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
source = int(sys.argv[sys.argv.index("--source") + 1]) if "--source" in sys.argv else 0
sys.path.insert(0, str(repo / "companion"))
import cheat_clean  # noqa: E402
from games import emulator_manager as em  # noqa: E402

req = urllib.request.Request(f"http://127.0.0.1:{port}/plugins/games/cheat-catalog?id={gid}", data=b"", method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    cleaned = json.loads(r.read().decode())
src = cleaned["sources"][source]
real = cheat_clean.expand(cleaned, source, picks)
manifest = json.loads((repo / "data/games/cheats.json").read_text())["games"][gid]
f = manifest["files"][source]
raw = (repo / f["local_path"]).read_bytes()
assert hashlib.sha256(raw).hexdigest().upper() == str(f["local_sha256"]).upper(), "the cached file's SHA-256 differs"
built = em.EmulatorManager._staged_cheat_file(raw, real)
text = built["bytes"].decode()
k = built["session"]["staged"]["count"]
print(json.dumps({
    "list_raw_entries": src.get("raw_count"), "list_shown": src.get("shown_count", len(src.get("entries", []))),
    "picks_sent": len(picks), "real_indexes": len(real), "staged_entries": k,
    "header_cheats_line": re.search(r"^cheats = (\d+)$", text, re.M).group(1),
    "enabled_true": len(re.findall(r"^cheat\d+_enable = true$", text, re.M)),
    "enabled_false": len(re.findall(r"^cheat\d+_enable = false$", text, re.M)),
    "descriptions": len(re.findall(r"^cheat\d+_desc = ", text, re.M)),
    "codes": len(re.findall(r"^cheat\d+_code = ", text, re.M)),
    "staged_sha256_prefix": built["session"]["staged"]["sha256"][:8],
    "pulses_bound": 2 * k + 4,
}))
