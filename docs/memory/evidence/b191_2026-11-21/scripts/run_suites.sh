#!/bin/bash
# Queue BJ: B191's suite three runs, then the suites of the files touched once (B178 / B181 / B185 the score kind's,
# B102 / B122 the learner's, B157-B176 the tool's, B103 / B124 the companion's) — in the /tmp work copy, TMPDIR on the
# main disk. usage: run_suites.sh <work copy> <out file> <temp dir>
W="$1"; O="$2"; export TMPDIR="$3"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O"
for run in 1 2 3; do echo "run $run b191_letters: $(one b191_letters)" >> "$O"; done
for t in b185_overtime b181_every_digit b178_score_kind b175_left_out b171_more_saves b163_rehearse b157_add_game \
         b162_solo_safe b167_pictures_start b169_solo_cells b158_winner_only b102_h7_endscreen b122_h7_places \
         b103_h7_minigame b124_party_four_seats; do
  echo "run 1 $t: $(one $t)" >> "$O"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
