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

from games.cheat_importer import SYSTEM_SPECS, run_cheat_update  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Update PrivyHub's local game-cheat cache using the existing "
            "Games catalog and A6.3 metadata identity. This tool never "
            "activates cheats."
        )
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use only already-cached Libretro indexes and cheat files.",
    )
    parser.add_argument(
        "--refresh-provider-cache",
        action="store_true",
        help="Refresh Libretro cheat indexes even if seven-day cache is fresh.",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help=(
            "Match/report cheat coverage only. Do not alter managed cheat "
            "files or data/games/cheats.json."
        ),
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
        report = run_cheat_update(
            PROJECT_ROOT,
            offline=args.offline,
            refresh_provider_cache=args.refresh_provider_cache,
            download_files=not args.no_download,
            only_system=args.system,
            limit=max(0, int(args.limit)),
        )
    except Exception as exc:
        print(
            "PrivyHub game cheat update failed: " + str(exc),
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        counts = report["counts"]
        print("PrivyHub game cheat update complete")
        print("Games scanned: " + str(counts["total_games"]))
        print("Games with cheats: " + str(counts["games_with_cheats"]))
        print("Cheat files matched: " + str(counts["cheat_files_matched"]))
        print("No cheats: " + str(counts["no_cheats"]))
        print("Ambiguous: " + str(counts["ambiguous"]))
        print("Metadata missing: " + str(counts["metadata_missing"]))
        print("Cheat files downloaded: " + str(counts["cheat_files_downloaded"]))
        print("Activation: DISABLED")
        print("Summary log: " + str(report["text_log_path"]))
        print(
            "Detailed log: "
            + str(PROJECT_ROOT / "logs" / "games" / "game_cheat_update.json")
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
