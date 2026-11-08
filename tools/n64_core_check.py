#!/usr/bin/env python3
"""B59: is the N64 core in place? -- "bundled" (in RetroArch's cores folder) or "fetch needed". Looks only: no network,
the core is never loaded or run. With --keys: the core-options keys B59 writes, found / missing as byte strings in the
installed core (A runs this after the fetch, before the first launch; a missing key is inert -- the core default runs).

    python3 tools/n64_core_check.py [--keys] [--core mupen64plus_next] [--root <repo>]

With --remap (B62): the core remap file against the default N64 layout (matches / matches core / differs / absent),
the remap files that would shadow it, the folder's writability. Read-only.

Prints one JSON object (no path outside the repo, no title). Exit 0 bundled, 3 fetch needed, 4 a key missing,
5 the remap differs.
Design: docs/memory/evidence/b59_2026-11-08/design_written_before_code.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))

import n64_session  # noqa: E402  (imported directly: the check needs no flag and changes nothing)

FETCH_HINT = ("A, with the user's go: the core's zip from the libretro buildbot for this RetroArch "
              "(stable/<version>/linux/x86_64/ if it lists per-core files, else nightly/linux/x86_64/latest/), "
              "unzipped into " + n64_session.CORES_DIR + "/, the zip's and the .so's sha256 recorded")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--keys", action="store_true", help="check the option keys in the installed core")
    ap.add_argument("--core", default=None, help="a core name (default: PRIVYHUB_N64_CORE, else mupen64plus_next)")
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--remap", action="store_true",
                    help="B62: the core remap against the default layout (read-only; before any launch)")
    ap.add_argument("--config-dir", type=Path, default=None,
                    help="RetroArch's config dir (default: $XDG_CONFIG_HOME or ~/.config, + retroarch/config)")
    a = ap.parse_args(argv)
    env = dict(os.environ)
    if a.core is not None:
        env[n64_session.CORE_ENV] = a.core
    out = n64_session.presence(a.root, env)
    code = 0 if out["state"] == "bundled" else 3
    if code:
        out["next"] = FETCH_HINT
    elif a.keys:
        core = Path(a.root) / n64_session.CORES_DIR / out["core"]
        if n64_session.options_library(out["core"]) is None:
            out["keys"] = {"found": [], "missing": [], "note": "no options written for this core"}
        else:
            out["keys"] = n64_session.keys_in_core(core)
            code = 4 if out["keys"]["missing"] else 0
    if a.remap:
        cfg = a.config_dir or (Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "retroarch/config")
        out["remap"] = n64_session.remap_check(cfg, out["core"])
        out["remap"]["layout_default"] = n64_session.DEFAULT_LAYOUT
        if out["remap"].get("state") == "differs" and not code:
            code = 5
    print(json.dumps(out, indent=1))
    return code


if __name__ == "__main__":
    sys.exit(main())
