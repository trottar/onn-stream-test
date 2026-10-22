#!/usr/bin/env python3
"""B7 (client): debug.privyhub.stall_signal absent = B5's client. For NativeStreamActivity.kt (vs B5's),
NativeControllerSender.kt and AvcLowLatencyDecoder.kt (vs HEAD): (1) only added lines (difflib), none removed or
changed; (2) every added code line in an allowed form. With the property absent `stallMonitor` is null (the JVM test
`noAndroidPropertyIsOff`), so `stallTick` is never set and the sender's loop calls nothing (`stallTick?.invoke`);
the new decoder accessor and `stallInputs()` are only called through them; the report gains no key.
    B7_ROOT=<root with PrivyHub/> python3 -B proof_flag_absent_client.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B7_ROOT", str(HERE.parents[3])))
J = ROOT / "PrivyHub/app/src/main/java/streaming"
ALLOWED = [r"^\s*//", r"^\s*$", r"^\s*[\})]\s*$", r"^\s*\}\s*catch",
           # NativeStreamActivity
           r"^\s*stallMonitor\?\.let \{ m -> controllerSender\?\.stallTick = \{ now -> m\.tick\(now, stallInputs\(\)\) \} \}$",
           r"^\s*private val stallMonitor: StallMonitor\? by lazy \{ StallSignalFlag\.fromSystem\(\)\?\.let \{ StallMonitor\(it\) \} \}$",
           r"^\s*private fun stallInputs\(\): StallInputs =$", r"^\s*StallInputs\($",
           r"^\s*(outputAgeMs|renderedFrames|inGate|released) = .*,$",
           r"^\s*stallMonitor\?\.let \{ m ->$", r'^\s*root\.put\("stall_signal_[a-z_]+", m\.\w+\)$',
           # NativeControllerSender
           r"^\s*@Volatile$", r"^\s*var stallTick: \(\(Long\) -> ByteArray\?\)\? = null$",
           r"^\s*stallTick\?\.invoke\(System\.nanoTime\(\) / 1_000_000L\)\?\.let \{ d ->$",
           r"^\s*try \{ socket\.send\(DatagramPacket\(d, d\.size\)\) \} catch \(_: Exception\) \{ sendErrors\.incrementAndGet\(\) \}$",
           # AvcLowLatencyDecoder
           r"^\s*fun renderedFrameCount\(\): Long = renderedFrames\.get\(\)$"]
pairs = [("NativeStreamActivity.kt", "predecessors/PrivyHub/NativeStreamActivity.kt"),
         ("NativeControllerSender.kt", "predecessors/PrivyHub/NativeControllerSender.kt"),
         ("AvcLowLatencyDecoder.kt", "predecessors/PrivyHub/AvcLowLatencyDecoder.kt")]
out = ["# B7 (client) — property absent = B5's client (only added lines, all in the allowed forms)", "",
       "| file | removed / changed | added | outside the forms |", "| --- | ---: | ---: | ---: |"]
ok, details = True, []
for new_rel, old_rel in pairs:
    old = (HERE / old_rel).read_text().splitlines(); new = (J / new_rel).read_text().splitlines()
    removed, added = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"): removed += old[i1:i2]
        if tag in ("replace", "insert"): added += new[j1:j2]
    bad = [l for l in added if not any(re.match(p, l) for p in ALLOWED)]
    ok &= not removed and not bad
    out.append(f"| `{new_rel}` | **{len(removed)}** | {len(added)} | **{len(bad)}** |")
    details += [f"### {new_rel}", "", "```"] + added + ["```", ""] + (["Outside:", ""] + bad + [""] if bad else [])
out += ["", f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**. New file `StallSignal.kt` (the flag, the datagram, the "
        "monitor) is reached only through `stallMonitor`, null without the property.", ""] + details
(HERE / "proof_flag_absent_client.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:8]))
sys.exit(0 if ok else 1)
