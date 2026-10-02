#!/bin/bash
# LINK-L2 -- C5-M4A's c5_m4a_hold.sh (copied from evidence/c5_m4a_2026-10-01/) with three changes: (1) the hold's
# name is an argument (H1..H6) and the hold runs through link_l2_run.sh (c5_m4_run.sh + the per-session
# adaptive disable after PLAYING); (2) LINK-L1's cold start (cl_b1_night.sh): the hold does not launch before
# COLD_MIN (default 30) minutes after the last session_ended in the recovery log, recorded in index.txt;
# (3) adb unavailable gets one `adb connect` to the device adb already knew (cl_b1_night.sh's adb_ok), else
# NOT RUN. The teardown is C5-M4A's unchanged: the unit restarted, so the companion is live by default again
# (the disable is per-session), and env_line prints the mode. C5-M4A's header follows.
# C5-M4A V5 -- one 20-min attract hold of Tekken 3 on the adopted 7000 stream carrying the ADOPTED 4x PS1 source
# (the core override + the 4x line are the real config now). Derived from C5-M4's c5_m4_table.sh (the D1
# pattern): no selector, no source files written; the only measurement file is the counter-only game override
# (c5_m4a_counter.sh), set before the hold and cleared on every exit path. T2 sampler at 10 s.
# usage: link_l2_hold.sh <runs dir> <hold name> [hold_s=1200]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO=/home/privyhub/Projects/onn-stream-test
OUT="$1"; mkdir -p "$OUT"
NAME="${2:?hold name}"
HOLD_S="${3:-1200}"
EXPECT_SHA=de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e
UNIT=privyhub-companion
SAMP="$OUT/t2_samples.jsonl"
log() { echo "[table $(date -u +%H:%M:%SZ)] $*"; }
cd "$REPO" || exit 1
restart_unit() {
  systemctl --user restart "$UNIT"
  for i in $(seq 1 30); do ss -lnt 2>/dev/null | grep -q ':8765 ' && break; sleep 1; done; sleep 2
}
env_line() {
  local MP; MP=$(systemctl --user show -p MainPID --value "$UNIT")
  log "$1: manager PRIVYHUB_* '$(systemctl --user show-environment | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')'; MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); environ PRIVYHUB_* '$(tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')'"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);a=d['adaptive_bitrate'];o=d['encoder_overrides'];print('[table] adaptive_bitrate mode',a.get('mode'),'configured',a.get('configured_mode'),'acts',a.get('acts'),'| bitrate',d.get('bitrate_kbps'),'profile',d.get('profile_id'),d.get('width'),d.get('height'),'any_override',o.get('any_override'),'profile_id_override',o.get('profile_id_override'),'fec_scheme_override',o.get('fec_scheme_override'),'active',d.get('active'))"
}
stop_game() {
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
}
teardown() {
  touch "$SAMP.stop"
  "$HERE/c5_m4a_counter.sh" clear
  systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID PRIVYHUB_FEC_SCHEME
  stop_game
  restart_unit
  env_line "teardown"
  log "measurement files: $(ls "$HOME/.config/retroarch/config/Beetle PSX HW" | grep -c '^Tekken 3') (want 0)"
  P=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://')
  DEV=$(adb shell sha256sum "$P" 2>/dev/null | awk '{print $1}')
  if [ "$DEV" = "$EXPECT_SHA" ]; then log "ADOPTED APK CONFIRMED (device hash $DEV)"; else log "APK MISMATCH: device $DEV"; fi
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/c5m4end.xml >/dev/null 2>&1
  NP=$(adb shell cat /sdcard/c5m4end.xml 2>/dev/null | grep -c 'NOW PLAYING')
  log "teardown: game active $A; NOW PLAYING on the launcher: $NP"
  if [ "$A" = "False" ] && [ "${NP:-0}" != "0" ]; then
    adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1; sleep 1
    adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1; sleep 7
    adb shell uiautomator dump /sdcard/c5m4end.xml >/dev/null 2>&1
    log "stale banner: force-stop + relaunch; NOW PLAYING now: $(adb shell cat /sdcard/c5m4end.xml 2>/dev/null | grep -c 'NOW PLAYING')"
  fi
  adb shell rm -f /sdcard/c5m4end.xml /sdcard/s1chk.xml >/dev/null 2>&1
}
[ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] || { log "FAILED: PRIVYHUB_* already in the manager"; exit 1; }
systemctl --user cat "$UNIT" | grep -q '^Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live$' || { log "FAILED: no live drop-in"; exit 1; }
ONN=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
[ -n "$ONN" ] && echo "$ONN" > /tmp/link_l2_onn_endpoint   # outside the repo; for the one reconnect only
[ -n "$ONN" ] || ONN=$(cat /tmp/link_l2_onn_endpoint 2>/dev/null)
if ! adb devices | awk 'NR>1 && $2=="device"' | grep -q .; then
  [ -n "$ONN" ] && { log "adb: no device; one reconnect"; adb connect "$ONN" >/dev/null 2>&1; sleep 3; }
  adb devices | awk 'NR>1 && $2=="device"' | grep -q . || { log "adb unavailable: NOT RUN"; exit 1; }
fi
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=int('${COLD_MIN:-30}'))
print(int(t.timestamp()))")
log "last session_ended $LAST; $NAME not before $(date -u -d @$READY +%H:%M:%SZ)"
echo "cold_start_$NAME last_session_ended $LAST" >> "$OUT/index.txt"
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
trap 'teardown; log "table done"' EXIT
env_line "start"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$OUT/t2_sampler.log" 2>&1 &
log "T2 sampler started (10 s); one hold, ${HOLD_S}s"
"$HERE/c5_m4a_counter.sh" set
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
log "$NAME begins (adopted 7000, the adopted 4x PS1 source, adaptive to shadow after PLAYING)"
ARM_PROFILE= "$HERE/link_l2_run.sh" "$NAME" H "$HOLD_S" "$OUT"; log "$NAME exit $?"
