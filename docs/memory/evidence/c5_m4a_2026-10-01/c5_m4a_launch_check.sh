#!/bin/bash
# C5-M4A V2/V3: one launch through the companion's own route (POST /plugins/games/launch, no stream), the
# window read with xdotool, the session's RetroArch log lines kept, then POST /plugins/games/stop.
# usage: c5_m4a_launch_check.sh <name> <game_id> <out_dir>
set -u
export DISPLAY=:0
NAME=$1; ID=$2; OUT=$3; REPO=/home/privyhub/Projects/onn-stream-test
mkdir -p "$OUT"; cd "$REPO" || exit 1
active() { curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null; }
[ "$(active)" = False ] || { echo "[$NAME] FAILED: a game is active"; exit 1; }
curl -s -X POST "localhost:8765/plugins/games/launch?id=$ID" > "$OUT/launch_$NAME.json"
W=
for i in $(seq 1 40); do sleep 1; W=$(xdotool search --onlyvisible --name '^RetroArch ' | head -1); [ -n "$W" ] && break; done
sleep 8
GEO=$(xdotool getwindowgeometry "$W" 2>/dev/null | grep -o '[0-9]*x[0-9]*' | tail -1)
cp -p data/games/retroarch/config/privyhub-session.cfg "$OUT/session_cfg_$NAME.txt"
LOGF=$(ls -t logs/games/*-$ID.log | head -1)
curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
for i in $(seq 1 25); do sleep 1; [ "$(active)" = False ] && break; done
sleep 2
grep -a -E 'Override|override|core options|Core options|HW render \(|Using resolution|Set video size|windowed fullscreen|multitap|Multitap' "$LOGF" | grep -v hdcache > "$OUT/ra_log_$NAME.txt"
echo "[$NAME] window ${GEO:-none}; $(grep -a -o 'HW render ([0-9x]*)' "$LOGF" | tail -1); $(grep -a -o 'Using resolution [0-9x]*' "$LOGF" | tail -1); active after stop: $(active)" | tee -a "$OUT/launch_index.txt"
