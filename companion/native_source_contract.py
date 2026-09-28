"""C6-D1: the generalized native source contract, as interfaces only.

Architecture record: `docs/memory/architecture/NATIVE_SOURCE_CONTRACT.md`.

**Nothing in production imports this module.** It names the four stages
every native source passes through -- source/capture, profile/encoder,
transport/FEC, client decoder feedback -- the lifecycle every source shares,
and the capability record a source must declare. `GamesSourceDescription`
fills that record from today's constants; it describes the games source,
it does not run it. The module must never import `native_stream` (the games
source's implementation): the unit test checks that it cannot drag
production in.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

import adaptive_bitrate
import native_fec_relay
import native_stream_profiles

CONTRACT_SCHEMA = "privyhub_native_source_contract_v1"


class SourceLifecycle(str, enum.Enum):
    """States every native source shares (C6: one lifecycle, many sources)."""

    IDLE = "IDLE"                # nothing running; no client session
    STARTING = "STARTING"        # capture, encoder and transport being brought up
    READY = "READY"              # first frame on the wire; client not yet playing
    PLAYING = "PLAYING"          # client reports frames rendered
    PAUSED = "PAUSED"            # source content held (games: core paused)
    RECOVERING = "RECOVERING"    # link lost; a source-defined recovery is running
    STOPPING = "STOPPING"
    FAILED = "FAILED"            # terminal for this session; reason exposed


class ActuatorClass(str, enum.Enum):
    """What a source may do to its own bitrate (`C3-L2`)."""

    NONE = "none"                                  # fixed profile only
    VIDEO_ONLY_RESTART = "video_only_restart"      # encoder restart; fallback/recovery only
    LIVE_BITRATE_RECONFIGURE = "live_bitrate_reconfigure"   # not available on Linux today


class AudioModel(str, enum.Enum):
    NONE = "none"
    SEPARATE_UDP_PCM = "separate_udp_pcm"          # games: own datagrams, redundancy, client cushion
    MUXED = "muxed"                                # audio inside the video transport (none today)


@dataclass(frozen=True)
class FecScheme:
    """A transport's FEC scheme, identified on the wire by its version byte (D114:
    identity from the packet, never from a setting)."""

    name: str
    wire_version: int
    group_size: int
    parities_per_group: int
    interleave_depth: int = 1


@dataclass(frozen=True)
class SourceCapabilities:
    """What every source must declare before a session starts."""

    source_kind: str
    capture_backend: str
    audio_model: AudioModel
    actuator_class: ActuatorClass
    validated_bitrates_kbps: tuple[int, ...]
    reference_bitrate_kbps: int
    supported_profiles: tuple[str, ...]
    fec_schemes: tuple[FecScheme, ...]
    client_input: str                       # the reverse path, source-specific
    diagnostics_identity_free: bool = True  # no source/request address in any field
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        """Contract checks; an empty list means the description conforms."""
        problems: list[str] = []
        if not self.source_kind or not self.capture_backend:
            problems.append("source_kind and capture_backend are required")
        if not self.supported_profiles:
            problems.append("at least one profile must be declared")
        if not self.fec_schemes:
            problems.append("at least one FEC scheme must be declared")
        if len({s.wire_version for s in self.fec_schemes}) != len(self.fec_schemes):
            problems.append("FEC wire versions must be unique (the client selects by version)")
        ladder = self.validated_bitrates_kbps
        if self.actuator_class is not ActuatorClass.NONE:
            if not ladder or list(ladder) != sorted(ladder):
                problems.append("an actuator needs an ascending validated ladder")
            if self.reference_bitrate_kbps not in ladder:
                problems.append("the reference bitrate must be a validated level")
        if not self.diagnostics_identity_free:
            problems.append("diagnostics must carry no address identity (D114)")
        return problems


@runtime_checkable
class SourceProfile(Protocol):
    """Profile/encoder stage: every stream parameter declared, none implied (C1)."""

    id: str
    width: int
    height: int
    fps: int
    bitrate_kbps: int
    max_bitrate_kbps: int
    gop_frames: int
    bframes: int

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class NativeSource(Protocol):
    """Source/capture + encoder: owns what is on screen and how it is encoded.

    Source-specific and outside the contract: the capture itself, audio
    buffering, and the input path back into the source."""

    def capabilities(self) -> SourceCapabilities: ...

    def lifecycle(self) -> SourceLifecycle: ...

    def start(self, profile: SourceProfile) -> None: ...

    def stop(self, reason: str) -> None: ...

    def status(self) -> Mapping[str, Any]: ...        # diagnostics, identity-free

    def set_bitrate(self, kbps: int, reason: str) -> Mapping[str, Any]:
        """Only for actuator_class != NONE; returns the transition's measured cost."""
        ...


@runtime_checkable
class Transport(Protocol):
    """Transport/FEC: what the transport owes every source."""

    def fec_scheme(self) -> FecScheme: ...

    def send(self, packet: bytes) -> None: ...

    def status(self) -> Mapping[str, Any]: ...        # counters only, no address


@runtime_checkable
class ClientFeedback(Protocol):
    """Client decoder feedback: heartbeat, telemetry snapshot, end-of-session report."""

    def telemetry(self) -> Mapping[str, Any]: ...     # privyhub_stream_telemetry_v1

    def heartbeat_rows(self) -> Sequence[Mapping[str, Any]]: ...

    def session_report(self) -> Mapping[str, Any] | None: ...


def _reference_profile() -> native_stream_profiles.NativeStreamProfile:
    return native_stream_profiles.NATIVE_GAME_720P60_REFERENCE


def games_source_description() -> SourceCapabilities:
    """The games source as it is today, from its own constants (not duplicated)."""
    profile = _reference_profile()
    return SourceCapabilities(
        source_kind="games",
        capture_backend="x11grab of the RetroArch window on the headless display (H2)",
        audio_model=AudioModel.SEPARATE_UDP_PCM,
        actuator_class=ActuatorClass(adaptive_bitrate_actuator_class()),
        validated_bitrates_kbps=tuple(adaptive_bitrate.LADDER_KBPS),
        reference_bitrate_kbps=profile.bitrate_kbps,
        supported_profiles=(profile.id,),
        fec_schemes=(
            FecScheme(
                name="xor8_1",
                wire_version=native_fec_relay.FEC_VERSION,
                group_size=profile.fec_group_size,
                parities_per_group=1,
            ),
        ),
        client_input="udp_full_state controller datagrams, 4 players (NativeControllerBridge)",
        notes=(
            f"profile fields: {sorted(profile.to_dict())}",
            "audio: redundancy copies/offset and the client cushion are profile fields",
        ),
    )


def adaptive_bitrate_actuator_class() -> str:
    """`C3-L2`: Linux is video_only_restart; the shadow controller holds no actuator."""
    return ActuatorClass.VIDEO_ONLY_RESTART.value


# The name the task uses.
GamesSourceDescription = games_source_description
