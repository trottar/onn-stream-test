#!/bin/bash
# queue AG, B90's final runs: the mutations, the suite on HEAD's code, 3 runs on the tree, the knob-0 proof.
R=/home/privyhub/Projects/onn-stream-test; D=$R/docs/memory/evidence/b90_2026-11-11; export TMPDIR=~/.cache/b_q21ag_tmp/t
cd $R && python3 -u -B $D/scripts/mutate.py $R /nonexistent $D/scripts/mutations.json tests/b90_cheat_staged test_b90.py > $D/tests_mutations.txt 2>&1
cd /tmp/b_q21ag_head_tests && { echo "tests/b90_cheat_staged on HEAD's code (/tmp/b_q21ag_head_tests: HEAD's companion/ tools/ tests/ + the B90 test dir), $(date -u +%FT%TZ)"; python3 -B -m unittest discover -s tests/b90_cheat_staged -v 2>&1 | grep -E "^test_|^Ran|^OK|^FAILED|^AssertionError" | cut -c1-260; } > $D/tests_on_head.txt
cd $R && { echo "B90 tests, 3 runs, $(date -u +%FT%TZ), the working tree, TMPDIR on the main disk, PRIVYHUB_* in the process: $(env | grep -c '^PRIVYHUB_')"
  for i in 1 2 3; do echo "run $i tests/b90_cheat_staged: $(python3 -B -m unittest discover -s tests/b90_cheat_staged 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
  echo "tests/b87_cheat_ready: $(python3 -B -m unittest discover -s tests/b87_cheat_ready 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"
  echo "tests/client_contract: $(python3 -B -m unittest discover -s tests/client_contract 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; } > $D/tests_x3.txt
cd ~ && python3 -I -B $D/scripts/proof_absent.py /tmp/b_q21ag_head_tests $R > $D/proof_absent_run.txt 2>&1
echo FINALDONE >> $D/tests_x3.txt
# then every host suite again on the final B90 copy (HEAD's run kept from the first pass)
S=~/.cache/b_q21ag_tmp; mkdir -p /tmp/b_q21ag_after_b90/docs && cp $R/docs/CHEATS.md /tmp/b_q21ag_after_b90/docs/
bash $R/docs/memory/evidence/b83_2026-11-10/scripts/run_host.sh /tmp/b_q21ag_after_b90 $S/host_after_b90_final.txt
mv /tmp/b_q21ag_after_b90/logs $S/hostrun_logs_from_after_b90_final 2>/dev/null; mv /tmp/b_q21ag_after_b90/docs $S/hostrun_docs_from_after_b90_final
echo HOSTDONE >> $D/tests_x3.txt
