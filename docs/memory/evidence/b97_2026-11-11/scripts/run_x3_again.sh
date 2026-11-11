#!/bin/bash
# B97: the 3 runs again after the fixtures' made-up descriptions were reworded (five generic ones also occur as real
# cheat names; the cheat-name check found them in b97.diff). Same work-copy form as run_all.sh; appended to tests_x3.txt.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b97_2026-11-11; S=/tmp/b_q22aj_b97
export TMPDIR=~/.cache/b_q21aj_tmp/t
. ~/.cache/b_q21ag_tmp/scripts/env.sh
W=$(mktemp -d -p ~/.cache/b_q21aj_tmp b97_x3b_XXXX)
cp -r $S/companion $S/tools $S/tests $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo; echo "B97 tests, 3 runs again after the fixture descriptions were reworded, $(date -u +%FT%TZ), nothing else running"
  for i in 1 2 3; do echo "run $i: $(python3 -B -m unittest discover -s tests/h7_rule_search 2>&1 | grep -E '^Ran|^OK|^FAILED|B96 time|B96 \(c\)' | tr '\n' ' ')"; done
  echo "RetroArch left: $(ps -eo args | grep -c '[R]etroArch-Linux')"; } >> $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 again DONE" >> $E/tests_x3.txt
