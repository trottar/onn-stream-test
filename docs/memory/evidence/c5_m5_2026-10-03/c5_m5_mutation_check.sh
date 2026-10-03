#!/bin/bash
# C5-M5 section 3 -- mutations of the new rules, each in a scratch copy of companion/ + the two test files;
# a mutation is CAUGHT if the C5M5Rung / C5M5Actuator classes fail on it. The tree is never edited.
REPO=/home/privyhub/Projects/onn-stream-test
M=(
 "companion/adaptive_bitrate_live.py|RUNG_CLEAN_NEEDED = 435|RUNG_CLEAN_NEEDED = 434|entry threshold 435 -> 434"
 "companion/adaptive_bitrate_live.py|if self.top and self.level_kbps == REFERENCE_KBPS and len(self.rung_window)|if self.top and self.level_kbps >= 0 and len(self.rung_window)|entry from any level"
 "companion/adaptive_bitrate_live.py|if self.top and self.level_kbps == REFERENCE_KBPS and len(self.rung_window)|if self.level_kbps == REFERENCE_KBPS and len(self.rung_window)|entry without the flag"
 "companion/adaptive_bitrate_live.py|if since < RUNG_REENTRY_HOLD_MS:|if since < 0:|no re-entry hold-down"
 "companion/adaptive_bitrate_live.py|RUNG_OSCILLATION_LEAVES = 2|RUNG_OSCILLATION_LEAVES = 3|rung oscillation after 3 leaves"
 "companion/adaptive_bitrate_live.py|        self.rung_window.clear()||rung window survives an SSRC change"
 "companion/adaptive_bitrate_live.py|        self.ladder = LADDER_WITH_RUNG_KBPS if self.top else LADDER_KBPS|        self.ladder = LADDER_WITH_RUNG_KBPS|the rung in the ladder without the flag"
 "companion/diagnostics/c3_linux_actuator_probe.py|LINUX_RUNG_LEVELS: dict[int, tuple[int, int]] = {12600: (1920, 1080)}|LINUX_RUNG_LEVELS: dict[int, tuple[int, int]] = {12600: (1280, 720)}|the rung's size"
 "companion/diagnostics/c3_linux_actuator_probe.py|            manager._active_width = target_width|            pass|active width not following the level"
 "companion/diagnostics/c3_linux_actuator_probe.py|        same_level_restart and target in LINUX_RUNG_LEVELS|        False|recovery at the rung rebuilt at 720p"
)
caught=0
for m in "${M[@]}"; do
  IFS='|' read -r file old new what <<< "$m"
  T=$(mktemp -d); mkdir -p "$T/tools" "$T/docs"
  cp -r "$REPO/companion" "$T/"; cp "$REPO/tools/test_adaptive_bitrate_live.py" "$REPO/tools/test_c3_f1_recovery_restart.py" "$T/tools/"
  ln -s "$REPO/docs/memory" "$T/docs/memory"
  python3 - "$T/$file" "$old" "$new" <<'PY'
import sys
p, old, new = sys.argv[1:4]
s = open(p).read()
assert s.count(old) >= 1, ("anchor missing", old)
open(p, "w").write(s.replace(old, new, 1))
PY
  if (cd "$T/tools" && env -u PRIVYHUB_NATIVE_PROFILE_ID python3 -m unittest test_adaptive_bitrate_live.C5M5Rung test_adaptive_bitrate_live.C5M5Actuator >/dev/null 2>&1); then
    echo "NOT CAUGHT  $what"
  else
    echo "CAUGHT      $what"; caught=$((caught+1))
  fi
  rm -rf "$T"
done
echo "mutations caught: $caught of ${#M[@]}"
