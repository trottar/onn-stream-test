#!/bin/bash
# C3-L3A-S1 -- the night. Two steps, so T0's headless check is read before
# the night is spent:
#
#   c3_l3a_s1_night.sh t0     start t2_sample.py (10 s) if it is not running,
#                             then T0 (probe smoke, 2 traversals, no park)
#   c3_l3a_s1_night.sh rest   wait until >= 41 min after the last
#                             session_ended (T1 cold), then T1 H1 T2 H2 T3 H3,
#                             each T finalized at once, then stop the sampler
#                             and tear down (companion left under systemd)
#
# H holds are the preceding T's Phase A length (phase_a_end_s, rounded).
# One session's failure is logged and the night moves on. The onn's adb
# endpoint is held in this process's memory only and never printed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
RUN="$HERE/c3_l3a_s1_run.sh"
PROBE="$REPO/tools/probe_c3_l3a_gameplay_acceptance.py"
log() { echo "[night $(date -u +%H:%M:%SZ)] $*"; }
cd "$REPO" || exit 1

ONN=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
adb_ok() {
  adb devices | awk 'NR>1 && $2=="device"' | grep -q . && return 0
  [ -n "$ONN" ] || return 1
  log "adb: no device; one reconnect"
  adb connect "$ONN" >/dev/null 2>&1; sleep 3
  adb devices | awk 'NR>1 && $2=="device"' | grep -q .
}

sampler_running() { pgrep -f "t2_sample.py $SAMP" >/dev/null; }
start_sampler() {
  if sampler_running; then log "sampler already running"; return; fi
  rm -f "$SAMP.stop"
  nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$HERE/t2_sampler.log" 2>&1 &
  log "sampler started (10 s)"
}

finalize_t() {  # $1 = arm
  local arm="$1" st="$OUT/state_$1.json" rep="$OUT/report_$1.json" dir="$OUT/finalize_$1"
  [ -f "$st" ] && [ -f "$rep" ] || { log "$arm: no state or report; finalize skipped"; return; }
  mkdir -p "$dir"
  local rid; rid=$(python3 -c "import json;print(json.load(open('$st'))['run_id'])")
  python3 "$PROBE" --finalize --state "$st" --decoder "$rep" > "$dir/finalize_stdout.txt" 2>&1
  log "$arm finalize exit $? (run $rid)"
  for f in "$REPO/logs/streaming/c3_l3a_runs/$rid.json" "$REPO/logs/streaming/c3_l3a_runs/$rid.txt"; do
    [ -f "$f" ] && mv "$f" "$dir/"
  done
  log "$arm c3_l3a_runs files left: $(find "$REPO/logs/streaming/c3_l3a_runs" -type f | wc -l)"
}

run_session() {  # arm mode hold [probe args]  (out_dir inserted in position 4)
  local arm="$1" mode="$2" hold="$3"; shift 3
  adb_ok || { log "$arm: adb unavailable; session NOT RUN"; echo "$arm NOT_RUN adb" >> "$OUT/index.txt"; return 1; }
  log "$arm ($mode) begins"
  "$RUN" "$arm" "$mode" "$hold" "$OUT" "$@"
  local rc=$?
  log "$arm ($mode) harness exit $rc"
  [ "$mode" = T ] && finalize_t "$arm"
  return $rc
}

phase_a_of() {  # arm -> seconds, or empty
  python3 -c "import json;print(round(json.load(open('$OUT/state_$1.json'))['phase_a_end_s']))" 2>/dev/null
}

case "${1:-}" in
t0)
  [ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] || { log "FAILED: PRIVYHUB_* set in the manager"; exit 1; }
  adb_ok || { log "adb unavailable: task NOT RUN"; exit 1; }
  start_sampler
  run_session T0 T 600 --traversals 2 --dwell-min 40 --dwell-max 50 --no-park
  log "T0 step done"
  ;;
rest)
  start_sampler
  LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
         | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
  READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=41)
print(int(t.timestamp()))")
  log "last session_ended $LAST; T1 not before $(date -u -d @$READY +%H:%M:%SZ)"
  echo "cold_start_last_session_ended $LAST" >> "$OUT/index.txt"
  while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
  for pair in "T1 H1" "T2 H2" "T3 H3"; do
    set -- $pair
    run_session "$1" T 1500 --traversals 10 --no-park
    HOLD=$(phase_a_of "$1")
    if [ -z "$HOLD" ]; then
      HOLD=840
      log "$2: no Phase A length from $1; holding the planned ${HOLD}s"
    fi
    run_session "$2" H "$HOLD"
  done
  sleep 30; touch "$SAMP.stop"; sleep 12
  log "sampler rows $(wc -l < "$SAMP")"
  # --- teardown: game ended, banner cleared, companion left under systemd ---
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
  adb shell input keyevent KEYCODE_HOME >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/s1end.xml >/dev/null 2>&1
  BANNER=$(adb shell cat /sdcard/s1end.xml 2>/dev/null | grep -c "NOW PLAYING")
  MP=$(systemctl --user show -p MainPID --value privyhub-companion)
  log "teardown: game active $A; NOW PLAYING on the launcher: $BANNER; MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c '^PRIVYHUB_') manager $(systemctl --user show-environment | grep -c '^PRIVYHUB_')"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);r=d['audio_redundancy'];c=d['audio_cushion'];o=d['encoder_overrides'];print('[night] bitrate',d.get('bitrate_kbps'),'cap',o['max_frame_size_bytes'],o['max_frame_size_source'],'cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',o['any_override'])"
  log "night done"
  ;;
*)
  echo "usage: $0 t0|rest"; exit 2;;
esac
