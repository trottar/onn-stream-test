#!/bin/bash
# C5-CLOSE section 1 (C5-M5B's 14 plus the rung-window rule's) -- mutations of the rung's rules, each in a scratch copy of companion/ + the two test files;
# a mutation is CAUGHT if the C5M5Rung / C5M5Actuator / C5CloseRungWindow classes fail on it. The tree is never edited.
REPO=/home/privyhub/Projects/onn-stream-test
M=(
 "companion/adaptive_bitrate_live.py|RUNG_CLEAN_NEEDED = 415 |RUNG_CLEAN_NEEDED = 414 |entry threshold 415 -> 414"
 "companion/adaptive_bitrate_live.py|RUNG_CLEAN_NEEDED = 415 |RUNG_CLEAN_NEEDED = 416 |entry threshold 415 -> 416"
 "companion/adaptive_bitrate_live.py|RUNG_CLEAN_NEEDED = 415 |RUNG_CLEAN_NEEDED = 435 |entry threshold back to C5-M5's 435"
 "companion/adaptive_bitrate_live.py|and sum(self.rung_window) >= RUNG_CLEAN_NEEDED|and sum(self.rung_window) > RUNG_CLEAN_NEEDED|entry comparison >= -> >"
 "companion/adaptive_bitrate_live.py|len(self.rung_window) >= RUNG_WINDOW_REPORTS \\|len(self.rung_window) >= 0 \\|entry without a full window"
 "companion/adaptive_bitrate_live.py|if self.top and self.level_kbps == REFERENCE_KBPS and len(self.rung_window)|if self.top and self.level_kbps >= 0 and len(self.rung_window)|entry from any level"
 "companion/adaptive_bitrate_live.py|if self.top and self.level_kbps == REFERENCE_KBPS and len(self.rung_window)|if self.level_kbps == REFERENCE_KBPS and len(self.rung_window)|entry without the flag"
 "companion/adaptive_bitrate_live.py|if since < RUNG_REENTRY_HOLD_MS:|if since < 0:|no re-entry hold-down"
 "companion/adaptive_bitrate_live.py|RUNG_OSCILLATION_LEAVES = 2|RUNG_OSCILLATION_LEAVES = 3|rung oscillation after 3 leaves"
 "companion/adaptive_bitrate_live.py|        self.rung_window.clear()||rung window survives an SSRC change"
 "companion/adaptive_bitrate_live.py|        self.ladder = LADDER_WITH_RUNG_KBPS if self.top else LADDER_KBPS|        self.ladder = LADDER_WITH_RUNG_KBPS|the rung in the ladder without the flag"
 "companion/diagnostics/c3_linux_actuator_probe.py|LINUX_RUNG_LEVELS: dict[int, tuple[int, int]] = {12600: (1920, 1080)}|LINUX_RUNG_LEVELS: dict[int, tuple[int, int]] = {12600: (1280, 720)}|the rung's size"
 "companion/diagnostics/c3_linux_actuator_probe.py|            manager._active_width = target_width|            pass|active width not following the level"
 "companion/diagnostics/c3_linux_actuator_probe.py|        same_level_restart and target in LINUX_RUNG_LEVELS|        False|recovery at the rung rebuilt at 720p"
 "companion/adaptive_bitrate_live.py|        if self.top and (ctx.get(\"guards\") or {}).get(\"recovery_playing\") is False:|        if False:|window rule removed (paused reports count)"
 "companion/adaptive_bitrate_live.py|.get(\"recovery_playing\") is False:|.get(\"recovery_playing\") is not True:|a report without the guard skipped"
 "companion/adaptive_bitrate_live.py|        if self.top and (ctx.get(\"guards\") or {}).get(\"recovery_playing\") is False:|        if (ctx.get(\"guards\") or {}).get(\"recovery_playing\") is False:|window rule without the flag"
 "companion/adaptive_bitrate_live.py|            self.rung_skipped_not_playing += 1\n            return|            self.rung_skipped_not_playing += 1|skip counted but the report still appended"
 "companion/adaptive_bitrate_live.py|            self.rung_skipped_not_playing += 1\n            return|            self.rung_skipped_not_playing += 1\n            self.rung_window.clear()\n            return|reset on a paused report instead of skip"
 "companion/adaptive_bitrate_live.py|            self._rung_append(False, ctx)|            self.rung_window.append(False)|resync while paused counted"
 "companion/adaptive_bitrate_live.py|        self._rung_append(bool(self.last_clean), ctx)|        self.rung_window.append(bool(self.last_clean))|evaluated report while paused counted"
 "companion/adaptive_bitrate_live.py|                               \"skipped_not_playing\": self.rung_skipped_not_playing,|                               \"skipped_not_playing\": 0,|status field not carrying the count"
)
caught=0
for m in "${M[@]}"; do
  IFS='|' read -r file old new what <<< "$m"
  T=$(mktemp -d); mkdir -p "$T/tools" "$T/docs"
  cp -r "$REPO/companion" "$T/"; cp "$REPO/tools/test_adaptive_bitrate_live.py" "$REPO/tools/test_c3_f1_recovery_restart.py" "$T/tools/"
  ln -s "$REPO/docs/memory" "$T/docs/memory"
  python3 - "$T/$file" "$old" "$new" <<'PY'
import sys
p, old, new = (a.replace("\\n", "\n") for a in sys.argv[1:4])
s = open(p).read()
assert s.count(old) >= 1, ("anchor missing", old)
open(p, "w").write(s.replace(old, new, 1))
PY
  if (cd "$T/tools" && env -u PRIVYHUB_NATIVE_PROFILE_ID python3 -m unittest test_adaptive_bitrate_live.C5M5Rung test_adaptive_bitrate_live.C5M5Actuator test_adaptive_bitrate_live.C5CloseRungWindow >/dev/null 2>&1); then
    echo "NOT CAUGHT  $what"
  else
    echo "CAUGHT      $what"; caught=$((caught+1))
  fi
  rm -rf "$T"
done
echo "mutations caught: $caught of ${#M[@]}"
