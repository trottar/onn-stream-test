#!/bin/bash
# C3-L4-N1 -- the silent live hold (handoff section 4): c3_l4_l2_2026-09-29/c3_l4_l2_night.sh with
# two changes: only PRIVYHUB_ADAPTIVE_BITRATE_MODE=live is set (never INJECT), and the one session is
# arm H, a 1800 s plain hold (c3_l4_n1_run.sh H H 1800). The teardown trap is L2's, unchanged: both flags
# unset on EVERY exit path, companion restarted through its unit, flags confirmed absent, stream 7000,
# game ended, banner checked. L2's header follows.
# C3-L4-L2 -- Session B2 only: the climb 5000 -> 7000 under the user's blend.
#   1. refuse if any PRIVYHUB_* is already in the manager; set
#      PRIVYHUB_ADAPTIVE_BITRATE_MODE=live and PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1;
#      start t2_sample.py (10 s);
#   2. Session B2 (c3_l4_l2_run.sh B2 B 1500): two injections 30 s apart, then
#      the hold runs 25 minutes after the first, then BACK;
#   3. teardown on EVERY exit path (trap), as L1's night script.
# Derived from c3_l4_l1_2026-09-28/c3_l4_l1_night.sh.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
RUN="$HERE/c3_l4_n1_run.sh"
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
  systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE PRIVYHUB_ADAPTIVE_BITRATE_INJECT
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
  log "flags unset: manager PRIVYHUB_* $(systemctl --user show-environment | grep -c '^PRIVYHUB_'); MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); PRIVYHUB_* in its environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c '^PRIVYHUB_'); ADAPTIVE_BITRATE_* in its environ $(tr '\0' '\n' < /proc/$MP/environ | grep -c '^PRIVYHUB_ADAPTIVE_BITRATE_')"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);r=d['audio_redundancy'];c=d['audio_cushion'];o=d['encoder_overrides'];print('[night] adaptive_bitrate',d.get('adaptive_bitrate'),'| bitrate',d.get('bitrate_kbps'),'profile',d.get('profile_id'),'cap',o['max_frame_size_bytes'],o['max_frame_size_source'],'cushion',c['queue_target_packets'],c['queue_capacity_packets'],c['source'],'redundancy',r['copies'],r['offset_packets'],r['source'],'any_override',o['any_override'],'active',d.get('active'))"
  log "inject route after teardown: $(curl -s -o /dev/null -w 'HTTP %{http_code}' -X POST 'localhost:8765/plugins/games/adaptive-bitrate/inject?class=FALLBACK')"
  adb shell input keyevent KEYCODE_HOME >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/l4end.xml >/dev/null 2>&1
  log "teardown: game active $A; NOW PLAYING on the launcher: $(adb shell cat /sdcard/l4end.xml 2>/dev/null | grep -c 'NOW PLAYING')"
  adb shell rm -f /sdcard/l4end.xml /sdcard/s1chk.xml >/dev/null 2>&1
}
trap 'teardown; log "night done"' EXIT

[ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] || { log "FAILED: PRIVYHUB_* already set in the manager"; exit 1; }
adb_ok || { log "adb unavailable: sessions NOT RUN"; exit 1; }
systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
log "flags set in the manager: $(systemctl --user show-environment | grep '^PRIVYHUB_' | tr '\n' ' ')"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$HERE/t2_sampler.log" 2>&1 &
log "sampler started (10 s)"
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
log "last session_ended $LAST"
echo "last_session_ended_before_H $LAST" >> "$OUT/index.txt"
if adb_ok; then
  log "H begins (1800 s, live, never INJECT)"
  "$RUN" H H 1800 "$OUT"; log "H harness exit $?"
else
  log "H: adb unavailable; NOT RUN"; echo "H NOT_RUN adb" >> "$OUT/index.txt"
fi
sleep 30

