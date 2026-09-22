#!/bin/bash
# D-BASE-P4: one attract-mode session with the air sampler running beside it.
# No code change anywhere; the sampler is host-side and reads the onn over adb.
#
# The companion pid is selected by EXECUTABLE BASENAME, never by a command-line
# match: a /bin/bash -c wrapper containing the script text matches `ps | grep`
# exactly as it matches `pgrep -f`, and killing it takes out the shell
# (exit 144). That bit D-BASE-P3's first harness.
#
# usage: p4_run.sh <label> <hold_seconds>
set -u
REPO=/home/privyhub/Projects/onn-stream-test
SCRATCH=/tmp/claude-1000/-home-privyhub-Projects-onn-stream-test/aeea06ae-e15e-4b0d-8cfd-6f3d4f138c4f/scratchpad/p4
LABEL="$1"; HOLD="$2"
TITLE=game_ps1_b0a5986638f61a11
SESSDIR="$REPO/logs/games/decoder_sessions"
HB="$REPO/logs/games/native_stream_heartbeat.log"
BEFORE=$(ls "$SESSDIR" | wc -l)
HB_OFFSET=$( [ -f "$HB" ] && wc -l < "$HB" || echo 0 )
cd "$REPO" || exit 1

companion_pid() {
  ps -eo pid,comm,args --no-headers \
    | awk '$2=="python3" && /privyhub_service\.py/ {print $1; exit}'
}
port_busy() { ss -lnt 2>/dev/null | grep -q ':8765 '; }

# --- 1. clean start: game ended, companion fresh (D-068) ----------------
if port_busy; then
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null 2>&1
  A=
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
  [ "${A:-False}" = "False" ] || { echo "[$LABEL] FAILED: game still active"; exit 1; }
fi
OLD=$(companion_pid); [ -n "$OLD" ] && kill "$OLD"
for i in $(seq 1 15); do port_busy || break; sleep 1; done
if port_busy; then echo "[$LABEL] FAILED: 8765 still bound"; exit 1; fi

nohup python3 ./companion/privyhub_service.py > "$SCRATCH/companion_${LABEL}.log" 2>&1 &
NEWPID=$!
for i in $(seq 1 15); do port_busy && break; sleep 1; done
SERVING=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
[ "$SERVING" = "$NEWPID" ] || { echo "[$LABEL] FAILED: serving ${SERVING:-none} != $NEWPID"; exit 1; }
PACE=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['native_stream']['fec']['pacing']['configured_us'])" 2>/dev/null)
echo "[$LABEL] companion $NEWPID serving; fec pacing=$PACE (P3 knob, must be 0)"

# --- 2. sampler: 30 s before, through, 30 s after ------------------------
SAMP="$SCRATCH/air_${LABEL}.jsonl"
rm -f "$SAMP" "$SAMP.stop"
nohup python3 "$SCRATCH/p4_sample.py" "$SAMP" 10 "$SAMP.stop" \
  > "$SCRATCH/sampler_${LABEL}.log" 2>&1 &
SAMPPID=$!
echo "[$LABEL] sampler $SAMPPID up; 30 s pre-window from $(date -u +%H:%M:%S)"
sleep 30

# --- 3. open the stream through the launcher (TOOLS.md) -----------------
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/p4chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/p4chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { echo "[$LABEL] FAILED to open stream"; touch "$SAMP.stop"; exit 1; }
STATE=
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { echo "[$LABEL] FAILED to reach PLAYING (${STATE:-none})"; touch "$SAMP.stop"; exit 1; }

T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$LABEL] PLAYING at $T0; holding ${HOLD}s, zero input"
sleep "$HOLD"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)

adb shell input keyevent KEYCODE_BACK
NEW=
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    NEW=$(ls -t "$SESSDIR" | head -1)
    echo "[$LABEL] report: $NEW"
    echo "$LABEL $HOLD $NEW $T0 $T1" >> "$SCRATCH/index.txt"
    break
  fi
done
[ -n "$NEW" ] || echo "[$LABEL] WARNING: no decoder report (a session that dies is a finding)"

# --- 4. 30 s post-window, then stop sampler and harvest -----------------
echo "[$LABEL] 30 s post-window"
sleep 30
touch "$SAMP.stop"; sleep 2; kill "$SAMPPID" 2>/dev/null
echo "[$LABEL] samples: $(wc -l < "$SAMP")"
python3 "$SCRATCH/p4_harvest.py" "$LABEL" "$SCRATCH"

# heartbeat slice for this session
tail -n +$((HB_OFFSET+1)) "$HB" > "$SCRATCH/heartbeat_${LABEL}.jsonl" 2>/dev/null
echo "[$LABEL] heartbeat lines: $(wc -l < "$SCRATCH/heartbeat_${LABEL}.jsonl")"

curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
echo "[$LABEL] done"
