#!/bin/bash
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b94_2026-11-11; export TMPDIR=~/.cache/b_q21ai_tmp/t
. ~/.cache/b_q21ag_tmp/scripts/env.sh
cd $R && { echo "B94 tests, 3 runs, $(date -u +%FT%TZ), the working tree, the companion's display, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/h7_rule_search 2>&1 | grep -E '^Ran|^OK|^FAILED|B94 time' | tr '\n' ' ')"; done
  echo "tests/h7_minigame_proof: $(python3 -B -m unittest discover -s tests/h7_minigame_proof 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"
  echo "RetroArch left: $(ps -eo args | grep -c '[R]etroArch-Linux')"; } > $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $R /nonexistent $E/scripts/mutations.json tests/h7_rule_search test_h7_rule_search.py > $E/tests_mutations.txt 2>&1
echo "RetroArch left after the mutations: $(ps -eo args | grep -c '[R]etroArch-Linux')" >> $E/tests_mutations.txt
echo DONE >> $E/tests_x3.txt
