#!/bin/bash
# Queue BE: B171/B172's suite three runs, B163 and B169 twice (their tests changed), B157, B162, B167 once — in the /tmp
# work copy, TMPDIR on the main disk. usage: run_suites.sh <work copy> <out dir> <temp dir>
W="$1"; O="$2"; export TMPDIR="$3"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 2400 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O/tests_x3.txt"
for run in 1 2 3; do echo "run $run b171_more_saves: $(one b171_more_saves)" >> "$O/tests_x3.txt"; done
for run in 1 2; do for t in b163_rehearse b169_solo_cells; do echo "run $run $t: $(one $t)" >> "$O/tests_x3.txt"; done; done
for t in b157_add_game b162_solo_safe b167_pictures_start; do echo "run 1 $t: $(one $t)" >> "$O/tests_x3.txt"; done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
