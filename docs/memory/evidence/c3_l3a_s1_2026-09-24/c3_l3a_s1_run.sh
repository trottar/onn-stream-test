#!/bin/bash
# C3-L3A-S1 -- the transition soak: one attract-mode session per call, the
# adopted profile, zero input, t2_sample.py running for the night (started by
# the night script, not here).
#
#   T arm: the C3.L3a probe runs during the hold, headless:
#          printf '\n' | probe --no-park <PROBE_ARGS>  -- the newline starts
#          Phase A, stdin is then at EOF and the mark reader exits (marks 0 by
#          construction). The hold is the probe's run.
#   H arm: a plain hold of <hold_s> seconds.
#
# Derived from d_base_p9_2026-09-23/p9_run.sh. Changes:
#   * no cushion argument and no set-/unset-environment at all: the adopted
#     profile only. Before the launch the script REFUSES to run if any
#     PRIVYHUB_* is in the user manager or the companion's environ, or if
#     native-stream-status does not read any_override false, cap 90000
#     (profile), cushion 12/17 (profile), redundancy 2/4 (profile);
#   * the socket sampler is gone (SAMPLER is not a parameter);
#   * T arm: waits for fresh telemetry, runs the probe with `timeout -s INT`
#     (SIGINT runs the probe's own restore), copies the probe's state file
#     the moment it returns, confirms bitrate_kbps 7000 before BACK and fires
#     one loopback transition to 7000 only if it is not;
#   * native-stream-status is saved at PLAYING (armcheck), at the end of the
#     hold before BACK (status_end), and after BACK with the frame series
#     (status), for the controller counters (item F);
#   * the adb monitor stops with the hold (a stop file), not on a timer;
#   * the index line carries the mode and the hold's start and end.
#
# usage: c3_l3a_s1_run.sh <arm> <T|H> <hold_s|probe_timeout_s> <out_dir> [probe args...]
set -u
export DISPLAY=:0
REPO=/home/privyhub/Projects/onn-stream-test
ARM="$1"; MODE="$2"; HOLD="$3"; SCRATCH="$4"; shift 4
PROBE_ARGS=("$@")
TITLE=game_ps1_b0a5986638f61a11
SESSDIR="$REPO/logs/games/decoder_sessions"
FRAMES="$REPO/logs/games/native_frame_sizes.jsonl"
ALPHA="$REPO/logs/games/native_video_alpha.log"
PSTATE="$REPO/logs/streaming/c3_l3a_gameplay_acceptance_state.json"
BEFORE=$(ls "$SESSDIR" | wc -l)
mkdir -p "$SCRATCH"
cd "$REPO" || exit 1
log() { echo "[$ARM $(date -u +%H:%M:%SZ)] $*"; }

port_busy() { ss -lnt 2>/dev/null | grep -q ':8765 '; }
game_active() {
  curl -s localhost:8765/plugins/games/status \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null
}
profile_check() {  # $1 = label; prints one line; returns non-zero unless adopted
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "
import sys, json
d = json.load(sys.stdin)
o, c, r = d['encoder_overrides'], d['audio_cushion'], d['audio_redundancy']
ok = (o.get('any_override') is False and o.get('max_frame_size_bytes') == 90000
      and o.get('max_frame_size_source') == 'profile'
      and (c['queue_target_packets'], c['queue_capacity_packets'], c['source']) == (12, 17, 'profile')
      and (r['copies'], r['offset_packets'], r['source']) == (2, 4, 'profile'))
print('[$ARM] $1: any_override', o.get('any_override'), 'cap', o.get('max_frame_size_bytes'),
      o.get('max_frame_size_source'), 'cushion', c['queue_target_packets'], c['queue_capacity_packets'],
      c['source'], 'redundancy', r['copies'], r['offset_packets'], r['source'], '->', 'ADOPTED' if ok else 'NOT ADOPTED')
sys.exit(0 if ok else 1)"
}

log "mode=$MODE hold/timeout=${HOLD}s probe_args=${PROBE_ARGS[*]:-none} heartbeat_ms=${PRIVYHUB_HEARTBEAT_MS:-default}"

