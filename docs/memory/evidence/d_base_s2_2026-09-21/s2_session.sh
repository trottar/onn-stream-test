#!/bin/bash
# D-BASE-S2: one uninterrupted 3-hour attract-mode session with host-side sampling.
# usage: s2_session.sh <LABEL> [HOLD_S]
set -u
REPO=/home/privyhub/Projects/onn-stream-test
HERE="$(cd "$(dirname "$0")" && pwd)"
LABEL="$1"; HOLD="${2:-10800}"
SESSDIR="$REPO/logs/games/decoder_sessions"
RECLOG="$REPO/logs/games/native_stream_recovery.log"
HBLOG="$REPO/logs/games/native_stream_heartbeat.log"
GAME=game_ps1_b0a5986638f61a11
OUT="$HERE/$LABEL"
mkdir -p "$OUT"

BEFORE=$(ls "$SESSDIR" | wc -l)
REC_OFFSET=$( [ -f "$RECLOG" ] && wc -l < "$RECLOG" || echo 0 )
HB_OFFSET=$( [ -f "$HBLOG" ] && wc -l < "$HBLOG" || echo 0 )

# fresh session
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
sleep 4
curl -s -X POST "localhost:8765/plugins/games/launch?id=$GAME" >/dev/null

OPENED=0
for attempt in 1 2 3; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/s2chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/s2chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
if [ "$OPENED" != "1" ]; then
  echo "$LABEL FAILED_TO_OPEN" >> "$HERE/s2_index.txt"
  echo "[$LABEL] FAILED to open stream"; exit 1
fi

echo "[$LABEL] streaming from $(date -u +%H:%M:%SZ) for ${HOLD}s"
python3 "$HERE/s2_sampler.py" "$OUT/samples.jsonl" "$HOLD" &
SAMPLER=$!
sleep "$HOLD"
wait $SAMPLER 2>/dev/null

adb shell input keyevent KEYCODE_BACK
REPORT=""
for i in $(seq 1 90); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    REPORT=$(ls -t "$SESSDIR" | head -1)
    cp "$SESSDIR/$REPORT" "$OUT/"
    break
  fi
done

tail -n +$((REC_OFFSET+1)) "$RECLOG" 2>/dev/null > "$OUT/recovery_lines.jsonl"
tail -n +$((HB_OFFSET+1)) "$HBLOG" 2>/dev/null > "$OUT/heartbeat_lines.jsonl"
curl -s localhost:8765/plugins/games/status > "$OUT/status_end.json"

if [ -n "$REPORT" ]; then
  echo "$LABEL $REPORT completed" >> "$HERE/s2_index.txt"
  echo "[$LABEL] report: $REPORT"
else
  echo "$LABEL NOREPORT" >> "$HERE/s2_index.txt"
  echo "[$LABEL] NO REPORT"
fi

# teardown between sessions: end the game, leave the companion up
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
sleep 3
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
sleep 5
adb shell uiautomator dump /sdcard/s2td.xml >/dev/null 2>&1
if adb shell cat /sdcard/s2td.xml 2>/dev/null | grep -qi "NOW PLAYING"; then
  echo "[$LABEL] WARNING banner still up"
fi
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
