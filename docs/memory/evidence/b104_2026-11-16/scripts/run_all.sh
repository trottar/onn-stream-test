#!/bin/bash
# B104: 3 runs of tests/b104_h7_tone and tests/b102_h7_endscreen on a work copy of the snapshot (/tmp/b_q26an:
# companion/ tools/ tests/ PrivyHub/), then the mutations from the snapshot (both suites per mutation).
# No RetroArch, no game picture: synthetic pictures only.
R=/home/privyhub/Projects/onn-stream-test; E=$R/docs/memory/evidence/b104_2026-11-16; S=/tmp/b_q26an
export TMPDIR=~/.cache/b_q26an_tmp/t H7_GIT_REPO=$R
W=$(mktemp -d -p ~/.cache/b_q26an_tmp b104_x3_XXXX)
cp -r $S/companion $S/tools $S/tests $S/PrivyHub $W/ && ln -s $R/runtime $W/runtime && mkdir -p $W/data/games/retroarch && cp $R/data/games/retroarch/retroarch.cfg $W/data/games/retroarch/
cd $W && { echo "B104 tests, 3 runs, $(date -u +%FT%TZ), a work copy of the snapshot, TMPDIR on the main disk"
  for i in 1 2 3; do for t in b104_h7_tone b102_h7_endscreen; do echo "run $i tests/$t: $(python3 -B -m unittest discover -s tests/$t 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done; done
  echo "temp dirs left by the runs (b104_* / b102_*): $(ls $TMPDIR | grep -c -E '^(b104_|b102_)')"; } > $E/tests_x3.txt
cd / && rm -rf $W
echo "x3 DONE" >> $E/tests_x3.txt
python3 -u -B $E/scripts/mutate.py $S $R $E/scripts/mutations.json tests/b104_h7_tone,tests/b102_h7_endscreen 'test_*.py' > $E/tests_mutations.txt 2>&1
echo "temp dirs left after the mutations (b_q26an_mut_*): $(ls $TMPDIR | grep -c '^b_q26an_mut_')" >> $E/tests_mutations.txt
