#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPANION_DIR = PROJECT_ROOT / "companion"

if str(COMPANION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPANION_DIR))

from games.metadata_importer import SYSTEM_SPECS, run_metadata_update  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Update PrivyHub's local game metadata and box-art cache using "
            "the existing Games catalog."
        )
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use only already-cached provider data/artwork.",
    )
    parser.add_argument(
        "--refresh-provider-cache",
        action="store_true",
        help=(
            "Refresh cached Libretro DAT sources even if the seven-day "
            "cache is still fresh."
        ),
    )
    parser.add_argument(
        "--no-artwork",
        action="store_true",
        help="Update metadata but do not download box art.",
    )
    parser.add_argument(
        "--system",
        choices=sorted(SYSTEM_SPECS),
        default="",
        help="Restrict the run to one PrivyHub game system.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Process at most N scanned games. Useful for diagnostics.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete run result as JSON.",
    )
    args = parser.parse_args()

    try:
        report = run_metadata_update(
            PROJECT_ROOT,
            offline=args.offline,
            refresh_provider_cache=args.refresh_provider_cache,
            download_artwork=not args.no_artwork,
            only_system=args.system,
            limit=max(0, int(args.limit)),
        )
    except Exception as exc:
        print(
            "PrivyHub game metadata update failed: " + str(exc),
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        counts = report["counts"]
        print("PrivyHub game metadata update complete")
        print("Games scanned: " + str(counts["total_games"]))
        print("Matched: " + str(counts["matched"]))
        print("Ambiguous: " + str(counts["ambiguous"]))
        print("No match: " + str(counts["no_match"]))
        print("Artwork downloaded: " + str(counts["artwork_downloaded"]))
        print("Artwork already cached: " + str(counts["artwork_cached"]))
        print("Summary log: " + str(report["text_log_path"]))
        print(
            "Detailed log: "
            + str(PROJECT_ROOT / "logs" / "games" / "game_metadata_update.json")
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