# --- the adopted profile, nothing in the environment ----------------------
MGR=$(systemctl --user show-environment | grep -c '^PRIVYHUB_')
[ "$MGR" = 0 ] || { log "FAILED: $MGR PRIVYHUB_* in the user manager"; exit 1; }

# --- clean slate (D-068) -------------------------------------------------
if port_busy; then
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null 2>&1
  A=
  for i in $(seq 1 20); do
    sleep 1; A=$(game_active); [ "$A" = "False" ] && break
  done
  [ "${A:-False}" = "False" ] || { log "FAILED: game still active"; exit 1; }
fi
UNIT=privyhub-companion
JSINCE=$(date '+%Y-%m-%d %H:%M:%S')
systemctl --user restart "$UNIT"
for i in $(seq 1 30); do port_busy && break; sleep 1; done
sleep 2
NEWPID=$(systemctl --user show -p MainPID --value "$UNIT")
SERVING=$(ss -lntp 2>/dev/null | grep ':8765 ' | grep -oP 'pid=\K[0-9]+' | head -1)
[ -n "$NEWPID" ] && [ "$SERVING" = "$NEWPID" ] || { log "FAILED: serving ${SERVING:-none} != MainPID ${NEWPID:-none}"; exit 1; }
ENVN=$(tr '\0' '\n' < /proc/$NEWPID/environ | grep -c '^PRIVYHUB_')
log "companion MainPID $NEWPID serving 8765; PRIVYHUB_* in its environ: $ENVN"
[ "$ENVN" = 0 ] || { log "FAILED: PRIVYHUB_* in the companion environ"; exit 1; }
profile_check "before launch" || { log "FAILED: profile not as adopted"; exit 1; }

ALPHA_MARK=$( [ -f "$ALPHA" ] && wc -c < "$ALPHA" || echo 0 )
sleep 20

# --- launch --------------------------------------------------------------
curl -s -X POST "localhost:8765/plugins/games/launch?id=$TITLE" >/dev/null
OPENED=0
for attempt in 1 2; do
  adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 7
  adb shell uiautomator dump /sdcard/s1chk.xml >/dev/null 2>&1
  if adb shell cat /sdcard/s1chk.xml | grep -q "now_playing_preview_host"; then
    adb shell input tap 1008 298
    sleep 3
    TOP=$(adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity)
    case "$TOP" in *NativeStreamActivity*) OPENED=1; break;; esac
  fi
done
[ "$OPENED" = "1" ] || { log "FAILED to open stream"; exit 1; }
STATE=
for i in $(seq 1 45); do
  sleep 1
  STATE=$(curl -s localhost:8765/plugins/games/status \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['recovery']['state'])" 2>/dev/null)
  [ "$STATE" = "PLAYING" ] && break
done
[ "${STATE:-}" = "PLAYING" ] || { log "FAILED to reach PLAYING (${STATE:-none})"; exit 1; }

curl -s "localhost:8765/plugins/games/native-stream-status" > "$SCRATCH/armcheck_${ARM}.json"
python3 -c "import json;d=json.load(open('$SCRATCH/armcheck_${ARM}.json'));open('$SCRATCH/encoder_cmd_${ARM}.txt','w').write(' '.join(d.get('encoder_command') or [])+'\n')"
profile_check "at PLAYING" || log "WARNING: profile not as adopted at PLAYING"

ADBMON="$SCRATCH/adb_during_hold_${ARM}.txt"
rm -f "$ADBMON.stop"
( n=0
  while [ ! -f "$ADBMON.stop" ]; do
    ps -eo pid,args --no-headers | awk '$2 ~ /(^|\/)adb$/ && $0 !~ /fork-server/ {print}' \
      | while read -r l; do echo "$(date -u +%H:%M:%S.%N | cut -c1-12) $l"; done
    n=$((n+1)); sleep 0.5
  done; echo "# polls $n" ) > "$ADBMON" 2>&1 &
MONPID=$!

