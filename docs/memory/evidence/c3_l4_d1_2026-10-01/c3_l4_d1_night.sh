#!/bin/bash
# C3-L4-D1 B3 -- proof that live acts from the default, then a hold. Derived from
# c3_l4_l1_2026-09-28/c3_l4_l1_night.sh; the mode is NEVER set or unset here: it comes from the unit's
# drop-in (B1). Order:
#   1. refuse unless the user manager carries no PRIVYHUB_* and the drop-in sets the live default;
#      start t2_sample.py (10 s);
#   2. Session I: set PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1 in the manager (this session only);
#      c3_l4_d1_run.sh I B 120 (one FALLBACK injection 120 s after PLAYING, 120 s + 60 s after it, BACK);
#      then unset it, restart the companion through its unit, and log I4: manager none, environ exactly
#      the drop-in's one name, inject route 403;
#   3. Session H: >= 30 min after Session I's session_ended, c3_l4_d1_run.sh H H 1800 (no flags at all);
#   4. teardown on EVERY exit path (trap): stop the sampler; unset-environment of the inject flag (and
#      of the mode, which only clears manager residue -- the drop-in is never touched); restart; confirm
#      manager none, environ exactly the one name, mode live; stream 7000; game ended; APK confirmed;
#      banner cleared (C5-M1's force-stop + relaunch if it stays).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO=/home/privyhub/Projects/onn-stream-test
OUT="$HERE/runs"; mkdir -p "$OUT"
SAMP="$HERE/t2_samples.jsonl"
RUN="$HERE/c3_l4_d1_run.sh"
UNIT=privyhub-companion
EXPECT_SHA=de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e
LIVE=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
log() { echo "[night $(date -u +%H:%M:%SZ)] $*"; }
cd "$REPO" || exit 1
ONN=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
adb_ok() {
  adb devices | awk 'NR>1 && $2=="device"' | grep -q . && return 0
  [ -n "$ONN" ] || return 1
  log "adb: no device; one reconnect"; adb connect "$ONN" >/dev/null 2>&1; sleep 3
  adb devices | awk 'NR>1 && $2=="device"' | grep -q .
}
env_line() {  # $1 label
  local MP; MP=$(systemctl --user show -p MainPID --value "$UNIT")
  log "$1: manager PRIVYHUB_* '$(systemctl --user show-environment | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')'; MainPID $MP; 8765 $(ss -lntp | grep ':8765 ' | grep -oP 'pid=\K[0-9]+'); environ PRIVYHUB_* '$(tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_' | tr '\n' ' ' | sed 's/ $//')'"
  curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);a=d['adaptive_bitrate'];o=d['encoder_overrides'];print('[night] adaptive_bitrate mode',a.get('mode'),'configured',a.get('configured_mode'),'acts',a.get('acts'),'level',a.get('level'),'inject_enabled',a.get('inject_enabled'),'| bitrate',d.get('bitrate_kbps'),'profile',d.get('profile_id'),'any_override',o.get('any_override'),'fec_scheme_override',o.get('fec_scheme_override'),'profile_id_override',o.get('profile_id_override'),'active',d.get('active'))"
  log "$1: inject route $(curl -s -o /dev/null -w 'HTTP %{http_code}' -X POST 'localhost:8765/plugins/games/adaptive-bitrate/inject?class=FALLBACK')"
}
restart_unit() {
  systemctl --user restart "$UNIT"
  for i in $(seq 1 30); do ss -lnt 2>/dev/null | grep -q ':8765 ' && break; sleep 1; done; sleep 2
}
teardown() {
  touch "$SAMP.stop"
  systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_INJECT PRIVYHUB_ADAPTIVE_BITRATE_MODE
  curl -s -X POST localhost:8765/plugins/games/stop >/dev/null
  for i in $(seq 1 20); do
    sleep 1
    A=$(curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;print(json.load(sys.stdin)['active'])" 2>/dev/null)
    [ "$A" = "False" ] && break
  done
  restart_unit
  env_line "teardown"
  P=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://')
  DEV=$(adb shell sha256sum "$P" 2>/dev/null | awk '{print $1}')
  if [ "$DEV" = "$EXPECT_SHA" ]; then log "ADOPTED APK CONFIRMED (device hash $DEV)"; else log "APK MISMATCH: device $DEV"; fi
  adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
  sleep 6
  adb shell uiautomator dump /sdcard/d1end.xml >/dev/null 2>&1
  NP=$(adb shell cat /sdcard/d1end.xml 2>/dev/null | grep -c 'NOW PLAYING')
  log "teardown: game active $A; NOW PLAYING on the launcher: $NP"
  if [ "$A" = "False" ] && [ "${NP:-0}" != "0" ]; then
    adb shell am force-stop com.safeiot.privyhub >/dev/null 2>&1; sleep 1
    adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1; sleep 7
    adb shell uiautomator dump /sdcard/d1end.xml >/dev/null 2>&1
    log "stale banner: force-stop + relaunch; NOW PLAYING now: $(adb shell cat /sdcard/d1end.xml 2>/dev/null | grep -c 'NOW PLAYING')"
  fi
  adb shell rm -f /sdcard/d1end.xml /sdcard/s1chk.xml >/dev/null 2>&1
}
trap 'teardown; log "night done"' EXIT

[ "$(systemctl --user show-environment | grep -c '^PRIVYHUB_')" = 0 ] || { log "FAILED: PRIVYHUB_* already in the manager"; exit 1; }
systemctl --user cat "$UNIT" | grep -q "^Environment=$LIVE\$" || { log "FAILED: no live drop-in"; exit 1; }
adb_ok || { log "adb unavailable: sessions NOT RUN"; exit 1; }
env_line "start"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$HERE/t2_sampler.log" 2>&1 &
log "sampler started (10 s)"

# --- Session I: the injection, on the default-live companion -----------------
systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1
log "inject flag set for Session I only: manager '$(systemctl --user show-environment | grep '^PRIVYHUB_' | tr '\n' ' ')'"
sleep 20
log "I begins"
"$RUN" I B 120 "$OUT"; log "I harness exit $?"
systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_INJECT
restart_unit
env_line "after I (I4)"

# --- Session H: the 30-minute hold on the default, no flags -----------------
LAST=$(grep '"session_ended"' "$REPO/logs/games/native_stream_recovery.log" | tail -1 \
       | python3 -c "import sys,json;print(json.loads(sys.stdin.read())['at_utc'])")
READY=$(python3 -c "
from datetime import datetime,timedelta,timezone
t=datetime.strptime('$LAST'[:19],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)+timedelta(minutes=30)
print(int(t.timestamp()))")
echo "last_session_ended_before_H $LAST" >> "$OUT/index.txt"
log "last session_ended $LAST; H not before $(date -u -d @$READY +%H:%M:%SZ)"
while [ "$(date +%s)" -lt "$READY" ]; do sleep 20; done
if adb_ok; then
  { echo "# H at $(date -u +%Y-%m-%dT%H:%M:%SZ)"; timedatectl; } > "$OUT/clock_H.txt"
  log "H begins (1800 s, local hour $(date +%H))"
  "$RUN" H H 1800 "$OUT"; log "H harness exit $?"
else
  log "H: adb unavailable; NOT RUN"; echo "H NOT_RUN adb" >> "$OUT/index.txt"
fi
sleep 30
