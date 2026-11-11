#!/bin/bash
# B90's apply-at-load reads (the design's table): a staged file of 2 picks from a made-up 12-entry list, both enabled,
# no command for 5 s, then RetroArch's log, core memory at the picks, and an index pulse per staged cheat.
R=/home/privyhub/Projects/onn-stream-test; S=$(dirname "$0")/b90_measure.py; OUT=${OUT:-$HOME/.cache/b_q21ag_tmp/measure/load_results.jsonl}
. "$(dirname "$0")/env.sh"
for sys in n64 snes ps1; do for a in 1 0; do
  W=$(mktemp -d -p ~/.cache/b_q21ag_tmp runXXXX); echo "{\"case\": \"$sys apply_cheats_after_load=$a\"}" >> "$OUT"
  timeout 120 python3 -I -B $S $R $R $W --system $sys --entries 12 --picks 2 --mode load --apply-at-load $a --window 5 >> "$OUT" 2>>"$OUT.err"
done; done
W=$(mktemp -d -p ~/.cache/b_q21ag_tmp runXXXX); echo '{"case": "snes, the file under the bsnes folder (where the hub stages today)"}' >> "$OUT"
timeout 120 python3 -I -B $S $R $R $W --system snes --entries 12 --picks 2 --mode load --apply-at-load 1 --window 5 --folder bsnes >> "$OUT" 2>>"$OUT.err"
echo "{\"retroarch_left\": $(ps -eo args | grep -c '[R]etroArch-Linux')}" >> "$OUT"