PRC=
if [ "$MODE" = "T" ]; then
  FRESH=
  for i in $(seq 1 30); do
    FRESH=$(curl -s localhost:8765/diagnostics/stream-telemetry \
        | python3 -c "import sys,json;print(json.load(sys.stdin).get('fresh'))" 2>/dev/null)
    [ "$FRESH" = "True" ] && break; sleep 1
  done
  log "telemetry fresh before the probe: ${FRESH:-?}"
  T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  log "PLAYING; probe starts at $T0 (timeout ${HOLD}s, SIGINT), zero input"
  STARTED_EPOCH=$(date +%s)
  printf '\n' | timeout -s INT "$HOLD" python3 tools/probe_c3_l3a_gameplay_acceptance.py \
      "${PROBE_ARGS[@]}" > "$SCRATCH/probe_${ARM}.log" 2>&1
  PRC=$?
  T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  if [ -f "$PSTATE" ] && [ "$(stat -c %Y "$PSTATE")" -ge "$STARTED_EPOCH" ]; then
    cp -p "$PSTATE" "$SCRATCH/state_${ARM}.json"
    log "probe exit $PRC; state copied ($(sha256sum "$SCRATCH/state_${ARM}.json" | cut -c1-16)...)"
  else
    log "probe exit $PRC; NO new state file"
  fi
  BR=$(curl -s localhost:8765/plugins/games/native-stream-status \
       | python3 -c "import sys,json;print(json.load(sys.stdin).get('bitrate_kbps'))" 2>/dev/null)
  if [ "$BR" != "7000" ]; then
    log "bitrate $BR after the probe; one loopback transition to 7000"
    curl -s -X POST "localhost:8765/plugins/games/c3-validated-bitrate-transition?target=7000" > "$SCRATCH/restore_${ARM}.json"
    BR=$(curl -s localhost:8765/plugins/games/native-stream-status \
         | python3 -c "import sys,json;print(json.load(sys.stdin).get('bitrate_kbps'))" 2>/dev/null)
  fi
  log "bitrate before BACK: $BR"
else
  T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  log "PLAYING at $T0; holding ${HOLD}s, zero input"
  sleep "$HOLD"
  T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
fi
touch "$ADBMON.stop"; wait "$MONPID"; rm -f "$ADBMON.stop"
log "adb client processes seen during hold: $(grep -vc '^#' "$ADBMON") ($(tail -1 "$ADBMON"))"
curl -s "localhost:8765/plugins/games/native-stream-status" > "$SCRATCH/status_end_${ARM}.json"

adb shell input keyevent KEYCODE_BACK
NEW=
for i in $(seq 1 30); do
  sleep 1
  AFTER=$(ls "$SESSDIR" | wc -l)
  if [ "$AFTER" -gt "$BEFORE" ]; then NEW=$(ls -t "$SESSDIR" | head -1); break; fi
done
[ -n "$NEW" ] && cp -p "$SESSDIR/$NEW" "$SCRATCH/report_${ARM}.json" \
              || log "WARNING: no decoder report appeared"
log "report: ${NEW:-none}"

curl -s "localhost:8765/plugins/games/native-stream-status?frame_series=1" > "$SCRATCH/status_${ARM}.json"
sleep 20

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
  | sed -E 's/\b(10\.[0-9]{1,3}|192\.168|172\.(1[6-9]|2[0-9]|3[01]))\.[0-9]{1,3}\.[0-9]{1,3}\b/<IP_REDACTED>/g; s/\b(169\.254)\.[0-9]{1,3}\.[0-9]{1,3}\b/<IP_REDACTED>/g; s/\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b/<MAC_REDACTED>/g' \
  > "$SCRATCH/companion_${ARM}.log" 2>&1
echo "$ARM $MODE $HOLD ${NEW:-none} $T0 $T1 probe_exit=${PRC:-na} mainpid=$NEWPID" >> "$SCRATCH/index.txt"
curl -s -X POST "localhost:8765/plugins/games/stop" >/dev/null
for i in $(seq 1 20); do
  sleep 1; A=$(game_active); [ "$A" = "False" ] && break
done
log "game active after stop: ${A:-?}"
log "done"
