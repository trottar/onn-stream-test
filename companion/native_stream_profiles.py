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

    # D-BASE-P6a, adopted 2026-09-22 on D-BASE-P6 evidence: the largest
    # single encoded frame, in bytes. 0 means uncapped.
    #
    # This is a transport parameter wearing an encoder's clothes. The loss
    # on this link is a per-frame micro-burst meeting the wireless queue,
    # and the burst is the frame; capping the frame removed 100 % of the
    # >= 80-packet frames and 7-9x of the loss with no measurable cost in
    # bitrate, fps, encoder CPU or GPU power. It belongs beside the other
    # static stream parameters for the same reason they do: it is part of
    # what makes this profile deliverable over one wireless hop.
    #
    # **Honoured by the `h264_vaapi` (Linux) builder only.** The deferred
    # Windows NVENC path logs that it ignores the field rather than
    # inventing a translation for it.
    max_frame_size_bytes: int = 0

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

        if self.max_frame_size_bytes < 0:
            raise ValueError(
                "Native stream profile max_frame_size_bytes must be >= 0"
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
            "max_frame_size_bytes": self.max_frame_size_bytes,
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
    # D-BASE-P6a: adopted 2026-09-22. See the field's note above and
    # `decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.
    max_frame_size_bytes=90_000,
)
