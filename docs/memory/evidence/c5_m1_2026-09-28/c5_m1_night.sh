#!/bin/bash
# C5-M1 step 4 -- six 20-minute attract-mode holds, strictly alternating
# B (adopted 720p60, selector unset) / A (1080p60 candidate, selector set):
# B1 A1 B2 A2 B3 A3. Each hold through c5_m1_run.sh (companion restarted
# through its unit with the selector set or unset; any_override and the
# profile fields checked before launch and at PLAYING). T2 sampler at 10 s.
# The first hold starts >= 41 min after the last session_ended.
# Derived from c4_m1_night.sh. No arm APK was built (the design, 1e): the
# adopted APK's device hash is checked at the start and the end, and it is
# reinstalled only if the hash differs.
# Teardown on EVERY exit path (trap): selector unset in the manager, companion
# restarted and the selector confirmed absent from its environ, adopted APK
# confirmed, game stopped, banner cleared, sampler stopped.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
ADOPTED_APK="$REPO/runtime/c4_m1/adopted_app-debug.apk"
ADOPTED_SHA=f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7
UNIT=privyhub-companion
log() { echo "[night $(date -u +%H:%M:%SZ)] $*"; }
cd "$REPO" || exit 1
ONN=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
adb_ok() {
  adb devices | awk 'NR>1 && $2=="device"' | grep -q . && return 0
  [ -n "$ONN" ] || return 1
  log "adb: no device; one reconnect"; adb connect "$ONN" >/dev/null 2>&1; sleep 3
  adb devices | awk 'NR>1 && $2=="device"' | grep -q .
}
teardown() {
  touch "$SAMP.stop"
  systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID PRIVYHUB_FEC_SCHEME
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
  systemctl --user restart "$UNIT"
  for i in $(seq 1 30); do ss -lnt 2>/dev/null | grep -q ':8765 ' && break; sleep 1; done; sleep 2
  MP=$(systemctl --user show -p MainPID --value "$UNIT")
  log "selector unset: manager PRIVYHUB_* $(systemctl --user show-environment | grep -c '^PRIVYHUB_'); MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* in its environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c '^PRIVYHUB_')"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);o=d['encoder_overrides'];c=d['audio_cushion'];r=d['audio_redundancy'];print('[night] profile',d.get('profile_id'),d.get('width'),d.get('height'),(d.get('profile_selection') or {}).get('source'),'| fec',d['fec'].get('version'),'| bitrate',d.get('bitrate_kbps'),'cap',o['max_frame_size_bytes'],o['max_frame_size_source'],'cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',o['any_override'],'active',d.get('active'),'adaptive',d['adaptive_bitrate'].get('mode'))"
  P=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://')
  DEV=$(adb shell sha256sum "$P" 2>/dev/null | awk '{print $1}')
  if [ "$DEV" = "$ADOPTED_SHA" ]; then
    log "ADOPTED APK CONFIRMED (device hash $DEV; no arm APK was built)"
  else
    for try in 1 2; do
      adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1
      adb install -r "$ADOPTED_APK" > "$HERE/adopted_reinstall_$try.txt" 2>&1
      P=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://')
      DEV=$(adb shell sha256sum "$P" 2>/dev/null | awk '{print $1}')
      log "adopted APK reinstall try $try: device hash $DEV"
      [ "$DEV" = "$ADOPTED_SHA" ] && { log "ADOPTED APK CONFIRMED"; break; }
    done
  fi
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/c5end.xml >/dev/null 2>&1
  log "teardown: game active $A; NOW PLAYING on the launcher: $(adb shell cat /sdcard/c5end.xml 2>/dev/null | grep -c 'NOW PLAYING')"
}
trap 'teardown; log "night done"' EXIT
adb_ok || { log "adb unavailable: holds NOT RUN"; exit 1; }
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$HERE/t2_sampler.log" 2>&1 &
log "sampler started (10 s)"
P0=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://'); log "device APK hash at start: $(adb shell sha256sum "$P0" 2>/dev/null | awk '{print $1}')"
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=41)
print(int(t.timestamp()))")
log "last session_ended $LAST; B1 not before $(date -u -d @$READY +%H:%M:%SZ)"
echo "cold_start_last_session_ended $LAST" >> "$OUT/index.txt"
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
for pair in "B1 B" "A1 A" "B2 B" "A2 A" "B3 B" "A3 A"; do
  set -- $pair
  if ! adb_ok; then log "$1: adb unavailable; NOT RUN"; echo "$1 NOT_RUN adb" >> "$OUT/index.txt"; continue; fi
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  log "$1 begins (arm $2, 1200 s)"
  PROFILE_ARM="$2" "$HERE/c5_m1_run.sh" "$1" H 1200 "$OUT"
  log "$1 harness exit $?"
done
sleep 30
