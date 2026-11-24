#!/bin/bash
# every suite at once, each to its end; one output file each (scratch, off the repo)
cd "$(git rev-parse --show-toplevel)"
out="$HOME/b208_scratch"/runs/suites; mkdir -p $out
export TMPDIR="$HOME/b208_scratch"/tmp
for s in b204_every_number b200_drawn_places b198_max_score b181_every_digit b185_overtime b178_score_kind b175_left_out b171_more_saves b157_add_game b191_letters b103_h7_minigame b114_party_minigame_hang b124_party_four_seats; do
  ( start=$(date +%s); python3 -m unittest discover -s tests/$s > $out/$s.txt 2>&1; rc=$?; echo "$s rc=$rc $(( $(date +%s) - start ))s" >> $out/summary.txt ) &
done
wait
echo ALL_DONE >> $out/summary.txt
