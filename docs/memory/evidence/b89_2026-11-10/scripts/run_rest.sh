#!/bin/bash
# queue AF: B89's JVM mutations, the client tests x3, the full JVM suite, B87 / B88 x3, the host suites (HEAD vs B87+B88)
S=~/.cache/b_q20af_tmp; export TMPDIR=$S; E=/home/privyhub/Projects/onn-stream-test/docs/memory/evidence
W=/tmp/b_q20af_work/PrivyHub; M=$E/b89_2026-11-10/scripts/mutate_jvm.sh
T=com.safeiot.privyhub.streaming.B89MappingPictureTest; F=app/src/main/java/streaming/MappingPicture.kt
{
bash $M $W $F $T K1 '        for ((s, labels) in sends) if (s in out) out[s] = labels.joinToString("+")' '        for ((s, labels) in sends) if (s in out) out[s] = labels.first()'
bash $M $W $F $T K2 '    const val MAX_SCREEN_SHARE = 0.2f' '    const val MAX_SCREEN_SHARE = 0.5f'
bash $M $W $F $T K3 'at("start", 0.57f, 0.283f, 0.07f, 0.026f)' 'at("start", 0.45f, 0.283f, 0.07f, 0.026f)'
bash $M $W $F $T K4 '        val left = right.reversed().map { (x, y) -> (1f - x) to y }' '        val left = right.reversed().map { (x, y) -> (0.98f - x) to y }'
bash $M $W $F $T K5 '        "l" -> "L1"; "r" -> "R1"; "l2" -> "L2"; "r2" -> "R2"; "l3" -> "L3"; "r3" -> "R3"' '        "l" -> "R1"; "r" -> "L1"; "l2" -> "L2"; "r2" -> "R2"; "l3" -> "L3"; "r3" -> "R3"'
} > $E/b89_2026-11-10/tests_mutations_jvm.txt 2>&1
R=$W/app/build/test-results/testDebugUnitTest
{ echo "B89 / B86 JVM, 3 runs, from /tmp/b_q20af_work/PrivyHub (HEAD's client + B89), :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
for i in 1 2 3; do (cd $W && timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q --tests "$T" --tests 'com.safeiot.privyhub.streaming.B86MappingPictureTest' >/dev/null 2>&1; echo "rc=$?")
  for c in B89MappingPictureTest B86MappingPictureTest; do echo "run $i $c $(grep -o 'tests="[0-9]*" skipped="[0-9]*" failures="[0-9]*" errors="[0-9]*"' $R/TEST-com.safeiot.privyhub.streaming.$c.xml)"; done; done
} > $E/b89_2026-11-10/tests_x3.txt 2>&1
(cd $W && timeout 1800 bash ./gradlew :app:cleanTestDebugUnitTest :app:testDebugUnitTest --offline --no-configuration-cache -q >/dev/null 2>&1; echo "full rc=$?") > $S/jvm_work_full.txt
cat $R/*.xml | grep -o '<testsuite [^>]*' | grep -o 'tests="[0-9]*"\|failures="[0-9]*"\|errors="[0-9]*"' | awk -F'"' '{s[$1]+=$2} END {for (k in s) print k, s[k]}' >> $S/jvm_work_full.txt
cd /tmp/b_q20af_after_b88 && mkdir -p docs && cp /home/privyhub/Projects/onn-stream-test/docs/CHEATS.md docs/
for b in 87 88; do
  if [ $b = 87 ]; then suite=tests/b87_cheat_ready; pat=test_b87.py; else suite=tests/client_contract; pat=test_contract.py; fi
  { echo "B$b tests, 3 runs, $(date -u +%Y-%m-%dT%H:%M:%SZ), from a copy of HEAD + B87 + B88 (companion/ tools/ tests/ PrivyHub/), TMPDIR on the main disk, no PRIVYHUB_* in the process: $(env | grep -c '^PRIVYHUB_')"
    for i in 1 2 3; do echo "run $i $suite: $(python3 -B -m unittest discover -s $suite -p $pat 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; done
    echo "tests/art_systems (all): $(python3 -B -m unittest discover -s tests/art_systems 2>&1 | grep -E '^Ran|^OK|^FAILED' | tr '\n' ' ')"; } > $E/b${b}_2026-11-10/tests_x3.txt
done
rm -rf /tmp/b_q20af_after_b88/docs
for d in base after_b88; do mkdir -p /tmp/b_q20af_$d/docs && cp /home/privyhub/Projects/onn-stream-test/docs/CHEATS.md /tmp/b_q20af_$d/docs/; bash $E/b83_2026-11-10/scripts/run_host.sh /tmp/b_q20af_$d $S/host_$d.txt; mv /tmp/b_q20af_$d/logs $S/hostrun_logs_from_$d 2>/dev/null; mv /tmp/b_q20af_$d/docs $S/hostrun_docs_from_$d; done
echo ALLDONE
