#!/usr/bin/env bash
# E4-S3B (ladder_fix.md): wait for the in-flight suite (step mem:1G) to exit, record the step, resume the driver.
cd /home/privyhub/Projects/onn-stream-test
D=docs/memory/evidence/e4_s3b_2026-10-10
while [ -e /proc/$1 ]; do sleep 10; done
sleep 70   # the stand-in read-back's last tick
python3 $D/e4_s3b_ladder.py record mem:1G >> $D/ladder_stdout.log 2>&1
python3 $D/e4_s3b_ladder.py run >> $D/ladder_stdout.log 2>&1
echo resume-done >> $D/ladder_stdout.log
