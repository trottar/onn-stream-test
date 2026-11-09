"""B70-B72 client mutations: one copy of /tmp/b_q18z_work/PrivyHub under TMPDIR (the main disk), each mutation an
exact one-place edit, the item's JVM class run (gradlew --offline --no-configuration-cache), the edit reverted; the
copy removed at the end. Prints one line per mutation."""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
SRC = Path("/tmp/b_q18z_work/PrivyHub")
J = "app/src/main/java/streaming/"
M = [
 ("B70 M1 the pointer-class bit no longer a pointer source", J + "PointerGuard.kt",
  "(source and SOURCE_CLASS_POINTER) != 0 || FULL.any", "FULL.any", "B70PointerTest"),
 ("B70 M2 the guard on when off", J + "PointerGuard.kt",
  "        if (!enabled || !isPointerSource(source)) return false\n", "        if (!isPointerSource(source)) return false\n",
  "B70PointerTest"),
 ("B70 M3 SOURCE_TOUCHPAD dropped (and the pointer bit not enough for it)", J + "PointerGuard.kt",
  "intArrayOf(SOURCE_MOUSE, SOURCE_TOUCHPAD, SOURCE_MOUSE_RELATIVE", "intArrayOf(SOURCE_MOUSE, SOURCE_MOUSE_RELATIVE",
  "B70PointerTest"),
 ("B70 M4 the capture not asked at focus", J + "PointerGuard.kt",
  "            captureRequests += 1\n            host.requestCapture()\n", "            captureRequests += 1\n",
  "B70PointerTest"),
 ("B71 M1 the entry with one disc (discs >= 1)", J + "DiscChange.kt",
  "if (discs == null || discs <= 1) return null", "if (discs == null || discs < 1) return null", "B71DiscChangeTest"),
 ("B71 M2 the current marker on the wrong disc", J + "DiscChange.kt",
  'if (i == state.disc) " (in the tray)"', 'if (i == (state.disc ?: 0) + 1) " (in the tray)"', "B71DiscChangeTest"),
 ("B72a M1 the card's gap dropped", J + "N64LayoutCard.kt",
  "maxOf(basePx, cardBottomPx + GAP_PX)", "maxOf(basePx, cardBottomPx)", "B72ClientTest"),
 ("B72a M2 the property ignored (always the top)", J + "N64LayoutCard.kt",
  "        if (top) android.view.Gravity.TOP", "        if (true) android.view.Gravity.TOP", "B72ClientTest"),
 ("B72a M3 the top card keeps B67's key (never shown again on an onn that saw it)", J + "N64LayoutCard.kt",
  "if (top) KEY_SHOWN_TOP else KEY_SHOWN", "KEY_SHOWN", "B72ClientTest"),
]
if len(sys.argv) > 1:                       # a title prefix: only those mutations
    M = [m for m in M if m[0].startswith(sys.argv[1])]
base = Path(os.environ.get("TMPDIR", "/tmp"))
d = Path(tempfile.mkdtemp(prefix="b70_jvm_mut_", dir=base)) / "PrivyHub"
shutil.copytree(SRC, d, ignore=shutil.ignore_patterns("build", ".gradle"))
try:
    for title, rel, old, new, cls in M:
        f = d / rel
        s = f.read_text()
        assert s.count(old) == 1, title
        f.write_text(s.replace(old, new))
        res = d / "app/build/test-results/testDebugUnitTest"
        shutil.rmtree(res, ignore_errors=True)
        r = subprocess.run(["bash", "./gradlew", ":app:testDebugUnitTest", "--offline", "--no-configuration-cache", "-q",
                            "--tests", f"com.safeiot.privyhub.streaming.{cls}"], cwd=d, capture_output=True, text=True,
                           timeout=900)
        x = res / f"TEST-com.safeiot.privyhub.streaming.{cls}.xml"
        counts = re.search(r'tests="(\d+)" skipped="\d+" failures="(\d+)" errors="(\d+)"', x.read_text()[:2000]) if x.exists() else None
        failing = re.findall(r'<testcase name="([^"]+)"[^>]*>\s*<failure', x.read_text()) if x.exists() else []
        what = (f"{cls} tests {counts.group(1)} failures {counts.group(2)} errors {counts.group(3)}" if counts
                else "no result (compile failed)")
        print(f"{title}: {'CAUGHT' if r.returncode else 'SURVIVED'} -- {what}; failing: {', '.join(failing)}", flush=True)
        f.write_text(s)
finally:
    shutil.rmtree(d.parent)
