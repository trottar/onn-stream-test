#!/bin/bash
# queue AG: every host suite on full exports of HEAD (/tmp/b_q21ag_base) and HEAD + b90 (/tmp/b_q21ag_after_b90), queue
# AC's run_host.sh; TMPDIR on the main disk; docs/CHEATS.md copied in for B81's docs test; the suites' logs/ and the
# docs/ copies moved (not deleted) to ~/.cache/b_q21ag_tmp/ afterwards.
S=~/.cache/b_q21ag_tmp; export TMPDIR=$S/t; E=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence
for d in base after_b90; do mkdir -p /tmp/b_q21ag_$d/docs && cp /home/privyhub/Projects/onn-stream-test/docs/CHEATS.md /tmp/b_q21ag_$d/docs/
  bash $E/b83_2026-11-10/scripts/run_host.sh /tmp/b_q21ag_$d $S/host_$d.txt
  mv /tmp/b_q21ag_$d/logs $S/hostrun_logs_from_$d 2>/dev/null; mv /tmp/b_q21ag_$d/docs $S/hostrun_docs_from_$d; done
echo ALLDONE >> $S/host_after_b90.txt
