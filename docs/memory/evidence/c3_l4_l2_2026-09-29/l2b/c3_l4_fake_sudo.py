#!/usr/bin/env python3
"""TEST ONLY: a fake `sudo` for tools/c3_l4_nft_night.py (`--fast --sudo-cmd tools/c3_l4_fake_sudo.py`).

It never runs anything as root and never runs `nft`. It logs its argv to
$FAKE_SUDO_DIR/argv.jsonl and models the one table the harness may build
(`inet privyhub_fault`) in $FAKE_SUDO_DIR/state.json, answering `nft list`
the way nft prints it (counters included; the counter rule grows at the 7000
wire rate, ~1,083 kB/s, so the calibration has something to read).

  sudo -v            -> 0 (the "password"); removes $FAKE_SUDO_DIR/deny
  sudo -n -v         -> 0, or "sudo: a password is required" (rc 1) while deny exists
  sudo -n nft ...    -> the model, or the same refusal while deny exists
                        (while $FAKE_SUDO_DIR/mangle exists, `list table` shows an empty chain:
                        the harness's verify-mismatch path)
  anything else      -> rc 2 ("fake sudo: unexpected")
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

D = Path(os.environ.get("FAKE_SUDO_DIR", "/tmp/c3_l4_fake_sudo"))
T = "inet privyhub_fault"
RATE_7000 = 1_083_000


def load() -> dict:
    try:
        return json.loads((D / "state.json").read_text())
    except Exception:
        return {"table": False, "chain": False, "rules": []}


def save(st: dict) -> None:
    (D / "state.json").write_text(json.dumps(st))


def err(msg: str, rc: int = 1) -> int:
    sys.stderr.write(msg + "\n")
    return rc


def render(st: dict) -> str:
    now = time.time()
    lines = [f"table {T} {{", "\tchain flt {", "\t\ttype filter hook output priority filter; policy accept;"]
    for r in ([] if (D / "mangle").exists() else st["rules"]):
        age = max(0.0, now - r["t0"])
        byts = int(age * RATE_7000) if r["text"].endswith(" counter") else int(age * 20_000)
        pk = byts // 1200
        lines.append("\t\t" + r["text"].replace(" counter", f" counter packets {pk} bytes {byts}", 1))
    lines += ["\t}", "}"]
    return "\n".join(lines) + "\n"


def nft(args: list[str]) -> int:
    st = load()
    cmd = " ".join(args)
    if cmd == f"add table {T}":
        st["table"] = True
    elif cmd == f"add chain {T} flt {{ type filter hook output priority 0; }}":
        if not st["table"]:
            return err("Error: Could not process rule: No such file or directory")
        st["chain"] = True
    elif cmd.startswith(f"add rule {T} flt "):
        if not st["chain"]:
            return err("Error: Could not process rule: No such file or directory")
        st["rules"].append({"text": cmd[len(f"add rule {T} flt "):], "t0": time.time()})
    elif cmd == f"flush chain {T} flt":
        if not st["chain"]:
            return err("Error: Could not process rule: No such file or directory")
        st["rules"] = []
    elif cmd == f"delete table {T}":
        if not st["table"]:
            return err("Error: Could not process rule: No such file or directory\n"
                       f"delete table {T}\n                   ^^^^^^^^^^^^^^")
        st = {"table": False, "chain": False, "rules": []}
    elif cmd == "list tables":
        sys.stdout.write("table inet filter\n" + (f"table {T}\n" if st["table"] else ""))
        return 0
    elif cmd == f"list table {T}":
        if not st["table"]:
            return err("Error: No such file or directory\nlist table inet privyhub_fault\n"
                       "                ^^^^^^^^^^^^^^")
        sys.stdout.write(render(st))
        return 0
    else:
        return err(f"Error: syntax error (fake nft does not model: {cmd})")
    save(st)
    return 0


def main() -> int:
    D.mkdir(parents=True, exist_ok=True)
    args = sys.argv[1:]
    with open(D / "argv.jsonl", "a") as fh:
        fh.write(json.dumps({"t": time.time(), "argv": args}) + "\n")
    if args == ["-v"]:
        (D / "deny").unlink(missing_ok=True)
        return 0
    if args[:1] != ["-n"]:
        return err(f"fake sudo: unexpected {args}", 2)
    if (D / "deny").exists():
        return err("sudo: a password is required")
    rest = args[1:]
    if rest == ["-v"]:
        return 0
    if rest[:1] != ["nft"]:
        return err(f"fake sudo: unexpected {rest}", 2)
    return nft(rest[1:])


if __name__ == "__main__":
    sys.exit(main())
