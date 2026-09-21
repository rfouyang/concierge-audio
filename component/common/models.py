"""Provider-neutral models and errors shared by audio workflows."""

from __future__ import annotations

from dataclasses import dataclass


class ConciergeAudioError(Exception):
    """Base class for expected application errors."""


class ValidationError(ConciergeAudioError):
    """Raised when an application request is not valid."""


class ConfigurationError(ConciergeAudioError):
    """Raised when required service configuration is missing."""


class AudioValidationError(ConciergeAudioError):
    """Raised when generated audio is not valid for Unitree G1 playback."""


@dataclass(frozen=True, slots=True)
class WavInfo:
    """Verified WAV properties."""

    sample_rate: int
    channels: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class GeneratedAudio:
    """Successful synthesis result returned to the app layer."""

    audio: bytes
    trace_id: str
    wav_info: WavInfo
    usage_characters: int | None
    synthesis_details: dict | None = None
