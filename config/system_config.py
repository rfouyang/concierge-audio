"""System-level Flask and Unitree G1 audio configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemConfig:
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000
    flask_debug: bool = False
    max_content_length: int = 2 * 1024 * 1024
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_sample_width_bytes: int = 2

    @classmethod
    def from_env(cls) -> "SystemConfig":
        return cls(
            flask_host=os.getenv("FLASK_HOST", "127.0.0.1"),
            flask_port=int(os.getenv("FLASK_PORT", "5000")),
            flask_debug=_read_bool("FLASK_DEBUG", False),
        )


def _read_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}
