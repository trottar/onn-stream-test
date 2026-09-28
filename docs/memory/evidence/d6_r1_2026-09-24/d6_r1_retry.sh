#!/bin/bash
# D6-R1 retry (one each) of the three runs the onn's screensaver ended:
# fwd3 now, rev2 at +150 s, rev3 at +450 s (>= 5 min after rev2).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
log() { echo "[d6r $(date -u +%H:%M:%SZ)] $*"; }
START=$(date +%s)
at() { while [ "$(date +%s)" -lt $((START + $1)) ]; do sleep 5; done; }
log "fwd3b"; "$HERE/d6_r1_run.sh" fwd d6_r1_fwd3b "$HERE/fwd3b"
at 150; log "rev2b"; "$HERE/d6_r1_run.sh" rev d6_r1_rev2b "$HERE/rev2b"
at 450; log "rev3b"; "$HERE/d6_r1_run.sh" rev d6_r1_rev3b "$HERE/rev3b"
adb shell am start -n com.safeiot.privyhub/.MainActivity >/dev/null 2>&1
log "wakefulness after: $(adb shell dumpsys power | grep -m1 mWakefulness= | tr -d ' \r')"
log done
