#!/bin/bash
# B2: host wired directly into the Opal. One attract-mode session of the PS1
# reference title, 120 s, zero input, BACK to end.
# usage: b2_run.sh <label> <clean|pulse>
#   pulse = a single 3 s SIGSTOP/SIGCONT on the x11grab encoder at 60 s
#           (D-BASE-R3a G3 method: STOP re-applied every 200 ms, then CONT)
set -u
REPO=/home/privyhub/Projects/onn-stream-test
SCRATCH=/tmp/claude-1000/-home-privyhub-Projects-onn-stream-test/aeea06ae-e15e-4b0d-8cfd-6f3d4f138c4f/scratchpad/b2
LABEL="$1"; MODE="${2:-clean}"
TITLE=game_ps1_b0a5986638f61a11
SESSDIR="$REPO/logs/games/decoder_sessions"
RECLOG="$REPO/logs/games/native_stream_recovery.log"
BEFORE=$(ls "$SESSDIR" | wc -l)
REC_OFFSET=$( [ -f "$RECLOG" ] && wc -l < "$RECLOG" || echo 0 )

# fresh start: a prior run leaves the game active-and-paused, and a launch
# for the same title is then a no-op (TOOLS.md)
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
for i in $(seq 1 20); do
  sleep 1
  A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
  [ "$A" = "False" ] && break
done
[ "${A:-}" = "False" ] || { echo "[$LABEL] FAILED: game still active before launch"; exit 1; }

curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do            # never retry a failing action more than twice
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/b2chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/b2chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { echo "[$LABEL] FAILED to open stream"; exit 1; }

STATE=
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { echo "[$LABEL] FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

T0=$(date -u +%H:%M:%S)
if [ "$MODE" = "pulse" ]; then
  echo "[$LABEL] 120 s hold, single 3 s encoder stall at 60 s, from $T0"
  sleep 60
  PIDS=$(pgrep -f "x11grab" 2>/dev/null)
  echo "[$LABEL]   STOP at $(date -u +%H:%M:%S.%3N) pids: $(echo $PIDS | tr '\n' ' ')"
  END=$(( $(date +%s%3N) + 3000 ))
  while [ "$(date +%s%3N)" -lt "$END" ]; do
    for p in $PIDS; do kill -STOP "$p" 2>/dev/null; done
    sleep 0.2
  done
  for p in $PIDS; do kill -CONT "$p" 2>/dev/null; done
  echo "[$LABEL]   CONT at $(date -u +%H:%M:%S.%3N)"
  sleep 57
else
  echo "[$LABEL] 120 s hold, zero input, from $T0"
  sleep 120
fi

adb shell input keyevent KEYCODE_BACK
NEW=
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    NEW=$(ls -t "$SESSDIR" | head -1)
    echo "[$LABEL] report: $NEW"
    echo "$LABEL $MODE $NEW" >> "$SCRATCH/index.txt"
    break
  fi
done
[ -n "$NEW" ] || echo "[$LABEL] WARNING: no decoder report appeared"

echo "[$LABEL] --- recovery log lines for this run ---"
tail -n +$((REC_OFFSET+1)) "$RECLOG" 2>/dev/null | python3 -c "
import sys,json
for l in sys.stdin:
    try:
        r=json.loads(l)
    except Exception:
        continue
    print('   ',r.get('at_utc'),r.get('event'),r.get('trigger') or '')
"
# leave nothing stopped, and leave the game stopped for the next session
for p in $(pgrep -f "x11grab" 2>/dev/null); do kill -CONT "$p" 2>/dev/null; done
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
echo "[$LABEL] done"
