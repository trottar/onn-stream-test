#!/bin/bash
# C5-CLOSE section 2 -- one real `tools/ps1_look.sh 4x --attract` dry pass: the helper's stdin is a fifo; Enter is
# written 30 s after the helper prints PLAYING (or after 240 s without it, which the helper's own wait outlasts).
set -u
REPO=/home/privyhub/Projects/onn-stream-test; D="$REPO/docs/memory/evidence/c5_close_2026-10-05/attract"
cd "$REPO" || exit 1
OUT="$D/attract_dry_pass.txt"; : > "$OUT"; [ -p "$D/enter.fifo" ] || mkfifo "$D/enter.fifo"
( T=0; until grep -q '^\[ps1_look\] PLAYING$' "$OUT" || [ "$T" -ge 240 ]; do sleep 1; T=$((T+1)); done
  grep -q '^\[ps1_look\] PLAYING$' "$OUT" && { sleep 30; adb shell dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity | sed 's/{[^ ]* [^ ]* /{.. /' > "$D/top_at_playing.txt"; }
  echo > "$D/enter.fifo" ) &
exec 3<> "$D/enter.fifo"   # held open read-write: opening the fifo does not block
tools/ps1_look.sh 4x --attract <&3 2>&1 | tee -a "$OUT"
echo "helper exit ${PIPESTATUS[0]}" >> "$OUT"
wait
rm -f "$D/enter.fifo"; touch "$D/DONE"
