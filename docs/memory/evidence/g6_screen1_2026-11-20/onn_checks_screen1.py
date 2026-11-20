"""G6-SCREEN1: the onn's code paths unchanged -- G6-HM4b's five checks (onn_unchanged_checks.txt) again, read only.
Run from the repository root: python3 docs/memory/evidence/g6_screen1_2026-11-20/onn_checks_screen1.py"""
import hashlib, re, subprocess, sys

PRE_G6 = "f52ce75b"          # the G6 record, before any G6 code
BASE = "HEAD"                # G6-HM4b's tree (3320a0ae and later: no G6 code since)
NSA = "PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt"
MAIN = "PrivyHub/app/src/main/java/MainActivity.kt"
MANIFEST = "PrivyHub/app/src/main/AndroidManifest.xml"


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout


def nsa_element(text):
    lines = text.splitlines(keepends=True)
    i = next(k for k, l in enumerate(lines) if "NativeStreamActivity" in l)
    s = i
    while "<activity" not in lines[s]:
        s -= 1
    e = i
    while not ("/>" in lines[e] or "</activity>" in lines[e]):
        e += 1
    return hashlib.sha256("".join(lines[s:e + 1]).encode()).hexdigest()[:16]


fails, out = [], []
changed = [l for l in git("diff", "--name-only", BASE).splitlines()] + \
          [l for l in git("ls-files", "--others", "--exclude-standard").splitlines()]
code = sorted(p for p in changed if p.startswith("PrivyHub/") and p.endswith(".kt"))

# 1 the manifest's NativeStreamActivity element
pre, now = nsa_element(git("show", f"{PRE_G6}:{MANIFEST}")), nsa_element(open(MANIFEST, encoding="utf-8").read())
m_changed = MANIFEST in changed
out.append(f"1 manifest NativeStreamActivity element vs pre-G6: {pre} {now} {'EQUAL' if pre == now else 'DIFFERENT'} | manifest changed by SCREEN1: {'yes' if m_changed else 'no'}")
if pre != now or m_changed:
    fails.append("1")

# 2 NativeStreamActivity: every hunk a hook or the hook's call; every hook's default today's expression
diff = git("diff", "-U0", BASE, "--", NSA)
added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
removed = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
# the scaled-copy call's lines (its closing ")" stays: the new call `pausedFramePreview(source)` ends with it)
expected_removed = ["            Bitmap.createScaledBitmap(", "                source,", "                480,",
                    "                270,", "                true"]
src = open(NSA, encoding="utf-8").read()
hooks = {
    "H1 streamOrientation": "protected open val streamOrientation: Int get() = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE",
    "H2 wrapStreamLayer": "protected open fun wrapStreamLayer(streamLayer: FrameLayout): View = streamLayer",
    "H3 exemptFromPointerGuard": "protected open fun exemptFromPointerGuard(event: MotionEvent): Boolean = false",
    "H4 connectedPadDevices": "protected open fun connectedPadDevices(): List<PadDevice> = AndroidPadDevice.connected()",
    "H5 onPlayersOpened": "protected open fun onPlayersOpened(selfRestart: Boolean) {}",
    "H6 onGameplayReleased": "protected open fun onGameplayReleased() {}",
    "H7 putHandheldReport": "protected open fun putHandheldReport(report: JSONObject) {}",
    "H10 onGameSystem": "protected open fun onGameSystem(system: String?) {}",
    "H11 pausedFramePreview": "protected open fun pausedFramePreview(source: Bitmap): Bitmap =\n        Bitmap.createScaledBitmap(\n            source,\n            480,\n            270,\n            true\n        )",
}
ok_hooks = sum(1 for v in hooks.values() if v in src)
removed_ok = [r for r in removed if r.strip()] == expected_removed
allowed_added = ("// G6-SCREEN1", "onGameSystem(json.optJSONObject(\"game_session\")?.optJSONObject(\"game\")?.optString(\"system\"))",
                 "val preview =", "pausedFramePreview(", "source", ")", "/** H10", "/** H11", "protected open fun",
                 "Bitmap.createScaledBitmap(", "480,", "270,", "true", "protected val streamSurface: View get() = surfaceView")
stray = [a for a in added if a.strip() and not a.strip().startswith(allowed_added)]
out.append(f"2 NativeStreamActivity hunks: {len(added)} lines added, {len(removed)} removed; removed = the scaled-copy expression moved into H11's default: {'yes' if removed_ok else 'NO'}; other lines: {len(stray)} | hook defaults today's: {ok_hooks}/{len(hooks)}")
out.append("  added: H10 onGameSystem (no-op default; one call after H5), H11 pausedFramePreview (default = the replaced expression), accessor streamSurface (H8's kind)")
if not removed_ok or stray or ok_hooks != len(hooks):
    fails.append("2")
    out.extend("  stray: " + s for s in stray)

# 3 PadSlots.kt and PointerGuard.kt unchanged since pre-G6
for f in ("PrivyHub/app/src/main/java/streaming/PadSlots.kt", "PrivyHub/app/src/main/java/streaming/PointerGuard.kt"):
    same = git("diff", "--name-only", PRE_G6, "--", f).strip() == ""
    out.append(f"3 {f.rsplit('/', 1)[1]} {'unchanged since pre-G6' if same else 'CHANGED'}")
    if not same:
        fails.append("3")

# 4 MainActivity untouched by SCREEN1; its G6 statement still inside useHandheldGameScreen()
main_changed = MAIN in changed
inside = "if (useHandheldGameScreen()) HandheldStreamActivity::class.java else NativeStreamActivity::class.java" in open(MAIN, encoding="utf-8").read()
out.append(f"4 MainActivity changed by SCREEN1: {'yes' if main_changed else 'no'} | its G6 statement still inside useHandheldGameScreen(): {'OK' if inside else 'NO'}")
if main_changed or not inside:
    fails.append("4")

# 5 companion/ and tools/ untouched
ct = [p for p in changed if p.startswith(("companion/", "tools/"))]
out.append(f"5 companion/ and tools/ changed: {'yes ' + str(ct) if ct else 'no'}")
if ct:
    fails.append("5")

out.append(f"SCREEN1's code change: files {code}")
out.append("ALL FIVE OK" if not fails else "FAILED: " + ", ".join(fails))
print("\n".join(out))
sys.exit(1 if fails else 0)
