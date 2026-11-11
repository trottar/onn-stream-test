#!/bin/bash
# B90's measurement set (made-up lists; the synthetic ROMs; temp folders under ~/.cache; the companion's display).
# staged: the B90 tree's code (/tmp/b_q21ag_after_b90) on all three cores; walk: HEAD's code (/tmp/b_q21ag_base) on N64.
R=/home/privyhub/Projects/onn-stream-test; S=$(dirname "$0")/b90_measure.py; OUT=${OUT:-$HOME/.cache/b_q21ag_tmp/measure/results.jsonl}
. "$(dirname "$0")/env.sh"
for sys in n64 snes ps1; do for n in 12 188 677 2092; do for k in 1 2 4; do
  W=$(mktemp -d -p ~/.cache/b_q21ag_tmp runXXXX); timeout 600 python3 -I -B $S $R /tmp/b_q21ag_after_b90 $W --system $sys --entries $n --picks $k --mode staged >> "$OUT" 2>>"$OUT.err" || echo "{\"failed\": \"staged $sys $n $k\"}" >> "$OUT"
done; done; done
for n in 12 188 677 2092; do for k in 1 2 4; do
  W=$(mktemp -d -p ~/.cache/b_q21ag_tmp runXXXX); timeout 3000 python3 -I -B $S $R /tmp/b_q21ag_base $W --system n64 --entries $n --picks $k --mode walk >> "$OUT" 2>>"$OUT.err" || echo "{\"failed\": \"walk n64 $n $k\"}" >> "$OUT"
done; done
echo "{\"retroarch_left\": $(ps -eo args | grep -c '[R]etroArch-Linux')}" >> "$OUT"
