#!/bin/bash
# B98: 3 runs of the suite on a work copy of the B98 snapshot (/tmp/b_q23ak_b98: companion/ tools/ tests/ PrivyHub/),
# RetroArch linked read-only from the repo's runtime/, the base config copied; then the mutations from the snapshot.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b98_2026-11-11; S=/tmp/b_q23ak_b98
export TMPDIR=~/.cache/b_q22ak_tmp/t H7_GIT_REPO=$R
. ~/.cache/b_q21ag_tmp/scripts/env.sh
W=$(mktemp -d -p ~/.cache/b_q22ak_tmp b98_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B98 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the B98 snapshot, the companion's display, TMPDIR on the main disk"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/h7_rule_search 2>&1 | grep -E '^Ran|^OK|^FAILED|B96 time|B96 \(c\)' | tr '\n' ' ')"; done
  echo "tests/h7_minigame_proof: $(python3 -B -m unittest discover -s tests/h7_minigame_proof 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"
  echo "RetroArch left: $(ps -eo args | grep -c '[R]etroArch-Linux')"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/h7_rule_search 'test_*.py' > $E/tests_mutations.txt 2>&1
echo "RetroArch left after the mutations: $(ps -eo args | grep -c '[R]etroArch-Linux')" >> $E/tests_mutations.txt
