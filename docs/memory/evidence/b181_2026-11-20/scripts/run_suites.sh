#!/bin/bash
# Queue BH: B181's suite three runs, B178's twice (its tests changed for B181-B183, disclosed), B157-B176's and the
# suites of the files touched once — in the /tmp work copy, TMPDIR on the main disk, HEAD's code for `today` by
# `git archive` (read only). usage: run_suites.sh <work copy> <out dir> <temp dir> <repo>
W="$1"; O="$2"; export TMPDIR="$3"; export H7_GIT_REPO="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O/tests_x3.txt"
for run in 1 2 3; do echo "run $run b181_every_digit: $(one b181_every_digit)" >> "$O/tests_x3.txt"; done
for run in 1 2; do echo "run $run b178_score_kind: $(one b178_score_kind)" >> "$O/tests_x3.txt"; done
for t in b175_left_out b171_more_saves b163_rehearse b157_add_game b162_solo_safe b167_pictures_start b169_solo_cells \
         b158_winner_only b102_h7_endscreen b122_h7_places b103_h7_minigame b124_party_four_seats; do
  echo "run 1 $t: $(one $t)" >> "$O/tests_x3.txt"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O/tests_x3.txt"
