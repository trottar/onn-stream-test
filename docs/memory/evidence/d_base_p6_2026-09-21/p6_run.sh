#!/bin/bash
# D-BASE-P6 -- one attract-mode session per encoder ARM.
#
# The arm IS whatever the encoder was started with, so the companion is
# restarted for every arm with the arm's environment and the built argv is
# captured from `native-stream-status` BEFORE the hold begins. Nothing is
# adopted: the caller restores the default and re-measures (A0').
#
# Instruments, all from D-BASE-P5 plus P6's byte counters:
#   1. frame size in packets AND payload bytes, from the relay;
#   2. the onn's /proc/net/udp6 receive-queue drops, every 2 s over adb;
#   3. the D-BASE-R5 heartbeat loss counters.
# Slices are taken BY TIMESTAMP, never by line offset (the 4 MiB rotation).
#
# usage: ARM_ENV... p6_run.sh <arm> <hold_seconds> <scratch_dir>
#   e.g. PRIVYHUB_ENC_MAX_FRAME_SIZE=40000 p6_run.sh A1 1200 /tmp/p6
set -u
REPO=/home/privyhub/Projects/onn-stream-test
ARM="$1"; HOLD="$2"; SCRATCH="$3"
TITLE=game_ps1_b0a5986638f61a11
SESSDIR="$REPO/logs/games/decoder_sessions"
HERE="$(cd "$(dirname "$0")" && pwd)"
P5="$REPO/docs/memory/evidence/d_base_p5_2026-09-21"
SOCK="$SCRATCH/socket_${ARM}.jsonl"
FRAMES="$REPO/logs/games/native_frame_sizes.jsonl"
ALPHA="$REPO/logs/games/native_video_alpha.log"
BEFORE=$(ls "$SESSDIR" | wc -l)
mkdir -p "$SCRATCH"
cd "$REPO" || exit 1

companion_pid() {
  ps -eo pid,comm,args --no-headers \
    | awk '$2=="python3" && /privyhub_service\.py/ {print $1; exit}'
}
port_busy() { ss -lnt 2>/dev/null | grep -q ':8765 '; }

echo "[$ARM] knobs: MAX_FRAME_SIZE=${PRIVYHUB_ENC_MAX_FRAME_SIZE:-unset} BUFSIZE_K=${PRIVYHUB_ENC_BUFSIZE_K:-unset} BYTE_CAP=${PRIVYHUB_FRAME_BYTE_CAP:-unset}"

# --- clean slate (D-068) -------------------------------------------------
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
  [ "${A:-False}" = "False" ] || { echo "[$ARM] FAILED: game still active"; exit 1; }
fi
OLD=$(companion_pid); [ -n "$OLD" ] && kill "$OLD"
for i in $(seq 1 15); do port_busy || break; sleep 1; done
port_busy && { echo "[$ARM] FAILED: 8765 still bound"; exit 1; }

# the arm's environment is inherited by the companion, and therefore by
# the encoder command it builds and by the relay's byte cap
nohup python3 ./companion/privyhub_service.py > "$SCRATCH/companion_${ARM}.log" 2>&1 &
NEWPID=$!
for i in $(seq 1 15); do port_busy && break; sleep 1; done
SERVING=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
[ "$SERVING" = "$NEWPID" ] || { echo "[$ARM] FAILED: serving ${SERVING:-none} != $NEWPID"; exit 1; }
echo "[$ARM] companion $NEWPID serving"

ALPHA_MARK=$( [ -f "$ALPHA" ] && wc -c < "$ALPHA" || echo 0 )

rm -f "$SOCK" "$SOCK.stop"
nohup python3 "$P5/p5_socket_sample.py" "$SOCK" 2 \
  > "$SCRATCH/socksampler_${ARM}.log" 2>&1 &
sleep 20

# --- launch --------------------------------------------------------------
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/p6chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/p6chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { touch "$SOCK.stop"; echo "[$ARM] FAILED to open stream"; exit 1; }
STATE=
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { touch "$SOCK.stop"; echo "[$ARM] FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

# --- the arm, confirmed from the running encoder, before the hold --------
curl -s "localhost:8765/plugins/games/native-stream-status" \
  > "$SCRATCH/armcheck_${ARM}.json"
python3 - "$SCRATCH/armcheck_${ARM}.json" "$ARM" "$SCRATCH/encoder_cmd_${ARM}.txt" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
cmd = d.get("encoder_command") or []
ov = d.get("encoder_overrides") or {}
open(sys.argv[3], "w").write(" ".join(cmd) + "\n")
print("[%s] encoder argv: ... %s" % (sys.argv[2], " ".join(cmd[-14:])))
print("[%s] overrides: max_frame_size=%s bufsize_kbits=%s"
      % (sys.argv[2], ov.get("max_frame_size_bytes"), ov.get("bufsize_kbits")))
fs = (d.get("fec") or {}).get("frame_sizes") or {}
print("[%s] relay byte cap under test: %s" % (sys.argv[2], fs.get("byte_cap")))
PYEOF

T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$ARM] PLAYING at $T0; holding ${HOLD}s, zero input"
sleep "$HOLD"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)

adb shell input keyevent KEYCODE_BACK
NEW=
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then NEW=$(ls -t "$SESSDIR" | head -1); break; fi
done
[ -n "$NEW" ] && cp "$SESSDIR/$NEW" "$SCRATCH/report_${ARM}.json" \
              || echo "[$ARM] WARNING: no decoder report appeared"
echo "[$ARM] report: ${NEW:-none}"

curl -s "localhost:8765/plugins/games/native-stream-status?frame_series=1" \
  > "$SCRATCH/status_${ARM}.json"

sleep 20
touch "$SOCK.stop"
sleep 5

# the encoder's own progress lines for this arm only
tail -c "+$((ALPHA_MARK + 1))" "$ALPHA" > "$SCRATCH/alpha_${ARM}.log" 2>/dev/null

python3 - "$FRAMES" "$T0" "$T1" "$SCRATCH/frames_${ARM}.jsonl" <<'PYEOF'
import json, sys, os, glob
live, t0, t1, out = sys.argv[1:5]
rows, seen = [], set()
files = sorted(glob.glob(os.path.join(
    os.path.dirname(live), "stream_log_archive", os.path.basename(live) + "*")))
files.append(live)
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
        ts = r.get("at_utc", "")
        if t0 <= ts[:19] + "Z" <= t1:
            seen.add(line)
            rows.append(r)
rows.sort(key=lambda r: r.get("t", 0))
with open(out, "w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
print("[frames] %d seconds in the session window" % len(rows))
PYEOF

python3 - "$T0" "$T1" "$SCRATCH/heartbeat_${ARM}.jsonl" <<'PYEOF'
import json, sys, glob, os
t0, t1, out = sys.argv[1:4]
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
print("[heartbeat] %d lines" % len(rows))
PYEOF

echo "$ARM $HOLD ${NEW:-none} $T0 $T1 ${PRIVYHUB_ENC_MAX_FRAME_SIZE:-none} ${PRIVYHUB_ENC_BUFSIZE_K:-none}" >> "$SCRATCH/index.txt"
echo "[$ARM] socket rounds: $(wc -l < "$SOCK")"
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
echo "[$ARM] done"
