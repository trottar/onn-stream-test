#!/bin/bash
# D-BASE-P2b: one 120 s attract session in a named arm.
# usage: session.sh <LABEL> <on|off>
set -u
REPO=/home/privyhub/Projects/onn-stream-test
S=/tmp/claude-1000/-home-privyhub-Projects-onn-stream-test/a49eb391-4ee4-458f-9a04-d136c736803f/scratchpad/p2b
LABEL="$1"; ARM="$2"
SESSDIR="$REPO/logs/games/decoder_sessions"
GAME=game_ps1_b0a5986638f61a11
APK="$S/app-hold${ARM}.apk"

BEFORE=$(ls "$SESSDIR" | wc -l)

# install the arm's build (also ends the old app process)
adb install -r "$APK" >/dev/null 2>&1 || { echo "[$LABEL] install failed"; exit 1; }

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
  adb shell uiautomator dump /sdcard/p2bchk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/p2bchk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { echo "[$LABEL] FAILED to open stream"; exit 1; }

echo "[$LABEL] arm=$ARM holding 120 s from $(date -u +%H:%M:%S)"
sleep 120
adb shell input keyevent KEYCODE_BACK

for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    NEW=$(ls -t "$SESSDIR" | head -1)
    echo "$LABEL $ARM $NEW" >> "$S/index.txt"
    echo "[$LABEL] report: $NEW"
    break
  fi
done
