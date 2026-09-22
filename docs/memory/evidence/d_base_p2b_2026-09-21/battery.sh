#!/bin/bash
# D-BASE-P2b: ten sessions, strictly alternating hold-off / hold-on, starting off.
# A session with a discontinuity inside the first 30 s is rejected and re-run
# (at most two re-runs per slot). Every session, accepted or rejected, is
# logged to all_sessions.txt so the rejected ones can still be read.
set -u
S=/tmp/claude-1000/-home-privyhub-Projects-onn-stream-test/a49eb391-4ee4-458f-9a04-d136c736803f/scratchpad/p2b
SESSDIR=/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions

early_disc() {  # $1 = report filename -> prints count of discontinuities < 30 s
  python3 -c "
import json,sys
r=json.load(open('$SESSDIR/$1'))['report']
print(len([d for d in r['stream_discontinuities'] if d['elapsed_ms'] < 30000]))
"
}

for slot in 1 2 3 4 5 6 7 8 9 10; do
  if [ $((slot % 2)) -eq 1 ]; then ARM=off; else ARM=on; fi
  ACCEPTED=0
  for try in 1 2 3; do
    LABEL="S${slot}${ARM}t${try}"
    "$S/session.sh" "$LABEL" "$ARM" > "$S/log_$LABEL.txt" 2>&1
    REPORT=$(awk -v l="$LABEL" '$1==l{print $3}' "$S/index.txt" | tail -1)
    if [ -z "$REPORT" ]; then
      echo "$LABEL $ARM NOREPORT" >> "$S/all_sessions.txt"
      continue
    fi
    ED=$(early_disc "$REPORT")
    if [ "$ED" = "0" ]; then
      echo "$LABEL $ARM $REPORT accepted" >> "$S/all_sessions.txt"
      echo "slot$slot $ARM $REPORT" >> "$S/accepted.txt"
      ACCEPTED=1
      break
    else
      echo "$LABEL $ARM $REPORT rejected_early_disc=$ED" >> "$S/all_sessions.txt"
    fi
  done
  [ "$ACCEPTED" = "1" ] || echo "slot$slot $ARM NONE_ACCEPTED" >> "$S/accepted.txt"
done
echo "BATTERY DONE" >> "$S/all_sessions.txt"
