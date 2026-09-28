#!/bin/bash
# C4-M1 step 2: 3-minute smokes, B (override unset) then A (xor8_2); the
# override is unset on every exit path.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
trap 'systemctl --user unset-environment PRIVYHUB_FEC_SCHEME' EXIT
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
FEC_ARM=B "$HERE/c4_m1_run.sh" SB H 180 "$HERE/smoke"; echo "SB exit $?"
adb shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
FEC_ARM=A "$HERE/c4_m1_run.sh" SA H 180 "$HERE/smoke"; echo "SA exit $?"
echo "smoke done"
