#!/bin/bash
# C5-M4A V5 -- one 20-min attract hold of Tekken 3 on the adopted 7000 stream carrying the ADOPTED 4x PS1 source
# (the core override + the 4x line are the real config now). Derived from C5-M4's c5_m4_table.sh (the D1
# pattern): no selector, no source files written; the only measurement file is the counter-only game override
# (c5_m4a_counter.sh), set before the hold and cleared on every exit path. T2 sampler at 10 s.
# usage: c5_m4a_hold.sh <runs dir> [hold_s=1200]
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO=/home/privyhub/Projects/onn-stream-test
OUT="$1"; mkdir -p "$OUT"
HOLD_S="${2:-1200}"
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
adb devices | awk 'NR>1 && $2=="device"' | grep -q . || { log "adb unavailable: NOT RUN"; exit 1; }
trap 'teardown; log "table done"' EXIT
env_line "start"
rm -f "$SAMP.stop"
nohup python3 "$HERE/t2_sample.py" "$SAMP" 10 >> "$OUT/t2_sampler.log" 2>&1 &
log "T2 sampler started (10 s); one hold, ${HOLD_S}s"
"$HERE/c5_m4a_counter.sh" set
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
log "b_adopted begins (adopted 7000, the adopted 4x PS1 source)"
ARM_PROFILE= "$HERE/c5_m4_run.sh" "b_adopted" H "$HOLD_S" "$OUT"; log "b_adopted exit $?"
