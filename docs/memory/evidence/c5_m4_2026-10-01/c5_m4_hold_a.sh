#!/bin/bash
# C5-M4 (a) -- one hold WITHOUT a stream: the attract title launched through the companion (no client),
# unpaused through RetroArch's command port (as C5-M1/M3's offline step), the sampler for HOLD s,
# then paused and stopped. usage: c5_m4_hold_a.sh <name> <scale> <hold_s> <out_dir>
set -u
export DISPLAY=:0
NAME=$1; SCALE=$2; HOLD=$3; OUT=$4
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO=/home/privyhub/Projects/onn-stream-test
TITLE=game_ps1_b0a5986638f61a11
mkdir -p "$OUT"; cd "$REPO" || exit 1
log() { echo "[$NAME $(date -u +%H:%M:%SZ)] $*"; }
active() { curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null; }
[ "$(active)" = False ] || { log "FAILED: a game is active"; exit 1; }
"$HERE/c5_m4_source.sh" set "$SCALE" || exit 1
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" > "$OUT/launch_$NAME.json"
for i in $(seq 1 30); do sleep 1; W=$(xdotool search --onlyvisible --name '^RetroArch ' | head -1); [ -n "$W" ] && break; done
sleep 4
PORT=$(grep -oP 'network_cmd_port = "\K[0-9]+' data/games/retroarch/config/privyhub-session.cfg)
RA="python3 $HERE/ra_cmd.py $PORT"
LOGF=$(ls -t logs/games/*-$TITLE.log | head -1)
GEO=$(xdotool getwindowgeometry "$W" | grep -o "[0-9]*x[0-9]*"); S0=$($RA GET_STATUS); log "window $W $GEO; status: $S0"
case "$S0" in *PAUSED*) $RA PAUSE_TOGGLE >/dev/null;; esac
sleep 1; S1=$($RA GET_STATUS); log "status after unpause: $S1"
case "$S1" in *PLAYING*) ;; *) log "FAILED: not PLAYING"; curl -s -X POST localhost:8765/plugins/games/stop >/dev/null; exit 1;; esac
rm -f "$OUT/$NAME.stop"
python3 "$HERE/c5_m4_sampler.py" "$OUT/$NAME" --thumbs "$OUT/thumbs_$NAME" &
SP=$!
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ); log "PLAYING at $T0; holding ${HOLD}s, zero input, no stream"
sleep "$HOLD"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
touch "$OUT/$NAME.stop"; wait $SP; rm -f "$OUT/$NAME.stop"
log "status at end: $($RA GET_STATUS)"
$RA PAUSE_TOGGLE >/dev/null; sleep 1; log "status after pause: $($RA GET_STATUS)"
curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
for i in $(seq 1 20); do sleep 1; [ "$(active)" = False ] && break; done
grep -a -E 'HW render \(|Game-specific (overrides|core options)|Using resolution|Saved game-specific' "$LOGF" > "$OUT/ra_log_$NAME.txt"
log "RetroArch: $(grep -a -o 'HW render ([0-9x]*)' "$LOGF" | tail -1); $(grep -a -o 'Using resolution [0-9x]*' "$LOGF" | tail -1); game active after stop: $(active)"
echo "$NAME a $SCALE $T0 $T1 window=$GEO" >> "$OUT/index.txt"
