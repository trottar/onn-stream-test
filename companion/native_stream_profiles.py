from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# D-BASE-P9: the client allocates its audio queue at this bound
# (`NativeAudioReceiver.MAX_QUEUE_PACKETS`, 32 x 5 ms = 160 ms).
AUDIO_QUEUE_MAX_PACKETS = 32
AUDIO_PACKET_MS = 5
# D-BASE-P10: the client's de-duplication window is 64 sequences and it
# holds at most 2 + offset placeholders per gap; 16 ticks = 80 ms.
AUDIO_REDUNDANCY_MAX_OFFSET = 16


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

    # D-BASE-P9, the user's decision of 2026-09-23: the client's audio
    # cushion, in 5 ms packets, passed to the client in the stream-start
    # response (`audio_cushion`). The TARGET is the startup prefill; the
    # CAPACITY is the depth the running queue settles at (every arrival
    # hole is concealed, the late burst refills the queue to it), so the
    # capacity is what sets the steady audio latency. Defaults are the
    # client's historical 3 / 8. Overridable per session from the
    # environment (`PRIVYHUB_AUDIO_QUEUE_{TARGET,CAPACITY}_PACKETS`).
    audio_queue_target_packets: int = 3
    audio_queue_capacity_packets: int = 8

    # D-BASE-P10: audio redundancy. With copies = 2 the host sender sends
    # every audio datagram a second time `offset_packets` 5 ms ticks later
    # (same sequence, timestamp and payload) and the client keeps the first
    # to arrive. T3 located the warm-state audio loss between the ends,
    # where neither end can recover the same packet; a copy can. copies = 1
    # is off. Overridable per session from the environment
    # (`PRIVYHUB_AUDIO_REDUNDANCY_{COPIES,OFFSET_PACKETS}`).
    audio_redundancy_copies: int = 1
    audio_redundancy_offset_packets: int = 4

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

        if not (
            1
            <= self.audio_queue_target_packets
            <= self.audio_queue_capacity_packets
            <= AUDIO_QUEUE_MAX_PACKETS
        ):
            raise ValueError(
                "Native stream profile audio queue must satisfy "
                f"1 <= target <= capacity <= {AUDIO_QUEUE_MAX_PACKETS}"
            )

        if self.audio_redundancy_copies not in (1, 2):
            raise ValueError(
                "Native stream profile audio_redundancy_copies must be 1 or 2"
            )

        if not 1 <= self.audio_redundancy_offset_packets <= AUDIO_REDUNDANCY_MAX_OFFSET:
            raise ValueError(
                "Native stream profile audio_redundancy_offset_packets must be "
                f"between 1 and {AUDIO_REDUNDANCY_MAX_OFFSET}"
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
            "audio_queue_target_packets": self.audio_queue_target_packets,
            "audio_queue_capacity_packets": self.audio_queue_capacity_packets,
            "audio_redundancy_copies": self.audio_redundancy_copies,
            "audio_redundancy_offset_packets": self.audio_redundancy_offset_packets,
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
    # D-BASE-P9 / P9a, ADOPTED by the user 2026-09-23 (D-BASE-T2 Part 0):
    # +9 packets of steady depth. Measured three times: starvation episodes
    # -98-99.5 % for +33.5-37.9 ms of queue residence; underruns inside
    # the 3 / 8 noise band. `decisions/D-BASE-P9_AUDIO_CUSHION.md`.
    audio_queue_target_packets=12,
    audio_queue_capacity_packets=17,
    # D-BASE-P10, ADOPTED by the user 2026-09-23: every audio datagram sent
    # twice, the copy 4 ticks (20 ms) later. Warm, interleaved: audio loss
    # -96.4 / -98.2 %, +1.6 Mbps on the wire; video rows unchanged or better.
    # `decisions/D-BASE-P10_AUDIO_REDUNDANCY.md`.
    audio_redundancy_copies=2,
    audio_redundancy_offset_packets=4,
)


# C5-M1 (2026-09-28): 1080p60 as a CAPABILITY CANDIDATE, never the default.
# Selectable only through PRIVYHUB_NATIVE_PROFILE_ID for comparison holds;
# nothing is adopted. Bitrate at bits-per-pixel parity with the adopted
# profile (7000 kbps at 1280x720x60 -> 15,750 at 1920x1080x60); the frame cap
# is the adopted 90,000 scaled by the bitrate ratio, rounded to 10 KB (above
# the IDR sizes measured offline at this bitrate). The audio cushion and
# redundancy are the adopted values, unchanged. Design, numbers and the
# pre-registered holds: evidence/C5_M1_1080P60_PROFILE_2026-09-28.md.
NATIVE_GAME_1080P60_CANDIDATE = NativeStreamProfile(
    id="native_game_1080p60_candidate",
    width=1920,
    height=1080,
    fps=60,
    bitrate_kbps=15750,
    max_bitrate_kbps=15750,
    gop_frames=15,
    bframes=0,
    fec_group_size=8,
    max_frame_size_bytes=200_000,
    audio_queue_target_packets=12,
    audio_queue_capacity_packets=17,
    audio_redundancy_copies=2,
    audio_redundancy_offset_packets=4,
)

