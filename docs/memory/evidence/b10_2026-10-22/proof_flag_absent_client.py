#!/usr/bin/env python3
"""B10 (client): debug.privyhub.loss_guard absent = the CONFIRMED client (cb0935c8's sources, HEAD 0f4b551). For
RtpH264Receiver.kt, NativeStreamActivity.kt and NativeControllerSender.kt (vs predecessors/): (1) only added lines
(difflib), none removed or changed; (2) every added code line in an allowed form. With the property absent `lossGuard`
is null (the JVM test `flagTable`: fromSystem() is null off-device), so: the receiver's `lossGuard?.onDrop()` calls
nothing; `lossGuard?.deliver(isIdr) == false` is `null == false` = false, so the original `else` branch runs exactly as
before; `keyframeTick` is never set (the sender calls nothing); the report and the heartbeat gain nothing
(`lossGuard?.query() ?: ""`). The JVM test `receiverWithoutAGuardIsToday` runs the real receiver with no guard.
    B10_ROOT=<root with PrivyHub/> python3 -B proof_flag_absent_client.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B10_ROOT", str(HERE.parents[3])))
J = "PrivyHub/app/src/main/java/streaming"
ALLOWED = [r"^\s*//", r"^\s*$", r"^\s*[\})]\s*$", r"^\s*@Volatile$",
           # RtpH264Receiver
           r"^\s*var lossGuard: LossGuard\? = null$",
           r"^\s*if \(!waitingForIdr\) lossGuard\?\.onDrop\(\)$",
           r"^\s*if \(currentCorrupt && !waitingForIdr\) lossGuard\?\.onDrop\(\)$",
           r"^\s*\} else if \(lossGuard\?\.deliver\(isIdr\) == false\) \{$",
           # NativeControllerSender
           r"^\s*var keyframeTick: \(\(\) -> ByteArray\?\)\? = null$",
           r"^\s*keyframeTick\?\.invoke\(\)\?\.let \{ d ->$",
           r"^\s*try \{ socket\.send\(DatagramPacket\(d, d\.size\)\) \} catch \(_: Exception\) \{ sendErrors\.incrementAndGet\(\) \}$",
           # NativeStreamActivity
           r"^\s*lossGuard\?\.let \{ g -> controllerSender\?\.keyframeTick = \{ g\.takeRequest\(\) \} \}$",
           r"^\s*receiver\?\.lossGuard = lossGuard$",
           r"^\s*lossGuard\?\.let \{ g ->$",
           r'^\s*root\.put\("(loss_guard_[a-z_]+|frames_after_dropped_reference|keyframe_requests_sent)", g\.[\w.]+(\(\))?\)$',
           r"^\s*private val lossGuard: LossGuard\? by lazy \{ LossGuardFlag\.fromSystem\(\)\?\.let \{ LossGuard\(it\) \} \}$",
           r'^\s*\(lossGuard\?\.query\(\) \?: ""\) \+$']
FILES = ("RtpH264Receiver.kt", "NativeStreamActivity.kt", "NativeControllerSender.kt")
out = ["# B10 (client) — property absent = the CONFIRMED client (only added lines, all in the allowed forms)", "",
       "| file | removed / changed | added | outside the forms |", "| --- | ---: | ---: | ---: |"]
ok, details = True, []
for name in FILES:
    old = (HERE / "predecessors" / J / name).read_text().splitlines(); new = (ROOT / J / name).read_text().splitlines()
    removed, added = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"): removed += old[i1:i2]
        if tag in ("replace", "insert"): added += new[j1:j2]
    bad = [l for l in added if not any(re.match(p, l) for p in ALLOWED)]
    ok &= not removed and not bad
    out.append(f"| `{name}` | **{len(removed)}** | {len(added)} | **{len(bad)}** |")
    details += [f"### {name}", "", "```"] + added + ["```", ""] + (["Outside:", ""] + bad + [""] if bad else [])
out += ["", f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**. New file `LossGuard.kt` (the flag, the datagram, the "
        "guard) is reached only through `lossGuard`, null without the property.", ""] + details
(HERE / "proof_flag_absent_client.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:8]))
sys.exit(0 if ok else 1)
