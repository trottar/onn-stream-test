#!/usr/bin/env python3
"""PREPUSH (2026-10-05) -- read-only audit of a commit range before the user's push. Git reads only (log, diff,
ls-files, show, cat-file, rev-parse, status); no fetch / add / commit / push. Every file is read at HEAD from git.

    prepush_audit.py <base> [--json out.json]     (base = origin/main)

1. the range and commits; the working tree status;
2. files: name-status counts, the diff stat summary, sizes at HEAD, the five largest;
3. the redactor (h2_prep_redact.py --check, run per file on the HEAD blob) over every added/modified TEXT file,
   and, in-process with the same patterns, every match with file and line, classified;
4. a keyword grep over the same set: private IPv4, MAC, SSID, `adb connect <address>`, serial, password, token,
   secret, `BEGIN ... KEY`; a keyword line is a CANDIDATE only if a value is assigned to it;
5. ignored categories in `git ls-files`;
Hits are printed redacted (the matched value is never printed, only its class)."""
import importlib.util, json, re, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
RED = REPO / "docs/memory/evidence/h2_prep_2026-09-22/h2_prep_redact.py"
spec = importlib.util.spec_from_file_location("red", RED); red = importlib.util.module_from_spec(spec); spec.loader.exec_module(red)
BASE = sys.argv[1]
def git(*a, binary=False):
    r = subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")
out = {}
P = print
P(f"== 1. range {BASE}..HEAD  ({git('rev-parse', '--short', BASE).strip()}..{git('rev-parse', '--short', 'HEAD').strip()})")
commits = git("log", "--format=%h %s", f"{BASE}..HEAD").splitlines()
P(f"commits: {len(commits)}")
for c in commits: P("  " + c[:150])
P("working tree (git status --short):")
for l in git("status", "--short").splitlines(): P("  " + l)
P(f"\n== 2. files")
ns = [l.split("\t") for l in git("diff", "--name-status", "--no-renames", f"{BASE}..HEAD").splitlines()]
cnt = Counter(x[0][0] for x in ns); P(f"name-status: {dict(cnt)}")
P("diff --stat: " + git("diff", "--stat", f"{BASE}..HEAD").splitlines()[-1].strip())
am = [x[1] for x in ns if x[0][0] in "AM"]
sizes = {}
for line in git("ls-tree", "-r", "-l", "HEAD").splitlines():
    meta, path = line.split("\t", 1); parts = meta.split()
    sizes[path] = int(parts[3]) if parts[3] != "-" else 0
tot = sum(sizes.get(p, 0) for p in am)
P(f"added/modified files: {len(am)}; total size at HEAD {tot} bytes ({tot / 2**20:.1f} MiB)")
P("five largest:"); [P(f"  {sizes[p]:>10}  {p}") for p in sorted(am, key=lambda p: -sizes.get(p, 0))[:5]]
binary = {l.split("\t")[2] for l in git("diff", "--numstat", "--no-renames", f"{BASE}..HEAD").splitlines() if l.startswith("-\t-\t")}
text = [p for p in am if p not in binary]
P(f"binary (numstat '-'): {len([p for p in am if p in binary])}; text: {len(text)}")
P("binary files:"); [P(f"  {sizes.get(p,0):>10}  {p}") for p in sorted(p for p in am if p in binary)]
# ---- 3. redactor
NAMES = ["uuid=", "uuid", "mac", "ipv4", "ipv6", "adb-serial-line"]
FP_V4 = {"127.0.0.1": "loopback", "0.0.0.0": "any-address bind", "0.9.44.1": "Beetle PSX HW core version"}
DOC = ("192.0.2.", "198.51.100.", "203.0.113.")
def private(ip):
    o = [int(x) for x in ip.split(".")]
    return o[0] == 10 or (o[0] == 172 and 16 <= o[1] <= 31) or (o[0] == 192 and o[1] == 168) or (o[0] == 169 and o[1] == 254) or (o[0] == 100 and 64 <= o[1] <= 127)
def classify_v4(ip):
    if ip in FP_V4: return "FP", FP_V4[ip]
    if ip.startswith(DOC): return "FP", "RFC 5737 documentation address"
    if not all(0 <= int(x) <= 255 for x in ip.split(".")): return "FP", "not an address (octet > 255)"
    if private(ip): return "FINDING", "private-range IPv4"
    return "REVIEW", "public-shaped IPv4"
