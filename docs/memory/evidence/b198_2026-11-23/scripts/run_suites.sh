#!/bin/bash
# Queue BL: B198's suite three runs, then B178-B195's suites and the suites of the code touched (register / learn in
# tools/party_add_game.py; the version-4 reader in tools/h7_endscreen.py) once each — in the work copy on the main
# disk, TMPDIR there, HEAD's code for `today` by `git archive` (read only). usage: run_suites.sh <work copy> <out file>
# <temp dir> <repo>
W="$1"; O="$2"; export TMPDIR="$3"; export H7_GIT_REPO="$4"
mkdir -p "$TMPDIR"; cd "$W" || exit 1
one() { (env -u PRIVYPARTY_GODOT -u PRIVYPARTY_REPO timeout 3600 python3 -W ignore -m unittest discover -s "tests/$1" 2>&1) | grep -E "^Ran|^OK|^FAILED|^FAIL:|^ERROR:" | tr '\n' ' '; }
: > "$O"
for run in 1 2 3; do echo "run $run b198_max_score: $(one b198_max_score)" >> "$O"; done
for t in b178_score_kind b181_every_digit b185_overtime b191_letters b195_close_solo b175_left_out b171_more_saves \
         b157_add_game b163_rehearse b158_winner_only b162_solo_safe b169_solo_cells b167_pictures_start \
         b102_h7_endscreen b122_h7_places b103_h7_minigame b124_party_four_seats; do
  echo "run 1 $t: $(one $t)" >> "$O"
done
echo "temp dirs left: $(ls "$TMPDIR" | wc -l)" >> "$O"
