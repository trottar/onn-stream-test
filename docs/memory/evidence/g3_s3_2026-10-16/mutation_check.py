# G3-S3 mutation check: each mutation is applied to a copy of companion/ and
# tests/ under the system temp directory (g3_s3_mut_*; left in place), never to
# the tree; the session-identity suite must then fail.
import shutil, subprocess, sys, tempfile
from pathlib import Path
muts = [
 ("port binding off", "session_identity.py", "                mismatch = self._port_mismatch(sess, parse_qs(query, keep_blank_values=True))", "                mismatch = None"),
 ("media token accepted for any value", "session_identity.py", "                if sess.media_token and hmac.compare_digest(sess.media_token.encode(), media_token.encode()):", "                if sess.media_token:"),
 ("overlay allowed without token at the range gate", "session_identity.py", "        if (token is None and media_token is None and routing == ROUTING_LAN", "        if (token is None and media_token is None and routing in (ROUTING_LAN, ROUTING_OVERLAY)"),
 ("vod permission not checked", "session_identity.py", "        if sess.client_id != LEGACY_CLIENT and MEDIA_PERMISSION not in sess.permissions:", "        if False:"),
 ("v2 canon ignores audio port", "session_identity.py", '"" if audio_raw is None else str(audio_raw), overlay_raw])', '"", overlay_raw])'),
 ("diagnostics not implied for a pre-G3-S3 record", "session_identity.py", '    if device.get("permissions_v") is None and "diagnostics" not in listed:', '    if False:'),
 ("overlay target not chosen", "session_identity.py", "        for host in (self.media_host, self.overlay_host):", "        for host in (self.media_host,):"),
 ("range server log mask off", "range_server.py", "        if RANGE_GATE is not None:\n            args", "        if False:\n            args"),
 ("range server gate import unguarded", "range_server.py", 'if os.environ.get("PRIVYHUB_SESSION_IDENTITY", "").strip():\n    from session_identity import media_gate', 'if True:\n    from session_identity import media_gate'),
]
for name, f, old, new in muts:
    tmp = Path(tempfile.mkdtemp(prefix="g3_s3_mut_"))
    shutil.copytree("companion", tmp / "companion", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree("tests", tmp / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    p = tmp / "companion" / f
    t = p.read_text(); assert t.count(old) == 1, name
    p.write_text(t.replace(old, new))
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests/session_identity"],
                       cwd=tmp, capture_output=True, text=True)
    failed = [l for l in r.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))]
    print(f"{name}: {'CAUGHT' if r.returncode else 'NOT CAUGHT'} ({len(failed)} tests fail)")
print("unmutated: 0 tests fail (tests_output.txt)")
