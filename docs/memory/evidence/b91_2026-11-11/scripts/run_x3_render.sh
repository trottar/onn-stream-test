#!/bin/bash
# queue AG: B91 / B89 / B86 JVM x3 in the work copy (HEAD's client + B91), the renders, the full JVM suite.
S=~/.cache/b_q21ag_tmp; export TMPDIR=$S/t; E=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence/b91_2026-11-11
W=/tmp/b_q21ag_work/PrivyHub; R=$W/app/build/test-results/testDebugUnitTest
{ echo "B91 / B89 / B86 JVM, 3 runs, from /tmp/b_q21ag_work/PrivyHub (HEAD's client + B91), :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for i in 1 2 3; do (cd $W && timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q --tests '*B91*' --tests '*B89*' --tests '*B86*' >/dev/null 2>&1; echo "rc=$?")
  for c in B91MappingBesideTest B89MappingPictureTest B86MappingPictureTest; do echo "run $i $c $(grep -o 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' $R/TEST-com.safeiot.privyhub.streaming.$c.xml)"; done; done
} > $E/tests_x3.txt 2>&1
mkdir -p $E/render
(cd $W && B91_RENDER_DIR=$E/render timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q --tests '*B91*' >/dev/null 2>&1; echo "render rc=$?") > $S/render_rc.txt
(cd $W && timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q >/dev/null 2>&1; echo "full rc=$?") > $E/tests_jvm_work_full.txt
cat $R/*.xml | grep -o '<testsuite [^>]*' | grep -o 'tests="[0-9]*"\|failures="[0-9]*"\|errors="[0-9]*"' | awk -F'"' '{s[$1]+=$2} END {for (k in s) print k, s[k]}' >> $E/tests_jvm_work_full.txt
echo ALLDONE >> $S/render_rc.txt
