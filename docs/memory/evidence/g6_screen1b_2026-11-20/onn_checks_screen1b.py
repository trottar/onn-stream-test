"""G6-SCREEN1b: the onn's code paths unchanged -- the five checks again (G6-SCREEN1's onn_checks_screen1.py), read only,
against G6-SCREEN1's commit (HEAD). Check 4 now allows MainActivity's one added term, behind useHandheldGameScreen();
check 5: tools/ untouched and companion/ changed only in the four files of the hub change (the no-field launch is
proved identical by no_field_identity_check.py).
Run from the repository root: python3 docs/memory/evidence/g6_screen1b_2026-11-20/onn_checks_screen1b.py"""
import hashlib, re, subprocess, sys

PRE_G6 = "f52ce75b"          # the G6 record, before any G6 code
BASE = "HEAD"                # G6-SCREEN1's commit (27b3c937)
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
out.append(f"1 manifest NativeStreamActivity element vs pre-G6: {pre} {now} {'EQUAL' if pre == now else 'DIFFERENT'} | manifest changed by SCREEN1b: {'yes' if m_changed else 'no'}")
if pre != now or m_changed:
    fails.append("1")

# 2 NativeStreamActivity: every hunk a hook or the hook's call; every hook's default today's expression
diff = git("diff", "-U0", BASE, "--", NSA)
added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
removed = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
# the scaled-copy call's lines (its closing ")" stays: the new call `pausedFramePreview(source)` ends with it)
expected_removed = []        # SCREEN1b only adds
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
    "H12 onGameWidescreen": "protected open fun onGameWidescreen(widescreen: Boolean?) {}",
    "H11 pausedFramePreview": "protected open fun pausedFramePreview(source: Bitmap): Bitmap =\n        Bitmap.createScaledBitmap(\n            source,\n            480,\n            270,\n            true\n        )",
}
ok_hooks = sum(1 for v in hooks.values() if v in src)
removed_ok = [r for r in removed if r.strip()] == expected_removed
allowed_added = ("// G6-SCREEN1b", "onGameWidescreen(json.optJSONObject(\"game_session\")?.let { if (it.has(\"widescreen\")) it.optBoolean(\"widescreen\") else null })",
                 "/** H12", "protected open fun onGameWidescreen(widescreen: Boolean?) {}")
stray = [a for a in added if a.strip() and not a.strip().startswith(allowed_added)]
out.append(f"2 NativeStreamActivity hunks: {len(added)} lines added, {len(removed)} removed; other lines: {len(stray)} | hook defaults today's: {ok_hooks}/{len(hooks)}")
out.append("  added: H12 onGameWidescreen (no-op default; one call after H10, reading the reply's game_session only)")
if not removed_ok or stray or ok_hooks != len(hooks):
    fails.append("2")
    out.extend("  stray: " + s for s in stray)

# 3 PadSlots.kt and PointerGuard.kt unchanged since pre-G6
for f in ("PrivyHub/app/src/main/java/streaming/PadSlots.kt", "PrivyHub/app/src/main/java/streaming/PointerGuard.kt"):
    same = git("diff", "--name-only", PRE_G6, "--", f).strip() == ""
    out.append(f"3 {f.rsplit('/', 1)[1]} {'unchanged since pre-G6' if same else 'CHANGED'}")
    if not same:
        fails.append("3")

# 4 MainActivity: its one added term behind useHandheldGameScreen() ("" on the onn: no touchscreen, so no choice)
mtext = open(MAIN, encoding="utf-8").read()
inside = "if (useHandheldGameScreen()) HandheldStreamActivity::class.java else NativeStreamActivity::class.java" in mtext
mdiff = git("diff", "-U0", BASE, "--", MAIN)
m_add = [l[1:].strip() for l in mdiff.splitlines() if l.startswith("+") and not l.startswith("+++")]
m_rem = [l[1:].strip() for l in mdiff.splitlines() if l.startswith("-") and not l.startswith("---")]
m_ok = (m_rem == ["DiscSafe.launchSuffix(startDisc)"]
        and m_add == ["DiscSafe.launchSuffix(startDisc) +",
                      "// G6-SCREEN1b: the handheld screen's launch (PS2 without its widescreen patch); \"\" = today's URL",
                      "com.safeiot.privyhub.streaming.HandheldGeometry.launchSuffix(useHandheldGameScreen())"])
out.append(f"4 MainActivity: {len(m_add)} lines added, {len(m_rem)} removed; only the launch URL's added term launchSuffix(useHandheldGameScreen()): {'OK' if m_ok else 'NO'} | the screen choice still inside useHandheldGameScreen(): {'OK' if inside else 'NO'}")
if not (m_ok and inside):
    fails.append("4")

# 5 tools/ untouched; companion/ only the hub change's four files
tl = [p for p in changed if p.startswith("tools/")]
cp = sorted(p for p in changed if p.startswith("companion/"))
want = ["companion/games/emulator_manager.py", "companion/plugins/games.py", "companion/ps2_patches.py", "companion/relaunch_ports.py"]
out.append(f"5 tools/ changed: {'yes ' + str(tl) if tl else 'no'} | companion/ changed: {cp} ({'the four expected' if cp == want else 'UNEXPECTED'})")
if tl or cp != want:
    fails.append("5")

out.append(f"SCREEN1b's client code change: files {code}")
out.append("ALL FIVE OK" if not fails else "FAILED: " + ", ".join(fails))
print("\n".join(out))
sys.exit(1 if fails else 0)
