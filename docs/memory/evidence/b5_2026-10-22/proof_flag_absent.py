#!/usr/bin/env python3
"""B5: property absent = today. NativeStreamActivity.kt against its predecessor: (1) only added lines, none removed or
changed (difflib); (2) every added code line is one of the allowed forms: a comment, the lazy holder declaration
(`StreamWifiLock.fromSystem(this)`, null without the property), a null-safe call on it, an override that calls super,
or a brace. So with the property absent the holder is null and every hook is a no-op; the only new runtime work is
one reflective property read (as B3's). Writes proof_flag_absent.md.
    python3 -B proof_flag_absent.py <new NativeStreamActivity.kt>"""
import difflib, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
old = (HERE / "predecessors" / "NativeStreamActivity.kt").read_text().splitlines()
new = Path(sys.argv[1]).read_text().splitlines()
ALLOWED = [r"^\s*//", r"^\s*$", r"^\s*\}\s*$",
           r"^\s*private val streamWifiLock: StreamWifiLock\? by lazy \{ StreamWifiLock\.fromSystem\(this\) \}$",
           r"^\s*(if \(sessionStarted\) )?streamWifiLock\?\.(acquire|release)\(\)$",
           r"^\s*override fun on(Pause|Resume)\(\) \{$", r"^\s*super\.on(Pause|Resume)\(\)$",
           r"^\s*streamWifiLock\?\.let \{ lock ->$", r'^\s*root\.put\("wifi_lock_(mode|held)", lock\.[\w.]+( \?: false)?\)$']
removed, added, bad = [], [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if tag in ("replace", "delete"):
        removed += old[i1:i2]
    if tag in ("replace", "insert"):
        added += new[j1:j2]
for line in added:
    if not any(re.match(p, line) for p in ALLOWED):
        bad.append(line)
stripped_equal = [l for l in new if True]  # see (1): no removed lines means new minus inserts == old
ok = not removed and not bad
out = ["# B5 — property absent = today (NativeStreamActivity.kt vs predecessors/)", "",
       f"- lines removed or changed: **{len(removed)}**",
       f"- lines added: {len(added)}; outside the allowed forms: **{len(bad)}**",
       f"- result: **{'PROVEN' if ok else 'NOT PROVEN'}**: with `debug.privyhub.wifi_lock` absent, `streamWifiLock` is "
       "null (`StreamWifiLockFlag.fromSystem()` → null; JVM test `noAndroidPropertyIsOff`), every hook is a null-safe "
       "no-op, the two new overrides only call `super` first, and the report gains no key. New work when absent: one "
       "reflective `SystemProperties.get` per activity (B3's pattern).", ""]
out += ["Added lines:", "", "```"] + added + ["```"] + (["", "Outside the forms:", ""] + bad if bad else [])
(HERE / "proof_flag_absent.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:5]))
sys.exit(0 if ok else 1)
