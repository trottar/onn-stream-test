#!/bin/bash
cd "$(git rev-parse --show-toplevel)"
out="$HOME/b208_scratch"/runs/bq; mkdir -p $out
export TMPDIR="$HOME/b208_scratch"/tmp
for s in b204_every_number b200_drawn_places b198_max_score b181_every_digit b185_overtime b178_score_kind b175_left_out b171_more_saves b157_add_game b208_survey b210_keep_result; do
  ( start=$(date +%s); python3 -m unittest discover -s tests/$s > $out/$s.txt 2>&1; rc=$?; echo "$s rc=$rc $(( $(date +%s) - start ))s" >> $out/summary.txt ) &
done
for i in 1 2 3; do
  ( python3 -m unittest discover -s tests/b214_variants > $out/b214_run$i.txt 2>&1; echo "b214 run$i rc=$?" >> $out/summary.txt ) &
done
wait
echo ALL_DONE >> $out/summary.txt
