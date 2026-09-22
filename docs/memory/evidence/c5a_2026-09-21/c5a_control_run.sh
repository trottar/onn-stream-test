#!/bin/bash
# C5a: one 150 s session with four short encoder stalls at 30/60/90/120 s.
# usage: run.sh <label> <pulse_seconds>
set -u
REPO=/home/privyhub/Projects/onn-stream-test
SCRATCH=/tmp/claude-1000/-home-privyhub-Projects-onn-stream-test/a49eb391-4ee4-458f-9a04-d136c736803f/scratchpad/c5a
LABEL="CTRL"; PULSE=0
SESSDIR="$REPO/logs/games/decoder_sessions"
RECLOG="$REPO/logs/games/native_stream_recovery.log"
BEFORE=$(ls "$SESSDIR" | wc -l)
REC_OFFSET=$( [ -f "$RECLOG" ] && wc -l < "$RECLOG" || echo 0 )

# fresh start: the previous run leaves the game active-and-paused
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
sleep 4
curl -s -X POST "localhost:8765/plugins/games/launch?id=game_ps1_b0a5986638f61a11" >/dev/null
OPENED=0
for attempt in 1 2 3; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/c5achk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/c5achk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { echo "[$LABEL] FAILED to open stream"; exit 1; }
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { echo "[$LABEL] FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

pulse() {
  local R
  R=$(curl -s -X POST --max-time 15 "localhost:8765/plugins/games/c3-actuator-continuity-cycle")
  echo "[$LABEL]   actuator encoder-only restart at $(date -u +%H:%M:%S.%3N): $(echo "$R" | head -c 160)"
}

echo "[$LABEL] 150 s hold, encoder-only restarts at 30/60/90/120 s, from $(date -u +%H:%M:%S)"
sleep 30; pulse
sleep 30; pulse
sleep 30; pulse
sleep 30; pulse
sleep 30
adb shell input keyevent KEYCODE_BACK
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    NEW=$(ls -t "$SESSDIR" | head -1)
    echo "[$LABEL] report: $NEW"
    echo "$LABEL $NEW" >> "$SCRATCH/index.txt"
    break
  fi
done
echo "[$LABEL] --- recovery log lines for this run ---"
tail -n +$((REC_OFFSET+1)) "$RECLOG" 2>/dev/null | python3 -c "
import sys,json
for l in sys.stdin:
    r=json.loads(l)
    print('   ',r['at_utc'],r['event'],r.get('trigger') or '')
"
# any SIGCONT left to do
for p in $(pgrep -f "x11grab" 2>/dev/null); do kill -CONT "$p" 2>/dev/null; done
