#!/bin/bash
# Queue BN: the new suite three runs, then every earlier suite once, 12 at a time (the 90-minute limit), each in its own
# temp dir under <temp>. usage: run_parallel.sh <work copy> <out file> <temp dir>
W="$1"; O="$2"; T="$3"; mkdir -p "$T"; cd "$W" || exit 1
one() { mkdir -p "$T/$1"; echo "$1: $( (TMPDIR="$T/$1" env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' ') left $(ls "$T/$1" | wc -l)"; }
export -f one; export T
: > "$O"
for r in 1 2 3; do echo "run $r $(one b204_every_number)" >> "$O"; done
printf '%s\n' b200_drawn_places b201_find b198_max_score b178_score_kind b181_every_digit b185_overtime b191_letters \
  b195_close_solo b175_left_out b171_more_saves b157_add_game b163_rehearse b158_winner_only b162_solo_safe \
  b169_solo_cells b167_pictures_start b102_h7_endscreen b122_h7_places b103_h7_minigame b124_party_four_seats \
  | xargs -P 12 -I{} bash -c 'echo "run 1 $(one {})"' >> "$O"
echo "done" >> "$O"
