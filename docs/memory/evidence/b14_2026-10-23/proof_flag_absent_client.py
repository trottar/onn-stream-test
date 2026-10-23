#!/usr/bin/env python3
"""B14 (client): debug.privyhub.link_notice absent = the predecessors (NativeStreamActivity.kt = B11-B13's tree,
DiagnosticsActivity.kt = HEAD 3eb900c): only added lines, all in the allowed forms. Without the property `linkNotice`
is null (LinkNoticeTest.flagTable: off-device off): no view is created (`if (linkNotice != null)`), the UI tick calls
nothing (`linkNotice?.let`), `noticeSampler` is null and never read, the heartbeat adds "" and the report no key; the
diagnostics page adds no view (`if (LinkNoticeFlag.fromSystem())`). `noticeView` stays null (`noticeView?.` no-ops).
    B14_ROOT=<root with PrivyHub/> python3 -B proof_flag_absent_client.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B14_ROOT", str(HERE.parents[3])))
ALLOWED = [r"^\s*//", r"^\s*$", r"^\s*[\})]\s*$", r"^\s*\}\)\s*$", r"^\s*\}\s*,\s*$",
           # NativeStreamActivity
           r"^\s*if \(linkNotice != null\) \{$", r"^\s*val notice = TextView\(this\)\.apply \{$",
           r"^\s*setTextColor\(Color\.WHITE\)$", r"^\s*setBackgroundColor\(0xCC000000\.toInt\(\)\)$", r"^\s*textSize = 15f$",
           r"^\s*setPadding\(20, 12, 20, 12\)$", r"^\s*visibility = View\.GONE$", r"^\s*noticeView = notice$",
           r"^\s*root\.addView\(notice, FrameLayout\.LayoutParams\($",
           r"^\s*FrameLayout\.LayoutParams\.WRAP_CONTENT, FrameLayout\.LayoutParams\.WRAP_CONTENT$",
           r"^\s*\)\.apply \{ gravity = Gravity\.BOTTOM or Gravity\.START; setMargins\(24, 24, 24, 24\) \}\)$",
           r"^\s*linkNotice\?\.let \{ tickLinkNotice\(it\) \}$", r"^\s*linkNotice\?\.onSessionStart\(\)$",
           r"^\s*noticeView\?\.visibility = View\.GONE$",
           r"^\s*private val linkNotice: LinkNotice\? by lazy \{ if \(LinkNoticeFlag\.fromSystem\(\)\) LinkNotice\(\) else null \}$",
           r"^\s*private val noticeSampler: LinkSampler\? by lazy \{$",
           r"^\s*if \(linkNotice != null && linkSampler == null\) LinkSampler\(\{ readWifi\(applicationContext\) \}\) else null$",
           r"^\s*private var noticeView: TextView\? = null$", r"^\s*private fun tickLinkNotice\(n: LinkNotice\) \{$",
           r"^\s*if \(!sessionStarted\) return$", r"^\s*val s = \(linkSampler \?: noticeSampler\)\?\.current\(\)$",
           r"^\s*when \(val ev = n\.update\(s, System\.nanoTime\(\) / 1_000_000L\)\) \{$",
           r"^\s*is LinkNotice\.Event\.Shown -> \{$", r"^\s*noticeView\?\.text = ev\.text$",
           r"^\s*noticeView\?\.visibility = View\.(VISIBLE|GONE)$", r"^\s*LinkNoticeStatus\.\w+ = .*$",
           r"^\s*LinkNotice\.Event\.Cleared -> \{$", r"^\s*null -> \{\}$",
           r'^\s*\(linkNotice\?\.query\(\) \?: ""\) \+$', r"^\s*linkNotice\?\.let \{ n ->$",
           r'^\s*root\.put\("link_notice_(shown|last_reasons)", n\.\w+\)$',
           # DiagnosticsActivity
           r"^import com\.safeiot\.privyhub\.streaming\.LinkNotice(Flag|Status)$",
           r"^\s*if \(LinkNoticeFlag\.fromSystem\(\)\) \{$", r"^\s*content\.addView\($", r"^\s*TextView\(this\)\.apply \{$",
           r'^\s*text = LinkNoticeStatus\.lastText\?\.let \{ "Last link notice:\\n\$it" \} \?: "Link notice: none shown"$',
           r"^\s*ViewGroup\.LayoutParams\(ViewGroup\.LayoutParams\.MATCH_PARENT, ViewGroup\.LayoutParams\.WRAP_CONTENT\)$"]
FILES = ("PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt", "PrivyHub/app/src/main/java/diagnostics/DiagnosticsActivity.kt")
out = ["# B14 (client) — property absent = the predecessors (only added lines, all in the allowed forms)", "",
       "| file | removed / changed | added | outside the forms |", "| --- | ---: | ---: | ---: |"]
ok, details = True, []
for rel in FILES:
    old = (HERE / "predecessors" / rel).read_text().splitlines(); new = (ROOT / rel).read_text().splitlines()
    removed, added = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"): removed += old[i1:i2]
        if tag in ("replace", "insert"): added += new[j1:j2]
    bad = [l for l in added if not any(re.match(p, l) for p in ALLOWED)]
    ok &= not removed and not bad
    out.append(f"| `{rel.split('/')[-1]}` | **{len(removed)}** | {len(added)} | **{len(bad)}** |")
    details += [f"### {rel.split('/')[-1]}", "", "```"] + added + ["```", ""] + (["Outside:", ""] + bad + [""] if bad else [])
out += ["", f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**. New file `LinkNotice.kt` is reached only through "
        "`linkNotice` (null without the property) and the diagnostics page's flag check.", ""] + details
(HERE / "proof_flag_absent_client.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:7]))
sys.exit(0 if ok else 1)
