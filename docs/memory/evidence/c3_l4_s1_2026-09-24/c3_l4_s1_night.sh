#!/bin/bash
# C3-L4-S1 -- the shadow night. Derived from c3_l3a_s1_night.sh (rest step):
#   1. set PRIVYHUB_ADAPTIVE_BITRATE_MODE=shadow in the user manager (the ONLY
#      PRIVYHUB_* allowed), start t2_sample.py (10 s);
#   2. wait until >= 41 min after the last session_ended (H1 cold);
#   3. H1 20 min, H2 20 min, H3 60 min, H4 20 min: plain attract-mode holds,
#      each through c3_l4_s1_run.sh (which restarts the companion through its
#      unit and refuses to run unless the mode reads shadow and the profile is
#      the adopted one);
#   4. stop the sampler; UNSET the flag; restart the companion through its
#      unit; confirm the flag is absent from the manager AND the new MainPID's
#      environ and that adaptive_bitrate.mode reads off; tear down (game ended,
#      banner cleared) and print the profile.
# The flag is unset on EVERY exit path (trap). One hold's failure is logged
# and the night moves on. The onn's adb endpoint stays in memory only.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
RUN="$HERE/c3_l4_s1_run.sh"
UNIT=privyhub-companion
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

teardown() {
  touch "$SAMP.stop"
  systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
  systemctl --user restart "$UNIT"
  for i in $(seq 1 30); do ss -lnt 2>/dev/null | grep -q ':8765 ' && break; sleep 1; done
  sleep 2
  MP=$(systemctl --user show -p MainPID --value "$UNIT")
  log "flag unset: manager PRIVYHUB_* $(systemctl --user show-environment | grep -c '^PRIVYHUB_'); MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* in its environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c '^PRIVYHUB_')"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);r=d['audio_redundancy'];c=d['audio_cushion'];o=d['encoder_overrides'];print('[night] adaptive_bitrate',d.get('adaptive_bitrate'),'| bitrate',d.get('bitrate_kbps'),'cap',o['max_frame_size_bytes'],o['max_frame_size_source'],'cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',o['any_override'],'active',d.get('active'))"
  adb shell input keyevent KEYCODE_HOME >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/l4end.xml >/dev/null 2>&1
  log "teardown: game active $A; NOW PLAYING on the launcher: $(adb shell cat /sdcard/l4end.xml 2>/dev/null | grep -c 'NOW PLAYING')"
}
trap 'teardown; log "night done"' EXIT

[ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] || { log "FAILED: PRIVYHUB_* already set in the manager"; exit 1; }
adb_ok || { log "adb unavailable: holds NOT RUN"; exit 1; }
systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE=shadow
log "flag set in the manager: $(systemctl --user show-environment | grep '^PRIVYHUB_')"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$HERE/t2_sampler.log" 2>&1 &
log "sampler started (10 s)"
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=41)
print(int(t.timestamp()))")
log "last session_ended $LAST; H1 not before $(date -u -d @$READY +%H:%M:%SZ)"
echo "cold_start_last_session_ended $LAST" >> "$OUT/index.txt"
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
for pair in "H1 1200" "H2 1200" "H3 3600" "H4 1200"; do
  set -- $pair
  if ! adb_ok; then log "$1: adb unavailable; NOT RUN"; echo "$1 NOT_RUN adb" >> "$OUT/index.txt"; continue; fi
  log "$1 begins (${2}s)"
  "$RUN" "$1" H "$2" "$OUT"
  log "$1 harness exit $?"
done
sleep 30
