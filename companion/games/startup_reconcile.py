from __future__ import annotations

import json
import time

from collections.abc import Callable
from pathlib import Path
from typing import Any

from games.metadata_importer import (
    DEFAULT_PROVIDER_CACHE_TTL_SECONDS,
    run_metadata_update,
    scan_privyhub_games,
)


RETRY_INCOMPLETE_AFTER_SECONDS = DEFAULT_PROVIDER_CACHE_TTL_SECONDS
STARTUP_LOG_JSON = Path("logs/games/game_metadata_startup_reconcile.json")
STARTUP_LOG_TEXT = Path("logs/games/game_metadata_startup_reconcile.txt")

INCOMPLETE_MATCH_STATUSES = {
    "provider_unavailable",
}
INCOMPLETE_ARTWORK_STATUSES = {
    "invalid_payload",
    "missing",
    "missing_offline",
}


def _read_json_dict(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _game_ids(games: list[dict[str, Any]]) -> set[str]:
    return {
        str(game.get("id", "")).strip()
        for game in games
        if str(game.get("id", "")).strip()
    }


def _metadata_games(payload: dict[str, Any]) -> dict[str, Any]:
    games = payload.get("games", {})
    return games if isinstance(games, dict) else {}


def _incomplete_count(
    metadata_games: dict[str, Any],
    discovered_ids: set[str],
) -> int:
    incomplete = 0

    for game_id in discovered_ids:
        record = metadata_games.get(game_id)
        if not isinstance(record, dict):
            continue

        match = record.get("match", {})
        if not isinstance(match, dict):
            match = {}

        match_status = str(match.get("status", "")).strip().casefold()
        if match_status in INCOMPLETE_MATCH_STATUSES:
            incomplete += 1
            continue

        if match_status != "matched":
            continue

        artwork = record.get("artwork", {})
        if not isinstance(artwork, dict):
            artwork = {}

        artwork_status = str(
            artwork.get("status", "")
        ).strip().casefold()

        if artwork_status in INCOMPLETE_ARTWORK_STATUSES:
            incomplete += 1

    return incomplete


def _reconcile_decision(
    metadata: dict[str, Any],
    discovered_ids: set[str],
    *,
    now_unix_ms: int,
) -> dict[str, Any]:
    metadata_games = _metadata_games(metadata)
    metadata_ids = {str(game_id) for game_id in metadata_games}
    reasons: list[str] = []

    if not metadata:
        reasons.append("metadata_missing_or_invalid")

    if discovered_ids != metadata_ids:
        reasons.append("library_changed")

    incomplete_count = _incomplete_count(
        metadata_games,
        discovered_ids,
    )

    generated_unix_ms = 0
    try:
        generated_unix_ms = max(
            0,
            int(metadata.get("generated_unix_ms", 0)),
        )
    except (TypeError, ValueError):
        generated_unix_ms = 0

    age_ms = max(0, now_unix_ms - generated_unix_ms)
    retry_age_ms = RETRY_INCOMPLETE_AFTER_SECONDS * 1000

    if (
        incomplete_count > 0
        and (
            generated_unix_ms <= 0
            or age_ms >= retry_age_ms
        )
    ):
        reasons.append("incomplete_retry_due")

    return {
        "needed": bool(reasons),
        "reasons": reasons,
        "discovered_count": len(discovered_ids),
        "metadata_count": len(metadata_ids),
        "incomplete_count": incomplete_count,
        "generated_unix_ms": generated_unix_ms,
        "metadata_age_ms": age_ms,
    }


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _write_status(
    project_root: Path,
    payload: dict[str, Any],
) -> None:
    json_path = project_root / STARTUP_LOG_JSON
    text_path = project_root / STARTUP_LOG_TEXT

    _atomic_json_write(json_path, payload)

    reasons = payload.get("reasons", [])
    if not isinstance(reasons, list):
        reasons = []

    counts = payload.get("metadata_update_counts", {})
    if not isinstance(counts, dict):
        counts = {}

    lines = [
        "PrivyHub game metadata startup reconciliation",
        f"Result: {payload.get('result', 'UNKNOWN')}",
        f"Reason(s): {', '.join(str(item) for item in reasons) if reasons else '<none>'}",
        f"Discovered games: {payload.get('discovered_count', 0)}",
        f"Metadata entries before: {payload.get('metadata_count_before', 0)}",
        f"Incomplete entries before: {payload.get('incomplete_count_before', 0)}",
        f"Metadata update invoked: {bool(payload.get('metadata_update_invoked', False))}",
        f"Catalog cache invalidated: {bool(payload.get('catalog_cache_invalidated', False))}",
    ]

    if counts:
        lines.extend(
            [
                f"Updater games scanned: {counts.get('total_games', 0)}",
                f"Updater matched: {counts.get('matched', 0)}",
                f"Updater ambiguous: {counts.get('ambiguous', 0)}",
                f"Updater no match: {counts.get('no_match', 0)}",
                f"Updater provider unavailable: {counts.get('provider_unavailable', 0)}",
                f"Updater prior preserved: {counts.get('prior_preserved', 0)}",
                f"Artwork downloaded: {counts.get('artwork_downloaded', 0)}",
                f"Artwork cached: {counts.get('artwork_cached', 0)}",
                f"Artwork missing: {counts.get('artwork_missing', 0)}",
            ]
        )

    error = str(payload.get("error", "")).strip()
    if error:
        lines.append(f"Error: {error}")

    lines.append(
        "Privacy: startup summary contains counts only; ROM filenames/titles are omitted."
    )

    text_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = text_path.with_name(text_path.name + ".tmp")
    temporary.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(text_path)


def run_startup_metadata_reconcile(
    project_root: Path,
    invalidate_cache: Callable[[], None],
) -> None:
    project_root = project_root.resolve()
    now_ms = int(time.time() * 1000)

    running = {
        "schema": 1,
        "result": "RUNNING",
        "generated_unix_ms": now_ms,
        "reasons": [],
        "discovered_count": 0,
        "metadata_count_before": 0,
        "incomplete_count_before": 0,
        "metadata_update_invoked": False,
        "catalog_cache_invalidated": False,
    }

    try:
        _write_status(project_root, running)

        games = scan_privyhub_games(project_root)
        discovered_ids = _game_ids(games)

        metadata_path = (
            project_root
            / "data"
            / "games"
            / "metadata.json"
        )
        metadata = _read_json_dict(metadata_path)
        decision = _reconcile_decision(
            metadata,
            discovered_ids,
            now_unix_ms=now_ms,
        )

        base = {
            "schema": 1,
            "generated_unix_ms": int(time.time() * 1000),
            "reasons": list(decision["reasons"]),
            "discovered_count": int(decision["discovered_count"]),
            "metadata_count_before": int(decision["metadata_count"]),
            "incomplete_count_before": int(decision["incomplete_count"]),
            "metadata_update_invoked": False,
            "catalog_cache_invalidated": False,
        }

        if not decision["needed"]:
            payload = {
                **base,
                "result": "SKIPPED_CURRENT",
            }
            _write_status(project_root, payload)
            print(
                "PrivyHub game metadata startup reconciliation: "
                "SKIPPED_CURRENT"
            )
            return

        report = run_metadata_update(
            project_root,
            offline=False,
            refresh_provider_cache=False,
            download_artwork=True,
        )

        counts = report.get("counts", {})
        if not isinstance(counts, dict):
            counts = {}

        invalidate_cache()

        payload = {
            **base,
            "result": "RECONCILED",
            "generated_unix_ms": int(time.time() * 1000),
            "metadata_update_invoked": True,
            "catalog_cache_invalidated": True,
            "metadata_update_counts": {
                key: int(counts.get(key, 0) or 0)
                for key in (
                    "total_games",
                    "matched",
                    "ambiguous",
                    "no_match",
                    "provider_unavailable",
                    "prior_preserved",
                    "artwork_downloaded",
                    "artwork_cached",
                    "artwork_missing",
                    "errors",
                )
            },
        }
        _write_status(project_root, payload)
        print(
            "PrivyHub game metadata startup reconciliation: "
            f"RECONCILED ({payload['metadata_update_counts']['total_games']} games)"
        )

    except Exception as exc:
        payload = {
            **running,
            "result": "FAILED",
            "generated_unix_ms": int(time.time() * 1000),
            "error": f"{type(exc).__name__}: {exc}",
        }
        try:
            _write_status(project_root, payload)
        except Exception:
            pass
        print(
            "PrivyHub game metadata startup reconciliation: "
            f"FAILED ({type(exc).__name__})"
        )
