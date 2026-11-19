#!/bin/sh
# B164: the board's check N times in a scratch copy of the board's tree at REV (bb9dcd5: HEAD's two files before mine;
# 9a803d6 or a working copy: mine), Godot headless, Godot's own folders in the scratch (B145's wrapper's way), with a
# trace added to the scratch copy only: each go the stand-in hub takes in the three-practice scenario, each showing of
# the load screen there, and each press the stand-in screen counts as "during a practice" (whether the board's pad
# gate was in the tree then). Godot's path and the board's repo are read at run time, never printed.
# usage: b164_runs.sh <board repo> <rev | WORK> <runs> <out file> [check file to use instead of REV's]
# ALT_BOARD=<file>: a board file used instead (the scratch mutation)
set -eu
REPO="$1"; REV="$2"; RUNS="$3"; OUT="$4"; ALT="${5:-}"
G=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/privyhub/party.json')))['godot'])")
S=$(mktemp -d -p "${TMPDIR:-/tmp}" b164_check_XXXX)
trap 'rm -rf "$S"' EXIT
mkdir -p "$S/repo" "$S/x"
if [ "$REV" = "WORK" ]; then
  git -C "$REPO" archive HEAD | tar -x -C "$S/repo"
  cp "$REPO/minigames/hub_minigame.gd" "$S/repo/minigames/hub_minigame.gd"
  cp "$REPO/checks/hub_minigame_check.gd" "$S/repo/checks/hub_minigame_check.gd"
else
  git -C "$REPO" archive "$REV" | tar -x -C "$S/repo"
fi
[ -n "$ALT" ] && cp "$ALT" "$S/repo/checks/hub_minigame_check.gd"
[ -n "${ALT_BOARD:-}" ] && cp "$ALT_BOARD" "$S/repo/minigames/hub_minigame.gd"
python3 - "$S/repo/checks/hub_minigame_check.gd" <<'EOF'
import sys
p = sys.argv[1]; s = open(p).read()
pairs = [
 ("\t\t\tpads_in_practice += 1\n",
  "\t\t\tpads_in_practice += 1\n\t\t\tprint(\"TRACE counted %d ms; showings %d %s; gate in the tree %s\" % [Time.get_ticks_msec(), shows.size(), str(show_modes), str(get_tree().root.get_children().any(func(n): return n.has_method(\"restore\")))])\n"),
 ("\t\tbehind = show_modes[-1] == \"practice\"\n",
  "\t\tbehind = show_modes[-1] == \"practice\"\n\t\tprint(\"TRACE show %d ms; mode %s\" % [Time.get_ticks_msec(), show_modes[-1]])\n"),
 ("\t\t\tst[\"mode\"] = \"practice\" if path.contains(\"practice=1\") else \"play\"\n",
  "\t\t\tst[\"mode\"] = \"practice\" if path.contains(\"practice=1\") else \"play\"\n\t\t\tif scenario == \"hpractice\":\n\t\t\t\tprint(\"TRACE go taken %d ms; %s\" % [Time.get_ticks_msec(), st[\"mode\"]])\n"),
]
for old, new in pairs:
    if s.count(old) != 1:
        sys.exit("ANCHOR MISSING: " + old.strip()[:60])
    s = s.replace(old, new)
open(p, "w").write(s)
EOF
export XDG_DATA_HOME="$S/x" XDG_CONFIG_HOME="$S/x" XDG_CACHE_HOME="$S/x"
timeout 300 "$G" --headless --path "$S/repo" --import >/dev/null 2>&1 || true
: > "$OUT"
i=1
while [ "$i" -le "$RUNS" ]; do
  t0=$(date +%s)
  timeout 300 "$G" --headless --path "$S/repo" --script res://checks/hub_minigame_check.gd > "$S/run.txt" 2>&1 || true
  v=$(grep -E "CHECK: (PASS|FAIL)" "$S/run.txt" | head -1 || true)
  printf 'run %s (%ss): %s\n' "$i" "$(( $(date +%s) - t0 ))" "${v:-no verdict}" >> "$OUT"
  grep -E "  FAIL:|^TRACE" "$S/run.txt" | sed 's/^/    /' >> "$OUT" || true
  i=$((i + 1))
done
