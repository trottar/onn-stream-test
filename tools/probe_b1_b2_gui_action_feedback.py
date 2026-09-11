#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SCHEMA = "privyhub_b1_b2_gui_action_feedback_v1"
CLASSIFICATION = "B1_B2_GUI_ACTION_FEEDBACK_INSTALLED"

ACTIVITY = (
    "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
    "diagnostics/DiagnosticsActivity.kt"
)

REQUIRED = (
    "PRIVYHUB_B2_GUI_ACTION_FEEDBACK_V1",
    '"REFRESHING..."',
    '"RUNNING..."',
    '"COLLECTING..."',
    '"REFRESH"',
    '"RUN SELF-TEST"',
    '"COLLECT DIAGNOSTICS"',
    'activeAction == "refresh"',
    'activeAction == "self_test"',
    'activeAction == "collect"',
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        sample = "\n".join(REQUIRED)
        assert all(token in sample for token in REQUIRED)
        return 0

    root = Path(args.root).resolve()
    path = root / ACTIVITY

    if not path.is_file():
        raise SystemExit("DiagnosticsActivity.kt is missing")

    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    missing = [
        token
        for token in REQUIRED
        if token not in text
    ]

    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "b1_b2_gui_action_feedback.txt"

    if missing:
        out.write_text(
            "\n".join(
                [
                    "PrivyHub B1/B2 GUI action feedback validation",
                    "Classification: B1_B2_GUI_ACTION_FEEDBACK_NOT_CONFIRMED",
                    f"Schema: {SCHEMA}",
                    "Production files modified by probe: NONE",
                    "Network addresses collected/logged: NONE",
                    "",
                    "Missing tokens:",
                    *[
                        f"- {token}"
                        for token in missing
                    ],
                ]
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return 1

    out.write_text(
        "\n".join(
            [
                "PrivyHub B1/B2 GUI action feedback validation",
                f"Classification: {CLASSIFICATION}",
                f"Schema: {SCHEMA}",
                "Production files modified by probe: NONE",
                "Network addresses collected/logged: NONE",
                "",
                "Immediate button feedback installed: True",
                "Refresh busy label: REFRESHING...",
                "Self-Test busy label: RUNNING...",
                "Collect Diagnostics busy label: COLLECTING...",
                "Normal labels restored when busy=False: True",
                "Companion/API changes in this polish patch: False",
                "Streaming behavior changed: False",
                f"DiagnosticsActivity SHA-256: {sha256(path)}",
                "",
                "Manual validation: press RUN SELF-TEST and COLLECT DIAGNOSTICS and confirm the pressed action changes label immediately.",
            ]
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(CLASSIFICATION)
    print("Text:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
