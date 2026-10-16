"""G1-S1: `python3 -m companion.overlay --state` — one read, as the companion would.

Reads the host through the selected provider (`--provider`, else
`PRIVYHUB_OVERLAY_PROVIDER`, else `none`) and prints the public state as
JSON: the endpoint redacted to present/absent + a short hash, no
diagnostics unless `--diagnostics` (booleans and enums only). It does not
touch the running companion.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

from . import OVERLAY_PROVIDER_ENV, PROVIDERS, select_provider
from .none import NoneProvider


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m companion.overlay")
    ap.add_argument("--state", action="store_true", help="print the overlay state once")
    ap.add_argument("--provider", choices=PROVIDERS, help=f"default: ${OVERLAY_PROVIDER_ENV}, else none")
    ap.add_argument("--diagnostics", action="store_true", help="add the provider's booleans/enums")
    args = ap.parse_args(argv)
    if not args.state:
        ap.print_help()
        return 2

    env = dict(os.environ)
    if args.provider:
        env[OVERLAY_PROVIDER_ENV] = args.provider
    provider = select_provider(env) or NoneProvider()
    state = provider.state()
    doc = {
        "selected_by": "--provider" if args.provider else (
            OVERLAY_PROVIDER_ENV if os.environ.get(OVERLAY_PROVIDER_ENV, "").strip() else "default (none)"),
        "tailscale_binary_installed": shutil.which("tailscale") is not None,
        "state": state.public(),
    }
    if args.diagnostics:
        doc["diagnostics"] = state.diagnostics
    json.dump(doc, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
