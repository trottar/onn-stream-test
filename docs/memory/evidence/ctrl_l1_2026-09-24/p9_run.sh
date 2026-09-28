#!/bin/bash
# D-BASE-P9 -- the deeper audio cushion, one 20-minute attract-mode session
# per arm, adopted profile, sampler OFF, heartbeat default, zero input:
#   A2  3 / 8   (PRIVYHUB_AUDIO_QUEUE_*=3/8 through the new setting)
#   B   12 / 17 (the profile default: +9 packets = +45 ms)
#   B'  12 / 24 (the handoff's literal numbers)
# Derived from d_base_p8_2026-09-22/p8_run.sh; changes: the companion is
# restarted through its systemd user unit (H3) -- never kill + nohup -- with
# the arm's cushion in the user manager's environment (set-environment,
# transient; unset by the caller); 8765 must be owned by the unit's MainPID;
# the companion log is the unit's journal for the arm.
#
# usage: TARGET=n CAPACITY=n | (unset for the profile) p9_run.sh <arm> <hold_s> <out_dir>
set -u
export DISPLAY=:0
SAMPLER="${SAMPLER:-off}"
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

echo "[$ARM] sampler=$SAMPLER heartbeat_ms=${PRIVYHUB_HEARTBEAT_MS:-default} cushion=${TARGET:-profile}/${CAPACITY:-profile}"
echo "[$ARM] env: MAX_FRAME_SIZE=${PRIVYHUB_ENC_MAX_FRAME_SIZE:-unset} BUFSIZE_K=${PRIVYHUB_ENC_BUFSIZE_K:-unset} BYTE_CAP=${PRIVYHUB_FRAME_BYTE_CAP:-unset}"
echo "[$ARM] env | grep PRIVYHUB_ENC ->"
env | grep PRIVYHUB_ENC || echo "    (nothing, as the validating run requires)"

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
UNIT=privyhub-companion
if [ -n "${TARGET:-}" ]; then
  systemctl --user set-environment PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS="$TARGET" \
    PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS="$CAPACITY"
else
  systemctl --user unset-environment PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS \
    PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS
fi
JSINCE=$(date '+%Y-%m-%d %H:%M:%S')
systemctl --user restart "$UNIT"
for i in $(seq 1 30); do port_busy && break; sleep 1; done
NEWPID=$(systemctl --user show -p MainPID --value "$UNIT")
SERVING=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
[ -n "$NEWPID" ] && [ "$SERVING" = "$NEWPID" ] || { echo "[$ARM] FAILED: serving ${SERVING:-none} != MainPID ${NEWPID:-none}"; exit 1; }
echo "[$ARM] companion MainPID $NEWPID serving 8765"
echo "[$ARM] cushion env in companion environ: $(tr '\0' '\n' < /proc/$NEWPID/environ | grep PRIVYHUB_AUDIO_QUEUE | tr '\n' ' ')"
curl -s localhost:8765/plugins/games/native-stream-status \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('[$ARM] audio_cushion', d['audio_cushion'])"

ALPHA_MARK=$( [ -f "$ALPHA" ] && wc -c < "$ALPHA" || echo 0 )

rm -f "$SOCK" "$SOCK.stop"
if [ "$SAMPLER" = "on" ]; then
  nohup python3 "$P5/p5_socket_sample.py" "$SOCK" 2 \
    > "$SCRATCH/socksampler_${ARM}.log" 2>&1 &
else
  : > "$SOCK"
fi
sleep 20

# --- launch --------------------------------------------------------------
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/p9chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/p9chk.xml | grep -q "now_playing_preview_host"; then
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
print("[%s] audio_cushion at PLAYING: %s" % (sys.argv[2], d.get("audio_cushion")))
PYEOF

python3 -c "import json;d=json.load(open('$SCRATCH/armcheck_${ARM}.json'));o=d.get('encoder_overrides',{});print('[$ARM] any_override', o.get('any_override'), 'max_frame_size', o.get('max_frame_size_bytes'), o.get('max_frame_size_source'))"

T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$ARM] PLAYING at $T0; holding ${HOLD}s, zero input"
ADBMON="$SCRATCH/adb_during_hold_${ARM}.txt"
( end=$(( $(date +%s) + HOLD )); n=0
  while [ "$(date +%s)" -lt "$end" ]; do
    ps -eo pid,args --no-headers | awk '$2 ~ /(^|\/)adb$/ && $0 !~ /fork-server/ {print}' \
      | while read -r l; do echo "$(date -u +%H:%M:%S.%N | cut -c1-12) $l"; done
    n=$((n+1)); sleep 0.5
  done; echo "# polls $n" ) > "$ADBMON" 2>&1 &
MONPID=$!
sleep "$HOLD"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
wait "$MONPID"
echo "[$ARM] adb client processes seen during hold: $(grep -vc '^#' "$ADBMON") ($(tail -1 "$ADBMON"))"

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

journalctl --user -u "$UNIT" --since "$JSINCE" --no-pager -o short-iso \
  > "$SCRATCH/companion_${ARM}.log" 2>&1
echo "$ARM $HOLD ${NEW:-none} $T0 $T1 sampler=$SAMPLER heartbeat_ms=${PRIVYHUB_HEARTBEAT_MS:-default} cushion=${TARGET:-profile}/${CAPACITY:-profile} mainpid=$NEWPID" >> "$SCRATCH/index.txt"
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
for i in $(seq 1 20); do
  sleep 1
  A=$(curl -s localhost:8765/plugins/games/status \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
  [ "$A" = "False" ] && break
done
echo "[$ARM] game active after stop: ${A:-?}"
echo "[$ARM] done"
