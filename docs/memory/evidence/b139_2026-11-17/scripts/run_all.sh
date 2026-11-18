#!/bin/bash
# Queue AW: B139 / B140 / B141 with B137 / B133 / B134 three times, then the earlier suites once (B137's run_others.sh
# list), in the /tmp work copy, TMPDIR on the main disk, HEAD's code by git. usage: run_all.sh <work copy> <repo> <out dir>
W="$1"; REPO="$2"; O="$3"
export H7_GIT_REPO="$REPO"
cd "$W" || exit 1
: > "$O/tests_x3.txt"
for run in 1 2 3; do for t in b139_party_clean_window b140_party_begin_shown b141_party_select_held b137_party_no_press \
                               b133_party_prepare_go b134_party_practice; do
  r=$( (timeout 1800 python3 -m unittest discover -s "tests/$t" 2>&1) | grep -E "^Ran|^OK|^FAILED" | tr '\n' ' ')
  echo "run $run $t: $r" >> "$O/tests_x3.txt"
done; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
bash "$REPO/docs/memory/evidence/b137_2026-11-17/scripts/run_others.sh" "$W" "$REPO" "$O/tests_others.txt"
