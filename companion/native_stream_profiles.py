from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NativeStreamProfile:
    id: str
    width: int
    height: int
    fps: int
    bitrate_kbps: int
    max_bitrate_kbps: int
    gop_frames: int
    bframes: int
    fec_group_size: int

    def __post_init__(self) -> None:
        if not self.id or self.id != self.id.strip():
            raise ValueError("Native stream profile id must be non-empty and trimmed")

        for name in (
            "width",
            "height",
            "fps",
            "bitrate_kbps",
            "max_bitrate_kbps",
            "gop_frames",
        ):
            if int(getattr(self, name)) <= 0:
                raise ValueError(f"Native stream profile {name} must be positive")

        if self.max_bitrate_kbps < self.bitrate_kbps:
            raise ValueError(
                "Native stream profile max_bitrate_kbps must be >= bitrate_kbps"
            )

        if self.bframes < 0:
            raise ValueError("Native stream profile bframes must be >= 0")

        if self.fec_group_size < 1 or self.fec_group_size > 8:
            raise ValueError(
                "Native stream profile fec_group_size must be between 1 and 8"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "bitrate_kbps": self.bitrate_kbps,
            "max_bitrate_kbps": self.max_bitrate_kbps,
            "gop_frames": self.gop_frames,
            "bframes": self.bframes,
            "fec_group_size": self.fec_group_size,
        }


NATIVE_GAME_720P60_REFERENCE = NativeStreamProfile(
    id="native_game_720p60_reference",
    width=1280,
    height=720,
    fps=60,
    bitrate_kbps=7000,
    max_bitrate_kbps=7000,
    gop_frames=15,
    bframes=0,
    fec_group_size=8,
)