# C5-M2 (2026-09-29): the three 1080p60 follow-up arms C5-M1 named, as
# CAPABILITY CANDIDATES, never the default; selectable only through
# PRIVYHUB_NATIVE_PROFILE_ID for comparison holds. Each is 1920x1080 @ 60,
# GOP 15 (the recovery contract: an IDR every 250 ms), no B-frames, FEC 8, the
# adopted audio cushion and redundancy; only the bitrate and the frame cap
# differ. c1 bounds the per-frame burst exactly as on 720p (the adopted 90 KB,
# <= ~75 packets) at parity bitrate; c2 is the bitrate lever alone (80 %, the
# cap scaled by C5-M1's ratio); c3 is both levers.
# Record: evidence/C5_M2_1080P60_FOLLOWUP_2026-09-29.md.
def _c5_1080p60(profile_id: str, bitrate_kbps: int, cap_bytes: int) -> NativeStreamProfile:
    return NativeStreamProfile(
        id=profile_id,
        width=1920,
        height=1080,
        fps=60,
        bitrate_kbps=bitrate_kbps,
        max_bitrate_kbps=bitrate_kbps,
        gop_frames=15,
        bframes=0,
        fec_group_size=8,
        max_frame_size_bytes=cap_bytes,
        audio_queue_target_packets=12,
        audio_queue_capacity_packets=17,
        audio_redundancy_copies=2,
        audio_redundancy_offset_packets=4,
    )


NATIVE_GAME_1080P60_C1_PARITY_CAP90 = _c5_1080p60("native_game_1080p60_c1_parity_cap90", 15750, 90_000)
NATIVE_GAME_1080P60_C2_80PCT_CAP160 = _c5_1080p60("native_game_1080p60_c2_80pct_cap160", 12600, 160_000)
NATIVE_GAME_1080P60_C3_80PCT_CAP90 = _c5_1080p60("native_game_1080p60_c3_80pct_cap90", 12600, 90_000)

# C5-M3 (2026-09-29): three LOW rungs screened for Phase G's remote transport,
# never the default and never on the live ladder (5000-7000); selectable only
# through PRIVYHUB_NATIVE_PROFILE_ID. GOP 15, bframes 0, FEC 8, the adopted
# cushion and redundancy, and the adopted 90,000-byte cap in every arm, so the
# bitrate or the size is the only lever. The client needs no change: its
# decoder is configured with 1280x720 as a hint and the stream's own SPS sets
# the decoded size; the full-screen SurfaceView is scaled by the compositor.
# Record: evidence/C5_M3_LOW_RUNG_SCREENING_2026-09-29.md.
def _c5_low_rung(profile_id: str, width: int, height: int, bitrate_kbps: int) -> NativeStreamProfile:
    return NativeStreamProfile(
        id=profile_id,
        width=width,
        height=height,
        fps=60,
        bitrate_kbps=bitrate_kbps,
        max_bitrate_kbps=bitrate_kbps,
        gop_frames=15,
        bframes=0,
        fec_group_size=8,
        max_frame_size_bytes=90_000,
        audio_queue_target_packets=12,
        audio_queue_capacity_packets=17,
        audio_redundancy_copies=2,
        audio_redundancy_offset_packets=4,
    )


NATIVE_GAME_720P60_4000 = _c5_low_rung("native_game_720p60_4000", 1280, 720, 4000)
NATIVE_GAME_720P60_3000 = _c5_low_rung("native_game_720p60_3000", 1280, 720, 3000)
NATIVE_GAME_540P60_3500 = _c5_low_rung("native_game_540p60_3500", 960, 540, 3500)

# C5-M1: the profile selector. Unset or empty -> the adopted reference
# profile, exactly as before the selector existed. A known id -> that
# profile, and the companion reports it as an override. An unknown id ->
# the adopted profile, flagged `profile_id_ignored` (never a guess).
PROFILE_ID_ENV = "PRIVYHUB_NATIVE_PROFILE_ID"
NATIVE_STREAM_PROFILES: dict[str, NativeStreamProfile] = {
    profile.id: profile
    for profile in (
        NATIVE_GAME_720P60_REFERENCE,
        NATIVE_GAME_1080P60_CANDIDATE,
        NATIVE_GAME_1080P60_C1_PARITY_CAP90,
        NATIVE_GAME_1080P60_C2_80PCT_CAP160,
        NATIVE_GAME_1080P60_C3_80PCT_CAP90,
        NATIVE_GAME_720P60_4000,
        NATIVE_GAME_720P60_3000,
        NATIVE_GAME_540P60_3500,
    )
}


def select_native_profile(
    environ: Any,
) -> tuple[NativeStreamProfile, dict[str, Any]]:
    """The profile a stream uses, and how it was chosen."""

    requested = str(environ.get(PROFILE_ID_ENV, "") or "").strip()

    if not requested:
        return NATIVE_GAME_720P60_REFERENCE, {
            "env": PROFILE_ID_ENV,
            "requested": None,
            "source": "default",
            "profile_id": NATIVE_GAME_720P60_REFERENCE.id,
            "profile_id_ignored": False,
        }

    profile = NATIVE_STREAM_PROFILES.get(requested)

    return (profile or NATIVE_GAME_720P60_REFERENCE), {
        "env": PROFILE_ID_ENV,
        "requested": requested,
        "source": PROFILE_ID_ENV if profile is not None else "default",
        "profile_id": (profile or NATIVE_GAME_720P60_REFERENCE).id,
        "profile_id_ignored": profile is None,
    }
