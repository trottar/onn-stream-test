#!/bin/bash
# C5-M5B -- the end state, read-only: flags, live default, stream, adopted PS1 files, the look's session file, the APK.
set -u
REPO=/home/privyhub/Projects/onn-stream-test; HERE="$(cd "$(dirname "$0")" && pwd)"
echo "# C5-M5B final state at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "manager PRIVYHUB_*: $(systemctl --user show-environment | grep -c '^PRIVYHUB_') (want 0)"
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
echo "companion environ PRIVYHUB_*: '$(tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_' | sort | tr '\n' ' ' | sed 's/ $//')' (want PRIVYHUB_ADAPTIVE_BITRATE_MODE=live)"
echo "drop-in: $(systemctl --user cat privyhub-companion | grep '^Environment=')"
curl -s localhost:8765/plugins/games/native-stream-status | python3 -c "import sys,json;d=json.load(sys.stdin);a=d.get('adaptive_bitrate') or {};o=d.get('encoder_overrides') or {};print('stream:',d.get('bitrate_kbps'),'kbps',d.get('width'),'x',d.get('height'),'profile',d.get('profile_id'),'any_override',o.get('any_override'),'| adaptive mode',a.get('mode'),'configured',a.get('configured_mode'),'acts',a.get('acts'),'ladder',a.get('validated_ladder_kbps'))"
curl -s localhost:8765/plugins/games/status | python3 -c "import sys,json;d=json.load(sys.stdin);print('game active:',d.get('active'))"
if (cd "$HOME/.config/retroarch/config/Beetle PSX HW" && sha256sum -c --quiet "$HERE/adopted_ps1_sha256.txt") >/dev/null 2>&1; then echo "adopted PS1 files: BYTE-IDENTICAL (8 of 8)"; else echo "adopted PS1 files: CHANGED"; fi
echo "measurement files in the core's config dir: $(ls "$HOME/.config/retroarch/config/Beetle PSX HW" | grep -c '^Tekken 3') (want 0)"
echo "look session file present: $([ -e "$REPO/data/games/retroarch/config/privyhub-look-session.opt" ] && echo yes || echo no) (want no)"
P=$(adb shell pm path com.safeiot.privyhub | tr -d '\r' | sed 's/^package://')
echo "APK on the onn: $(adb shell sha256sum "$P" 2>/dev/null | awk '{print $1}') (want de072762...835e)"
echo "shadow module: $(sha256sum "$REPO/companion/adaptive_bitrate.py" | cut -c1-16)... (want d66211b38175b8c5)"
