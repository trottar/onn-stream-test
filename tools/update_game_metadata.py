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

from games.metadata_importer import (  # noqa: E402
    run_metadata_dry_run,
    run_metadata_update,
    system_specs,
)


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
        choices=sorted(system_specs()),   # B76: the three more with PRIVYHUB_ART_SYSTEMS=1
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "B76: report matched / unmatched counts per system and the misses "
            "as labels; no box art or per-title request, nothing written but "
            "the per-system list cache."
        ),
    )
    args = parser.parse_args()

    if args.dry_run:
        try:
            report = run_metadata_dry_run(
                PROJECT_ROOT,
                offline=args.offline,
                only_system=args.system,
            )
        except Exception as exc:
            print(
                "PrivyHub game metadata dry run failed: " + type(exc).__name__,
                file=sys.stderr,
            )
            return 1
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("PrivyHub game metadata dry run (nothing fetched per title)")
            for system_id, row in sorted(report["systems"].items()):
                print(
                    f"{system_id}: {row['matched']} matched, "
                    f"{row['total'] - row['matched']} unmatched of {row['total']} "
                    f"(ambiguous {row['ambiguous']}, no match {row['no_match']}, "
                    f"list unavailable {row['provider_unavailable']})"
                )
                misses = report["misses"].get(system_id, [])
                if misses:
                    print("  misses: " + ", ".join(misses))
                # B82: the folder / list state, with B76's knob (the report then carries "listed")
                state = report.get("listed", {}).get(system_id, {})
                if state.get("folder") == "unavailable":
                    print("  folder unavailable (the drive or folder is not reachable)")
                if state.get("list") == "unavailable":
                    print("  list unavailable (RetroArch's list could not be read)")
            for system_id, count in sorted(report["not_offered"].items()):
                print(f"{system_id}: {count} not offered (system not in the fetcher's map)")
        return 0

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
