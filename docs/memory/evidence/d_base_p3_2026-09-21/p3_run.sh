#!/bin/bash
# D-BASE-P3: one attract-mode session of the PS1 reference title, 120 s,
# zero input, with the relay's sender pacer at <pacing_us> (0 = off).
# The companion is restarted for every session because the knob is read from
# the environment at relay start (D-068: a stale process is not evidence).
#
# The companion pid is selected by EXECUTABLE BASENAME, never by a command
# line match: a /bin/bash -c wrapper whose text contains the script name
# matches a `ps | grep` just as it matches `pgrep -f`, and killing it takes
# out the shell (exit 144). This bit the first draft of this harness.
#
# usage: p3_run.sh <label> <pacing_us>
set -u
REPO=/home/privyhub/Projects/onn-stream-test
SCRATCH=/tmp/claude-1000/-home-privyhub-Projects-onn-stream-test/aeea06ae-e15e-4b0d-8cfd-6f3d4f138c4f/scratchpad/p3
LABEL="$1"; PACING="$2"
TITLE=game_ps1_b0a5986638f61a11
SESSDIR="$REPO/logs/games/decoder_sessions"
BEFORE=$(ls "$SESSDIR" | wc -l)
cd "$REPO" || exit 1

companion_pid() {
  ps -eo pid,comm,args --no-headers \
    | awk '$2=="python3" && /privyhub_service\.py/ {print $1; exit}'
}

port_busy() { ss -lnt 2>/dev/null | grep -q ':8765 '; }

# --- 1. end any game, then replace the companion with one on this arm ----
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

OLD=$(companion_pid)
if [ -n "$OLD" ]; then kill "$OLD"; fi
for i in $(seq 1 15); do port_busy || break; sleep 1; done
if port_busy; then echo "[$LABEL] FAILED: 8765 still bound"; exit 1; fi

PRIVYHUB_FEC_PACING_US="$PACING" nohup python3 ./companion/privyhub_service.py \
  > "$SCRATCH/companion_${LABEL}.log" 2>&1 &
NEWPID=$!
for i in $(seq 1 15); do port_busy && break; sleep 1; done
SERVING=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
if [ "$SERVING" != "$NEWPID" ]; then
  echo "[$LABEL] FAILED: serving pid ${SERVING:-none} != launched $NEWPID"; exit 1
fi
CONF=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['native_stream']['fec']['pacing']['configured_us'])" 2>/dev/null)
if [ "$CONF" != "$PACING" ]; then
  echo "[$LABEL] FAILED: relay reports pacing ${CONF:-none}, wanted $PACING"; exit 1
fi
echo "[$LABEL] companion pid $NEWPID serving, PRIVYHUB_FEC_PACING_US=$CONF"

# --- 2. open the stream through the launcher (TOOLS.md) ------------------
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/p3chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/p3chk.xml | grep -q "now_playing_preview_host"; then
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

# --- 3. hold, capture the relay while it still runs, then BACK ----------
echo "[$LABEL] 120 s hold, zero input, from $(date -u +%H:%M:%S)"
sleep 120
curl -s localhost:8765/plugins/games/native-stream-status \
  > "$SCRATCH/relay_${LABEL}.json" 2>/dev/null
python3 - "$SCRATCH/relay_${LABEL}.json" "$LABEL" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
n = d.get("native_stream", d)
f = n.get("fec", {}); p = f.get("pacing", {})
print(f"[{sys.argv[2]}]   relay rtp={f.get('rtp_packets')} parity={f.get('parity_packets')} "
      f"errs={f.get('send_errors')} send_call_max_us={f.get('send_call_max_us')}")
print(f"[{sys.argv[2]}]   pacing enabled={p.get('enabled')} cfg={p.get('configured_us')} "
      f"p50={p.get('achieved_spacing_p50_us')} p99={p.get('achieved_spacing_p99_us')} "
      f"clamped={p.get('clamped_frames')} late={p.get('late_frames')} "
      f"maxq={p.get('max_queue_depth')} start_delay_max_us={p.get('max_start_delay_us')}")
PY

adb shell input keyevent KEYCODE_BACK
NEW=
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then
    NEW=$(ls -t "$SESSDIR" | head -1)
    echo "[$LABEL] report: $NEW"
    echo "$LABEL $PACING $NEW" >> "$SCRATCH/index.txt"
    break
  fi
done
[ -n "$NEW" ] || echo "[$LABEL] WARNING: no decoder report appeared"

# --- 4. first-30 s discontinuity screen ---------------------------------
if [ -n "$NEW" ]; then
  python3 - "$SESSDIR/$NEW" "$LABEL" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))["report"]
disc = r.get("stream_discontinuities") or []
early = [d for d in disc if d.get("elapsed_ms", 10**9) < 30000]
print(f"[{sys.argv[2]}]   discontinuities={len(disc)} in_first_30s={len(early)}"
      + ("  -> REJECT, re-run" if early else "  -> accept"))
PY
fi

curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
echo "[$LABEL] done"
