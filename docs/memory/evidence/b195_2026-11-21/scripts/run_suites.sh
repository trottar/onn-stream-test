#!/bin/bash
# Queue BK: B195's suite three runs, then the suites of the code touched once (solo / close / bench: B162, B169, B171's
# B172, B157, B163, B158, B175; B191's letters path) — in the /tmp work copy, TMPDIR on the main disk.
# usage: run_suites.sh <work copy> <out file> <temp dir>
W="$1"; O="$2"; export TMPDIR="$3"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O"
for run in 1 2 3; do echo "run $run b195_close_solo: $(one b195_close_solo)" >> "$O"; done
for t in b162_solo_safe b169_solo_cells b171_more_saves b157_add_game b163_rehearse b158_winner_only b175_left_out \
         b191_letters; do
  echo "run 1 $t: $(one $t)" >> "$O"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
