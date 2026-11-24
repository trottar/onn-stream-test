#!/bin/bash
# Queue BO: the suites BN named worth running every time, once, all at once, each in its own temp dir.
# usage: run_every_time.sh <work copy> <out file> <temp dir>
W="$1"; O="$2"; T="$3"; mkdir -p "$T"; cd "$W" || exit 1
one() { mkdir -p "$T/$1"; echo "$1: $( (TMPDIR="$T/$1" env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3000 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' ') left $(ls "$T/$1" | wc -l)"; }
export -f one; export T
printf '%s\n' b204_every_number b200_drawn_places b198_max_score b181_every_digit b185_overtime b178_score_kind \
  b175_left_out b171_more_saves b157_add_game | xargs -P 9 -I{} bash -c 'echo "run 1 $(one {})"' > "$O"
echo done >> "$O"
