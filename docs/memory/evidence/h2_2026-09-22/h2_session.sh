#!/bin/bash
# H2 check 3: one attract-mode session of the PS1 reference title, 120 s,
# zero input, BACK to end, on the headless host (DisplayPort dummy plug).
# Same open/hold/close shape as b2_2026-09-21/b2_run.sh and
# d_base_t1_2026-09-21/t1_session.sh; additionally saves
# native-stream-status mid-session (capture_target, encoder_overrides).
# usage: h2_session.sh <LABEL> [HOLD_S]
set -u
REPO=/home/privyhub/Projects/onn-stream-test
HERE="$(cd "$(dirname "$0")" && pwd)"
LABEL="$1"; HOLD="${2:-120}"
SESSDIR="$REPO/logs/games/decoder_sessions"
RECLOG="$REPO/logs/games/native_stream_recovery.log"
HBLOG="$REPO/logs/games/native_stream_heartbeat.log"
SAMPLE_LOG="$REPO/logs/games/host_resource_samples.jsonl"
VLOG="$REPO/logs/games/native_video_alpha.log"
GAME=game_ps1_b0a5986638f61a11
OUT="$HERE/$LABEL"
mkdir -p "$OUT"

BEFORE=$(ls "$SESSDIR" | wc -l)
off() { [ -f "$1" ] && wc -l < "$1" || echo 0; }
REC_OFFSET=$(off "$RECLOG"); HB_OFFSET=$(off "$HBLOG")
SAMPLE_OFFSET=$(off "$SAMPLE_LOG"); V_OFFSET=$(off "$VLOG")

# fresh start: a prior run leaves the game active-and-paused (TOOLS.md)
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
A=
for i in $(seq 1 20); do
  sleep 1
  A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
  [ "$A" = "False" ] && break
done
[ "${A:-}" = "False" ] || { echo "[$LABEL] FAILED: game still active before launch"; exit 1; }

curl -s -X POST "localhost:8765/plugins/games/launch?id=$GAME" >/dev/null
OPENED=0
for attempt in 1 2; do            # never retry a failing action more than twice
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/h2chk.xml >/dev/null 2>&1
  # The R3b N150 recovery save is kept on disk on purpose (R3c); the launcher
  # raises its prompt over the preview. BACK fires the dialog's cancel
  # listener, which only hides it -- no recovery action is requested.
  if adb shell cat /sdcard/h2chk.xml | grep -q 'text="Recovery Save"'; then
    echo "[$LABEL] recovery prompt up; dismissing with BACK (no action)"
    adb shell input keyevent KEYCODE_BACK >/dev/null 2>&1
    sleep 2
    adb shell uiautomator dump /sdcard/h2chk.xml >/dev/null 2>&1
  fi
  if adb shell cat /sdcard/h2chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { echo "$LABEL FAILED_TO_OPEN" >> "$HERE/h2_index.txt"; echo "[$LABEL] FAILED to open stream"; exit 1; }

STATE=
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { echo "[$LABEL] FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

echo "[$LABEL] ${HOLD} s hold, zero input, from $(date -u +%H:%M:%SZ)"
sleep 30
curl -s localhost:8765/plugins/games/native-stream-status > "$OUT/native_stream_status_mid.json"
sleep $((HOLD - 30))

adb shell input keyevent KEYCODE_BACK
REPORT=
for i in $(seq 1 60); do
  sleep 1
  if [ "$(ls "$SESSDIR" | wc -l)" -gt "$BEFORE" ]; then
    REPORT=$(ls -t "$SESSDIR" | head -1); cp "$SESSDIR/$REPORT" "$OUT/"; break
  fi
done

tail -n +$((REC_OFFSET+1)) "$RECLOG" 2>/dev/null > "$OUT/recovery_lines.jsonl"
tail -n +$((HB_OFFSET+1)) "$HBLOG" 2>/dev/null > "$OUT/heartbeat_lines.jsonl"
tail -n +$((SAMPLE_OFFSET+1)) "$SAMPLE_LOG" 2>/dev/null > "$OUT/host_resource_samples.jsonl"
tail -n +$((V_OFFSET+1)) "$VLOG" 2>/dev/null | sed -E 's/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/<IP_REDACTED>/g' > "$OUT/native_video_alpha_lines.log"
if [ -n "$REPORT" ]; then
  echo "$LABEL $REPORT completed" >> "$HERE/h2_index.txt"; echo "[$LABEL] report: $REPORT"
else
  echo "$LABEL NOREPORT" >> "$HERE/h2_index.txt"; echo "[$LABEL] NO REPORT"
fi

# teardown: end the game, clear the launcher banner, leave the companion up
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
sleep 3
curl -s localhost:8765/plugins/games/status > "$OUT/status_end.json"
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
sleep 5
adb shell uiautomator dump /sdcard/h2td.xml >/dev/null 2>&1
if adb shell cat /sdcard/h2td.xml 2>/dev/null | grep -qi "NOW PLAYING"; then
  echo "[$LABEL] WARNING banner still up"
else
  echo "[$LABEL] banner clear"
fi
adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
echo "[$LABEL] done"
