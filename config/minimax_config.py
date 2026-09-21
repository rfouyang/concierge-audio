"""MiniMax service configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MinimaxConfig:
    api_key: str
    api_base_url: str = "https://api.minimax.io"
    connect_timeout_seconds: float = 10.0
    read_timeout_seconds: float = 120.0
    voice_cache_seconds: int = 300
    max_segments: int = 50

    @classmethod
    def from_env(cls) -> "MinimaxConfig":
        return cls(
            api_key=os.getenv("MINIMAX_API_KEY", "").strip(),
            api_base_url=os.getenv(
                "MINIMAX_API_BASE_URL",
                "https://api.minimax.io",
            ).rstrip("/"),
            connect_timeout_seconds=float(
                os.getenv("MINIMAX_CONNECT_TIMEOUT_SECONDS", "10")
            ),
            read_timeout_seconds=float(
                os.getenv("MINIMAX_READ_TIMEOUT_SECONDS", "120")
            ),
            voice_cache_seconds=int(
                os.getenv(
                    "MINIMAX_VOICE_CACHE_SECONDS",
                    os.getenv("VOICE_CACHE_SECONDS", "300"),
                )
            ),
            max_segments=int(os.getenv("MINIMAX_MAX_SEGMENTS", "50")),
        )
