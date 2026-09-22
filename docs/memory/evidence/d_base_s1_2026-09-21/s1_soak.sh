#!/bin/bash
# D-BASE-S1: four 30-minute soak sessions, >= 2 minutes idle between.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
HOLD="${1:-1800}"
IDLE="${2:-150}"
for n in 1 2 3 4; do
  "$HERE/s1_session.sh" "S$n" "$HOLD" >> "$HERE/s1_soak.log" 2>&1
  if [ "$n" != "4" ]; then
    echo "[soak] idle ${IDLE}s after S$n at $(date -u +%H:%M:%SZ)" >> "$HERE/s1_soak.log"
    sleep "$IDLE"
  fi
done
echo "SOAK DONE" >> "$HERE/s1_index.txt"
