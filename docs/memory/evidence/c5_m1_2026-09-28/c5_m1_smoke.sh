#!/bin/bash
# C5-M1 step 3: 3-minute smokes, B (selector unset, adopted) then A (the
# 1080p60 candidate); the selector is unset on every exit path and the
# companion restarted without it.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
trap 'systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID; systemctl --user restart privyhub-companion; sleep 4; echo "[smoke] selector unset; manager PRIVYHUB_* $(systemctl --user show-environment | grep -c ^PRIVYHUB_); companion environ PRIVYHUB_* $(tr "\0" "\n" < /proc/$(systemctl --user show -p MainPID --value privyhub-companion)/environ | grep -c ^PRIVYHUB_)"' EXIT
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
PROFILE_ARM=B "$HERE/c5_m1_run.sh" SB H 180 "$HERE/smoke"; echo "SB exit $?"
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
PROFILE_ARM=A "$HERE/c5_m1_run.sh" SA H 180 "$HERE/smoke"; echo "SA exit $?"
echo "smoke done"
