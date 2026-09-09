#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        required=True,
    )
    args = parser.parse_args()

    root = Path(
        args.root
    ).resolve()

    project = (
        root
        / "tools"
        / "a4_audio_mute_probe"
        / "A4AudioMuteProbe.csproj"
    )

    if not project.is_file():
        print(
            f"ERROR: probe project missing: {project}",
            file=sys.stderr,
        )
        return 1

    result = subprocess.run(
        [
            "dotnet",
            "run",
            "--project",
            str(project),
            "--configuration",
            "Release",
            "--no-build",
            "--",
            "--root",
            str(root),
        ],
        cwd=str(root),
        check=False,
    )

    return int(
        result.returncode
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