red_fail, hits = [], defaultdict(list)
blobs = {}
for p in text:
    b = git("show", f"HEAD:{p}", binary=True); blobs[p] = b.decode("utf-8", "replace")
    rc = subprocess.run([sys.executable, str(RED), "--check"], input=b, capture_output=True).returncode
    if rc: red_fail.append(p)
for p in red_fail:
    for n, line in enumerate(blobs[p].splitlines(), 1):
        if red.EDID_LINE.match(line): hits[p].append((n, "edid-line", "REVIEW", "32-hex indented line"))
        for i, (pat, _) in enumerate(red.PATTERNS):
            for m in pat.finditer(line):
                v = m.group(0)
                if NAMES[i] == "ipv4": c, why = classify_v4(v); key = v if c == "FP" else "<redacted>"
                else: c, why, key = "REVIEW", NAMES[i], "<redacted>"
                hits[p].append((n, NAMES[i], c, why, v))
P(f"\n== 3. redactor --check over {len(text)} text files: PASS {len(text) - len(red_fail)}, flagged {len(red_fail)}")
summ = Counter()
for p, hs in hits.items():
    for h in hs: summ[(h[1], h[2], h[3])] += 1
for k, v in sorted(summ.items()): P(f"  {v:>7}  {k[0]:<16} {k[2]:<8} {k[1]}" if False else f"  {v:>7}  {k[0]:<16} {k[1]:<8} {k[2]}")
json_out = {"redactor_hits": {p: [list(h[:4]) for h in hs] for p, hs in hits.items()}}
review = [(p, h) for p, hs in hits.items() for h in hs if h[2] != "FP"]
P(f"non-FP redactor hits (FINDING or REVIEW): {len(review)}")
# ---- 4. keyword grep
KW = {
 "ssid": re.compile(r"\bssid\b", re.I),
 "adb-connect": re.compile(r"adb\s+connect\s+(\S+)", re.I),
 "serial": re.compile(r"serial", re.I),
 "password": re.compile(r"passw(or)?d", re.I),
 "token": re.compile(r"\btoken", re.I),
 "secret": re.compile(r"secret", re.I),
 "private-key": re.compile(r"BEGIN [A-Z ]*KEY"),
}
ASSIGN = re.compile(r"(ssid|serial(no|_number)?|passw(or)?d|token|secret)[\"']?\s*[:=]\s*[\"']?(?!<)([^\s\"',}<>]{4,})", re.I)
kw = defaultdict(list)
for p in text:
    for n, line in enumerate(blobs[p].splitlines(), 1):
        for k, pat in KW.items():
            m = pat.search(line)
            if not m: continue
            if k == "adb-connect":
                tgt = m.group(1)
                cand = not tgt.startswith("<") and not tgt.startswith("$") and bool(re.search(r"\d+\.\d+\.\d+\.\d+|:\d{2,5}", tgt))
            elif k == "private-key": cand = True
            else:
                a = ASSIGN.search(line); cand = bool(a)
            kw[k].append((p, n, cand, line.strip()[:200]))
P(f"\n== 4. keyword grep over the same {len(text)} files (a line is a CANDIDATE when a value is assigned)")
for k in KW:
    c = [x for x in kw[k] if x[2]]
    P(f"  {k:<12} lines {len(kw[k]):>6}; candidates {len(c)}")
json_out["kw_candidates"] = {k: [x[:3] + (x[3],) for x in kw[k] if x[2]] for k in KW}
json_out["review"] = [(p, h[0], h[1], h[3], h[4]) for p, h in review]
# ---- 5. ignored categories
ls = git("ls-files").splitlines()
IGN = re.compile(r"(\.apk$|\.pem$|\.key$|\.keystore$|\.jks$|(^|/)\.env|\.state($|\.)|\.srm$|\.sav$|^(logs|runtime|data|games|media|cache)/)", re.I)
ign = [p for p in ls if IGN.search(p)]
big = [p for p in ls if sizes.get(p, 0) > 20 * 2**20]
bigmedia = [p for p in ls if re.search(r"\.(mkv|mp4|png)$", p, re.I) and sizes.get(p, 0) > 2**20]
P(f"\n== 5. ignored categories in git ls-files ({len(ls)} tracked): pattern matches {len(ign)}; > 20 MB {len(big)}; mkv/mp4/png > 1 MB {len(bigmedia)}")
for p in ign + big + bigmedia: P(f"  {sizes.get(p,0):>10}  {p}")
json_out.update(ignored=ign, big=big, bigmedia=bigmedia)
if "--json" in sys.argv:
    Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(json_out, indent=1, default=str))
