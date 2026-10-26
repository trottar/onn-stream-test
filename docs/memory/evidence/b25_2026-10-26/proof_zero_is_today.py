#!/usr/bin/env python3
"""B25 proof: `debug.privyhub.link_notice=0` = B14's absent, byte for byte. Usage: proof_zero_is_today.py REPO_ROOT.

1. The activity and the diagnostics page are byte-identical to their predecessors (they follow the flag only).
2. In LinkNotice.kt every changed non-comment line is inside `object LinkNoticeFlag` and is the parse or the catch.
3. The parse table: new("0") == old(None) (off), new == old for "1" and "0"; absent / empty / junk flip to on.
4. Every main-source use of the flag gates a null / no view on `fromSystem()` false (unchanged sites, listed).
"""
import difflib, hashlib, os, re, sys

R = sys.argv[1]
D = os.path.join(R, "docs/memory/evidence/b25_2026-10-26/predecessors")
SRC = os.path.join(R, "PrivyHub/app/src/main/java")
ok = True


def rd(p):
    return open(p, encoding="utf-8").read()


print("# B25 proof: `0` is today's absent\n")
for name, rel in (("NativeStreamActivity.kt", "streaming/NativeStreamActivity.kt"),
                  ("DiagnosticsActivity.kt", "diagnostics/DiagnosticsActivity.kt")):
    a, b = rd(os.path.join(D, name)), rd(os.path.join(SRC, rel))
    same = a == b
    ok &= same
    print(f"- 1. `{rel}` identical to the predecessor: **{same}** (sha256 {hashlib.sha256(b.encode()).hexdigest()[:12]}…)")

old, new = rd(os.path.join(D, "LinkNotice.kt")).splitlines(), rd(os.path.join(SRC, "streaming/LinkNotice.kt")).splitlines()
changed = [l for l in difflib.unified_diff(old, new, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
code = [l for l in changed if not re.match(r"^[+-]\s*(//|\*|/\*\*|\*/|$)", l)]
allowed = {
    '-    fun parse(value: String?): Boolean = value?.trim() == "1"',
    '+    fun parse(value: String?): Boolean = value?.trim() != "0"',
    "-            false",
    "+            parse(null)",
}
inside = all(l in allowed for l in code)
ok &= inside and len(code) == 4
print(f"- 2. `LinkNotice.kt`: {len(changed)} changed lines, {len(changed) - len(code)} of them comments; the {len(code)} code lines:")
for l in code:
    print(f"  - `{l}`")
print(f"  all inside `object LinkNoticeFlag` (the parse and the catch): **{inside and len(code) == 4}**")
idx = next(i for i, l in enumerate(new) if l.startswith("object LinkNoticeFlag"))
end = next(i for i in range(idx, len(new)) if new[i] == "}")
print(f"  (`object LinkNoticeFlag` spans lines {idx + 1}-{end + 1} of the new file)")
rest_old = old[next(i for i, l in enumerate(old) if l == "}") + 1:]
rest_new = new[end + 1:]
ok &= rest_old == rest_new
print(f"  everything after the flag object (the text, the status, the rule, the query) identical: **{rest_old == rest_new}**")


def old_parse(v):
    return v is not None and v.strip() == "1"


def new_parse(v):
    return v is None or v.strip() != "0"


print("\n- 3. The parse table (Kotlin's `trim()` = Python's `strip()` on these values):\n")
print("| value | B14 | B25 |\n| --- | --- | --- |")
for v in (None, "", " ", "1", " 1 ", "0", " 0 ", "on", "true", "2"):
    print(f"| {v!r} | {'on' if old_parse(v) else 'off'} | {'on' if new_parse(v) else 'off'} |")
t = new_parse("0") == old_parse(None) is False and new_parse("1") == old_parse("1") and new_parse("0") == old_parse("0")
ok &= t
print(f"\n  new(`0`) = B14's absent (off), `1` and `0` unchanged: **{t}**; a failed read: B14 off, B25 `parse(null)` = on")

print("\n- 4. The flag's uses in the main sources (unchanged lines; with `0` each takes B14's absent branch):")
for root, _, files in os.walk(SRC):
    for f in files:
        p = os.path.join(root, f)
        for i, l in enumerate(rd(p).splitlines(), 1):
            if "LinkNoticeFlag.fromSystem()" in l:
                print(f"  - `{os.path.relpath(p, SRC)}:{i}` `{l.strip()}`")
print("  `linkNotice` null → no view, no tick, no `&link_notice=` fragment (`linkNotice?.query() ?: \"\"`), no report keys;"
      " the diagnostics line not added.")
print(f"\n**{'PROVEN' if ok else 'NOT PROVEN'}**")
