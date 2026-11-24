#!/bin/bash
# Queue BM: B200's and B201's suites three runs, then B178-B198's suites and the suites of the code touched once each — in
# the work copy on the main disk, TMPDIR there. usage: run_suites.sh <work copy> <out file> <temp dir> <repo> [quick]
W="$1"; O="$2"; export TMPDIR="$3"; export H7_GIT_REPO="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O"
if [ "$5" != "old" ]; then
  for run in 1 2 3; do for t in b200_drawn_places b201_find; do echo "run $run $t: $(one $t)" >> "$O"; done; done
fi
if [ "$5" != "new" ]; then
for t in b198_max_score b178_score_kind b181_every_digit b185_overtime b191_letters b195_close_solo b175_left_out \
         b171_more_saves b157_add_game b163_rehearse b158_winner_only b162_solo_safe b169_solo_cells b167_pictures_start \
         b102_h7_endscreen b122_h7_places b103_h7_minigame b124_party_four_seats; do
  echo "run 1 $t: $(one $t)" >> "$O"
done
fi
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
