#!/bin/bash
# O1 -- one attract-mode session with the Opal air sampler running 60 s
# before and 60 s after it. Zero input. Read-only on the Opal throughout.
#
# The heartbeat slice is taken by TIMESTAMP, never by line offset: the log
# rotates at 4 MiB mid-session (D-BASE-R5), which makes an offset-based
# slice come back empty. Both the live log and the archive are read and
# filtered on `received_at_utc` inside the session window.
#
# usage: o1_run.sh <label> <hold_seconds> <scratch_dir>
set -u
REPO=/home/privyhub/Projects/onn-stream-test
LABEL="$1"; HOLD="$2"; SCRATCH="$3"
TITLE=game_ps1_b0a5986638f61a11
SESSDIR="$REPO/logs/games/decoder_sessions"
HERE="$(cd "$(dirname "$0")" && pwd)"
AIR="$SCRATCH/air_${LABEL}.jsonl"
BEFORE=$(ls "$SESSDIR" | wc -l)
mkdir -p "$SCRATCH"
cd "$REPO" || exit 1

companion_pid() {
  ps -eo pid,comm,args --no-headers \
    | awk '$2=="python3" && /privyhub_service\.py/ {print $1; exit}'
}
port_busy() { ss -lnt 2>/dev/null | grep -q ':8765 '; }

# --- clean slate ---------------------------------------------------------
if port_busy; then
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null 2>&1
  A=
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
  [ "${A:-False}" = "False" ] || { echo "[$LABEL] FAILED: game still active"; exit 1; }
fi
OLD=$(companion_pid); [ -n "$OLD" ] && kill "$OLD"
for i in $(seq 1 15); do port_busy || break; sleep 1; done
port_busy && { echo "[$LABEL] FAILED: 8765 still bound"; exit 1; }

nohup python3 ./companion/privyhub_service.py > "$SCRATCH/companion_${LABEL}.log" 2>&1 &
NEWPID=$!
for i in $(seq 1 15); do port_busy && break; sleep 1; done
SERVING=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
[ "$SERVING" = "$NEWPID" ] || { echo "[$LABEL] FAILED: serving ${SERVING:-none} != $NEWPID"; exit 1; }
echo "[$LABEL] companion $NEWPID serving"

# --- sampler up first, so it covers the 60 s before the stream -----------
rm -f "$AIR" "$AIR.stop"
nohup "$HERE/o1_opal_sample.sh" "$AIR" 10 wlan1 > "$SCRATCH/sampler_${LABEL}.log" 2>&1 &
echo "[$LABEL] sampler up; 60 s of quiet-link baseline"
sleep 60

# --- launch --------------------------------------------------------------
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/o1chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/o1chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { touch "$AIR.stop"; echo "[$LABEL] FAILED to open stream"; exit 1; }
STATE=
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { touch "$AIR.stop"; echo "[$LABEL] FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$LABEL] PLAYING at $T0; holding ${HOLD}s, zero input"
sleep "$HOLD"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# --- end the session, keep sampling 60 s past it -------------------------
adb shell input keyevent KEYCODE_BACK
NEW=
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then NEW=$(ls -t "$SESSDIR" | head -1); break; fi
done
[ -n "$NEW" ] && cp "$SESSDIR/$NEW" "$SCRATCH/report_${LABEL}.json" \
              || echo "[$LABEL] WARNING: no decoder report appeared"
echo "[$LABEL] report: ${NEW:-none}"
sleep 60
touch "$AIR.stop"
sleep 15

# --- heartbeat slice, by timestamp ---------------------------------------
python3 - "$T0" "$T1" "$SCRATCH/heartbeat_${LABEL}.jsonl" <<'PYEOF'
import json, sys, glob, os
t0, t1, out = sys.argv[1], sys.argv[2], sys.argv[3]
repo = "/home/privyhub/Projects/onn-stream-test"
files = sorted(glob.glob(repo + "/logs/games/stream_log_archive/native_stream_heartbeat.log*"))
files.append(repo + "/logs/games/native_stream_heartbeat.log")
rows, seen = [], set()
for f in files:
    if not os.path.exists(f):
        continue
    for line in open(f, errors="replace"):
        line = line.strip()
        if not line or line in seen:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = r.get("received_at_utc", "")
        if "lost_packets" in r and t0 <= ts[:19] + "Z" <= t1:
            seen.add(line)
            rows.append(r)
rows.sort(key=lambda r: r["elapsed_ms"])
with open(out, "w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
print("[heartbeat] %d lines %s .. %s" % (
    len(rows), rows[0]["received_at_utc"] if rows else "-",
    rows[-1]["received_at_utc"] if rows else "-"))
PYEOF

echo "$LABEL $HOLD ${NEW:-none} $T0 $T1" >> "$SCRATCH/index.txt"
echo "[$LABEL] air rounds: $(wc -l < "$AIR")"
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
echo "[$LABEL] done"
