#!/bin/bash
# Queue BF: B175/B176's suite three runs, B171 and B163 twice (their tests changed), B157, B162, B167, B169 once — in
# the /tmp work copy, TMPDIR on the main disk. usage: run_suites.sh <work copy> <out dir> <temp dir>
W="$1"; O="$2"; export TMPDIR="$3"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 2400 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O/tests_x3.txt"
for run in 1 2 3; do echo "run $run b175_left_out: $(one b175_left_out)" >> "$O/tests_x3.txt"; done
for run in 1 2; do for t in b171_more_saves b163_rehearse; do echo "run $run $t: $(one $t)" >> "$O/tests_x3.txt"; done; done
for t in b157_add_game b162_solo_safe b167_pictures_start b169_solo_cells; do echo "run 1 $t: $(one $t)" >> "$O/tests_x3.txt"; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
