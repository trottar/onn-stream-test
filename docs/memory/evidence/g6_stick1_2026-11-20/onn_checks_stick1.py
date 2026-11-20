"""G6-STICK1: the onn's code paths unchanged -- the five checks again (as G6-SCREEN1b's), read only, against G6-SCREEN1b's
commit (HEAD). This change touches the touch pad's own files only: NativeStreamActivity, MainActivity, the manifest,
PadSlots, PointerGuard, companion/, tools/ and data/ are all unchanged.
Run from the repository root: python3 docs/memory/evidence/g6_stick1_2026-11-20/onn_checks_stick1.py"""
import hashlib, subprocess, sys

PRE_G6 = "f52ce75b"
BASE = "HEAD"   # G6-SCREEN1b (b2716e17)
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


changed = git("diff", "--name-only", BASE).splitlines() + git("ls-files", "--others", "--exclude-standard").splitlines()
fails, out = [], []
pre, now = nsa_element(git("show", f"{PRE_G6}:{MANIFEST}")), nsa_element(open(MANIFEST, encoding="utf-8").read())
out.append(f"1 manifest NativeStreamActivity element vs pre-G6: {pre} {now} {'EQUAL' if pre == now else 'DIFFERENT'} | manifest changed by STICK1: {'yes' if MANIFEST in changed else 'no'}")
if pre != now or MANIFEST in changed:
    fails.append("1")
src = open(NSA, encoding="utf-8").read()
hooks = ["protected open val streamOrientation: Int get() = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE",
         "protected open fun wrapStreamLayer(streamLayer: FrameLayout): View = streamLayer",
         "protected open fun exemptFromPointerGuard(event: MotionEvent): Boolean = false",
         "protected open fun connectedPadDevices(): List<PadDevice> = AndroidPadDevice.connected()",
         "protected open fun onPlayersOpened(selfRestart: Boolean) {}", "protected open fun onGameplayReleased() {}",
         "protected open fun putHandheldReport(report: JSONObject) {}", "protected open fun onGameSystem(system: String?) {}",
         "protected open fun onGameWidescreen(widescreen: Boolean?) {}",
         "protected open fun pausedFramePreview(source: Bitmap): Bitmap =\n        Bitmap.createScaledBitmap("]
ok_hooks = sum(1 for h in hooks if h in src)
out.append(f"2 NativeStreamActivity changed by STICK1: {'yes' if NSA in changed else 'no'} | hook defaults today's: {ok_hooks}/{len(hooks)}")
if NSA in changed or ok_hooks != len(hooks):
    fails.append("2")
for f in ("PrivyHub/app/src/main/java/streaming/PadSlots.kt", "PrivyHub/app/src/main/java/streaming/PointerGuard.kt"):
    same = git("diff", "--name-only", PRE_G6, "--", f).strip() == ""
    out.append(f"3 {f.rsplit('/', 1)[1]} {'unchanged since pre-G6' if same else 'CHANGED'}")
    if not same:
        fails.append("3")
inside = "if (useHandheldGameScreen()) HandheldStreamActivity::class.java else NativeStreamActivity::class.java" in open(MAIN, encoding="utf-8").read()
out.append(f"4 MainActivity changed by STICK1: {'yes' if MAIN in changed else 'no'} | its G6 statements still inside useHandheldGameScreen(): {'OK' if inside else 'NO'}")
if MAIN in changed or not inside:
    fails.append("4")
hub = [p for p in changed if p.startswith(("companion/", "tools/", "data/"))]
out.append(f"5 companion/, tools/ and data/ changed: {'yes ' + str(hub) if hub else 'no'}")
if hub:
    fails.append("5")
code = sorted(p for p in changed if p.startswith("PrivyHub/"))
out.append(f"STICK1's code change: files {code}")
out.append("ALL FIVE OK" if not fails else "FAILED: " + ", ".join(fails))
print("\n".join(out))
sys.exit(1 if fails else 0)
