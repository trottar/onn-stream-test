#!/bin/sh
# B145: the board's check under Godot headless in a scratch copy of the board's tree (the repo's HEAD archived, my two
# files copied from its working tree); Godot's own folders in the scratch; everything removed after. Godot's path and
# the board's repo are read at run time (the hub's party config / the argument), never printed.
set -eu
REPO="$1"; RUNS="${2:-1}"; CHECK="${3:-res://checks/hub_minigame_check.gd}"
G=$(python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/.config/privyhub/party.json')))['godot'])")
S=$(mktemp -d -p "${TMPDIR:-/tmp}" b145_check_XXXX)
trap 'rm -rf "$S"' EXIT
mkdir -p "$S/repo" "$S/x"
git -C "$REPO" archive HEAD | tar -x -C "$S/repo"
cp "$REPO/minigames/hub_minigame.gd" "$S/repo/minigames/hub_minigame.gd"
cp "$REPO/checks/hub_minigame_check.gd" "$S/repo/checks/hub_minigame_check.gd"
export XDG_DATA_HOME="$S/x" XDG_CONFIG_HOME="$S/x" XDG_CACHE_HOME="$S/x"
timeout 300 "$G" --headless --path "$S/repo" --import >/dev/null 2>&1 || true
i=1
while [ "$i" -le "$RUNS" ]; do
  printf 'run %s: ' "$i"
  timeout 300 "$G" --headless --path "$S/repo" --script "$CHECK" 2>&1 | grep -E "CHECK: (PASS|FAIL)|  FAIL:" || echo "no verdict"
  i=$((i + 1))
done
