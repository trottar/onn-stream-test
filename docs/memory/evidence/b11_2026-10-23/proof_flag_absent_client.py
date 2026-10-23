#!/usr/bin/env python3
"""B11 (client): debug.privyhub.restart_guard absent = the CONFIRMED client (bf5114a2's sources, HEAD 3eb900c).
NativeStreamActivity.kt vs predecessors/: (1) only added lines (difflib); (2) every added code line in an allowed form.
Without the property `restartGuard` is null (RestartGuardTest.flagTable: fromSystem() false off-device), so: notePause,
onSurfaceLost, onSessionStopped are `?.` no-ops; `restart` is null, so the old report / stop are not posted, the audio
receiver is neither replaced nor restarted (`if (restart != null)`), and the report gains no key. The two new private
functions are called only from the guard's flush.
    B11_ROOT=<root with PrivyHub/> python3 -B proof_flag_absent_client.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B11_ROOT", str(HERE.parents[3])))
J = "PrivyHub/app/src/main/java/streaming"
ALLOWED = [r"^\s*//", r"^\s*$", r"^\s*[\})]\s*$",
           r"^\s*private val restartGuard: RestartGuard\? by lazy \{ if \(RestartGuardFlag\.fromSystem\(\)\) RestartGuard\(\) else null \}$",
           r"^\s*private fun postRestartReport\(host: String, report: String\) \{$",
           r'^\s*httpPostBody\("http://\$host:\$CONTROL_PORT" \+ DecoderReportUpload\.PATH, DecoderReportUpload\.encode\(report\),$',
           r"^\s*DecoderReportUpload\.CONTENT_TYPE\)$",
           r"^\s*private fun postRestartStop\(host: String\) \{$",
           r'^\s*httpPost\("http://\$host:\$CONTROL_PORT" \+ "/plugins/games/native-stream-stop"\)$',
           r"^\s*restartGuard\?\.notePause\(\)$",
           r"^\s*if \(sessionStarted\) \{$",
           r"^\s*restartGuard\?\.onSurfaceLost\($",
           r"^\s*cachedSessionReport,$",
           r"^\s*decoder\?\.lastOutputAgeMs\(\) \?: -1L,$",
           r"^\s*if \(lastRtpAdvanceAtNs > 0L\) \(System\.nanoTime\(\) - lastRtpAdvanceAtNs\) / 1_000_000L else -1L,$",
           r"^\s*recoveryActive$",
           r"^\s*restartGuard\?\.onSessionStopped\(\)$",
           r"^\s*val restart = restartGuard\?\.takePending\(\)$",
           r"^\s*restart\?\.let \{ p -> restartGuard\?\.flush\(p, \{ r -> postRestartReport\(host, r\) \}, \{ postRestartStop\(host\) \}\) \}$",
           r"^\s*if \(restart != null\) \{$",
           r"^\s*audioReceiver\?\.stop\(\)$",
           r"^\s*audioReceiver = NativeAudioReceiver\(port = AUDIO_PORT\)$",
           r"^\s*if \(restart != null\) audioReceiver\?\.start\(\)$",
           r'^\s*restartGuard\?\.lastCause\?\.let \{ c -> root\.put\("restart_cause", JSONObject\(c\)\) \}$']
name = "NativeStreamActivity.kt"
old = (HERE / "predecessors" / J / name).read_text().splitlines(); new = (ROOT / J / name).read_text().splitlines()
removed, added = [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if tag in ("replace", "delete"): removed += old[i1:i2]
    if tag in ("replace", "insert"): added += new[j1:j2]
bad = [l for l in added if not any(re.match(p, l) for p in ALLOWED)]
ok = not removed and not bad
out = ["# B11 (client) — property absent = the CONFIRMED client (only added lines, all in the allowed forms)", "",
       "| file | removed / changed | added | outside the forms |", "| --- | ---: | ---: | ---: |",
       f"| `{name}` | **{len(removed)}** | {len(added)} | **{len(bad)}** |", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**. New file `RestartGuard.kt` is reached only through "
       "`restartGuard`, null without the property.", "", "```"] + added + ["```"] + (["", "Outside:"] + bad if bad else [])
(HERE / "proof_flag_absent_client.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:8]))
sys.exit(0 if ok else 1)
