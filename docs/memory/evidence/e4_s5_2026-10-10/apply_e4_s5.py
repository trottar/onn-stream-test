#!/usr/bin/env python3
"""E4-S5 -- apply the one change the offline pass named (companion/native_stream.py, behind
PRIVYHUB_SNES_CAPTURE_FIX=output_rate): the x11grab encoder's output rate set explicitly to the profile's fps. Staged
while E4-S3 / E4-S4 ran; applied only after E4-S4's runs. Refuses on an anchor or parse failure (the predecessor bytes
restored); writes e4_s5_change.diff and change_sha256.txt."""
import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NS = REPO / "companion/native_stream.py"

ANCHOR = '''            "-f",
            "rtp",
            destination,
        ]

        return command
    @staticmethod
    def _kill_managed_process('''
CHANGE = '''            "-f",
            "rtp",
            destination,
        ]

        # E4-S5: PRIVYHUB_SNES_CAPTURE_FIX=output_rate -> the encoder's output rate is the profile's fps (an output -r)
        # instead of x11grab's probed input rate (tbr). A small capture window (the SNES core's 897x672) is sometimes
        # probed at 59 or 59.94 from its first frames, and the encoder then drops one frame per second (or per ~16 s)
        # for the whole session (E4-S5 §1). Absent = today.
        if os.environ.get("PRIVYHUB_SNES_CAPTURE_FIX") == "output_rate":
            at = command.index("-an")
            command[at:at] = ["-r", str(self.FPS)]

        return command
    @staticmethod
    def _kill_managed_process('''


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    src = NS.read_text()
    if src.count(ANCHOR) != 1:
        sys.exit(f"refusing: anchor found {src.count(ANCHOR)} times")
    bk = HERE / "predecessor_native_stream.py.txt"
    bk.write_bytes(NS.read_bytes())
    pre = sha(NS)
    NS.write_text(src.replace(ANCHOR, CHANGE))
    r = subprocess.run([sys.executable, "-c", f"import ast; ast.parse(open({str(NS)!r}).read())"], capture_output=True, text=True)
    if r.returncode:
        NS.write_bytes(bk.read_bytes())
        sys.exit(f"parse failed, predecessor restored: {r.stderr}")
    diff = subprocess.run(["diff", "-u", "--label", "a/companion/native_stream.py", "--label", "b/companion/native_stream.py",
                           str(bk), str(NS)], capture_output=True, text=True).stdout
    (HERE / "e4_s5_change.diff").write_text(diff)
    (HERE / "change_sha256.txt").write_text(f"predecessor companion/native_stream.py {pre}\nafter companion/native_stream.py {sha(NS)}\n")
    print("applied", (HERE / "change_sha256.txt").read_text())


if __name__ == "__main__":
    main()
