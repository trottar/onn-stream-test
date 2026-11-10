#!/bin/bash
# queue AE: the JVM suite in the APK tree, the APK twice, the baseline once. Offline, --no-configuration-cache;
# nothing installed; outputs under ~/.cache/b_q20ae_tmp/.
S=~/.cache/b_q20ae_tmp; export TMPDIR=$S
A=/tmp/b_q20ae_apk/PrivyHub; O=/tmp/b_q20ae_apko/PrivyHub
(cd $A && timeout 1800 bash ./gradlew :app:testDebugUnitTest --offline --no-configuration-cache -q > $S/jvm_apk.log 2>&1; echo "rc=$?" >> $S/jvm_apk.log)
for n in 1 2; do
  (cd $A && timeout 1800 bash ./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache -q > $S/apk$n.log 2>&1; echo "rc=$?" >> $S/apk$n.log)
  mkdir -p $S/apk$n && cp $A/app/build/outputs/apk/debug/app-debug.apk $S/apk$n/
done
(cd $O && timeout 1800 bash ./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache -q > $S/apko.log 2>&1; echo "rc=$?" >> $S/apko.log)
mkdir -p $S/apko && cp $O/app/build/outputs/apk/debug/app-debug.apk $S/apko/
sha256sum $S/apk1/app-debug.apk $S/apk2/app-debug.apk $S/apko/app-debug.apk > $S/apk_sums.txt
echo ALLDONE >> $S/apk_sums.txt
