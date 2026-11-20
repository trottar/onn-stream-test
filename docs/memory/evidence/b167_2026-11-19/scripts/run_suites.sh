#!/bin/bash
# Queue BD: B167 and B169 three runs each, B163 twice (its tests changed), B157 and B162 once — in the /tmp work copy,
# TMPDIR on the main disk, HEAD's code read by git. usage: run_suites.sh <work copy> <repo> <out dir> <temp dir>
W="$1"; O="$3"; export H7_GIT_REPO="$2" TMPDIR="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 2400 python3 -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O/tests_x3.txt"
for run in 1 2 3; do for t in b167_pictures_start b169_solo_cells; do echo "run $run $t: $(one $t)" >> "$O/tests_x3.txt"; done; done
for run in 1 2; do echo "run $run b163_rehearse: $(one b163_rehearse)" >> "$O/tests_x3.txt"; done
for t in b157_add_game b162_solo_safe; do echo "run 1 $t: $(one $t)" >> "$O/tests_x3.txt"; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
