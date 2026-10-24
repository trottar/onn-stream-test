#!/usr/bin/env python3
"""B16 (client): the host's `stall_resume` key absent = today (the tree after B15).
NativeStreamActivity.kt vs predecessors/: (1) only added lines (difflib); (2) every added line one of the forms below.
Without the key `fastReady` stays null: the only assignment of a FastReady sits inside `if (json.optJSONObject(
"stall_resume")?.optBoolean("fast_ready", false) == true)`, false when the host's start response has no such key (the
host adds it only with PRIVYHUB_STALL_RESUME=1: the host proof). Then every other new statement is a `fastReady?.let`
no-op, `fastReady = null` (null to null), or a declaration: the lazy `fastReadyTick` is touched only inside
`fastReady?.let` blocks and its own body (never initialised), `fastReadyInputs()` is called only from that body, and
the report gains no key. FastReady.kt is new and reached only through `fastReady`.
    B16_ROOT=<root with PrivyHub/> python3 -B proof_flag_absent_client.py"""
import difflib, os, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("B16_ROOT", str(HERE.parents[3])))
J = "PrivyHub/app/src/main/java/streaming"
FORMS = {
    "no-op without a FastReady (`?.` on null)": [
        "fastReady?.let { uiHandler.removeCallbacks(fastReadyTick) }", "fastReady?.let { f ->",
        "root.put(\"fast_ready_releases\", f.releases)", "root.put(\"fast_ready_frame_to_post_ms\", f.lastFrameToPostMs)",
        "f.onRecoveryEntered(decoder?.renderedFrameCount() ?: 0L)", "uiHandler.removeCallbacks(fastReadyTick)",
        "uiHandler.postDelayed(fastReadyTick, 50L)"],
    "null to null": ["fastReady = null"],
    "the one gate (false without the host's key) and its body": [
        "if (json.optJSONObject(FastReadyHint.KEY)?.optBoolean(FastReadyHint.FIELD, false) == true) {",
        "fastReady = FastReady()"],
    "declarations reached only through a FastReady": [
        "@Volatile", "private var fastReady: FastReady? = null", "private val fastReadyTick: Runnable by lazy {",
        "object : Runnable {", "override fun run() {", "val f = fastReady ?: return",
        "if (!sessionStarted || stopping || !recoveryActive || gameplayReleased) return",
        "if (f.tick(fastReadyInputs())) {", "requestGameplayRelease()", "return", "uiHandler.postDelayed(this, 50L)",
        "private fun fastReadyInputs(): FastReadyInputs =", "FastReadyInputs(", "recoveryActive = recoveryActive,",
        "released = gameplayReleased,", "requestInFlight = releaseRequestInFlight,",
        "hostMetadataComplete = hostMetadataComplete,", "waitingForIdr = receiver?.snapshot()?.waitingForIdr ?: true,",
        "renderedFrames = decoder?.renderedFrameCount() ?: 0L,", "outputAgeMs = decoder?.lastOutputAgeMs() ?: -1L,"],
}
ALLOWED = {l for ls in FORMS.values() for l in ls}
name = "NativeStreamActivity.kt"
old = (HERE / "predecessors" / name).read_text().splitlines(); new = (ROOT / J / name).read_text().splitlines()
removed, added = [], []
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
    if tag in ("replace", "delete"): removed += old[i1:i2]
    if tag in ("replace", "insert"): added += new[j1:j2]
def ok_line(l):
    s = l.strip()
    return s == "" or s.startswith("//") or re.fullmatch(r"[\})]+", s) is not None or s in ALLOWED
bad = [l for l in added if not ok_line(l)]
# the gate appears once, and FastReady() is constructed only there
gate = [i for i, l in enumerate(new) if "FastReadyHint.KEY" in l]
ctor = [i for i, l in enumerate(new) if "FastReady()" in l]
gate_ok = len(gate) == 1 and ctor == [gate[0] + 1]
tick_refs = [l.strip() for l in new if "fastReadyTick" in l]
tick_ok = sorted(tick_refs) == sorted(["fastReady?.let { uiHandler.removeCallbacks(fastReadyTick) }",
                                       "private val fastReadyTick: Runnable by lazy {",
                                       "uiHandler.removeCallbacks(fastReadyTick)", "uiHandler.postDelayed(fastReadyTick, 50L)"])
ok = not removed and not bad and gate_ok and tick_ok
out = ["# B16 (client) — the host's key absent = today (only added lines, all in the stated forms)", "",
       "| file | removed / changed | added | outside the forms | the one gate | `fastReadyTick` only in `?.let` |",
       "| --- | ---: | ---: | ---: | --- | --- |",
       f"| `{name}` | **{len(removed)}** | {len(added)} | **{len(bad)}** | {'yes' if gate_ok else 'NO'} | "
       f"{'yes' if tick_ok else 'NO'} |", "",
       f"Result: **{'PROVEN' if ok else 'NOT PROVEN'}**. `FastReady.kt` (new) is reached only through `fastReady`.", ""]
for k, ls in FORMS.items():
    out.append(f"- {k}: " + ", ".join(f"`{l}`" for l in ls))
out += ["", "```"] + added + ["```"] + (["", "Outside:"] + bad if bad else [])
(HERE / "proof_flag_absent_client.md").write_text("\n".join(out) + "\n")
print("\n".join(out[:7]))
sys.exit(0 if ok else 1)
